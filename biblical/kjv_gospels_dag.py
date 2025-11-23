#!/usr/bin/env python3
"""
KJV Gospels DAG Builder

Creates a word-based directed acyclic graph (DAG) from the King James Version
of the four Gospels. Downloads JSON files from the aruljohn/Bible-kjv repository,
parses the English text, and builds a word transition graph.
"""

import json
import re
import urllib.request
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import argparse


class KJVGospelsDAGBuilder:
    """Builds a word-based DAG from the KJV Gospels"""

    GOSPELS = {
        'Matthew': 'Matthew.json',
        'Mark': 'Mark.json',
        'Luke': 'Luke.json',
        'John': 'John.json'
    }

    BASE_URL = "https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/"

    def __init__(self, gospels: List[str] = None, cache_dir: str = "data/kjv",
                 min_word_length: int = 2, lowercase: bool = True):
        """
        Initialize the KJV gospels DAG builder

        Args:
            gospels: List of gospel names to include (default: all four)
            cache_dir: Directory to cache downloaded JSON files
            min_word_length: Minimum word length to include
            lowercase: Whether to convert all words to lowercase
        """
        if gospels is None:
            self.gospels = list(self.GOSPELS.keys())
        else:
            self.gospels = gospels

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.min_word_length = min_word_length
        self.lowercase = lowercase

        # Graph data structures
        self.word_transitions = defaultdict(Counter)  # word -> {next_word: count}
        self.word_frequencies = Counter()  # word -> total occurrences
        self.unique_words = set()
        self.gospel_stats = {}  # Statistics per gospel

    def download_gospel(self, gospel_name: str) -> Path:
        """
        Download a gospel's JSON file from the repository

        Args:
            gospel_name: Gospel name (e.g., 'Matthew', 'John')

        Returns:
            Path to the downloaded JSON file
        """
        filename = self.GOSPELS[gospel_name]
        url = f"{self.BASE_URL}{filename}"
        cache_file = self.cache_dir / filename

        # Use cached file if it exists
        if cache_file.exists():
            print(f"  Using cached: {gospel_name}")
            return cache_file

        # Download the file
        print(f"  Downloading: {gospel_name}")
        try:
            urllib.request.urlretrieve(url, cache_file)
            return cache_file
        except Exception as e:
            print(f"  Error downloading {gospel_name}: {e}")
            return None

    def tokenize_verse(self, text: str) -> List[str]:
        """
        Tokenize KJV verse text into words

        Args:
            text: KJV verse text

        Returns:
            List of word tokens
        """
        # Remove punctuation except apostrophes in contractions
        text = re.sub(r"[^\w\s']", ' ', text)

        # Split into words
        words = text.split()

        # Filter and clean words
        tokens = []
        for word in words:
            # Strip leading/trailing apostrophes
            word = word.strip("'")

            # Convert to lowercase if specified
            if self.lowercase:
                word = word.lower()

            # Filter by length
            if len(word) < self.min_word_length:
                continue

            # Keep only alphabetic words (no numbers)
            if not word.isalpha():
                continue

            tokens.append(word)

        return tokens

    def process_gospel(self, gospel_name: str) -> int:
        """
        Process a single gospel and add to the graph

        Args:
            gospel_name: Gospel name

        Returns:
            Number of words processed
        """
        json_file = self.download_gospel(gospel_name)
        if not json_file:
            return 0

        word_count = 0
        gospel_tokens = []

        # Read and parse JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract verses from all chapters
        for chapter in data.get('chapters', []):
            for verse in chapter.get('verses', []):
                text = verse.get('text', '')
                if not text:
                    continue

                tokens = self.tokenize_verse(text)
                gospel_tokens.extend(tokens)
                word_count += len(tokens)

        # Build transitions for this gospel
        for i in range(len(gospel_tokens) - 1):
            current_word = gospel_tokens[i]
            next_word = gospel_tokens[i + 1]

            # Track transition
            self.word_transitions[current_word][next_word] += 1

            # Track word frequency
            self.word_frequencies[current_word] += 1
            self.unique_words.add(current_word)

            # Also add the last word's frequency
            if i == len(gospel_tokens) - 2:
                self.word_frequencies[next_word] += 1
                self.unique_words.add(next_word)

        self.gospel_stats[gospel_name] = {
            'word_count': word_count,
            'unique_words': len(set(gospel_tokens))
        }

        print(f"  Processed {gospel_name}: {word_count} words, {len(set(gospel_tokens))} unique")
        return word_count

    def build_graph(self):
        """Build the word transition graph from all gospels"""
        print(f"Building DAG from {len(self.gospels)} gospels...")

        total_words = 0
        for gospel in self.gospels:
            words = self.process_gospel(gospel)
            total_words += words

        print(f"\nTotal words processed: {total_words}")
        print(f"Total unique words: {len(self.unique_words)}")

    def normalize_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Normalize transition counts to probabilities

        Returns:
            Dictionary of word -> {next_word: probability}
        """
        normalized = {}

        for word, transitions in self.word_transitions.items():
            total_transitions = sum(transitions.values())
            normalized[word] = {
                next_word: count / total_transitions
                for next_word, count in transitions.items()
            }

        return normalized

    def to_system_graph_json(self) -> dict:
        """
        Convert word graph to system_of_systems_graph.json format

        Returns:
            Dictionary compatible with reflow graph format
        """
        normalized_weights = self.normalize_weights()

        # Build nodes list
        nodes = []
        for word in sorted(self.unique_words):
            node = {
                "id": f"kjv_{word}",
                "name": word,
                "type": "english_word",
                "raw": {
                    "word": word,
                    "frequency": self.word_frequencies.get(word, 0),
                    "outgoing_transitions": len(self.word_transitions.get(word, {})),
                    "framework": "kjv_text_flow"
                },
                "functions": [
                    {
                        "function_id": f"F-KJV-{abs(hash(word)) % 100000:05d}",
                        "function_name": f"Token: {word}",
                        "description": f"Represents the English word '{word}' in the KJV text flow"
                    }
                ]
            }
            nodes.append(node)

        # Build edges list
        edges = []
        for source_word, transitions in self.word_transitions.items():
            for target_word, count in transitions.items():
                probability = normalized_weights[source_word][target_word]

                edge = {
                    "source": f"kjv_{source_word}",
                    "target": f"kjv_{target_word}",
                    "type": "word_transition",
                    "interaction_type": "follows",
                    "weight": probability,
                    "raw": {
                        "transition_count": count,
                        "transition_probability": probability,
                        "source_word": source_word,
                        "target_word": target_word
                    }
                }
                edges.append(edge)

        # Calculate total transitions
        total_transitions = sum(
            sum(transitions.values())
            for transitions in self.word_transitions.values()
        )

        # Build the complete graph structure
        graph = {
            "metadata": {
                "generated": datetime.utcnow().isoformat(),
                "framework": "KJV Text Flow",
                "framework_id": "kjv_english_flow",
                "component_term": "english_word",
                "connection_term": "transition",
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "tool_version": "1.0.0",
                "source": "King James Version (KJV) Bible",
                "source_repository": "https://github.com/aruljohn/Bible-kjv",
                "gospels_included": self.gospels,
                "gospel_stats": self.gospel_stats,
                "total_tokens": sum(self.word_frequencies.values()),
                "unique_words": len(self.unique_words),
                "total_transitions": total_transitions
            },
            "graph": {
                "directed": True,
                "multigraph": False,
                "graph": {},
                "nodes": nodes,
                "links": edges
            },
            "architectural_issues": {
                "circular_dependencies": [],
                "orphaned_nodes": [],
                "dead_ends": [],  # Words with no outgoing transitions
                "unreachable_words": []  # Words with no incoming transitions
            },
            "architectural_issues_summary": {
                "total_issues": 0,
                "by_type": {}
            }
        }

        # Analyze for dead ends and unreachable words
        words_with_outgoing = set(self.word_transitions.keys())
        words_with_incoming = set()
        for transitions in self.word_transitions.values():
            words_with_incoming.update(transitions.keys())

        dead_ends = self.unique_words - words_with_outgoing
        unreachable = self.unique_words - words_with_incoming

        graph["architectural_issues"]["dead_ends"] = sorted(dead_ends)
        graph["architectural_issues"]["unreachable_words"] = sorted(unreachable)

        issue_count = len(dead_ends) + len(unreachable)
        graph["architectural_issues_summary"]["total_issues"] = issue_count
        graph["architectural_issues_summary"]["by_type"] = {
            "dead_ends": len(dead_ends),
            "unreachable_words": len(unreachable)
        }

        return graph

    def save_graph(self, output_path: str):
        """
        Save the graph to a JSON file

        Args:
            output_path: Path to save the JSON file
        """
        graph = self.to_system_graph_json()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"Graph saved to: {output_path}")
        print(f"{'='*60}")
        print(f"  Nodes: {graph['metadata']['num_nodes']:,}")
        print(f"  Edges: {graph['metadata']['num_edges']:,}")
        print(f"  Total tokens: {graph['metadata']['total_tokens']:,}")
        print(f"  Unique words: {graph['metadata']['unique_words']:,}")
        print(f"  Dead ends: {len(graph['architectural_issues']['dead_ends']):,}")
        print(f"  Unreachable words: {len(graph['architectural_issues']['unreachable_words']):,}")
        print(f"{'='*60}")


def main():
    """Command-line interface for KJV gospels DAG builder"""
    parser = argparse.ArgumentParser(
        description='Build a word-based DAG from the KJV Gospels'
    )
    parser.add_argument('-o', '--output', default='data/kjv_gospels_dag.json',
                        help='Output JSON file path (default: data/kjv_gospels_dag.json)')
    parser.add_argument('-g', '--gospels', nargs='+',
                        choices=['Matthew', 'Mark', 'Luke', 'John'],
                        help='Specific gospels to process (default: all four)')
    parser.add_argument('--cache-dir', default='data/kjv',
                        help='Directory to cache JSON files (default: data/kjv)')
    parser.add_argument('-m', '--min-length', type=int, default=2,
                        help='Minimum word length (default: 2)')
    parser.add_argument('--keep-case', action='store_true',
                        help='Keep original case (default: lowercase all)')

    args = parser.parse_args()

    # Build the DAG
    print("KJV Gospels DAG Builder")
    print("=" * 60)

    builder = KJVGospelsDAGBuilder(
        gospels=args.gospels,
        cache_dir=args.cache_dir,
        min_word_length=args.min_length,
        lowercase=not args.keep_case
    )
    builder.build_graph()
    builder.save_graph(args.output)

    return 0


if __name__ == '__main__':
    exit(main())
