#!/usr/bin/env python3
"""
Minimal Anchor Translator

Uses graph topology and minimal known translations (anchor words) to infer
unknown word translations between Greek and English. This demonstrates that
with only 2-4 known word pairs, we can bootstrap cross-lingual inference
by comparing neighborhood structures in both language DAGs.

Algorithm:
1. Extract k-hop neighborhoods around anchor words in both languages
2. Compute structural signatures for all words relative to anchors
3. Match words across languages based on neighborhood similarity
4. Rank translation candidates by structural alignment scores

Theoretical basis: Words occupying similar topological positions relative
to anchor words likely have similar semantic functions.
"""

import json
import argparse
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import math


class GraphNeighborhood:
    """Represents a word's neighborhood in the DAG"""

    def __init__(self, word: str):
        self.word = word
        self.incoming = defaultdict(float)  # {source_word: weight}
        self.outgoing = defaultdict(float)  # {target_word: weight}
        self.two_hop_neighbors = set()  # Words reachable in 2 hops
        self.anchor_distances = {}  # {anchor_word: min_distance}
        self.anchor_paths = defaultdict(list)  # {anchor_word: [path_types]}

    def add_incoming(self, source: str, weight: float):
        self.incoming[source] = weight

    def add_outgoing(self, target: str, weight: float):
        self.outgoing[target] = weight

    def get_signature_vector(self) -> Dict[str, float]:
        """
        Create a feature vector representing this word's structural position

        Features:
        - Incoming degree
        - Outgoing degree
        - Weighted incoming/outgoing ratios
        - Anchor distance statistics
        """
        return {
            'in_degree': len(self.incoming),
            'out_degree': len(self.outgoing),
            'in_weight_sum': sum(self.incoming.values()),
            'out_weight_sum': sum(self.outgoing.values()),
            'two_hop_size': len(self.two_hop_neighbors),
            'avg_anchor_distance': self._avg_anchor_distance(),
            'min_anchor_distance': self._min_anchor_distance(),
        }

    def _avg_anchor_distance(self) -> float:
        if not self.anchor_distances:
            return float('inf')
        return sum(self.anchor_distances.values()) / len(self.anchor_distances)

    def _min_anchor_distance(self) -> float:
        if not self.anchor_distances:
            return float('inf')
        return min(self.anchor_distances.values())


class StructuralSignature:
    """Represents a word's structural relationship to anchor words"""

    def __init__(self, word: str):
        self.word = word
        self.anchor_features = {}  # {anchor_name: feature_dict}

    def add_anchor_relationship(self, anchor_name: str, features: Dict[str, any]):
        """
        Add features describing relationship to a specific anchor

        Features per anchor:
        - graph_distance: minimum hops to reach anchor
        - precedes_anchor: whether word typically comes before anchor
        - follows_anchor: whether word typically comes after anchor
        - shared_predecessors: overlap in incoming edges
        - shared_successors: overlap in outgoing edges
        - cooccurrence_score: how often they appear in similar contexts
        """
        self.anchor_features[anchor_name] = features

    def similarity_to(self, other: 'StructuralSignature', anchor_pairs: List[Tuple[str, str]]) -> float:
        """
        Compute similarity score between two structural signatures

        Args:
            other: The other structural signature (in target language)
            anchor_pairs: List of (source_anchor, target_anchor) pairs

        Returns a score in [0, 1] where higher means more similar topology
        """
        if not anchor_pairs:
            return 0.0

        total_similarity = 0.0
        weights = 0.0

        for source_anchor, target_anchor in anchor_pairs:
            if source_anchor in self.anchor_features and target_anchor in other.anchor_features:
                anchor_sim = self._compare_anchor_features(
                    self.anchor_features[source_anchor],
                    other.anchor_features[target_anchor]
                )
                total_similarity += anchor_sim
                weights += 1.0

        return total_similarity / weights if weights > 0 else 0.0

    def _compare_anchor_features(self, f1: Dict, f2: Dict) -> float:
        """Compare two feature dictionaries for a single anchor"""
        score = 0.0
        count = 0

        # Distance similarity (closer distances = higher similarity)
        if 'graph_distance' in f1 and 'graph_distance' in f2:
            d1, d2 = f1['graph_distance'], f2['graph_distance']
            if d1 < float('inf') and d2 < float('inf'):
                # Exponential decay: same distance = 1.0, each hop difference reduces score
                distance_diff = abs(d1 - d2)
                score += math.exp(-distance_diff / 2.0)
                count += 1

        # Directional relationship (before/after anchor)
        if 'precedes_anchor' in f1 and 'precedes_anchor' in f2:
            if f1['precedes_anchor'] == f2['precedes_anchor']:
                score += 1.0
            count += 1

        if 'follows_anchor' in f1 and 'follows_anchor' in f2:
            if f1['follows_anchor'] == f2['follows_anchor']:
                score += 1.0
            count += 1

        # Shared neighbor overlap (Jaccard similarity)
        if 'shared_predecessors' in f1 and 'shared_predecessors' in f2:
            score += self._jaccard_similarity(
                f1['shared_predecessors'],
                f2['shared_predecessors']
            ) * 0.5  # Weight neighbor overlap less than direct relationships
            count += 0.5

        if 'shared_successors' in f1 and 'shared_successors' in f2:
            score += self._jaccard_similarity(
                f1['shared_successors'],
                f2['shared_successors']
            ) * 0.5
            count += 0.5

        # Co-occurrence score similarity
        if 'cooccurrence_score' in f1 and 'cooccurrence_score' in f2:
            s1, s2 = f1['cooccurrence_score'], f2['cooccurrence_score']
            # Normalize and compare
            max_score = max(s1, s2)
            if max_score > 0:
                score += min(s1, s2) / max_score
                count += 0.3

        return score / count if count > 0 else 0.0

    @staticmethod
    def _jaccard_similarity(set1: Set, set2: Set) -> float:
        """Jaccard similarity: |intersection| / |union|"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0


class MinimalAnchorTranslator:
    """
    Infers cross-lingual word translations using minimal anchor words
    and graph topology
    """

    def __init__(self, greek_dag_path: str, english_dag_path: str, max_hops: int = 3):
        """
        Initialize translator with both language DAGs

        Args:
            greek_dag_path: Path to Greek gospels DAG JSON
            english_dag_path: Path to English gospels DAG JSON
            max_hops: Maximum graph distance to explore for neighborhoods
        """
        self.max_hops = max_hops

        print(f"Loading Greek DAG from {greek_dag_path}...")
        with open(greek_dag_path, 'r', encoding='utf-8') as f:
            greek_data = json.load(f)

        print(f"Loading English DAG from {english_dag_path}...")
        with open(english_dag_path, 'r', encoding='utf-8') as f:
            english_data = json.load(f)

        # Build graph structures
        self.greek_graph = self._build_graph_index(greek_data, 'greek_')
        self.english_graph = self._build_graph_index(english_data, 'kjv_')

        # Count actual edges
        greek_edge_count = sum(len(targets) for targets in self.greek_graph['edges'].values())
        english_edge_count = sum(len(targets) for targets in self.english_graph['edges'].values())

        print(f"Greek graph: {len(self.greek_graph['nodes'])} nodes, {greek_edge_count} edges")
        print(f"English graph: {len(self.english_graph['nodes'])} nodes, {english_edge_count} edges")

        # Storage for computed signatures
        self.greek_signatures = {}
        self.english_signatures = {}

    def _build_graph_index(self, dag_data: Dict, prefix: str) -> Dict:
        """
        Build indexed graph structure for efficient traversal

        Returns:
            {
                'nodes': {word: node_data},
                'edges': {source: {target: weight}},
                'reverse_edges': {target: {source: weight}},
                'prefix': str
            }
        """
        nodes = {}
        edges = defaultdict(dict)
        reverse_edges = defaultdict(dict)

        graph = dag_data.get('graph', {})

        # Index nodes
        for node in graph.get('nodes', []):
            node_id = node['id']
            # Remove prefix to get clean word
            word = node_id[len(prefix):] if node_id.startswith(prefix) else node_id
            nodes[word] = node

        # Index edges (links)
        for link in graph.get('links', []):
            source_id = link['source']
            target_id = link['target']
            weight = link.get('weight', 1.0)

            # Remove prefix
            source = source_id[len(prefix):] if source_id.startswith(prefix) else source_id
            target = target_id[len(prefix):] if target_id.startswith(prefix) else target_id

            edges[source][target] = weight
            reverse_edges[target][source] = weight

        return {
            'nodes': nodes,
            'edges': edges,
            'reverse_edges': reverse_edges,
            'prefix': prefix
        }

    def extract_neighborhood(self, word: str, graph: Dict, max_hops: int = 2) -> GraphNeighborhood:
        """
        Extract k-hop neighborhood for a word in the graph

        Args:
            word: The word to analyze
            graph: Graph structure from _build_graph_index
            max_hops: Maximum distance to explore

        Returns:
            GraphNeighborhood object with neighborhood information
        """
        neighborhood = GraphNeighborhood(word)

        if word not in graph['nodes']:
            return neighborhood

        # Direct predecessors (incoming edges)
        if word in graph['reverse_edges']:
            for source, weight in graph['reverse_edges'][word].items():
                neighborhood.add_incoming(source, weight)

        # Direct successors (outgoing edges)
        if word in graph['edges']:
            for target, weight in graph['edges'][word].items():
                neighborhood.add_outgoing(target, weight)

        # Two-hop neighbors (for richer context)
        if max_hops >= 2:
            # Two hops forward
            for next_word in neighborhood.outgoing.keys():
                if next_word in graph['edges']:
                    for two_hop_word in graph['edges'][next_word].keys():
                        neighborhood.two_hop_neighbors.add(two_hop_word)

            # Two hops backward
            for prev_word in neighborhood.incoming.keys():
                if prev_word in graph['reverse_edges']:
                    for two_hop_word in graph['reverse_edges'][prev_word].keys():
                        neighborhood.two_hop_neighbors.add(two_hop_word)

        return neighborhood

    def compute_anchor_distance(self, word: str, anchor: str, graph: Dict, max_hops: int = 5) -> int:
        """
        Compute minimum graph distance from word to anchor using BFS

        Returns:
            Minimum number of hops, or float('inf') if unreachable
        """
        if word == anchor:
            return 0

        if word not in graph['nodes'] or anchor not in graph['nodes']:
            return float('inf')

        # BFS in both directions (forward and backward)
        visited = {word}
        queue = [(word, 0)]

        while queue:
            current, dist = queue.pop(0)

            if dist >= max_hops:
                break

            # Check forward edges
            if current in graph['edges']:
                for neighbor in graph['edges'][current].keys():
                    if neighbor == anchor:
                        return dist + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

            # Check backward edges
            if current in graph['reverse_edges']:
                for neighbor in graph['reverse_edges'][current].keys():
                    if neighbor == anchor:
                        return dist + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

        return float('inf')

    def compute_structural_signature(self, word: str, graph: Dict,
                                    anchor_words: List[str]) -> StructuralSignature:
        """
        Compute structural signature for a word relative to anchors

        Args:
            word: Word to analyze
            graph: Graph structure
            anchor_words: List of anchor words in this language

        Returns:
            StructuralSignature encoding relationships to all anchors
        """
        signature = StructuralSignature(word)
        neighborhood = self.extract_neighborhood(word, graph, max_hops=2)

        for anchor in anchor_words:
            if anchor not in graph['nodes']:
                continue

            anchor_neighborhood = self.extract_neighborhood(anchor, graph, max_hops=2)

            # Compute features for this anchor
            features = {
                'graph_distance': self.compute_anchor_distance(word, anchor, graph, max_hops=5),
                'precedes_anchor': anchor in neighborhood.outgoing,
                'follows_anchor': anchor in neighborhood.incoming,
                'shared_predecessors': set(neighborhood.incoming.keys()) & set(anchor_neighborhood.incoming.keys()),
                'shared_successors': set(neighborhood.outgoing.keys()) & set(anchor_neighborhood.outgoing.keys()),
                'cooccurrence_score': self._cooccurrence_score(neighborhood, anchor_neighborhood),
            }

            signature.add_anchor_relationship(anchor, features)

        return signature

    def _cooccurrence_score(self, n1: GraphNeighborhood, n2: GraphNeighborhood) -> float:
        """
        Compute how similar two words' contexts are (shared neighbors)
        """
        n1_context = set(n1.incoming.keys()) | set(n1.outgoing.keys())
        n2_context = set(n2.incoming.keys()) | set(n2.outgoing.keys())

        if not n1_context or not n2_context:
            return 0.0

        intersection = len(n1_context & n2_context)
        union = len(n1_context | n2_context)

        return intersection / union if union > 0 else 0.0

    def find_translation_candidates(self, greek_word: str, anchor_pairs: List[Tuple[str, str]],
                                   top_k: int = 10, min_confidence: float = 0.1) -> List[Dict]:
        """
        Find English translation candidates for a Greek word using anchor-based inference

        Args:
            greek_word: Greek word to translate
            anchor_pairs: List of (greek, english) known translation pairs
            top_k: Number of top candidates to return
            min_confidence: Minimum similarity score threshold

        Returns:
            List of candidate translations with scores, sorted by confidence
        """
        if greek_word not in self.greek_graph['nodes']:
            return []

        # Extract anchor words
        greek_anchors = [gk for gk, _ in anchor_pairs]
        english_anchors = [en for _, en in anchor_pairs]

        # Compute structural signature for the Greek word
        greek_sig = self.compute_structural_signature(
            greek_word, self.greek_graph, greek_anchors
        )

        # Compare against all English words
        candidates = []

        for english_word in self.english_graph['nodes'].keys():
            # Compute English word's signature
            english_sig = self.compute_structural_signature(
                english_word, self.english_graph, english_anchors
            )

            # Compute similarity (use anchor pairs for cross-lingual comparison)
            similarity = greek_sig.similarity_to(english_sig, anchor_pairs)

            if similarity >= min_confidence:
                candidates.append({
                    'greek': greek_word,
                    'english': english_word,
                    'confidence': similarity,
                    'anchor_details': self._get_anchor_details(greek_sig, english_sig, anchor_pairs)
                })

        # Sort by confidence (descending)
        candidates.sort(key=lambda x: x['confidence'], reverse=True)

        return candidates[:top_k]

    def _get_anchor_details(self, greek_sig: StructuralSignature,
                          english_sig: StructuralSignature,
                          anchor_pairs: List[Tuple[str, str]]) -> Dict:
        """Get detailed comparison per anchor for interpretation"""
        details = {}

        for greek_anchor, english_anchor in anchor_pairs:
            if greek_anchor in greek_sig.anchor_features and english_anchor in english_sig.anchor_features:
                gf = greek_sig.anchor_features[greek_anchor]
                ef = english_sig.anchor_features[english_anchor]

                details[f"{greek_anchor}→{english_anchor}"] = {
                    'greek_distance': gf.get('graph_distance', float('inf')),
                    'english_distance': ef.get('graph_distance', float('inf')),
                    'both_precede': gf.get('precedes_anchor', False) and ef.get('precedes_anchor', False),
                    'both_follow': gf.get('follows_anchor', False) and ef.get('follows_anchor', False),
                }

        return details

    def batch_translate(self, greek_words: List[str], anchor_pairs: List[Tuple[str, str]],
                       top_k: int = 5) -> Dict[str, List[Dict]]:
        """
        Translate multiple Greek words at once

        Returns:
            {greek_word: [candidates]}
        """
        results = {}

        for greek_word in greek_words:
            print(f"  Translating: {greek_word}")
            candidates = self.find_translation_candidates(greek_word, anchor_pairs, top_k=top_k)
            results[greek_word] = candidates

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Anchor Translator: Infer translations using graph topology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use only 2 anchor words to infer others
  python3 minimal_anchor_translator.py \\
    --greek data/byzantine_gospels_dag.json \\
    --english data/kjv_gospels_dag.json \\
    --anchors "καί:and" "δὲ:but" \\
    --translate "ἐν" "εἰς" "ὁ"

  # Find translation for a single word with 4 anchors
  python3 minimal_anchor_translator.py \\
    --greek data/byzantine_gospels_dag.json \\
    --english data/kjv_gospels_dag.json \\
    --anchors "καί:and" "δὲ:but" "ἐν:in" "εἰς:into" \\
    --translate "ὁ" \\
    --top-k 10
        """
    )

    parser.add_argument('--greek', required=True, help='Path to Greek DAG JSON')
    parser.add_argument('--english', required=True, help='Path to English DAG JSON')
    parser.add_argument('--anchors', nargs='+', required=True,
                       help='Known translation pairs (format: greek:english)')
    parser.add_argument('--translate', nargs='+', required=True,
                       help='Greek words to find English translations for')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of top candidates to show (default: 5)')
    parser.add_argument('--min-confidence', type=float, default=0.1,
                       help='Minimum confidence threshold (default: 0.1)')
    parser.add_argument('--output', help='Output JSON file (optional)')

    args = parser.parse_args()

    # Parse anchor pairs
    anchor_pairs = []
    for anchor_spec in args.anchors:
        try:
            greek, english = anchor_spec.split(':')
            anchor_pairs.append((greek.strip(), english.strip()))
        except ValueError:
            print(f"Error: Invalid anchor format '{anchor_spec}'. Use 'greek:english'")
            return 1

    print(f"\nMinimal Anchor Translator")
    print(f"=" * 60)
    print(f"Using {len(anchor_pairs)} anchor word pairs:")
    for gk, en in anchor_pairs:
        print(f"  {gk} → {en}")
    print()

    # Initialize translator
    translator = MinimalAnchorTranslator(args.greek, args.english)

    # Translate words
    print(f"\nFinding translations for {len(args.translate)} Greek words...")
    print()

    results = translator.batch_translate(args.translate, anchor_pairs, top_k=args.top_k)

    # Display results
    print("\n" + "=" * 60)
    print("TRANSLATION CANDIDATES")
    print("=" * 60)

    for greek_word, candidates in results.items():
        print(f"\nGreek word: {greek_word}")
        print("-" * 60)

        if not candidates:
            print("  No candidates found (word may not exist in graph)")
            continue

        for i, candidate in enumerate(candidates, 1):
            print(f"\n  {i}. {candidate['english']}")
            print(f"     Confidence: {candidate['confidence']:.4f}")

            # Show anchor-specific details
            print(f"     Anchor relationships:")
            for anchor_name, details in candidate['anchor_details'].items():
                greek_dist = details['greek_distance']
                english_dist = details['english_distance']

                dist_str = f"{greek_dist} ↔ {english_dist}"
                if greek_dist == float('inf'):
                    dist_str = "unreachable"

                positions = []
                if details['both_precede']:
                    positions.append("both precede anchor")
                if details['both_follow']:
                    positions.append("both follow anchor")

                position_str = ", ".join(positions) if positions else "different positions"

                print(f"       {anchor_name}: distance={dist_str}, {position_str}")

    # Save to JSON if requested
    if args.output:
        output_data = {
            'metadata': {
                'anchor_pairs': [{'greek': gk, 'english': en} for gk, en in anchor_pairs],
                'num_anchors': len(anchor_pairs),
                'top_k': args.top_k,
                'min_confidence': args.min_confidence,
            },
            'translations': results
        }

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n\nResults saved to: {args.output}")

    print("\n")
    return 0


if __name__ == '__main__':
    exit(main())
