#!/usr/bin/env python3
"""
Byzantine Majority Text DAG Builder

Creates a word-based directed acyclic graph (DAG) from the Koine Greek
Byzantine Majority Text. Downloads CSV files from the byztxt repository,
parses the Greek text, and builds a word transition graph.
"""

import csv
import json
import re
import urllib.request
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse


class ByzantineTextDAGBuilder:
    """Builds a word-based DAG from the Byzantine Majority Text"""

    # All NT books in the Byzantine text repository
    NT_BOOKS = [
        'MAT', 'MAR', 'LUK', 'JOH', 'ACT',  # Gospels and Acts
        'ROM', '1CO', '2CO', 'GAL', 'EPH', 'PHP', 'COL',  # Paul's letters
        '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM',
        'HEB', 'JAM', '1PE', '2PE', '1JO', '2JO', '3JO', 'JUD', 'REV'  # General epistles
    ]

    BASE_URL = "https://raw.githubusercontent.com/byztxt/byzantine-majority-text/master/csv-unicode/ccat/with-variants/"

    def __init__(self, books: List[str] = None, cache_dir: str = "data/byzantine"):
        """
        Initialize the Byzantine text DAG builder

        Args:
            books: List of book abbreviations to include (default: all NT)
            cache_dir: Directory to cache downloaded CSV files
        """
        self.books = books if books else self.NT_BOOKS
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Graph data structures
        self.word_transitions = defaultdict(Counter)  # word -> {next_word: count}
        self.word_frequencies = Counter()  # word -> total occurrences
        self.unique_words = set()
        self.book_stats = {}  # Statistics per book

    def download_book(self, book_abbr: str) -> Path:
        """
        Download a book's CSV file from the repository

        Args:
            book_abbr: Book abbreviation (e.g., 'MAT', 'JOH')

        Returns:
            Path to the downloaded CSV file
        """
        url = f"{self.BASE_URL}{book_abbr}.csv"
        cache_file = self.cache_dir / f"{book_abbr}.csv"

        # Use cached file if it exists
        if cache_file.exists():
            print(f"  Using cached: {book_abbr}.csv")
            return cache_file

        # Download the file
        print(f"  Downloading: {book_abbr}.csv")
        try:
            urllib.request.urlretrieve(url, cache_file)
            return cache_file
        except Exception as e:
            print(f"  Error downloading {book_abbr}: {e}")
            return None

    def clean_greek_text(self, text: str) -> str:
        """
        Clean Greek text by removing textual apparatus notation

        Args:
            text: Raw Greek text with apparatus notation

        Returns:
            Cleaned Greek text
        """
        # Remove {NA ...} apparatus notation
        text = re.sub(r'\{NA[^}]+\}', '', text)

        # Remove {WH ...} apparatus notation (if present)
        text = re.sub(r'\{WH[^}]+\}', '', text)

        # Remove {TR ...} apparatus notation (if present)
        text = re.sub(r'\{TR[^}]+\}', '', text)

        # Remove paragraph markers
        text = text.replace('¶', '')

        # Remove any remaining curly braces
        text = re.sub(r'[{}]', '', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        return text

    def tokenize_greek(self, text: str) -> List[str]:
        """
        Tokenize Greek text into words

        Args:
            text: Cleaned Greek text

        Returns:
            List of Greek word tokens
        """
        # Greek Unicode range includes combining diacritics
        # Keep only Greek letters and combining marks
        # This pattern preserves accents, breathings, etc.
        text = re.sub(r'[^\u0370-\u03FF\u1F00-\u1FFF\s]', ' ', text)

        # Split into words
        words = text.split()

        # Filter empty strings
        tokens = [word for word in words if word.strip()]

        return tokens

    def process_book(self, book_abbr: str) -> int:
        """
        Process a single book and add to the graph

        Args:
            book_abbr: Book abbreviation

        Returns:
            Number of words processed
        """
        csv_file = self.download_book(book_abbr)
        if not csv_file:
            return 0

        word_count = 0
        book_tokens = []

        # Read and parse CSV
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract and clean the Greek text
                raw_text = row.get('text', '')
                if not raw_text:
                    continue

                clean_text = self.clean_greek_text(raw_text)
                tokens = self.tokenize_greek(clean_text)
                book_tokens.extend(tokens)
                word_count += len(tokens)

        # Build transitions for this book
        for i in range(len(book_tokens) - 1):
            current_word = book_tokens[i]
            next_word = book_tokens[i + 1]

            # Track transition
            self.word_transitions[current_word][next_word] += 1

            # Track word frequency
            self.word_frequencies[current_word] += 1
            self.unique_words.add(current_word)

            # Also add the last word's frequency
            if i == len(book_tokens) - 2:
                self.word_frequencies[next_word] += 1
                self.unique_words.add(next_word)

        self.book_stats[book_abbr] = {
            'word_count': word_count,
            'unique_words': len(set(book_tokens))
        }

        print(f"  Processed {book_abbr}: {word_count} words, {len(set(book_tokens))} unique")
        return word_count

    def build_graph(self):
        """Build the word transition graph from all books"""
        print(f"Building DAG from {len(self.books)} books...")

        total_words = 0
        for book in self.books:
            words = self.process_book(book)
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
                "id": f"greek_{word}",
                "name": word,
                "type": "greek_word",
                "raw": {
                    "word": word,
                    "frequency": self.word_frequencies.get(word, 0),
                    "outgoing_transitions": len(self.word_transitions.get(word, {})),
                    "framework": "byzantine_text_flow"
                },
                "functions": [
                    {
                        "function_id": f"F-GREEK-{abs(hash(word)) % 100000:05d}",
                        "function_name": f"Token: {word}",
                        "description": f"Represents the Greek word '{word}' in the Byzantine text flow"
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
                    "source": f"greek_{source_word}",
                    "target": f"greek_{target_word}",
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
                "framework": "Byzantine Text Flow",
                "framework_id": "byzantine_greek_flow",
                "component_term": "greek_word",
                "connection_term": "transition",
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "tool_version": "1.0.0",
                "source": "Robinson-Pierpont Byzantine Majority Text",
                "source_repository": "https://github.com/byztxt/byzantine-majority-text",
                "books_included": self.books,
                "book_stats": self.book_stats,
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
    """Command-line interface for Byzantine text DAG builder"""
    parser = argparse.ArgumentParser(
        description='Build a word-based DAG from the Byzantine Majority Text (Koine Greek)'
    )
    parser.add_argument('-o', '--output', default='data/byzantine_text_dag.json',
                        help='Output JSON file path (default: data/byzantine_text_dag.json)')
    parser.add_argument('-b', '--books', nargs='+',
                        help='Specific books to process (default: all NT books)')
    parser.add_argument('--cache-dir', default='data/byzantine',
                        help='Directory to cache CSV files (default: data/byzantine)')
    parser.add_argument('--gospels-only', action='store_true',
                        help='Process only the four Gospels')
    parser.add_argument('--epistles-only', action='store_true',
                        help='Process only the Epistles')

    args = parser.parse_args()

    # Determine which books to process
    books = None
    if args.gospels_only:
        books = ['MAT', 'MAR', 'LUK', 'JOH']
    elif args.epistles_only:
        books = ['ROM', '1CO', '2CO', 'GAL', 'EPH', 'PHP', 'COL',
                '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM',
                'HEB', 'JAM', '1PE', '2PE', '1JO', '2JO', '3JO', 'JUD']
    elif args.books:
        books = [b.upper() for b in args.books]

    # Build the DAG
    print("Byzantine Majority Text DAG Builder")
    print("=" * 60)

    builder = ByzantineTextDAGBuilder(books=books, cache_dir=args.cache_dir)
    builder.build_graph()
    builder.save_graph(args.output)

    return 0


if __name__ == '__main__':
    exit(main())
