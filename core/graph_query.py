"""
Graph Query System

Query word graphs using natural language questions. Finds shortest paths
between query terms to extract relevant subgraphs that may contain answers.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx


class GraphQueryEngine:
    """Query word transition graphs using natural language questions."""

    def __init__(self, graph_path: str):
        """
        Initialize with a word graph JSON file.

        Args:
            graph_path: Path to the graph JSON file
        """
        self.graph_path = Path(graph_path)
        self.G = nx.DiGraph()
        self.metadata = {}
        self.node_lookup = {}  # Map clean words to node IDs
        self._load_graph()
        self._build_lookup()

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

    def _build_lookup(self):
        """Build lookup table mapping clean words to node IDs."""
        for node_id in self.G.nodes():
            # Extract the actual word from node ID
            # Handles formats like: greek_Ἰησοῦς, kjv_jesus, or plain words
            if '_' in node_id:
                clean_word = node_id.split('_', 1)[1].lower()
            else:
                clean_word = node_id.lower()

            # Store both the original and lowercased versions
            if clean_word not in self.node_lookup:
                self.node_lookup[clean_word] = []
            self.node_lookup[clean_word].append(node_id)

    def extract_query_words(self, query: str) -> List[str]:
        """
        Extract meaningful words from a query string.

        Args:
            query: Natural language query

        Returns:
            List of words to search for
        """
        # Remove punctuation and convert to lowercase
        query = re.sub(r'[^\w\s]', ' ', query.lower())

        # Split into words
        words = query.split()

        # Remove common stop words that are unlikely to be meaningful in graph
        stop_words = {
            'did', 'does', 'do', 'is', 'was', 'were', 'are', 'am',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'as', 'by', 'with', 'from'
        }

        # Keep words that aren't stop words
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 1]

        return meaningful_words

    def find_matching_nodes(self, query_words: List[str]) -> Dict[str, List[str]]:
        """
        Find graph nodes that match query words.

        Args:
            query_words: List of words to search for

        Returns:
            Dict mapping query words to matching node IDs
        """
        matches = {}

        for word in query_words:
            word_lower = word.lower()

            # Direct lookup
            if word_lower in self.node_lookup:
                matches[word] = self.node_lookup[word_lower]
            else:
                # Try partial matching (e.g., "walking" might match "walk")
                partial_matches = []
                for clean_word, node_ids in self.node_lookup.items():
                    if word_lower in clean_word or clean_word in word_lower:
                        partial_matches.extend(node_ids)

                if partial_matches:
                    matches[word] = partial_matches

        return matches

    def find_connecting_paths(
        self,
        node_ids: List[str],
        max_path_length: Optional[int] = 10
    ) -> Dict:
        """
        Find shortest paths between all pairs of query nodes.

        Args:
            node_ids: List of node IDs to connect
            max_path_length: Maximum path length to consider (None = unlimited)

        Returns:
            Dict with path information
        """
        paths = []
        all_nodes = set(node_ids)
        all_edges = set()

        # Find shortest path between each pair of nodes
        for i, source in enumerate(node_ids):
            for target in node_ids[i+1:]:
                try:
                    # Try to find shortest path
                    if max_path_length:
                        # Use cutoff to limit path length
                        path = nx.shortest_path(
                            self.G,
                            source=source,
                            target=target,
                            weight=None  # Unweighted for shortest hop count
                        )
                        if len(path) > max_path_length:
                            continue
                    else:
                        path = nx.shortest_path(self.G, source=source, target=target)

                    # Add all nodes in the path
                    all_nodes.update(path)

                    # Add all edges in the path
                    for j in range(len(path) - 1):
                        all_edges.add((path[j], path[j+1]))

                    paths.append({
                        'source': source,
                        'target': target,
                        'path': path,
                        'length': len(path) - 1,
                        'path_text': ' → '.join(self._clean_node_name(n) for n in path)
                    })

                except nx.NetworkXNoPath:
                    # No path exists between these nodes
                    continue

        # Identify bridge nodes (appear in paths but not in original query)
        query_node_set = set(node_ids)
        bridge_nodes = all_nodes - query_node_set

        return {
            'paths': paths,
            'query_nodes': list(query_node_set),
            'bridge_nodes': list(bridge_nodes),
            'all_nodes': list(all_nodes),
            'all_edges': list(all_edges),
            'subgraph_size': {
                'nodes': len(all_nodes),
                'edges': len(all_edges)
            }
        }

    def _clean_node_name(self, node_id: str) -> str:
        """Extract clean word from node ID."""
        if '_' in node_id:
            return node_id.split('_', 1)[1]
        return node_id

    def build_query_subgraph(self, nodes: List[str], edges: List[Tuple[str, str]]) -> nx.DiGraph:
        """
        Build a subgraph containing only the specified nodes and edges.

        Args:
            nodes: List of node IDs to include
            edges: List of edge tuples (source, target)

        Returns:
            NetworkX DiGraph subgraph
        """
        subgraph = nx.DiGraph()

        # Add nodes with their attributes
        for node in nodes:
            if node in self.G:
                subgraph.add_node(node, **self.G.nodes[node])

        # Add edges with their attributes
        for source, target in edges:
            if self.G.has_edge(source, target):
                subgraph.add_edge(source, target, **self.G[source][target])

        return subgraph

    def query(
        self,
        question: str,
        max_path_length: int = 10,
        include_context: bool = True
    ) -> Dict:
        """
        Query the graph with a natural language question.

        Args:
            question: Natural language question
            max_path_length: Maximum path length between query terms
            include_context: Include surrounding context from the graph

        Returns:
            Dict with query results
        """
        print(f"\n{'='*80}")
        print(f"GRAPH QUERY")
        print(f"{'='*80}\n")
        print(f"Question: {question}\n")

        # Extract query words
        query_words = self.extract_query_words(question)
        print(f"Query terms extracted: {', '.join(query_words)}")

        # Find matching nodes
        matches = self.find_matching_nodes(query_words)

        if not matches:
            print("\n❌ No matching nodes found in graph")
            return {
                'question': question,
                'query_words': query_words,
                'matches': {},
                'paths': [],
                'subgraph': None
            }

        print(f"\nMatched nodes:")
        all_matched_nodes = []
        for word, node_ids in matches.items():
            print(f"  '{word}' → {len(node_ids)} nodes: {', '.join(self._clean_node_name(n) for n in node_ids[:3])}")
            all_matched_nodes.extend(node_ids)

        # Find connecting paths
        print(f"\nFinding shortest paths (max length: {max_path_length})...")
        path_info = self.find_connecting_paths(all_matched_nodes, max_path_length)

        print(f"\n✓ Found {len(path_info['paths'])} connecting paths")
        print(f"✓ Query subgraph: {path_info['subgraph_size']['nodes']} nodes, {path_info['subgraph_size']['edges']} edges")

        if path_info['bridge_nodes']:
            print(f"\nBridge words (connecting query terms):")
            bridge_words = [self._clean_node_name(n) for n in path_info['bridge_nodes'][:10]]
            print(f"  {', '.join(bridge_words)}")

        # Show sample paths
        if path_info['paths']:
            print(f"\nSample connecting paths:")
            for i, path in enumerate(path_info['paths'][:5], 1):
                print(f"  {i}. {path['path_text']} ({path['length']} hops)")

        # Build subgraph
        subgraph = self.build_query_subgraph(
            path_info['all_nodes'],
            path_info['all_edges']
        )

        print(f"\n{'='*80}\n")

        return {
            'question': question,
            'query_words': query_words,
            'matches': matches,
            'path_info': path_info,
            'subgraph': subgraph
        }

    def analyze_query_context(
        self,
        query_result: Dict,
        context_radius: int = 1
    ) -> Dict:
        """
        Analyze the context around query results.

        Args:
            query_result: Result from query() method
            context_radius: How many hops around query nodes to include

        Returns:
            Dict with context analysis
        """
        if query_result['subgraph'] is None:
            return {}

        subgraph = query_result['subgraph']

        # Analyze the subgraph structure
        analysis = {
            'node_degrees': {},
            'most_connected': [],
            'edge_weights': [],
            'narrative_fragments': []
        }

        # Calculate node degrees in subgraph
        for node in subgraph.nodes():
            in_deg = subgraph.in_degree(node)
            out_deg = subgraph.out_degree(node)
            analysis['node_degrees'][self._clean_node_name(node)] = {
                'in': in_deg,
                'out': out_deg,
                'total': in_deg + out_deg
            }

        # Find most connected nodes
        sorted_nodes = sorted(
            analysis['node_degrees'].items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        analysis['most_connected'] = sorted_nodes[:5]

        # Extract edge weights
        for source, target in subgraph.edges():
            weight = subgraph[source][target].get('weight', 0)
            analysis['edge_weights'].append({
                'from': self._clean_node_name(source),
                'to': self._clean_node_name(target),
                'probability': weight
            })

        # Sort by weight
        analysis['edge_weights'].sort(key=lambda x: x['probability'], reverse=True)

        # Try to reconstruct narrative fragments from paths
        for path_dict in query_result['path_info']['paths']:
            path = path_dict['path']
            fragment = ' '.join(self._clean_node_name(n) for n in path)
            analysis['narrative_fragments'].append(fragment)

        return analysis

    def export_query_result(
        self,
        query_result: Dict,
        context_analysis: Dict,
        output_path: str
    ):
        """
        Export query results to JSON file.

        Args:
            query_result: Result from query()
            context_analysis: Result from analyze_query_context()
            output_path: Path to save JSON
        """
        # Convert subgraph to JSON-serializable format
        subgraph_data = None
        if query_result['subgraph'] is not None:
            subgraph = query_result['subgraph']
            subgraph_data = {
                'nodes': [
                    {
                        'id': n,
                        'name': self._clean_node_name(n),
                        'attributes': dict(subgraph.nodes[n])
                    }
                    for n in subgraph.nodes()
                ],
                'edges': [
                    {
                        'source': s,
                        'target': t,
                        'attributes': dict(subgraph[s][t])
                    }
                    for s, t in subgraph.edges()
                ]
            }

        output_data = {
            'graph_source': str(self.graph_path),
            'question': query_result['question'],
            'query_words': query_result['query_words'],
            'matches': {k: v for k, v in query_result['matches'].items()},
            'path_info': {
                'num_paths': len(query_result['path_info']['paths']),
                'paths': query_result['path_info']['paths'],
                'query_nodes': query_result['path_info']['query_nodes'],
                'bridge_nodes': query_result['path_info']['bridge_nodes'],
                'subgraph_size': query_result['path_info']['subgraph_size']
            },
            'context_analysis': context_analysis,
            'subgraph': subgraph_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Query results exported to: {output_path}")


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python graph_query.py <graph_json_path> <question>")
        print("\nExamples:")
        print('  python graph_query.py data/kjv_gospels_dag.json "Did Jesus walk on water?"')
        print('  python graph_query.py data/byzantine_gospels_dag.json "Jesus disciples boat"')
        sys.exit(1)

    graph_path = sys.argv[1]
    question = ' '.join(sys.argv[2:])

    # Initialize query engine
    engine = GraphQueryEngine(graph_path)

    # Run query
    result = engine.query(question, max_path_length=10)

    # Analyze context
    if result['subgraph'] is not None:
        context = engine.analyze_query_context(result)

        print("\nCONTEXT ANALYSIS")
        print("="*80)
        print("\nMost connected words in query subgraph:")
        for word, degrees in context['most_connected']:
            print(f"  {word}: {degrees['total']} connections (in={degrees['in']}, out={degrees['out']})")

        print("\nNarrative fragments (paths between query terms):")
        for i, fragment in enumerate(context['narrative_fragments'][:5], 1):
            print(f"  {i}. {fragment}")

        print("\nTop probability edges:")
        for edge in context['edge_weights'][:5]:
            print(f"  {edge['from']} → {edge['to']} ({edge['probability']:.3f})")

        # Export results
        output_dir = Path("output/graph_queries")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename from question
        safe_question = re.sub(r'[^\w\s]', '', question.lower())[:50]
        safe_question = safe_question.replace(' ', '_')
        output_file = output_dir / f"{safe_question}.json"

        engine.export_query_result(result, context, str(output_file))


if __name__ == '__main__':
    main()
