#!/usr/bin/env python3
"""
Analyze Word Graph - Apply system analysis tools to word networks

Uses reflow's NetworkX analysis functions to analyze language structure:
- Centrality (key words that connect many other words)
- Communities (clusters of related words)
- DAG analysis (identify cycles in language flow)
- Gaps (orphaned words, dead ends, unreachable words)
"""

import json
import sys
import networkx as nx
from pathlib import Path
from typing import Dict, Any
import argparse


def load_word_graph(graph_path: str) -> tuple[nx.DiGraph, Dict]:
    """
    Load word graph from JSON and convert to NetworkX DiGraph

    Returns:
        (graph, metadata) tuple
    """
    with open(graph_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    G = nx.DiGraph()

    # Add nodes
    for node in data['graph']['nodes']:
        G.add_node(
            node['id'],
            name=node['name'],
            **node.get('raw', {})
        )

    # Add edges
    for edge in data['graph']['links']:
        G.add_edge(
            edge['source'],
            edge['target'],
            weight=edge.get('weight', 1.0),
            **edge.get('raw', {})
        )

    return G, data['metadata']


def analyze_centrality(G: nx.DiGraph) -> Dict[str, Any]:
    """Analyze word centrality - which words are most important/connected"""
    try:
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)

        # Get top 10 by each metric
        top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "analysis_type": "centrality",
            "top_by_degree": [
                {"word": word.replace("word_", ""), "score": score}
                for word, score in top_degree
            ],
            "top_by_betweenness": [
                {"word": word.replace("word_", ""), "score": score}
                for word, score in top_betweenness
            ],
            "top_by_closeness": [
                {"word": word.replace("word_", ""), "score": score}
                for word, score in top_closeness
            ],
            "interpretation": {
                "degree": "Words with most direct connections (most versatile words)",
                "betweenness": "Bridge words that connect different parts of text",
                "closeness": "Words closest to all other words (central to vocabulary)"
            }
        }
    except Exception as e:
        return {"error": str(e), "analysis_type": "centrality"}


def analyze_communities(G: nx.DiGraph) -> Dict[str, Any]:
    """Detect word communities - clusters of related words"""
    try:
        # Convert to undirected for community detection
        G_undirected = G.to_undirected()

        # Use greedy modularity communities
        communities = list(nx.community.greedy_modularity_communities(G_undirected))

        community_data = []
        for i, community in enumerate(communities[:10]):  # Top 10 communities
            words = [node.replace("word_", "") for node in community]
            community_data.append({
                "community_id": i,
                "size": len(words),
                "words": sorted(words)[:20]  # Show up to 20 words per community
            })

        return {
            "analysis_type": "communities",
            "num_communities": len(communities),
            "communities": community_data,
            "interpretation": "Groups of words that frequently occur together"
        }
    except Exception as e:
        return {"error": str(e), "analysis_type": "communities"}


def analyze_dag(G: nx.DiGraph) -> Dict[str, Any]:
    """Analyze if the graph is a DAG and detect cycles"""
    is_dag = nx.is_directed_acyclic_graph(G)

    result = {
        "analysis_type": "dag",
        "is_dag": is_dag
    }

    if not is_dag:
        try:
            # Find cycles
            cycles = list(nx.simple_cycles(G))

            # Get a few example cycles
            example_cycles = []
            for cycle in cycles[:5]:  # Show up to 5 cycles
                cycle_words = [node.replace("word_", "") for node in cycle]
                example_cycles.append({
                    "length": len(cycle_words),
                    "words": cycle_words
                })

            result.update({
                "num_cycles": len(cycles),
                "example_cycles": example_cycles,
                "interpretation": "Cycles indicate words that loop back to each other in the text"
            })
        except Exception as e:
            result["cycle_detection_error"] = str(e)
    else:
        result["interpretation"] = "Perfect DAG - no cycles in word transitions"

    return result


def detect_structural_issues(G: nx.DiGraph) -> Dict[str, Any]:
    """Detect structural issues like orphaned nodes, bottlenecks, etc."""

    # Find orphaned nodes (no incoming or outgoing edges)
    orphaned = [
        node.replace("word_", "")
        for node in G.nodes()
        if G.in_degree(node) == 0 and G.out_degree(node) == 0
    ]

    # Find dead ends (no outgoing edges)
    dead_ends = [
        node.replace("word_", "")
        for node in G.nodes()
        if G.out_degree(node) == 0 and G.in_degree(node) > 0
    ]

    # Find unreachable (no incoming edges)
    unreachable = [
        node.replace("word_", "")
        for node in G.nodes()
        if G.in_degree(node) == 0 and G.out_degree(node) > 0
    ]

    # Find bottlenecks (high betweenness centrality)
    betweenness = nx.betweenness_centrality(G)
    bottlenecks = [
        {"word": node.replace("word_", ""), "score": score}
        for node, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    return {
        "analysis_type": "structural_issues",
        "orphaned_nodes": {
            "count": len(orphaned),
            "words": sorted(orphaned),
            "interpretation": "Words that appear isolated (no connections)"
        },
        "dead_ends": {
            "count": len(dead_ends),
            "words": sorted(dead_ends)[:20],  # Limit display
            "interpretation": "Words that end sentences/phrases (no words follow them)"
        },
        "unreachable": {
            "count": len(unreachable),
            "words": sorted(unreachable)[:20],  # Limit display
            "interpretation": "Words that start sentences/phrases (no words lead to them)"
        },
        "bottlenecks": {
            "words": bottlenecks,
            "interpretation": "Words that must be passed through to connect different parts of text"
        }
    }


def analyze_connectivity(G: nx.DiGraph) -> Dict[str, Any]:
    """Analyze graph connectivity"""
    try:
        # Check if weakly or strongly connected
        is_weakly_connected = nx.is_weakly_connected(G)
        is_strongly_connected = nx.is_strongly_connected(G)

        result = {
            "analysis_type": "connectivity",
            "is_weakly_connected": is_weakly_connected,
            "is_strongly_connected": is_strongly_connected
        }

        # Get strongly connected components
        sccs = list(nx.strongly_connected_components(G))
        result["num_strongly_connected_components"] = len(sccs)

        # Get largest SCC
        if sccs:
            largest_scc = max(sccs, key=len)
            result["largest_scc_size"] = len(largest_scc)
            result["largest_scc_percentage"] = len(largest_scc) / len(G.nodes()) * 100

        result["interpretation"] = {
            "weakly_connected": "All words reachable ignoring edge direction",
            "strongly_connected": "Every word can reach every other word following edges",
            "sccs": "Groups of words that form circular paths"
        }

        return result
    except Exception as e:
        return {"error": str(e), "analysis_type": "connectivity"}


def generate_analysis_report(G: nx.DiGraph, metadata: Dict) -> Dict:
    """Generate complete analysis report"""

    report = {
        "metadata": {
            **metadata,
            "analysis_timestamp": str(Path(__file__).stat().st_mtime)
        },
        "basic_statistics": {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "density": nx.density(G),
            "average_in_degree": sum(dict(G.in_degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            "average_out_degree": sum(dict(G.out_degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        },
        "analyses": {}
    }

    print("Running centrality analysis...")
    report["analyses"]["centrality"] = analyze_centrality(G)

    print("Running community detection...")
    report["analyses"]["communities"] = analyze_communities(G)

    print("Running DAG analysis...")
    report["analyses"]["dag"] = analyze_dag(G)

    print("Detecting structural issues...")
    report["analyses"]["structural_issues"] = detect_structural_issues(G)

    print("Running connectivity analysis...")
    report["analyses"]["connectivity"] = analyze_connectivity(G)

    return report


def print_summary(report: Dict):
    """Print human-readable summary of analysis"""
    print("\n" + "="*70)
    print(f"WORD NETWORK ANALYSIS: {report['metadata'].get('book_title', 'Unknown')}")
    print("="*70)

    stats = report['basic_statistics']
    print(f"\nBasic Statistics:")
    print(f"  Words (nodes): {stats['num_nodes']}")
    print(f"  Transitions (edges): {stats['num_edges']}")
    print(f"  Density: {stats['density']:.4f}")
    print(f"  Avg transitions per word: {stats['average_out_degree']:.2f}")

    # Centrality
    if 'centrality' in report['analyses']:
        cent = report['analyses']['centrality']
        if 'top_by_degree' in cent:
            print(f"\nMost Connected Words (by degree):")
            for item in cent['top_by_degree'][:5]:
                print(f"  - {item['word']}: {item['score']:.3f}")

    # Communities
    if 'communities' in report['analyses']:
        comm = report['analyses']['communities']
        if 'num_communities' in comm:
            print(f"\nWord Communities: {comm['num_communities']} clusters found")
            if comm.get('communities'):
                print(f"  Largest community: {comm['communities'][0]['size']} words")

    # DAG
    if 'dag' in report['analyses']:
        dag = report['analyses']['dag']
        if dag.get('is_dag'):
            print(f"\nDAG Status: ✓ Perfect DAG (no cycles)")
        else:
            print(f"\nDAG Status: ✗ Contains {dag.get('num_cycles', 0)} cycles")

    # Structural issues
    if 'structural_issues' in report['analyses']:
        issues = report['analyses']['structural_issues']
        print(f"\nStructural Analysis:")
        print(f"  Dead ends (sentence-final words): {issues['dead_ends']['count']}")
        print(f"  Unreachable (sentence-initial words): {issues['unreachable']['count']}")
        print(f"  Orphaned words: {issues['orphaned_nodes']['count']}")

    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze word graph using system analysis tools'
    )
    parser.add_argument('graph_file', help='Path to word graph JSON file')
    parser.add_argument('-o', '--output', help='Output analysis JSON file')
    parser.add_argument('--summary-only', action='store_true',
                        help='Print summary only, do not save JSON')

    args = parser.parse_args()

    print(f"Loading word graph: {args.graph_file}")
    G, metadata = load_word_graph(args.graph_file)

    print(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    report = generate_analysis_report(G, metadata)

    print_summary(report)

    if not args.summary_only:
        output_path = args.output or Path(args.graph_file).parent / f"{Path(args.graph_file).stem}_analysis.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed analysis saved to: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
