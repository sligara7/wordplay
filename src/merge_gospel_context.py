"""
Merge Gospel and Historical Context DAGs

Combines Gospel word transition graphs with historical context DAGs to enable
cross-source querying and analysis.
"""

import json
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class GospelContextMerger:
    """Merge Gospel and historical context DAGs into unified graph."""

    def __init__(self):
        """Initialize merger."""
        self.graphs = {}  # name -> graph data
        self.merged_nodes = {}  # clean_word -> merged node data
        self.merged_edges = []
        self.touchpoints = set()  # Words appearing in multiple sources
        self.word_to_sources = defaultdict(set)  # Track which sources have each word

    def load_graph(self, name: str, path: str):
        """
        Load a graph JSON file.

        Args:
            name: Name/identifier for this graph
            path: Path to graph JSON file
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.graphs[name] = data

        nodes = data.get('graph', {}).get('nodes', [])
        print(f"Loaded '{name}': {len(nodes)} nodes")

    def extract_clean_word(self, node_id: str) -> str:
        """
        Extract the clean word from a node ID.

        Args:
            node_id: Node ID (e.g., 'kjv_jesus', 'greek_Ἰησοῦς', 'context_pilate')

        Returns:
            Clean word without prefix
        """
        if '_' in node_id:
            return node_id.split('_', 1)[1].lower()
        return node_id.lower()

    def analyze_touchpoints(self) -> Dict:
        """
        Analyze which words appear in multiple sources.

        Returns:
            Dict with touchpoint statistics
        """
        print("\nAnalyzing touchpoints...")

        # Build word -> sources mapping
        for graph_name, graph_data in self.graphs.items():
            nodes = graph_data.get('graph', {}).get('nodes', [])

            for node in nodes:
                clean_word = self.extract_clean_word(node['id'])
                self.word_to_sources[clean_word].add(graph_name)

        # Find touchpoints (words in 2+ sources)
        self.touchpoints = {
            word for word, sources in self.word_to_sources.items()
            if len(sources) > 1
        }

        # Calculate statistics
        stats = {
            'total_touchpoints': len(self.touchpoints),
            'touchpoint_list': sorted(list(self.touchpoints)),
            'source_combinations': defaultdict(int)
        }

        for word in self.touchpoints:
            sources = tuple(sorted(self.word_to_sources[word]))
            stats['source_combinations'][sources] += 1

        print(f"✓ Found {len(self.touchpoints)} touchpoint words")

        return stats

    def merge_graphs(self, merge_strategy: str = 'union') -> Dict:
        """
        Merge all loaded graphs.

        Args:
            merge_strategy: 'union' (all words) or 'intersection' (only touchpoints)

        Returns:
            Merged graph data
        """
        print(f"\nMerging graphs (strategy: {merge_strategy})...")

        # Determine which words to include
        if merge_strategy == 'intersection':
            words_to_include = self.touchpoints
        else:  # union
            words_to_include = set(self.word_to_sources.keys())

        print(f"Including {len(words_to_include)} words in merged graph")

        # Merge nodes
        for clean_word in words_to_include:
            sources = self.word_to_sources[clean_word]

            # Collect all node data for this word from different sources
            source_nodes = {}
            total_frequency = 0
            all_source_refs = []

            for graph_name, graph_data in self.graphs.items():
                if graph_name not in sources:
                    continue

                nodes = graph_data.get('graph', {}).get('nodes', [])

                for node in nodes:
                    if self.extract_clean_word(node['id']) == clean_word:
                        source_nodes[graph_name] = node
                        freq = node.get('raw', {}).get('frequency', 0)
                        total_frequency += freq

                        # Track which sources mention this word
                        source_info = {
                            'source': graph_name,
                            'node_id': node['id'],
                            'frequency': freq
                        }

                        # Add source-specific info if available
                        if 'sources' in node.get('raw', {}):
                            source_info['historical_sources'] = node['raw']['sources']

                        all_source_refs.append(source_info)

            # Create merged node
            merged_node = {
                'id': f'merged_{clean_word}',
                'name': clean_word,
                'type': 'merged_word',
                'raw': {
                    'word': clean_word,
                    'total_frequency': total_frequency,
                    'sources': list(sources),
                    'source_count': len(sources),
                    'source_details': all_source_refs,
                    'is_touchpoint': clean_word in self.touchpoints
                }
            }

            self.merged_nodes[clean_word] = merged_node

        # Merge edges
        edge_key_set = set()  # Track unique edges

        for graph_name, graph_data in self.graphs.items():
            links = graph_data.get('graph', {}).get('links', [])

            for link in links:
                source_clean = self.extract_clean_word(link['source'])
                target_clean = self.extract_clean_word(link['target'])

                # Only include edges between words we're keeping
                if source_clean not in words_to_include or target_clean not in words_to_include:
                    continue

                # Create edge key
                edge_key = (source_clean, target_clean)

                # Track edge sources
                weight = link.get('weight', 0)
                transition_count = link.get('raw', {}).get('transition_count', 0)

                # Find if we already have this edge
                existing_edge = None
                for edge in self.merged_edges:
                    if (self.extract_clean_word(edge['source']) == source_clean and
                        self.extract_clean_word(edge['target']) == target_clean):
                        existing_edge = edge
                        break

                if existing_edge:
                    # Merge with existing edge
                    existing_edge['raw']['edge_sources'].append({
                        'source': graph_name,
                        'weight': weight,
                        'transition_count': transition_count
                    })
                    # Update combined weight (average)
                    source_weights = [s['weight'] for s in existing_edge['raw']['edge_sources']]
                    existing_edge['weight'] = sum(source_weights) / len(source_weights)
                else:
                    # Create new merged edge
                    merged_edge = {
                        'source': f'merged_{source_clean}',
                        'target': f'merged_{target_clean}',
                        'type': 'word_transition',
                        'interaction_type': 'follows',
                        'weight': weight,
                        'raw': {
                            'edge_sources': [{
                                'source': graph_name,
                                'weight': weight,
                                'transition_count': transition_count
                            }]
                        }
                    }
                    self.merged_edges.append(merged_edge)

        print(f"✓ Merged {len(self.merged_nodes)} nodes")
        print(f"✓ Merged {len(self.merged_edges)} edges")

        return self.build_output()

    def build_output(self) -> Dict:
        """
        Build final merged graph output.

        Returns:
            Graph data in standard format
        """
        # Build metadata
        metadata = {
            'generated': datetime.now().isoformat(),
            'framework': 'Gospel + Historical Context Merged',
            'framework_id': 'gospel_context_merged',
            'component_term': 'merged_word',
            'connection_term': 'transition',
            'num_nodes': len(self.merged_nodes),
            'num_edges': len(self.merged_edges),
            'tool_version': '1.0.0',
            'source_graphs': list(self.graphs.keys()),
            'touchpoint_count': len(self.touchpoints),
            'merge_info': {
                'total_sources': len(self.graphs),
                'touchpoint_words': len(self.touchpoints),
                'unique_words': len(self.merged_nodes)
            }
        }

        # Add source graph metadata
        for name, graph_data in self.graphs.items():
            metadata[f'{name}_metadata'] = graph_data.get('metadata', {})

        # Build graph structure
        graph_data = {
            'metadata': metadata,
            'graph': {
                'directed': True,
                'multigraph': False,
                'nodes': list(self.merged_nodes.values()),
                'links': self.merged_edges
            }
        }

        return graph_data

    def export(self, output_path: str):
        """
        Export merged graph to JSON.

        Args:
            output_path: Path to save merged graph
        """
        graph_data = self.build_output()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved merged graph to: {output_path}")

    def print_touchpoint_report(self, stats: Dict):
        """Print report on touchpoints between sources."""
        print("\n" + "="*80)
        print("TOUCHPOINT ANALYSIS")
        print("="*80)

        print(f"\nTotal touchpoint words: {stats['total_touchpoints']}")

        print("\nSource combinations:")
        for sources, count in stats['source_combinations'].items():
            print(f"  {' + '.join(sources)}: {count} words")

        print("\nSample touchpoint words:")
        for word in sorted(stats['touchpoint_list'])[:20]:
            sources = self.word_to_sources[word]
            print(f"  '{word}' appears in: {', '.join(sources)}")


def main():
    """Merge Gospel and historical context DAGs."""
    import sys

    print("="*80)
    print("GOSPEL + HISTORICAL CONTEXT MERGER")
    print("="*80)

    merger = GospelContextMerger()

    # Load graphs
    print("\nLoading graphs...")
    merger.load_graph('kjv_gospels', 'data/kjv_gospels_dag.json')
    merger.load_graph('historical_context', 'data/historical_context_dag.json')

    # Optional: Load Byzantine gospels too
    if Path('data/byzantine_gospels_dag.json').exists():
        merger.load_graph('byzantine_gospels', 'data/byzantine_gospels_dag.json')

    # Analyze touchpoints
    stats = merger.analyze_touchpoints()

    # Print report
    merger.print_touchpoint_report(stats)

    # Merge
    merger.merge_graphs(merge_strategy='union')

    # Export
    output_path = 'data/gospel_context_merged.json'
    merger.export(output_path)

    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"\nMerged graph saved to: {output_path}")
    print("You can now query this graph with cross-source questions!")


if __name__ == '__main__':
    main()
