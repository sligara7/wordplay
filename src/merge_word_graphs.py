#!/usr/bin/env python3
"""
Merge Word Graphs - Combine word networks from multiple books

Uses techniques inspired by chain_reflow to merge word graphs from different books.
Identifies common words and compares transition probabilities.

This is particularly interesting for orthogonal books (different genres/topics)
to see how they find commonality in language structure.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple


class WordGraphMerger:
    """Merges word graphs from multiple books"""

    def __init__(self, graph_paths: List[str]):
        """
        Initialize the merger

        Args:
            graph_paths: List of paths to word graph JSON files
        """
        self.graph_paths = graph_paths
        self.graphs = []
        self.metadata = []

    def load_graphs(self):
        """Load all graph files"""
        for path in self.graph_paths:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.graphs.append(data)
                self.metadata.append(data['metadata'])

        print(f"Loaded {len(self.graphs)} graphs")
        for i, meta in enumerate(self.metadata):
            print(f"  {i+1}. {meta.get('book_title', 'Unknown')}: "
                  f"{meta['num_nodes']} words, {meta['num_edges']} transitions")

    def identify_touchpoints(self) -> Dict:
        """
        Identify touchpoints between graphs - words that appear in multiple books

        Returns:
            Dictionary of touchpoint analysis
        """
        # Build word sets for each graph
        word_sets = []
        for graph in self.graphs:
            words = {node['name'] for node in graph['graph']['nodes']}
            word_sets.append(words)

        # Find intersections
        touchpoints = {
            'common_to_all': set.intersection(*word_sets) if word_sets else set(),
            'pairwise_common': {},
            'unique_to_each': {}
        }

        # Pairwise intersections
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                title_i = self.metadata[i].get('book_title', f'Book {i}')
                title_j = self.metadata[j].get('book_title', f'Book {j}')
                key = f"{title_i} ∩ {title_j}"
                touchpoints['pairwise_common'][key] = word_sets[i] & word_sets[j]

        # Unique words
        for i, words in enumerate(word_sets):
            others = set.union(*[ws for j, ws in enumerate(word_sets) if j != i])
            title = self.metadata[i].get('book_title', f'Book {i}')
            touchpoints['unique_to_each'][title] = words - others

        return touchpoints

    def merge_graphs(self, merge_strategy: str = 'union') -> Dict:
        """
        Merge multiple word graphs into one

        Args:
            merge_strategy: 'union' (all words) or 'intersection' (only common words)

        Returns:
            Merged graph in system_of_systems_graph.json format
        """
        # Collect all nodes and edges
        all_words = set()
        word_metadata = defaultdict(lambda: {
            'frequency': 0,
            'appears_in': [],
            'source_graphs': []
        })

        # Collect transitions and their weights from each graph
        transitions = defaultdict(lambda: defaultdict(list))

        for idx, graph in enumerate(self.graphs):
            book_title = self.metadata[idx].get('book_title', f'Book {idx}')

            # Process nodes
            for node in graph['graph']['nodes']:
                word = node['name']
                all_words.add(word)
                word_metadata[word]['frequency'] += node['raw'].get('frequency', 0)
                word_metadata[word]['appears_in'].append(book_title)
                word_metadata[word]['source_graphs'].append(idx)

            # Process edges (transitions)
            for edge in graph['graph']['links']:
                source = edge['source'].replace('word_', '')
                target = edge['target'].replace('word_', '')
                prob = edge.get('weight', 0)
                count = edge['raw'].get('transition_count', 0)

                transitions[source][target].append({
                    'book': book_title,
                    'probability': prob,
                    'count': count
                })

        # Apply merge strategy
        if merge_strategy == 'intersection':
            # Only keep words that appear in all graphs
            common_words = set.intersection(*[
                {node['name'] for node in graph['graph']['nodes']}
                for graph in self.graphs
            ])
            all_words = common_words

        # Build merged nodes
        nodes = []
        for word in sorted(all_words):
            node_id = f"word_{word}"
            meta = word_metadata[word]

            node = {
                "id": node_id,
                "name": word,
                "type": "word",
                "raw": {
                    "word": word,
                    "total_frequency": meta['frequency'],
                    "appears_in_books": meta['appears_in'],
                    "num_books": len(meta['appears_in']),
                    "framework": "language_flow"
                },
                "functions": [
                    {
                        "function_id": f"F-{word.upper()}-01",
                        "function_name": f"Token: {word}",
                        "description": f"Word '{word}' appears in {len(meta['appears_in'])} book(s)"
                    }
                ]
            }
            nodes.append(node)

        # Build merged edges
        edges = []
        for source_word in transitions:
            if source_word not in all_words:
                continue

            for target_word, transition_data in transitions[source_word].items():
                if target_word not in all_words:
                    continue

                # Average the probabilities across books
                avg_prob = sum(t['probability'] for t in transition_data) / len(transition_data)
                total_count = sum(t['count'] for t in transition_data)

                edge = {
                    "source": f"word_{source_word}",
                    "target": f"word_{target_word}",
                    "type": "word_transition",
                    "interaction_type": "follows",
                    "weight": avg_prob,
                    "raw": {
                        "merged_from": [t['book'] for t in transition_data],
                        "num_books": len(transition_data),
                        "average_probability": avg_prob,
                        "total_transition_count": total_count,
                        "probabilities_by_book": {
                            t['book']: t['probability']
                            for t in transition_data
                        }
                    }
                }
                edges.append(edge)

        # Build merged graph
        merged_graph = {
            "metadata": {
                "generated": datetime.utcnow().isoformat(),
                "framework": "Language Flow (Merged)",
                "framework_id": "language_flow",
                "component_term": "word",
                "connection_term": "transition",
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "tool_version": "1.0.0",
                "merge_strategy": merge_strategy,
                "source_books": [m.get('book_title', f'Book {i}') for i, m in enumerate(self.metadata)],
                "num_source_books": len(self.graphs)
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
                "dead_ends": [],
                "unreachable_words": []
            },
            "merge_analysis": {
                "common_words_count": len([n for n in nodes if n['raw']['num_books'] == len(self.graphs)]),
                "unique_words_count": len([n for n in nodes if n['raw']['num_books'] == 1]),
                "shared_transitions_count": len([e for e in edges if e['raw']['num_books'] > 1])
            }
        }

        return merged_graph

    def analyze_orthogonality(self, touchpoints: Dict) -> Dict:
        """
        Analyze how orthogonal (different) the books are

        Returns:
            Orthogonality analysis
        """
        total_unique_words = set()
        for graph in self.graphs:
            words = {node['name'] for node in graph['graph']['nodes']}
            total_unique_words.update(words)

        common_words = touchpoints['common_to_all']

        # Calculate Jaccard similarity for each pair
        similarities = {}
        for key, common in touchpoints['pairwise_common'].items():
            # Get the two book indices from the key
            books = key.split(' ∩ ')
            if len(books) == 2:
                # Find word sets for these books
                words1 = {node['name'] for node in self.graphs[0]['graph']['nodes']}
                words2 = {node['name'] for node in self.graphs[1]['graph']['nodes']}

                union = words1 | words2
                intersection = words1 & words2

                if union:
                    jaccard = len(intersection) / len(union)
                    similarities[key] = jaccard

        analysis = {
            "total_unique_words": len(total_unique_words),
            "words_common_to_all": len(common_words),
            "percentage_common": (len(common_words) / len(total_unique_words) * 100) if total_unique_words else 0,
            "jaccard_similarities": similarities,
            "orthogonality_score": 1.0 - (len(common_words) / len(total_unique_words)) if total_unique_words else 0,
            "interpretation": {
                "orthogonality_score": "0.0 = identical vocabulary, 1.0 = completely different vocabulary",
                "jaccard_similarity": "0.0 = no overlap, 1.0 = identical vocabulary"
            }
        }

        return analysis


def main():
    parser = argparse.ArgumentParser(
        description='Merge word graphs from multiple books'
    )
    parser.add_argument('graph_files', nargs='+', help='Word graph JSON files to merge')
    parser.add_argument('-o', '--output', help='Output merged graph file',
                        default='output/merged_graph.json')
    parser.add_argument('-s', '--strategy', choices=['union', 'intersection'],
                        default='union',
                        help='Merge strategy: union (all words) or intersection (common words only)')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Only analyze touchpoints, do not merge')

    args = parser.parse_args()

    print(f"Merging {len(args.graph_files)} word graphs...")

    merger = WordGraphMerger(args.graph_files)
    merger.load_graphs()

    print("\nIdentifying touchpoints...")
    touchpoints = merger.identify_touchpoints()

    print(f"\nTouchpoint Analysis:")
    print(f"  Words common to all books: {len(touchpoints['common_to_all'])}")

    if touchpoints['pairwise_common']:
        print(f"  Pairwise common words:")
        for key, words in touchpoints['pairwise_common'].items():
            print(f"    {key}: {len(words)} words")

    print(f"\n  Unique words per book:")
    for title, words in touchpoints['unique_to_each'].items():
        print(f"    {title}: {len(words)} unique words")

    # Orthogonality analysis
    print(f"\nOrthogonality Analysis:")
    ortho = merger.analyze_orthogonality(touchpoints)
    print(f"  Orthogonality score: {ortho['orthogonality_score']:.3f}")
    print(f"  (0.0 = identical vocabulary, 1.0 = completely different)")

    if not args.analyze_only:
        print(f"\nMerging graphs (strategy: {args.strategy})...")
        merged = merger.merge_graphs(merge_strategy=args.strategy)

        # Save merged graph
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"\nMerged graph saved to: {output_path}")
        print(f"  Nodes: {merged['metadata']['num_nodes']}")
        print(f"  Edges: {merged['metadata']['num_edges']}")
        print(f"  Common words: {merged['merge_analysis']['common_words_count']}")
        print(f"  Unique words: {merged['merge_analysis']['unique_words_count']}")
        print(f"  Shared transitions: {merged['merge_analysis']['shared_transitions_count']}")

    return 0


if __name__ == '__main__':
    exit(main())
