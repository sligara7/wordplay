#!/usr/bin/env python3
"""
LLM Output Analyzer - Detect issues in LLM-generated text using word graphs

Analyzes LLM output to detect:
- Mode collapse (limited vocabulary)
- Repetitive patterns (excessive cycles)
- Unnatural transitions (sparse graph)
- Vocabulary mismatch (vs human baseline)
"""

import json
import argparse
from pathlib import Path
from word_graph_builder import WordGraphBuilder
import networkx as nx


class LLMAnalyzer:
    """Analyze LLM behavior using word graph techniques"""

    def __init__(self, reference_corpus_path=None):
        """
        Initialize with optional reference corpus

        Args:
            reference_corpus_path: Path to human-written text for comparison
        """
        self.reference_graph = None
        self.reference_G = None

        if reference_corpus_path:
            with open(reference_corpus_path, 'r') as f:
                text = f.read()
            builder = WordGraphBuilder(text, "Reference Corpus", lowercase=True, remove_stopwords=True)
            builder.build_graph()
            self.reference_graph = builder.to_system_graph_json()

            # Build NetworkX graph
            self.reference_G = nx.DiGraph()
            for node in self.reference_graph['graph']['nodes']:
                self.reference_G.add_node(node['id'], **node)
            for edge in self.reference_graph['graph']['links']:
                self.reference_G.add_edge(edge['source'], edge['target'], **edge)

    def analyze_llm_output(self, llm_generated_text, text_name="LLM Output"):
        """
        Analyze LLM-generated text

        Args:
            llm_generated_text: Text to analyze
            text_name: Name for the text sample

        Returns:
            Dictionary with analysis results
        """
        # Build graph from LLM output
        builder = WordGraphBuilder(llm_generated_text, text_name, lowercase=True, remove_stopwords=True)
        builder.build_graph()
        llm_graph = builder.to_system_graph_json()

        # Build NetworkX graph
        G = nx.DiGraph()
        for node in llm_graph['graph']['nodes']:
            G.add_node(node['id'], **node)
        for edge in llm_graph['graph']['links']:
            G.add_edge(edge['source'], edge['target'], **edge)

        # Compute basic metrics
        metrics = {
            'text_name': text_name,
            'vocabulary_size': llm_graph['metadata']['unique_words'],
            'total_tokens': llm_graph['metadata']['total_tokens'],
            'transitions': llm_graph['metadata']['num_edges'],
            'avg_transitions_per_word': (
                llm_graph['metadata']['num_edges'] / llm_graph['metadata']['unique_words']
                if llm_graph['metadata']['unique_words'] > 0 else 0
            ),
            'graph_density': nx.density(G) if G.number_of_nodes() > 0 else 0
        }

        # Detect issues
        issues = self._detect_issues(llm_graph, G)
        metrics['issues'] = issues

        # Compare to reference if available
        if self.reference_graph and self.reference_G:
            comparison = self._compare_to_reference(llm_graph, G, self.reference_graph, self.reference_G)
            metrics['comparison'] = comparison

        # Overall health score (0-100)
        health_score = self._compute_health_score(issues, metrics)
        metrics['health_score'] = health_score

        return metrics

    def _detect_issues(self, graph, G):
        """Detect common LLM issues from graph structure"""
        issues = []

        vocab_size = graph['metadata']['unique_words']
        num_edges = graph['metadata']['num_edges']

        # Issue 1: Mode collapse (very limited vocabulary)
        if vocab_size < 50:
            issues.append({
                'type': 'severe_mode_collapse',
                'severity': 'critical',
                'description': f'Severely limited vocabulary: only {vocab_size} unique words',
                'recommendation': 'Increase temperature, use top-p/top-k sampling, or increase diversity penalty'
            })
        elif vocab_size < 100:
            issues.append({
                'type': 'mode_collapse',
                'severity': 'high',
                'description': f'Limited vocabulary: {vocab_size} unique words',
                'recommendation': 'Consider increasing temperature or diversity penalty'
            })

        # Issue 2: Repetition (check for cycles)
        if G.number_of_nodes() > 0:
            try:
                cycles = list(nx.simple_cycles(G))
                num_cycles = len(cycles)

                # Count short cycles (likely repetitive phrases)
                short_cycles = [c for c in cycles if len(c) <= 3]

                if num_cycles > vocab_size * 0.5:  # More than 50% of words in cycles
                    issues.append({
                        'type': 'excessive_repetition',
                        'severity': 'high',
                        'description': f'Excessive repetition: {num_cycles} cycles detected ({len(short_cycles)} short cycles)',
                        'recommendation': 'Reduce repetition penalty or use no-repeat-ngram-size parameter'
                    })
            except Exception as e:
                pass  # Cycle detection can fail on large graphs

        # Issue 3: Sparse graph (unnatural transitions)
        if G.number_of_nodes() > 10:  # Only check if enough data
            density = nx.density(G)
            if density < 0.005:  # Very sparse
                issues.append({
                    'type': 'sparse_transitions',
                    'severity': 'medium',
                    'description': f'Very sparse graph (density: {density:.6f}) - limited word-to-word transitions',
                    'recommendation': 'May indicate unnatural language patterns or overly conservative sampling'
                })

        # Issue 4: Dead ends (many sentence-final words)
        dead_ends = [node for node in G.nodes() if G.out_degree(node) == 0 and G.in_degree(node) > 0]
        if len(dead_ends) > vocab_size * 0.3:  # More than 30% are dead ends
            issues.append({
                'type': 'excessive_dead_ends',
                'severity': 'medium',
                'description': f'Many dead-end words ({len(dead_ends)}): words that never lead to other words',
                'recommendation': 'May indicate truncated or incomplete generation'
            })

        # Issue 5: Disconnected graph (multiple components)
        if G.number_of_nodes() > 5:
            num_components = nx.number_weakly_connected_components(G)
            if num_components > 5:
                issues.append({
                    'type': 'disconnected_graph',
                    'severity': 'medium',
                    'description': f'Graph has {num_components} disconnected components - topics don\'t connect',
                    'recommendation': 'May indicate topic jumping or incoherent generation'
                })

        # Issue 6: Hub concentration (few words dominate)
        if G.number_of_nodes() > 10:
            degree_centrality = nx.degree_centrality(G)
            if degree_centrality:
                max_centrality = max(degree_centrality.values())
                if max_centrality > 0.5:  # One word connects to >50% of vocabulary
                    hub_words = [
                        node.replace('word_', '')
                        for node, cent in degree_centrality.items()
                        if cent > 0.3
                    ]
                    issues.append({
                        'type': 'hub_concentration',
                        'severity': 'low',
                        'description': f'Few words dominate connections: {hub_words[:3]}',
                        'recommendation': 'Expected for some texts, but may indicate overuse of common words'
                    })

        return issues

    def _compare_to_reference(self, llm_graph, llm_G, ref_graph, ref_G):
        """Compare LLM graph to reference corpus"""

        # Vocabulary comparison
        llm_words = {node['name'] for node in llm_graph['graph']['nodes']}
        ref_words = {node['name'] for node in ref_graph['graph']['nodes']}

        overlap = len(llm_words & ref_words)
        union_size = len(llm_words | ref_words)
        orthogonality = 1.0 - (overlap / union_size) if union_size > 0 else 0

        # Structural comparison
        llm_density = nx.density(llm_G) if llm_G.number_of_nodes() > 0 else 0
        ref_density = nx.density(ref_G) if ref_G.number_of_nodes() > 0 else 0

        llm_avg_degree = sum(dict(llm_G.degree()).values()) / llm_G.number_of_nodes() if llm_G.number_of_nodes() > 0 else 0
        ref_avg_degree = sum(dict(ref_G.degree()).values()) / ref_G.number_of_nodes() if ref_G.number_of_nodes() > 0 else 0

        # Similarity assessment
        similarity_score = 1.0 - orthogonality  # 0 = different, 1 = same

        assessment = "very similar" if similarity_score > 0.7 else \
                    "similar" if similarity_score > 0.5 else \
                    "somewhat different" if similarity_score > 0.3 else \
                    "very different"

        return {
            'vocabulary_overlap': overlap,
            'orthogonality': round(orthogonality, 3),
            'similarity_score': round(similarity_score, 3),
            'assessment': assessment,
            'structural_comparison': {
                'llm_density': round(llm_density, 6),
                'reference_density': round(ref_density, 6),
                'llm_avg_degree': round(llm_avg_degree, 2),
                'reference_avg_degree': round(ref_avg_degree, 2)
            },
            'interpretation': f'LLM output is {assessment} to reference corpus'
        }

    def _compute_health_score(self, issues, metrics):
        """
        Compute overall health score (0-100)

        100 = Perfect, no issues
        0 = Severe problems
        """
        score = 100

        # Deduct points for issues
        for issue in issues:
            if issue['severity'] == 'critical':
                score -= 30
            elif issue['severity'] == 'high':
                score -= 20
            elif issue['severity'] == 'medium':
                score -= 10
            elif issue['severity'] == 'low':
                score -= 5

        # Bonus for good metrics
        vocab_size = metrics['vocabulary_size']
        if vocab_size > 200:
            score += 10  # Good vocabulary diversity

        avg_transitions = metrics['avg_transitions_per_word']
        if 1.5 <= avg_transitions <= 3.0:
            score += 5  # Good branching factor

        return max(0, min(100, score))  # Clamp to 0-100


def print_analysis_report(analysis):
    """Print human-readable analysis report"""
    print("\n" + "="*70)
    print(f"LLM OUTPUT ANALYSIS: {analysis['text_name']}")
    print("="*70)

    print(f"\nBasic Metrics:")
    print(f"  Vocabulary size: {analysis['vocabulary_size']} words")
    print(f"  Total tokens: {analysis['total_tokens']}")
    print(f"  Transitions: {analysis['transitions']}")
    print(f"  Avg transitions per word: {analysis['avg_transitions_per_word']:.2f}")
    print(f"  Graph density: {analysis['graph_density']:.6f}")

    print(f"\nHealth Score: {analysis['health_score']}/100")
    if analysis['health_score'] >= 80:
        print("  Status: ✓ HEALTHY")
    elif analysis['health_score'] >= 60:
        print("  Status: ⚠ NEEDS ATTENTION")
    else:
        print("  Status: ✗ PROBLEMATIC")

    if analysis['issues']:
        print(f"\nIssues Detected ({len(analysis['issues'])}):")
        for i, issue in enumerate(analysis['issues'], 1):
            severity_symbol = "🔴" if issue['severity'] == 'critical' else \
                            "🟠" if issue['severity'] == 'high' else \
                            "🟡" if issue['severity'] == 'medium' else "🔵"
            print(f"\n  {i}. {severity_symbol} {issue['type'].upper()} ({issue['severity']})")
            print(f"     {issue['description']}")
            print(f"     → {issue['recommendation']}")
    else:
        print("\n✓ No issues detected!")

    if 'comparison' in analysis:
        comp = analysis['comparison']
        print(f"\nComparison to Reference Corpus:")
        print(f"  Similarity: {comp['similarity_score']:.3f} ({comp['assessment']})")
        print(f"  Vocabulary overlap: {comp['vocabulary_overlap']} words")
        print(f"  Orthogonality: {comp['orthogonality']:.3f}")
        print(f"  {comp['interpretation']}")

        struct = comp['structural_comparison']
        print(f"\n  Structural Comparison:")
        print(f"    LLM density:       {struct['llm_density']:.6f}")
        print(f"    Reference density: {struct['reference_density']:.6f}")
        print(f"    LLM avg degree:    {struct['llm_avg_degree']:.2f}")
        print(f"    Reference avg deg: {struct['reference_avg_degree']:.2f}")

    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze LLM-generated text using word graphs'
    )
    parser.add_argument('llm_output_file', help='File containing LLM-generated text')
    parser.add_argument('-r', '--reference', help='Reference corpus (human-written text) for comparison')
    parser.add_argument('-o', '--output', help='Output JSON file for detailed analysis')
    parser.add_argument('-n', '--name', default='LLM Output', help='Name for the text sample')

    args = parser.parse_args()

    # Read LLM output
    llm_output_path = Path(args.llm_output_file)
    if not llm_output_path.exists():
        print(f"Error: File not found: {args.llm_output_file}")
        return 1

    with open(llm_output_path, 'r', encoding='utf-8') as f:
        llm_text = f.read()

    # Initialize analyzer
    print(f"Analyzing LLM output: {llm_output_path}")
    if args.reference:
        print(f"Using reference corpus: {args.reference}")
        analyzer = LLMAnalyzer(reference_corpus_path=args.reference)
    else:
        print("No reference corpus provided")
        analyzer = LLMAnalyzer()

    # Analyze
    analysis = analyzer.analyze_llm_output(llm_text, text_name=args.name)

    # Print report
    print_analysis_report(analysis)

    # Save JSON if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nDetailed analysis saved to: {args.output}")

    return 0


if __name__ == '__main__':
    exit(main())
