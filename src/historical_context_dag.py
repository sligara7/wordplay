"""
Historical Context DAG Builder

Builds a word transition graph from historical sources about Jesus and his time period,
including Roman historians (Tacitus, Pliny, Suetonius), Josephus, and Talmudic references.
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


class HistoricalContextDAGBuilder:
    """Build word transition DAG from historical context sources."""

    def __init__(self, sources_path: str = "data/historical_context_sources.json"):
        """
        Initialize the builder.

        Args:
            sources_path: Path to JSON file with historical sources
        """
        self.sources_path = Path(sources_path)
        self.sources = []
        self.word_transitions = defaultdict(Counter)  # word -> {next_word: count}
        self.word_frequencies = Counter()
        self.unique_words = set()
        self.source_stats = {}
        self.word_sources = defaultdict(set)  # Track which sources mention each word

    def load_sources(self):
        """Load historical sources from JSON file."""
        with open(self.sources_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.sources = data.get('sources', [])

        print(f"Loaded {len(self.sources)} historical sources")
        for source in self.sources:
            print(f"  - {source['title']} ({source['author']}, {source['date']})")

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of words
        """
        # Convert to lowercase
        text = text.lower()

        # Replace punctuation with spaces (except hyphens in words)
        text = re.sub(r'[^\w\s\-]', ' ', text)

        # Split on whitespace
        words = text.split()

        # Filter out empty strings and very short words
        words = [w for w in words if len(w) > 1]

        return words

    def build_transitions(self):
        """Build word transitions from all sources."""
        print("\nBuilding word transitions...")

        for source in self.sources:
            source_id = source['id']
            text = source['text']

            # Tokenize
            words = self.tokenize(text)

            # Track stats
            self.source_stats[source_id] = {
                'title': source['title'],
                'author': source['author'],
                'date': source['date'],
                'type': source['type'],
                'word_count': len(words),
                'unique_words': len(set(words))
            }

            # Build transitions
            for i in range(len(words) - 1):
                current_word = words[i]
                next_word = words[i + 1]

                # Track transitions
                self.word_transitions[current_word][next_word] += 1

                # Track word frequencies
                self.word_frequencies[current_word] += 1
                self.unique_words.add(current_word)

                # Track which sources mention each word
                self.word_sources[current_word].add(source_id)

            # Don't forget the last word
            if words:
                last_word = words[-1]
                self.word_frequencies[last_word] += 1
                self.unique_words.add(last_word)
                self.word_sources[last_word].add(source_id)

        print(f"✓ Built {len(self.word_transitions)} transition nodes")
        print(f"✓ Total unique words: {len(self.unique_words)}")

    def normalize_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Normalize transition counts to probabilities.

        Returns:
            Dict of word -> {next_word: probability}
        """
        normalized = {}

        for word, next_words in self.word_transitions.items():
            total_transitions = sum(next_words.values())
            normalized[word] = {
                next_word: count / total_transitions
                for next_word, count in next_words.items()
            }

        return normalized

    def to_graph_json(self, output_path: str):
        """
        Export to graph JSON format compatible with system-of-systems architecture.

        Args:
            output_path: Path to save JSON file
        """
        print(f"\nExporting to {output_path}...")

        normalized_weights = self.normalize_weights()

        # Build nodes
        nodes = []
        for word in self.unique_words:
            node = {
                'id': f'context_{word}',
                'name': word,
                'type': 'context_word',
                'raw': {
                    'word': word,
                    'frequency': self.word_frequencies.get(word, 0),
                    'outgoing_transitions': len(self.word_transitions.get(word, {})),
                    'sources': list(self.word_sources.get(word, set()))
                }
            }
            nodes.append(node)

        # Build edges
        links = []
        for word, next_words in self.word_transitions.items():
            for next_word, count in next_words.items():
                probability = normalized_weights[word][next_word]

                link = {
                    'source': f'context_{word}',
                    'target': f'context_{next_word}',
                    'type': 'word_transition',
                    'interaction_type': 'follows',
                    'weight': probability,
                    'raw': {
                        'transition_count': count,
                        'transition_probability': probability
                    }
                }
                links.append(link)

        # Count total transitions
        total_transitions = sum(
            sum(transitions.values())
            for transitions in self.word_transitions.values()
        )

        # Build metadata
        metadata = {
            'generated': datetime.now().isoformat(),
            'framework': 'Historical Context Flow',
            'framework_id': 'historical_context_flow',
            'component_term': 'context_word',
            'connection_term': 'transition',
            'num_nodes': len(nodes),
            'num_edges': len(links),
            'tool_version': '1.0.0',
            'source': 'Historical sources about Jesus and 1st century',
            'sources_included': [s['id'] for s in self.sources],
            'source_stats': self.source_stats,
            'total_tokens': sum(s['word_count'] for s in self.source_stats.values()),
            'unique_words': len(self.unique_words),
            'total_transitions': total_transitions
        }

        # Assemble full structure
        graph_data = {
            'metadata': metadata,
            'graph': {
                'directed': True,
                'multigraph': False,
                'nodes': nodes,
                'links': links
            }
        }

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported {len(nodes)} nodes and {len(links)} edges")
        print(f"✓ Saved to {output_path}")

    def print_stats(self):
        """Print statistics about the built graph."""
        print("\n" + "="*80)
        print("HISTORICAL CONTEXT DAG STATISTICS")
        print("="*80)

        print(f"\nTotal sources: {len(self.sources)}")
        print(f"Total unique words: {len(self.unique_words)}")
        print(f"Total word transitions: {sum(sum(t.values()) for t in self.word_transitions.values())}")

        print("\nSource breakdown:")
        for source_id, stats in self.source_stats.items():
            print(f"\n  {stats['title']}")
            print(f"    Author: {stats['author']}")
            print(f"    Date: {stats['date']}")
            print(f"    Type: {stats['type']}")
            print(f"    Words: {stats['word_count']}")
            print(f"    Unique: {stats['unique_words']}")

        # Most common words
        print("\nMost frequent words:")
        for word, count in self.word_frequencies.most_common(20):
            sources = len(self.word_sources[word])
            print(f"  {word}: {count} occurrences ({sources} sources)")


def main():
    """Build the historical context DAG."""
    builder = HistoricalContextDAGBuilder()

    print("="*80)
    print("BUILDING HISTORICAL CONTEXT DAG")
    print("="*80)

    # Load sources
    builder.load_sources()

    # Build transitions
    builder.build_transitions()

    # Print stats
    builder.print_stats()

    # Export
    output_path = "data/historical_context_dag.json"
    builder.to_graph_json(output_path)

    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)
    print(f"\nHistorical context DAG saved to: {output_path}")
    print("This can now be merged with Gospel DAGs for cross-source querying.")


if __name__ == '__main__':
    main()
