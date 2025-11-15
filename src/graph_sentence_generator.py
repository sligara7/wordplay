"""
Graph Sentence Generator

Generates sentences from word transition graphs by following highest probability edges.
This implements a greedy walk strategy to discover the most characteristic phrases
in the graph.
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx


class GraphSentenceGenerator:
    """Generates sentences from word graphs using greedy probability walks."""

    def __init__(self, graph_path: str):
        """
        Initialize with a word graph JSON file.

        Args:
            graph_path: Path to the graph JSON file
        """
        self.graph_path = Path(graph_path)
        self.G = nx.DiGraph()
        self.metadata = {}
        self._load_graph()

    def _load_graph(self):
        """Load graph from JSON file into NetworkX DiGraph."""
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.metadata = data.get('metadata', {})
        graph_data = data.get('graph', {})

        # Add nodes
        for node in graph_data.get('nodes', []):
            self.G.add_node(
                node['id'],
                name=node.get('name', node['id']),
                **node.get('raw', {})
            )

        # Add edges with weights (probabilities)
        for edge in graph_data.get('links', []):
            weight = edge.get('weight', edge.get('raw', {}).get('transition_probability', 1.0))
            self.G.add_edge(
                edge['source'],
                edge['target'],
                weight=weight,
                **edge.get('raw', {})
            )

    def greedy_walk(
        self,
        start_node: str,
        max_length: int = 20,
        stop_at_cycle: bool = True
    ) -> Tuple[List[str], bool]:
        """
        Perform a greedy walk from a starting node, always following the highest
        probability edge.

        Args:
            start_node: Node to start the walk from
            max_length: Maximum number of steps to take
            stop_at_cycle: If True, stop when revisiting a node (cycle detected)

        Returns:
            Tuple of (path as list of words, whether_cycle_detected)
        """
        if start_node not in self.G:
            return [], False

        path = [start_node]
        visited = {start_node} if stop_at_cycle else set()
        current = start_node
        cycle_detected = False

        for _ in range(max_length - 1):
            # Get all outgoing edges with their weights
            successors = list(self.G.successors(current))

            if not successors:
                # Dead end - no outgoing edges
                break

            # Find the successor with highest probability
            best_next = max(
                successors,
                key=lambda n: self.G[current][n].get('weight', 0)
            )

            # Check for cycle
            if stop_at_cycle and best_next in visited:
                cycle_detected = True
                path.append(f"[{best_next}]")  # Mark cycle point
                break

            path.append(best_next)
            visited.add(best_next)
            current = best_next

        return path, cycle_detected

    def generate_from_random_nodes(
        self,
        num_samples: int = 10,
        max_length: int = 20,
        seed: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate sentences starting from random nodes.

        Args:
            num_samples: Number of random starting nodes to sample
            max_length: Maximum sentence length
            seed: Random seed for reproducibility

        Returns:
            List of dicts with keys: start_node, sentence, cycle_detected, length
        """
        if seed is not None:
            random.seed(seed)

        nodes = list(self.G.nodes())
        sample_size = min(num_samples, len(nodes))
        start_nodes = random.sample(nodes, sample_size)

        results = []
        for start in start_nodes:
            path, cycle = self.greedy_walk(start, max_length=max_length)
            results.append({
                'start_node': start,
                'sentence': ' '.join(path),
                'path': path,
                'cycle_detected': cycle,
                'length': len(path)
            })

        return results

    def generate_from_all_nodes(
        self,
        max_length: int = 20,
        max_nodes: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate sentences starting from all nodes (or a maximum number).

        Args:
            max_length: Maximum sentence length
            max_nodes: Maximum number of nodes to process (None = all)

        Returns:
            List of dicts with keys: start_node, sentence, cycle_detected, length
        """
        nodes = list(self.G.nodes())
        if max_nodes:
            nodes = nodes[:max_nodes]

        results = []
        for node in nodes:
            path, cycle = self.greedy_walk(node, max_length=max_length)
            results.append({
                'start_node': node,
                'sentence': ' '.join(path),
                'path': path,
                'cycle_detected': cycle,
                'length': len(path)
            })

        return results

    def analyze_patterns(
        self,
        sentences: List[Dict],
        min_ngram_length: int = 2,
        max_ngram_length: int = 5
    ) -> Dict:
        """
        Analyze patterns in generated sentences to find common phrases.

        Args:
            sentences: List of sentence dicts from generate_* methods
            min_ngram_length: Minimum n-gram size to analyze
            max_ngram_length: Maximum n-gram size to analyze

        Returns:
            Dict with pattern statistics
        """
        ngram_counts = defaultdict(Counter)

        for sent in sentences:
            path = sent['path']

            # Extract n-grams of various lengths
            for n in range(min_ngram_length, max_ngram_length + 1):
                for i in range(len(path) - n + 1):
                    ngram = tuple(path[i:i+n])
                    # Skip ngrams that contain cycle markers
                    if not any('[' in word for word in ngram):
                        ngram_counts[n][ngram] += 1

        # Find most common patterns for each n-gram size
        top_patterns = {}
        for n, counter in ngram_counts.items():
            top_patterns[f'{n}-grams'] = counter.most_common(10)

        # Analyze sentence statistics
        total_sentences = len(sentences)
        sentences_with_cycles = sum(1 for s in sentences if s['cycle_detected'])
        avg_length = sum(s['length'] for s in sentences) / total_sentences if total_sentences else 0

        # Find most common endpoints (where greedy walks tend to end up)
        endpoints = Counter()
        for sent in sentences:
            if not sent['cycle_detected'] and sent['path']:
                endpoint = sent['path'][-1]
                if '[' not in endpoint:  # Skip cycle markers
                    endpoints[endpoint] += 1

        return {
            'total_sentences': total_sentences,
            'sentences_with_cycles': sentences_with_cycles,
            'cycle_percentage': (sentences_with_cycles / total_sentences * 100) if total_sentences else 0,
            'average_length': avg_length,
            'top_patterns': top_patterns,
            'top_endpoints': endpoints.most_common(10),
            'unique_ngrams_by_size': {n: len(counter) for n, counter in ngram_counts.items()}
        }

    def print_analysis_report(
        self,
        num_samples: int = 20,
        max_length: int = 20,
        sample_mode: str = 'random',
        seed: Optional[int] = 42
    ):
        """
        Generate and print a comprehensive analysis report.

        Args:
            num_samples: Number of sentences to generate
            max_length: Maximum sentence length
            sample_mode: 'random' or 'all' nodes
            seed: Random seed for reproducibility
        """
        print(f"\n{'='*80}")
        print(f"GRAPH SENTENCE GENERATION ANALYSIS")
        print(f"{'='*80}")
        print(f"\nGraph: {self.graph_path.name}")
        print(f"Nodes: {self.G.number_of_nodes()}")
        print(f"Edges: {self.G.number_of_edges()}")

        if self.metadata:
            print(f"\nMetadata:")
            for key, value in self.metadata.items():
                print(f"  {key}: {value}")

        # Generate sentences
        print(f"\n{'-'*80}")
        print(f"Generating sentences (mode={sample_mode}, max_length={max_length})...")
        print(f"{'-'*80}\n")

        if sample_mode == 'random':
            sentences = self.generate_from_random_nodes(
                num_samples=num_samples,
                max_length=max_length,
                seed=seed
            )
        else:
            sentences = self.generate_from_all_nodes(
                max_length=max_length,
                max_nodes=num_samples
            )

        # Show sample sentences
        print("Sample Generated Sentences:")
        print("-" * 80)
        for i, sent in enumerate(sentences[:10], 1):
            cycle_marker = " [CYCLE]" if sent['cycle_detected'] else ""
            print(f"{i:2}. {sent['sentence']}{cycle_marker}")

        # Analyze patterns
        print(f"\n{'-'*80}")
        print("PATTERN ANALYSIS")
        print(f"{'-'*80}\n")

        analysis = self.analyze_patterns(sentences)

        print(f"Total sentences generated: {analysis['total_sentences']}")
        print(f"Sentences with cycles: {analysis['sentences_with_cycles']} ({analysis['cycle_percentage']:.1f}%)")
        print(f"Average sentence length: {analysis['average_length']:.1f} words")

        print(f"\nMost Common Endpoints (where greedy walks converge):")
        for endpoint, count in analysis['top_endpoints']:
            print(f"  '{endpoint}': {count} walks ended here ({count/analysis['total_sentences']*100:.1f}%)")

        print(f"\nTop Patterns by N-gram Size:")
        for ngram_type, patterns in analysis['top_patterns'].items():
            if patterns:
                print(f"\n  {ngram_type.upper()}:")
                for ngram, count in patterns[:5]:
                    phrase = ' '.join(ngram)
                    print(f"    {count:3} × '{phrase}'")

        print(f"\n{'='*80}\n")

        return sentences, analysis

    def find_longest_acyclic_paths(
        self,
        num_samples: int = 100,
        seed: Optional[int] = None
    ) -> List[Dict]:
        """
        Find the longest non-cyclic paths by trying many starting points.

        Args:
            num_samples: Number of random starting nodes to try
            seed: Random seed for reproducibility

        Returns:
            List of longest paths found, sorted by length
        """
        if seed is not None:
            random.seed(seed)

        nodes = list(self.G.nodes())
        sample_size = min(num_samples, len(nodes))
        start_nodes = random.sample(nodes, sample_size)

        paths = []
        for start in start_nodes:
            path, cycle = self.greedy_walk(start, max_length=100, stop_at_cycle=True)
            if not cycle:  # Only include non-cyclic paths
                paths.append({
                    'start_node': start,
                    'sentence': ' '.join(path),
                    'path': path,
                    'length': len(path)
                })

        # Sort by length descending
        paths.sort(key=lambda x: x['length'], reverse=True)
        return paths

    def identify_attractors(
        self,
        num_samples: int = 100,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Identify "attractor" nodes - nodes where many greedy walks converge.

        Args:
            num_samples: Number of walks to perform
            seed: Random seed for reproducibility

        Returns:
            Dict with attractor statistics
        """
        if seed is not None:
            random.seed(seed)

        nodes = list(self.G.nodes())
        sample_size = min(num_samples, len(nodes))
        start_nodes = random.sample(nodes, sample_size)

        # Track which nodes appear in each walk
        node_appearances = Counter()
        cycle_nodes = Counter()

        for start in start_nodes:
            path, cycle = self.greedy_walk(start, max_length=50)

            # Count how many walks pass through each node
            for node in path:
                # Skip cycle markers
                if '[' not in node:
                    node_appearances[node] += 1

            # Track cycle entry points
            if cycle and len(path) > 0:
                last_node = path[-1]
                if '[' in last_node:
                    # Extract the node from cycle marker [node]
                    cycle_node = last_node.strip('[]')
                    cycle_nodes[cycle_node] += 1

        # Calculate convergence metrics
        total_walks = sample_size
        top_attractors = []
        for node, count in node_appearances.most_common(20):
            convergence_rate = count / total_walks
            out_degree = self.G.out_degree(node)
            in_degree = self.G.in_degree(node)

            top_attractors.append({
                'node': node,
                'appearances': count,
                'convergence_rate': convergence_rate,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'is_cycle_point': node in cycle_nodes,
                'cycle_entries': cycle_nodes.get(node, 0)
            })

        return {
            'total_walks': total_walks,
            'top_attractors': top_attractors,
            'cycle_entry_points': cycle_nodes.most_common(10)
        }

    def export_results(
        self,
        sentences: List[Dict],
        analysis: Dict,
        output_path: str
    ):
        """
        Export analysis results to JSON file.

        Args:
            sentences: List of generated sentences
            analysis: Pattern analysis results
            output_path: Path to save JSON output
        """
        output_data = {
            'graph_source': str(self.graph_path),
            'metadata': self.metadata,
            'graph_stats': {
                'num_nodes': self.G.number_of_nodes(),
                'num_edges': self.G.number_of_edges()
            },
            'sentences': sentences,
            'analysis': analysis,
            'generated': str(Path(output_path).stem)
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults exported to: {output_path}")


def main():
    """Example usage and testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python graph_sentence_generator.py <graph_json_path> [num_samples] [max_length]")
        print("\nExample: python graph_sentence_generator.py output/byzantine_word_graph.json 30 15")
        sys.exit(1)

    graph_path = sys.argv[1]
    num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    max_length = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    generator = GraphSentenceGenerator(graph_path)
    sentences, analysis = generator.print_analysis_report(
        num_samples=num_samples,
        max_length=max_length,
        sample_mode='random',
        seed=42
    )


if __name__ == '__main__':
    main()
