#!/usr/bin/env python3
"""
Word Graph Builder - Creates directed graphs from book text

Tokenizes words in a text and builds a directed graph where:
- Nodes: Individual words (tokens)
- Edges: Word transitions (word A followed by word B)
- Edge weights: Transition counts (normalized to probabilities)

Output format compatible with reflow's system_of_systems_graph.json
"""

import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Set
import argparse
from pathlib import Path


class WordGraphBuilder:
    """Builds a directed word transition graph from text"""

    def __init__(self, text: str, book_title: str = "Untitled",
                 min_word_length: int = 2,
                 lowercase: bool = True,
                 remove_stopwords: bool = False):
        """
        Initialize the word graph builder

        Args:
            text: The text to analyze
            book_title: Title of the book/text
            min_word_length: Minimum word length to include
            lowercase: Whether to convert all words to lowercase
            remove_stopwords: Whether to remove common stopwords
        """
        self.text = text
        self.book_title = book_title
        self.min_word_length = min_word_length
        self.lowercase = lowercase
        self.remove_stopwords = remove_stopwords

        # Graph data structures
        self.word_transitions = defaultdict(Counter)  # word -> {next_word: count}
        self.word_frequencies = Counter()  # word -> total occurrences
        self.unique_words = set()

        # Common English stopwords (basic list)
        self.stopwords = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
            'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
            'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over',
            'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work',
            'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
            'give', 'day', 'most', 'us', 'is', 'was', 'are', 'been', 'has', 'had',
            'were', 'said', 'did', 'having', 'may', 'should', 'am'
        }

    def tokenize(self) -> List[str]:
        """
        Tokenize the text into words

        Returns:
            List of word tokens
        """
        # Remove punctuation except apostrophes in contractions
        # This preserves words like "don't", "isn't", etc.
        text = re.sub(r"[^\w\s']", ' ', self.text)

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

            # Filter stopwords if specified
            if self.remove_stopwords and word.lower() in self.stopwords:
                continue

            # Keep only alphabetic words (no numbers)
            if not word.isalpha():
                continue

            tokens.append(word)

        return tokens

    def build_graph(self):
        """Build the word transition graph from the text"""
        tokens = self.tokenize()

        # Build transitions and frequencies
        for i in range(len(tokens) - 1):
            current_word = tokens[i]
            next_word = tokens[i + 1]

            # Track transition
            self.word_transitions[current_word][next_word] += 1

            # Track word frequency
            self.word_frequencies[current_word] += 1
            self.unique_words.add(current_word)

            # Also add the last word's frequency
            if i == len(tokens) - 2:
                self.word_frequencies[next_word] += 1
                self.unique_words.add(next_word)

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
                "id": f"word_{word}",
                "name": word,
                "type": "word",
                "raw": {
                    "word": word,
                    "frequency": self.word_frequencies.get(word, 0),
                    "outgoing_transitions": len(self.word_transitions.get(word, {})),
                    "framework": "language_flow"
                },
                "functions": [
                    {
                        "function_id": f"F-{word.upper()}-01",
                        "function_name": f"Token: {word}",
                        "description": f"Represents the word '{word}' in the text flow"
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
                    "source": f"word_{source_word}",
                    "target": f"word_{target_word}",
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
                "framework": "Language Flow",
                "framework_id": "language_flow",
                "component_term": "word",
                "connection_term": "transition",
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "tool_version": "1.0.0",
                "book_title": self.book_title,
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

        print(f"Graph saved to: {output_path}")
        print(f"  Nodes: {graph['metadata']['num_nodes']}")
        print(f"  Edges: {graph['metadata']['num_edges']}")
        print(f"  Total tokens: {graph['metadata']['total_tokens']}")
        print(f"  Unique words: {graph['metadata']['unique_words']}")
        print(f"  Dead ends: {len(graph['architectural_issues']['dead_ends'])}")
        print(f"  Unreachable words: {len(graph['architectural_issues']['unreachable_words'])}")


def main():
    """Command-line interface for word graph builder"""
    parser = argparse.ArgumentParser(
        description='Build a word transition graph from text file'
    )
    parser.add_argument('input_file', help='Path to text file')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-t', '--title', help='Book title', default='Untitled')
    parser.add_argument('-m', '--min-length', type=int, default=2,
                        help='Minimum word length (default: 2)')
    parser.add_argument('--keep-case', action='store_true',
                        help='Keep original case (default: lowercase all)')
    parser.add_argument('--remove-stopwords', action='store_true',
                        help='Remove common stopwords')

    args = parser.parse_args()

    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}")
        return 1

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: same directory as input, with .json extension
        output_path = input_path.parent / f"{input_path.stem}_graph.json"

    # Build graph
    print(f"Building word graph from: {input_path}")
    print(f"Book title: {args.title}")

    builder = WordGraphBuilder(
        text=text,
        book_title=args.title,
        min_word_length=args.min_length,
        lowercase=not args.keep_case,
        remove_stopwords=args.remove_stopwords
    )

    builder.build_graph()
    builder.save_graph(str(output_path))

    return 0


if __name__ == '__main__':
    exit(main())
