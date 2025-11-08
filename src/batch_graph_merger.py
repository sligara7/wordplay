#!/usr/bin/env python3
"""
Batch Graph Merger - Merge multiple word graphs with multiple music graphs.

Enables cross-domain analysis:
- Merge 10 poems with 10 songs
- Find common patterns across corpora
- Identify representative structures
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict
from collections import Counter, defaultdict
import sys


class BatchGraphMerger:
    """Merge multiple graphs to find representative patterns."""

    def __init__(self):
        self.graphs = []
        self.metadata = []

    def load_graphs(self, file_paths: List[str]):
        """Load multiple graph JSON files."""
        for path in file_paths:
            with open(path, 'r') as f:
                graph = json.load(f)
                self.graphs.append(graph)
                self.metadata.append({
                    'path': path,
                    'title': graph.get('metadata', {}).get('title', Path(path).stem)
                })

        print(f"Loaded {len(self.graphs)} graphs")

    def find_common_nodes(self) -> Dict:
        """Find nodes (words/notes) common across all graphs."""
        all_node_sets = []

        for graph in self.graphs:
            nodes = set()
            for node in graph.get('graph', {}).get('nodes', []):
                # Extract the actual word/note (strip 'word_' or 'note_' prefix)
                name = node.get('name', '')
                nodes.add(name)
            all_node_sets.append(nodes)

        # Common to all
        common = set.intersection(*all_node_sets) if all_node_sets else set()

        # Union of all
        all_nodes = set.union(*all_node_sets) if all_node_sets else set()

        # Frequency across graphs
        node_frequency = Counter()
        for node_set in all_node_sets:
            for node in node_set:
                node_frequency[node] += 1

        return {
            'common_to_all': list(common),
            'total_unique': len(all_nodes),
            'node_frequency': node_frequency.most_common(50)
        }

    def find_common_transitions(self) -> Dict:
        """Find transitions common across graphs."""
        all_transition_sets = []

        for graph in self.graphs:
            transitions = set()
            for link in graph.get('graph', {}).get('links', []):
                # Get source and target, strip prefixes
                source = link.get('source', '').replace('word_', '').replace('note_', '')
                target = link.get('target', '').replace('word_', '').replace('note_', '')
                transitions.add((source, target))
            all_transition_sets.append(transitions)

        # Common transitions
        common = set.intersection(*all_transition_sets) if all_transition_sets else set()

        # Frequency
        transition_frequency = Counter()
        for trans_set in all_transition_sets:
            for transition in trans_set:
                transition_frequency[transition] += 1

        return {
            'common_transitions': [f"{s} → {t}" for s, t in common],
            'transition_frequency': [(f"{s} → {t}", count) for (s, t), count in transition_frequency.most_common(30)]
        }

    def compute_average_metrics(self) -> Dict:
        """Compute average graph metrics across all graphs."""
        metrics = {
            'num_nodes': [],
            'num_edges': [],
            'density': []
        }

        for graph in self.graphs:
            meta = graph.get('metadata', {})
            metrics['num_nodes'].append(meta.get('num_nodes', 0))
            metrics['num_edges'].append(meta.get('num_edges', 0))

            # Compute density if possible
            n = meta.get('num_nodes', 0)
            e = meta.get('num_edges', 0)
            if n > 1:
                density = e / (n * (n - 1))
                metrics['density'].append(density)

        return {
            'average_nodes': sum(metrics['num_nodes']) / len(metrics['num_nodes']) if metrics['num_nodes'] else 0,
            'average_edges': sum(metrics['num_edges']) / len(metrics['num_edges']) if metrics['num_edges'] else 0,
            'average_density': sum(metrics['density']) / len(metrics['density']) if metrics['density'] else 0,
            'min_nodes': min(metrics['num_nodes']) if metrics['num_nodes'] else 0,
            'max_nodes': max(metrics['num_nodes']) if metrics['num_nodes'] else 0
        }

    def create_representative_graph(self, min_frequency: int = 2) -> Dict:
        """
        Create a representative graph containing only common elements.

        Args:
            min_frequency: Minimum number of graphs an element must appear in
        """
        # Count node frequencies
        node_freq = Counter()
        for graph in self.graphs:
            for node in graph.get('graph', {}).get('nodes', []):
                name = node.get('name', '')
                node_freq[name] += 1

        # Count transition frequencies
        transition_freq = Counter()
        transition_weights = defaultdict(list)

        for graph in self.graphs:
            for link in graph.get('graph', {}).get('links', []):
                source = link.get('source', '')
                target = link.get('target', '')
                weight = link.get('weight', 0)

                transition_freq[(source, target)] += 1
                transition_weights[(source, target)].append(weight)

        # Filter by frequency
        common_nodes = {name for name, freq in node_freq.items() if freq >= min_frequency}
        common_transitions = {trans for trans, freq in transition_freq.items() if freq >= min_frequency}

        # Build representative graph
        nodes = []
        for name in common_nodes:
            nodes.append({
                'id': name,
                'name': name.replace('word_', '').replace('note_', ''),
                'type': 'common',
                'raw': {
                    'frequency_across_graphs': node_freq[name],
                    'appears_in': f"{node_freq[name]}/{len(self.graphs)} graphs"
                }
            })

        links = []
        for (source, target) in common_transitions:
            if source in common_nodes and target in common_nodes:
                avg_weight = sum(transition_weights[(source, target)]) / len(transition_weights[(source, target)])
                links.append({
                    'source': source,
                    'target': target,
                    'type': 'common_transition',
                    'weight': round(avg_weight, 4),
                    'raw': {
                        'frequency_across_graphs': transition_freq[(source, target)],
                        'average_weight': round(avg_weight, 4)
                    }
                })

        return {
            'metadata': {
                'framework': 'Representative Graph',
                'num_source_graphs': len(self.graphs),
                'min_frequency': min_frequency,
                'num_nodes': len(nodes),
                'num_edges': len(links)
            },
            'graph': {
                'directed': True,
                'nodes': nodes,
                'links': links
            }
        }

    def generate_comparison_report(self) -> Dict:
        """Generate comprehensive comparison report."""
        return {
            'num_graphs_analyzed': len(self.graphs),
            'graph_titles': [m['title'] for m in self.metadata],
            'common_elements': self.find_common_nodes(),
            'common_transitions': self.find_common_transitions(),
            'average_metrics': self.compute_average_metrics()
        }


def main():
    parser = argparse.ArgumentParser(
        description='Merge multiple word and music graphs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge all graphs in a directory
  python3 src/batch_graph_merger.py output/*.json -o output/merged_all.json

  # Merge word graphs and music graphs
  python3 src/batch_graph_merger.py output/word*.json output/music*.json -o output/cross_domain.json

  # Create representative graph (appears in 3+ graphs)
  python3 src/batch_graph_merger.py output/*.json -o output/representative.json --min-frequency 3

  # Analysis only (no output)
  python3 src/batch_graph_merger.py output/*.json --report-only
        """
    )

    parser.add_argument('graphs', nargs='+', help='Graph JSON files to merge')
    parser.add_argument('-o', '--output', help='Output merged graph file')
    parser.add_argument(
        '--min-frequency',
        type=int,
        default=2,
        help='Minimum graphs an element must appear in (default: 2)'
    )
    parser.add_argument('--report-only', action='store_true', help='Generate report without creating merged graph')

    args = parser.parse_args()

    # Validate inputs
    valid_files = [f for f in args.graphs if Path(f).exists()]
    if not valid_files:
        print("Error: No valid graph files found")
        return 1

    print(f"Processing {len(valid_files)} graph files...")

    # Create merger
    merger = BatchGraphMerger()
    merger.load_graphs(valid_files)

    # Generate comparison report
    report = merger.generate_comparison_report()

    print("\n" + "="*70)
    print("BATCH GRAPH ANALYSIS REPORT")
    print("="*70)

    print(f"\nGraphs Analyzed: {report['num_graphs_analyzed']}")
    for i, title in enumerate(report['graph_titles'], 1):
        print(f"  {i}. {title}")

    print(f"\n--- Common Elements ---")
    common = report['common_elements']
    print(f"Common to ALL graphs: {len(common['common_to_all'])} elements")
    if common['common_to_all']:
        print(f"  Examples: {', '.join(list(common['common_to_all'])[:10])}")

    print(f"\nMost frequent elements across graphs:")
    for element, count in common['node_frequency'][:10]:
        print(f"  {element}: appears in {count}/{report['num_graphs_analyzed']} graphs")

    print(f"\n--- Common Transitions ---")
    transitions = report['common_transitions']
    print(f"Transitions common to ALL: {len(transitions['common_transitions'])}")

    print(f"\nMost frequent transitions:")
    for transition, count in transitions['transition_frequency'][:10]:
        print(f"  {transition}: appears in {count} graphs")

    print(f"\n--- Average Metrics ---")
    metrics = report['average_metrics']
    print(f"Average nodes per graph: {metrics['average_nodes']:.1f}")
    print(f"Average edges per graph: {metrics['average_edges']:.1f}")
    print(f"Average density: {metrics['average_density']:.4f}")
    print(f"Range: {metrics['min_nodes']} - {metrics['max_nodes']} nodes")

    # Create representative graph
    if not args.report_only:
        if not args.output:
            args.output = 'output/representative_graph.json'

        print(f"\n--- Creating Representative Graph ---")
        print(f"Including elements appearing in {args.min_frequency}+ graphs")

        rep_graph = merger.create_representative_graph(min_frequency=args.min_frequency)

        # Save
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(rep_graph, f, indent=2)

        print(f"\nRepresentative graph saved to: {output_path}")
        print(f"  Nodes: {rep_graph['metadata']['num_nodes']}")
        print(f"  Edges: {rep_graph['metadata']['num_edges']}")

        print(f"\nNext step:")
        print(f"  Analyze: python3 src/analyze_word_graph.py {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
