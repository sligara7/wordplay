#!/usr/bin/env python3
"""
MIDI Graph Builder - Extends word_graph_builder.py for musical tokens.

This module builds graphs from MIDI tokens (note names like 'C4', 'D#5', etc.)
using the same structure as word graphs but without alphabetic-only constraints.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict, Counter


class MidiGraphBuilder:
    """
    Build transition graphs from MIDI tokens.

    Similar to WordGraphBuilder but designed for musical tokens (notes, chords, etc.)
    which may contain numbers and special characters.
    """

    def __init__(self, min_token_length=1):
        """
        Initialize the MIDI graph builder.

        Args:
            min_token_length: Minimum token length to include (default: 1)
        """
        self.min_token_length = min_token_length
        self.tokens = []
        self.graph = {}
        self.token_frequencies = Counter()

    def tokenize(self, text: str) -> List[str]:
        """
        Parse tokens from text.

        Args:
            text: Space-separated tokens (e.g., "C4 D4 E4 F4")

        Returns:
            List of tokens
        """
        # Split on whitespace
        tokens = text.split()

        # Filter by length only (no alphabetic constraints)
        tokens = [t for t in tokens if len(t) >= self.min_token_length]

        return tokens

    def build_graph(self, tokens: List[str]) -> Dict:
        """
        Build a directed graph from token transitions.

        Args:
            tokens: List of tokens

        Returns:
            Dictionary mapping token -> {next_token: count}
        """
        graph = defaultdict(Counter)

        # Count transitions
        for i in range(len(tokens) - 1):
            current = tokens[i]
            next_token = tokens[i + 1]
            graph[current][next_token] += 1
            self.token_frequencies[current] += 1

        # Don't forget the last token
        if tokens:
            self.token_frequencies[tokens[-1]] += 1

        self.graph = dict(graph)
        return self.graph

    def normalize_weights(self) -> Dict:
        """
        Convert transition counts to probabilities.

        Returns:
            Dictionary mapping token -> {next_token: probability}
        """
        normalized = {}

        for token, transitions in self.graph.items():
            total = sum(transitions.values())
            normalized[token] = {
                next_token: count / total
                for next_token, count in transitions.items()
            }

        return normalized

    def to_system_graph_json(self, title="MIDI Graph") -> Dict:
        """
        Convert to system_of_systems_graph.json format for compatibility with analysis tools.

        Args:
            title: Title for the graph metadata

        Returns:
            Dictionary in system graph format
        """
        normalized = self.normalize_weights()

        # Build nodes list
        nodes = []
        for token in sorted(self.token_frequencies.keys()):
            node = {
                "id": f"note_{token}",
                "name": token,
                "type": "note",
                "raw": {
                    "token": token,
                    "frequency": self.token_frequencies[token],
                    "outgoing_transitions": len(self.graph.get(token, {}))
                }
            }
            nodes.append(node)

        # Build links list
        links = []
        for source_token, transitions in self.graph.items():
            total_transitions = sum(transitions.values())

            for target_token, count in transitions.items():
                probability = count / total_transitions

                link = {
                    "source": f"note_{source_token}",
                    "target": f"note_{target_token}",
                    "type": "note_transition",
                    "weight": round(probability, 4),
                    "raw": {
                        "transition_count": count,
                        "transition_probability": round(probability, 4)
                    }
                }
                links.append(link)

        # Calculate statistics
        dead_ends = sum(1 for token in self.token_frequencies if token not in self.graph)
        all_tokens = set(self.token_frequencies.keys())
        reachable = set()
        for transitions in self.graph.values():
            reachable.update(transitions.keys())
        unreachable = len(all_tokens - reachable - set([self.tokens[0]])) if self.tokens else 0

        # Build complete structure
        result = {
            "metadata": {
                "framework": "Musical Flow",
                "num_nodes": len(nodes),
                "num_edges": len(links),
                "unique_tokens": len(self.token_frequencies),
                "total_tokens": sum(self.token_frequencies.values()),
                "title": title,
                "dead_ends": dead_ends,
                "unreachable": unreachable
            },
            "graph": {
                "directed": True,
                "nodes": nodes,
                "links": links
            }
        }

        return result

    def save_graph(self, output_path: str, title="MIDI Graph"):
        """
        Save graph to JSON file.

        Args:
            output_path: Path to output JSON file
            title: Title for the graph
        """
        graph_data = self.to_system_graph_json(title)

        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)

        print(f"Graph saved to: {output_path}")
        print(f"  Nodes: {graph_data['metadata']['num_nodes']}")
        print(f"  Edges: {graph_data['metadata']['num_edges']}")
        print(f"  Total tokens: {graph_data['metadata']['total_tokens']}")
        print(f"  Unique tokens: {graph_data['metadata']['unique_tokens']}")
        print(f"  Dead ends: {graph_data['metadata']['dead_ends']}")
        print(f"  Unreachable: {graph_data['metadata']['unreachable']}")


def main():
    parser = argparse.ArgumentParser(
        description='Build transition graphs from MIDI tokens',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build graph from MIDI tokens
  python3 src/midi_graph_builder.py music/song_tokens.txt -o output/song_graph.json -t "My Song"

  # Analyze the graph
  python3 src/analyze_word_graph.py output/song_graph.json

  # Complete workflow (tokenize + build + analyze)
  python3 src/midi_tokenizer.py music/song.mid -o music/song_tokens.txt
  python3 src/midi_graph_builder.py music/song_tokens.txt -o output/song_graph.json
  python3 src/analyze_word_graph.py output/song_graph.json
        """
    )

    parser.add_argument('input_file', help='Path to token file (space-separated tokens)')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file')
    parser.add_argument('-t', '--title', default='MIDI Graph', help='Graph title')
    parser.add_argument(
        '-m', '--min-length',
        type=int,
        default=1,
        help='Minimum token length (default: 1)'
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read input file
    print(f"Building MIDI graph from: {args.input_file}")
    with open(input_path, 'r') as f:
        text = f.read()

    # Build graph
    builder = MidiGraphBuilder(min_token_length=args.min_length)
    tokens = builder.tokenize(text)
    builder.tokens = tokens

    print(f"Tokenized: {len(tokens)} tokens")

    if not tokens:
        print("Warning: No tokens found after filtering")
        return 1

    builder.build_graph(tokens)
    builder.save_graph(args.output, title=args.title)

    print(f"\nNext step:")
    print(f"  Analyze: python3 src/analyze_word_graph.py {args.output}")

    return 0


if __name__ == '__main__':
    exit(main())
