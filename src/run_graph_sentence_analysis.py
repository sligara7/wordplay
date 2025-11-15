#!/usr/bin/env python3
"""
Comprehensive graph sentence analysis script.

Runs multiple analyses on word transition graphs:
- Greedy sentence generation
- Pattern identification
- Attractor node detection
- Longest acyclic paths
- Export results to JSON
"""

from pathlib import Path
from graph_sentence_generator import GraphSentenceGenerator


def run_comprehensive_analysis(
    graph_path: str,
    num_samples: int = 50,
    output_dir: str = "output/graph_analysis"
):
    """
    Run comprehensive analysis on a word graph.

    Args:
        graph_path: Path to the graph JSON file
        num_samples: Number of sentence samples to generate
        output_dir: Directory to save output files
    """
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE GRAPH SENTENCE ANALYSIS")
    print(f"{'='*80}\n")

    # Initialize generator
    gen = GraphSentenceGenerator(graph_path)
    graph_name = Path(graph_path).stem

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Generate sentences and analyze patterns
    print("Step 1: Generating sentences and analyzing patterns...")
    print("-" * 80)
    sentences, analysis = gen.print_analysis_report(
        num_samples=num_samples,
        max_length=20,
        sample_mode='random',
        seed=42
    )

    # 2. Identify attractor nodes
    print("\n" + "="*80)
    print("Step 2: Identifying attractor nodes...")
    print("="*80 + "\n")
    attractors = gen.identify_attractors(num_samples=100, seed=42)

    print(f"Top Attractor Nodes (appear in most greedy walks):")
    print("-" * 80)
    for i, attr in enumerate(attractors['top_attractors'][:10], 1):
        cycle_marker = " [CYCLE POINT]" if attr['is_cycle_point'] else ""
        print(f"{i:2}. {attr['node']}")
        print(f"    Convergence: {attr['convergence_rate']*100:.1f}% of walks")
        print(f"    Degree: in={attr['in_degree']}, out={attr['out_degree']}{cycle_marker}")

    print(f"\nCycle Entry Points (where cycles form):")
    for node, count in attractors['cycle_entry_points'][:5]:
        print(f"  {node}: {count} cycles")

    # 3. Find longest acyclic paths
    print("\n" + "="*80)
    print("Step 3: Finding longest non-cyclic paths...")
    print("="*80 + "\n")
    longest_paths = gen.find_longest_acyclic_paths(num_samples=200, seed=42)

    if longest_paths:
        print(f"Found {len(longest_paths)} non-cyclic paths")
        print(f"Longest path: {longest_paths[0]['length']} words\n")
        print("Top 5 Longest Paths:")
        print("-" * 80)
        for i, path_info in enumerate(longest_paths[:5], 1):
            print(f"{i}. Length {path_info['length']}: {path_info['sentence'][:100]}...")
    else:
        print("No non-cyclic paths found (all walks converge to cycles)")

    # 4. Export results
    print("\n" + "="*80)
    print("Step 4: Exporting results...")
    print("="*80 + "\n")

    # Combine all results
    full_analysis = {
        **analysis,
        'attractors': attractors,
        'longest_acyclic_paths': longest_paths[:20]  # Top 20
    }

    output_file = output_path / f"{graph_name}_sentence_analysis.json"
    gen.export_results(sentences, full_analysis, str(output_file))

    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80 + "\n")
    print(f"Graph: {graph_name}")
    print(f"Nodes: {gen.G.number_of_nodes()}")
    print(f"Edges: {gen.G.number_of_edges()}")
    print(f"Sentences generated: {len(sentences)}")
    print(f"Cycle rate: {analysis['cycle_percentage']:.1f}%")
    print(f"Top attractor convergence: {attractors['top_attractors'][0]['convergence_rate']*100:.1f}%")
    print(f"Top attractor node: {attractors['top_attractors'][0]['node']}")
    print(f"Non-cyclic paths found: {len(longest_paths)}")
    print(f"\nResults saved to: {output_file}")
    print("="*80 + "\n")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python run_graph_sentence_analysis.py <graph_json_path> [num_samples]")
        print("\nExamples:")
        print("  python run_graph_sentence_analysis.py data/byzantine_gospels_dag.json")
        print("  python run_graph_sentence_analysis.py data/kjv_gospels_dag.json 100")
        sys.exit(1)

    graph_path = sys.argv[1]
    num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    run_comprehensive_analysis(graph_path, num_samples)


if __name__ == '__main__':
    main()
