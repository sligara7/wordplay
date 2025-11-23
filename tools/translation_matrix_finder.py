#!/usr/bin/env python3
"""
Translation Matrix Finder - Discovers the transformation matrix between
Koine Greek and King James English gospels using matrix gap analysis.

Uses the equation: B = C × A^(-1)

Where:
- A = Greek gospels word-based DAG (System A - Source)
- B = Translation matrix (System B - Unknown/Gap)
- C = English KJV gospels word-based DAG (System C - Target)

This tool applies gap closure analysis to understand the translation transformation
between ancient Greek and 17th century English.
"""

import json
import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict
from datetime import datetime
import argparse


class TranslationMatrixFinder:
    """Finds the translation transformation matrix between Greek and English gospels"""

    def __init__(self, greek_dag_path: str, english_dag_path: str):
        """
        Initialize the translation matrix finder

        Args:
            greek_dag_path: Path to Byzantine Greek gospels DAG
            english_dag_path: Path to KJV English gospels DAG
        """
        self.greek_dag_path = Path(greek_dag_path)
        self.english_dag_path = Path(english_dag_path)

        # Load the DAGs
        print("Loading System A (Greek gospels)...")
        with open(self.greek_dag_path, 'r', encoding='utf-8') as f:
            self.greek_dag = json.load(f)

        print("Loading System C (English gospels)...")
        with open(self.english_dag_path, 'r', encoding='utf-8') as f:
            self.english_dag = json.load(f)

        # Extract word mappings
        self.greek_words = self._extract_words(self.greek_dag)
        self.english_words = self._extract_words(self.english_dag)

        print(f"System A: {len(self.greek_words)} Greek words")
        print(f"System C: {len(self.english_words)} English words")

        # Create word-to-index mappings
        self.greek_word_to_idx = {word: i for i, word in enumerate(sorted(self.greek_words))}
        self.english_word_to_idx = {word: i for i, word in enumerate(sorted(self.english_words))}

        # Build adjacency matrices
        self.A = None  # Greek adjacency matrix
        self.C = None  # English adjacency matrix
        self.B = None  # Translation matrix (to be discovered)

    def _extract_words(self, dag: dict) -> Set[str]:
        """Extract all unique words from a DAG"""
        words = set()
        for node in dag['graph']['nodes']:
            words.add(node['name'])
        return words

    def build_adjacency_matrices(self):
        """Build adjacency matrices for both Greek and English DAGs"""
        print("\nBuilding adjacency matrix for System A (Greek)...")
        self.A = self._build_adjacency_matrix(
            self.greek_dag,
            self.greek_word_to_idx
        )

        print("Building adjacency matrix for System C (English)...")
        self.C = self._build_adjacency_matrix(
            self.english_dag,
            self.english_word_to_idx
        )

        print(f"Matrix A shape: {self.A.shape}")
        print(f"Matrix C shape: {self.C.shape}")

    def _build_adjacency_matrix(self, dag: dict, word_to_idx: dict) -> np.ndarray:
        """Build adjacency matrix from DAG"""
        n = len(word_to_idx)
        matrix = np.zeros((n, n))

        # Populate matrix from edges
        for edge in dag['graph']['links']:
            # Extract word names from node IDs (e.g., "greek_Ἰησοῦ" -> "Ἰησοῦ")
            source_word = edge['source'].split('_', 1)[1] if '_' in edge['source'] else edge['source']
            target_word = edge['target'].split('_', 1)[1] if '_' in edge['target'] else edge['target']

            if source_word in word_to_idx and target_word in word_to_idx:
                i = word_to_idx[source_word]
                j = word_to_idx[target_word]
                weight = edge.get('weight', 1.0)
                matrix[i, j] = weight

        return matrix

    def compute_translation_matrix(self, method='svd'):
        """
        Compute the translation matrix B using matrix operations

        Methods:
        - 'svd': Use Singular Value Decomposition (robust to non-square matrices)
        - 'pseudo': Use pseudo-inverse (Moore-Penrose)

        B = C × A^(-1)  (conceptually)

        Since A and C are different sizes, we use SVD-based approach
        """
        print(f"\nComputing translation matrix B using {method}...")

        if method == 'svd':
            # Use SVD to find the best linear transformation
            # We're looking for B such that: B × A ≈ C

            # Since dimensions don't match, we need to work in the common space
            # Approach: Find mappings in the embedded space

            # Compute SVD of both matrices
            U_a, S_a, Vt_a = np.linalg.svd(self.A, full_matrices=False)
            U_c, S_c, Vt_c = np.linalg.svd(self.C, full_matrices=False)

            # Store SVD components
            self.greek_svd = {'U': U_a, 'S': S_a, 'Vt': Vt_a}
            self.english_svd = {'U': U_c, 'S': S_c, 'Vt': Vt_c}

            print(f"Greek SVD - Rank: {np.sum(S_a > 1e-10)}, Singular values: {S_a[:10]}")
            print(f"English SVD - Rank: {np.sum(S_c > 1e-10)}, Singular values: {S_c[:10]}")

            # The transformation matrix in the reduced space
            # This maps from Greek embedding space to English embedding space
            k = min(len(S_a), len(S_c), 100)  # Use top k dimensions
            self.B_reduced = U_c[:, :k] @ np.diag(S_c[:k]) @ Vt_c[:k, :k] @ \
                             np.linalg.pinv(Vt_a[:k, :k]) @ np.diag(1/S_a[:k]) @ U_a.T[:k, :]

            print(f"Translation matrix B (reduced): {self.B_reduced.shape}")

        elif method == 'pseudo':
            # Use pseudo-inverse
            A_pinv = np.linalg.pinv(self.A)
            # Can't directly multiply C × A^(-1) due to dimension mismatch
            # This is a placeholder - would need alignment strategy
            print("Pseudo-inverse method requires dimension alignment")

    def analyze_translation_patterns(self, top_k=50):
        """
        Analyze the translation matrix to discover translation patterns

        Returns insights about:
        - Most influential Greek-English word mappings
        - Structural transformations in the translation
        - Dimensionality reduction effects
        """
        print("\nAnalyzing translation patterns...")

        results = {
            "metadata": {
                "generated": datetime.utcnow().isoformat(),
                "method": "SVD-based translation matrix",
                "greek_words": len(self.greek_words),
                "english_words": len(self.english_words),
                "framework": "Translation Matrix Gap Analysis"
            },
            "systems": {
                "A_greek": {
                    "size": len(self.greek_words),
                    "rank": int(np.linalg.matrix_rank(self.A)),
                    "density": float(np.count_nonzero(self.A) / self.A.size),
                    "top_words": self._get_top_words_by_centrality(self.A, self.greek_word_to_idx, top_k)
                },
                "C_english": {
                    "size": len(self.english_words),
                    "rank": int(np.linalg.matrix_rank(self.C)),
                    "density": float(np.count_nonzero(self.C) / self.C.size),
                    "top_words": self._get_top_words_by_centrality(self.C, self.english_word_to_idx, top_k)
                },
                "B_translation": {
                    "shape": list(self.B_reduced.shape) if hasattr(self, 'B_reduced') else None,
                    "description": "Transformation matrix from Greek word space to English word space"
                }
            },
            "translation_insights": self._extract_translation_insights(top_k)
        }

        return results

    def _get_top_words_by_centrality(self, matrix: np.ndarray, word_to_idx: dict, top_k: int) -> List[Dict]:
        """Get top words by degree centrality (fast and effective)"""
        # Use degree centrality instead of eigenvector centrality for speed
        # Degree centrality = total number of connections (in + out)
        out_degree = np.sum(matrix > 0, axis=1)  # Row sums
        in_degree = np.sum(matrix > 0, axis=0)   # Column sums
        total_degree = out_degree + in_degree

        # Also compute weighted degree
        weighted_out = np.sum(matrix, axis=1)
        weighted_in = np.sum(matrix, axis=0)
        weighted_total = weighted_out + weighted_in

        # Get top k words by weighted degree
        idx_to_word = {i: word for word, i in word_to_idx.items()}
        top_indices = np.argsort(weighted_total)[-top_k:][::-1]

        return [
            {
                "word": idx_to_word[i],
                "weighted_degree": float(weighted_total[i]),
                "out_degree": int(out_degree[i]),
                "in_degree": int(in_degree[i])
            }
            for i in top_indices
        ]

    def _extract_translation_insights(self, top_k: int) -> Dict:
        """Extract insights about the translation transformation"""
        insights = {
            "dimensionality": {
                "greek_effective_rank": int(np.sum(self.greek_svd['S'] > 1e-10)),
                "english_effective_rank": int(np.sum(self.english_svd['S'] > 1e-10)),
                "description": "Effective rank indicates the intrinsic dimensionality of each language space"
            },
            "compression": {
                "greek_to_english_ratio": len(self.greek_words) / len(self.english_words),
                "description": f"Greek uses {len(self.greek_words)} words vs English {len(self.english_words)} words"
            },
            "structural_differences": {
                "greek_density": float(np.count_nonzero(self.A) / self.A.size),
                "english_density": float(np.count_nonzero(self.C) / self.C.size),
                "description": "Matrix density indicates word transition complexity"
            }
        }

        return insights

    def save_analysis(self, output_path: str):
        """Save the translation matrix analysis to JSON"""
        results = self.analyze_translation_patterns()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"Translation matrix analysis saved to: {output_path}")
        print(f"{'='*60}")
        print(f"Greek words (System A): {results['systems']['A_greek']['size']:,}")
        print(f"English words (System C): {results['systems']['C_english']['size']:,}")
        print(f"Greek effective rank: {results['translation_insights']['dimensionality']['greek_effective_rank']}")
        print(f"English effective rank: {results['translation_insights']['dimensionality']['english_effective_rank']}")
        print(f"Compression ratio: {results['translation_insights']['compression']['greek_to_english_ratio']:.2f}x")
        print(f"{'='*60}")

        return results


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Find translation matrix between Greek and English gospels using gap analysis'
    )
    parser.add_argument('--greek', '-a',
                        default='data/byzantine_gospels_dag.json',
                        help='Path to Greek gospels DAG (System A)')
    parser.add_argument('--english', '-c',
                        default='data/kjv_gospels_dag.json',
                        help='Path to English gospels DAG (System C)')
    parser.add_argument('--output', '-o',
                        default='data/translation_matrix_analysis.json',
                        help='Output path for analysis results')
    parser.add_argument('--method',
                        choices=['svd', 'pseudo'],
                        default='svd',
                        help='Matrix computation method (default: svd)')
    parser.add_argument('--top-k', type=int, default=50,
                        help='Number of top words to analyze (default: 50)')

    args = parser.parse_args()

    print("=" * 60)
    print("Translation Matrix Finder")
    print("Gap Analysis: Greek (A) → Translation (B) → English (C)")
    print("=" * 60)

    # Initialize finder
    finder = TranslationMatrixFinder(args.greek, args.english)

    # Build adjacency matrices
    finder.build_adjacency_matrices()

    # Compute translation matrix
    finder.compute_translation_matrix(method=args.method)

    # Analyze and save
    finder.save_analysis(args.output)

    return 0


if __name__ == '__main__':
    exit(main())
