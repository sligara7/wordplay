#!/usr/bin/env python3
"""
Matrix-Based Gap Detection for Chain Reflow

Uses linear algebra and matrix operations to mathematically infer missing
intermediate systems between known system architectures.

Key Insight (Homography Matrix Analogy):
Just as a homography matrix transforms one image perspective to another,
missing systems can be solved as transformation matrices:

    B = C * A^(-1)

Where:
- A is the "before" system (e.g., unchecked deer population)
- C is the "after" system (e.g., balanced ecosystem)
- B is the missing transformation (e.g., wolf predation system)

Advanced Multi-Layer Detection:
Using Singular Value Decomposition (SVD), we can detect if the missing
system B is actually composed of multiple subsystems:

    B = Bn * ... * B2 * B1

This is analogous to multi-layer neural networks where complex transformations
are decomposed into simpler sequential operations.

Example (Yellowstone Wolf Reintroduction):
- System A (vegetation): Degraded, over-browsed
- System C (deer): Unchecked population
- Missing System B decomposes into:
  - B1: Wolf predation (direct killing)
  - B2: Landscape of fear (behavioral change)
  - B3: Cascading ecosystem effects

Mathematical Approach:
1. Represent systems as adjacency matrices (graphs as matrices)
2. Solve for transformation matrix B = C * A^(-1)
3. Use SVD to decompose B into subsystems
4. Interpret matrix properties as system characteristics
5. Generate hypotheses about missing system identity

"""

import json
import sys
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class SystemType(Enum):
    """Types of systems in ecological/engineered contexts"""
    ECOLOGICAL = "ecological"
    ENGINEERED = "engineered"
    SOCIO_TECHNICAL = "socio_technical"
    BIOLOGICAL = "biological"
    UNKNOWN = "unknown"


@dataclass
class GraphSystem:
    """
    Represent a system-of-systems as graph matrices.

    A system is represented by:
    - Adjacency matrix: Node-to-node connections and weights
    - Node states: Current state of each component
    - Metadata: System properties and classifications
    """
    name: str
    nodes: List[str]
    adjacency: np.ndarray = None
    node_states: np.ndarray = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize matrices if not provided"""
        n = len(self.nodes)
        if self.adjacency is None:
            self.adjacency = np.zeros((n, n))
        if self.node_states is None:
            self.node_states = np.zeros(n)
        if self.metadata is None:
            self.metadata = {}

    @property
    def n(self) -> int:
        """Number of nodes in system"""
        return len(self.nodes)

    def add_edge(self, from_node: str, to_node: str, weight: float = 1.0):
        """Add weighted edge to adjacency matrix"""
        try:
            i = self.nodes.index(from_node)
            j = self.nodes.index(to_node)
            self.adjacency[i, j] = weight
        except ValueError as e:
            raise ValueError(f"Node not found: {e}")

    def set_node_state(self, node: str, state: float):
        """Set state value for a node"""
        try:
            i = self.nodes.index(node)
            self.node_states[i] = state
        except ValueError as e:
            raise ValueError(f"Node not found: {e}")

    def get_matrix_properties(self) -> Dict[str, Any]:
        """Compute matrix properties for interpretation"""
        rank = np.linalg.matrix_rank(self.adjacency)
        eigenvalues, _ = np.linalg.eig(self.adjacency)
        max_eigenvalue = np.max(np.abs(eigenvalues))

        return {
            "rank": int(rank),
            "condition_number": float(np.linalg.cond(self.adjacency)),
            "max_eigenvalue": float(max_eigenvalue),
            "trace": float(np.trace(self.adjacency)),
            "frobenius_norm": float(np.linalg.norm(self.adjacency, 'fro')),
            "is_singular": bool(np.linalg.det(self.adjacency) == 0)
        }

    @classmethod
    def from_json(cls, filepath: Path) -> 'GraphSystem':
        """
        Load system from JSON file with auto-format detection.

        Supports three formats:
        1. Ecosystem format: {graph: {nodes: [{id, name}], links: [{source, target, strength}]}}
        2. System of systems format: {system_of_systems_graph: {nodes: [{node_id, node_name}], edges: [...]}}
        3. Simple format: {nodes: [{id}], edges: [{source, target}]}
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Format detection and normalization
        graph_data = None
        system_name = filepath.stem
        metadata = {}

        # Format 1: Check for ecosystem format {metadata: {...}, graph: {nodes, links}}
        if 'graph' in data and isinstance(data['graph'], dict):
            graph_data = data['graph']
            system_name = data.get('metadata', {}).get('system_name', filepath.stem)
            metadata = data.get('metadata', {})
            # Normalize ecosystem format: links → edges, strength → weight
            if 'links' in graph_data and 'edges' not in graph_data:
                graph_data['edges'] = graph_data.pop('links')
            # Extract nodes
            if 'nodes' in graph_data:
                nodes = [n.get('id', n.get('name', f"node_{i}")) for i, n in enumerate(graph_data['nodes'])]
            else:
                raise ValueError("No nodes found in ecosystem graph")

        # Format 2: Check for system_of_systems_graph format
        elif 'system_of_systems_graph' in data:
            sos_graph = data['system_of_systems_graph']
            graph_data = sos_graph
            system_name = sos_graph.get('metadata', {}).get('system_name', filepath.stem)
            metadata = sos_graph.get('metadata', {})
            # Normalize field names: node_id → id
            if 'nodes' in graph_data:
                nodes = [n.get('node_id', n.get('id', f"node_{i}")) for i, n in enumerate(graph_data['nodes'])]
            else:
                raise ValueError("No nodes found in system_of_systems_graph")

        # Format 3: Simple direct format {nodes: [...], edges: [...]}
        elif 'nodes' in data:
            graph_data = data
            nodes = [n.get('id', n.get('node_id', f"node_{i}")) for i, n in enumerate(data['nodes'])]
            metadata = data.get('architecture_metadata', {})

        elif 'components' in data:
            graph_data = data
            nodes = [c.get('id', c.get('component_id', f"comp_{i}")) for i, c in enumerate(data['components'])]
            metadata = data.get('architecture_metadata', {})

        else:
            raise ValueError(f"Unknown graph format in {filepath}. Expected 'graph', 'system_of_systems_graph', 'nodes', or 'components' key")

        # Create system
        system = cls(
            name=system_name,
            nodes=nodes,
            metadata=metadata
        )

        # Load edges (supports both 'edges' and 'links' naming)
        edges_key = 'edges' if 'edges' in graph_data else 'links' if 'links' in graph_data else None
        if edges_key:
            for edge in graph_data[edges_key]:
                # Support various weight field names
                weight = edge.get('weight', edge.get('strength', 1.0))
                # Handle different edge formats
                source = edge.get('source', edge.get('from'))
                target = edge.get('target', edge.get('to'))
                if source and target:
                    try:
                        system.add_edge(source, target, weight)
                    except ValueError:
                        # Skip edges referencing nodes not in our node list
                        # (e.g., "MISSING_SYSTEM" placeholders)
                        pass

        # Load node states if available
        if 'components' in graph_data:
            for comp in graph_data['components']:
                if 'state' in comp:
                    comp_id = comp.get('id', comp.get('component_id'))
                    if comp_id:
                        try:
                            system.set_node_state(comp_id, comp['state'])
                        except ValueError:
                            pass

        return system

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary"""
        return {
            "name": self.name,
            "nodes": self.nodes,
            "adjacency_matrix": self.adjacency.tolist(),
            "node_states": self.node_states.tolist(),
            "matrix_properties": self.get_matrix_properties(),
            "metadata": self.metadata
        }


@dataclass
class SystemInteraction:
    """
    Represents interaction/dependency between two systems.

    In the homography analogy:
    - Source system provides input
    - Target system is affected by source
    - Interaction strength determines coupling
    """
    source_system: str
    target_system: str
    interaction_type: str  # "controls", "affects", "depends_on", etc.
    strength: float = 1.0  # 0-1 scale
    mechanism: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MissingSystemSolver:
    """
    Solve for missing intermediary system using matrix operations.

    Given:
    - System A (before state)
    - System C (after state)
    - Interaction between them

    Solve for:
    - System B (transformation that connects A to C)

    Mathematical approach:
        B should transform A to C
        C_state = B * A_state
        Therefore: B = C_state * A_state^(-1)

    For ecosystem example:
        A = Vegetation (degraded)
        C = Deer population (unchecked)
        B = Missing predator control system
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def solve(self,
              system_a: GraphSystem,
              system_c: GraphSystem,
              interaction: Optional[SystemInteraction] = None) -> Dict[str, Any]:
        """
        Solve for missing system B that links A and C.

        Returns:
            Dictionary containing:
            - transformation_matrix: The B matrix
            - properties: Interpreted characteristics
            - confidence: Solution quality metrics
            - hypotheses: Possible identities for B
        """
        if self.verbose:
            print(f"Solving for missing system between:")
            print(f"  System A: {system_a.name} ({system_a.n} nodes)")
            print(f"  System C: {system_c.name} ({system_c.n} nodes)")

        # Align dimensionality (if systems have different sizes)
        max_n = max(system_a.n, system_c.n)
        A_padded = self._pad_matrix(system_a.adjacency, max_n)
        C_padded = self._pad_matrix(system_c.adjacency, max_n)

        # Solve B = C * A^(-1)
        A_inv = np.linalg.pinv(A_padded)  # Use pseudoinverse for robustness
        B_matrix = C_padded @ A_inv

        # Compute solution quality metrics
        reconstruction_error = np.linalg.norm(C_padded - B_matrix @ A_padded, 'fro')

        result = {
            "transformation_matrix": B_matrix.tolist(),
            "dimensions": list(B_matrix.shape),
            "properties": self._interpret_transformation_matrix(B_matrix),
            "confidence": self._calculate_confidence(B_matrix, reconstruction_error),
            "hypotheses": self._generate_hypotheses(B_matrix, system_a, system_c),
            "reconstruction_error": float(reconstruction_error),
            "solver_method": "pseudoinverse"
        }

        if self.verbose:
            print(f"  Solution rank: {result['properties']['rank']}")
            print(f"  Confidence: {result['confidence']['overall']:.2f}")
            print(f"  Reconstruction error: {reconstruction_error:.4f}")

        return result

    def _pad_matrix(self, matrix: np.ndarray, target_size: int) -> np.ndarray:
        """Pad matrix with zeros to target size"""
        current_size = matrix.shape[0]
        if current_size >= target_size:
            return matrix

        padded = np.zeros((target_size, target_size))
        padded[:current_size, :current_size] = matrix
        return padded

    def _interpret_transformation_matrix(self, B: np.ndarray) -> Dict[str, Any]:
        """Interpret mathematical properties of transformation matrix"""
        rank = np.linalg.matrix_rank(B)
        eigenvalues, eigenvectors = np.linalg.eig(B)

        # Classify transformation type
        is_identity = np.allclose(B, np.eye(B.shape[0]))
        is_sparse = np.sum(np.abs(B) > 0.01) / B.size < 0.3
        is_diagonal = np.allclose(B, np.diag(np.diagonal(B)))

        return {
            "rank": int(rank),
            "full_rank": bool(rank == B.shape[0]),
            "eigenvalue_magnitudes": [float(abs(ev)) for ev in eigenvalues[:5]],
            "dominant_eigenvalue": float(max(abs(eigenvalues))),
            "is_identity": bool(is_identity),
            "is_sparse": bool(is_sparse),
            "is_diagonal": bool(is_diagonal),
            "sparsity": float(np.sum(np.abs(B) > 0.01) / B.size),
            "frobenius_norm": float(np.linalg.norm(B, 'fro'))
        }

    def _calculate_confidence(self, B: np.ndarray, error: float) -> Dict[str, Any]:
        """Calculate confidence metrics for solution"""
        rank = np.linalg.matrix_rank(B)
        max_rank = B.shape[0]

        # Low reconstruction error = high confidence
        error_score = np.exp(-error)

        # Full rank = well-determined system
        rank_score = rank / max_rank

        # Not too sparse or too dense
        sparsity = np.sum(np.abs(B) > 0.01) / B.size
        sparsity_score = 1.0 - abs(sparsity - 0.5)  # Prefer moderate sparsity

        overall = (error_score + rank_score + sparsity_score) / 3.0

        return {
            "overall": float(overall),
            "reconstruction_quality": float(error_score),
            "rank_quality": float(rank_score),
            "sparsity_quality": float(sparsity_score),
            "interpretation": self._confidence_interpretation(overall)
        }

    def _confidence_interpretation(self, score: float) -> str:
        """Human-readable confidence interpretation"""
        if score >= 0.8:
            return "HIGH - Strong evidence for specific missing system"
        elif score >= 0.6:
            return "MEDIUM - Likely missing system, needs validation"
        elif score >= 0.4:
            return "LOW - Weak evidence, multiple possibilities"
        else:
            return "VERY_LOW - Insufficient data or poorly constrained"

    def _generate_hypotheses(self,
                           B: np.ndarray,
                           system_a: GraphSystem,
                           system_c: GraphSystem) -> List[Dict[str, Any]]:
        """Generate hypotheses about missing system identity"""
        hypotheses = []

        properties = self._interpret_transformation_matrix(B)

        # Hypothesis 1: Based on matrix rank
        if properties['full_rank']:
            hypotheses.append({
                "type": "complex_system",
                "description": "Full-rank transformation suggests complex multi-component system",
                "confidence": 0.7,
                "characteristics": ["multiple interacting components", "distributed control"]
            })
        elif properties['rank'] < 3:
            hypotheses.append({
                "type": "simple_system",
                "description": "Low-rank transformation suggests simple regulatory mechanism",
                "confidence": 0.8,
                "characteristics": ["single dominant mechanism", "centralized control"]
            })

        # Hypothesis 2: Based on sparsity
        if properties['is_sparse']:
            hypotheses.append({
                "type": "targeted_intervention",
                "description": "Sparse matrix suggests targeted intervention on specific components",
                "confidence": 0.75,
                "characteristics": ["selective pressure", "keystone species", "critical component"]
            })

        # Hypothesis 3: Based on eigenvalues
        dominant_ev = properties['dominant_eigenvalue']
        if dominant_ev > 1.5:
            hypotheses.append({
                "type": "amplifying_system",
                "description": "Dominant eigenvalue > 1 suggests amplifying or cascading mechanism",
                "confidence": 0.7,
                "characteristics": ["trophic cascade", "positive feedback", "growth mechanism"]
            })
        elif dominant_ev < 0.5:
            hypotheses.append({
                "type": "dampening_system",
                "description": "Dominant eigenvalue < 1 suggests dampening or stabilizing mechanism",
                "confidence": 0.7,
                "characteristics": ["negative feedback", "regulatory control", "homeostasis"]
            })

        return hypotheses


class MultiLayerGapDetector:
    """
    Detect and decompose missing systems into multiple subsystems using SVD.

    Key Insight (Neural Network Analogy):
    Just as deep neural networks decompose complex transformations into
    multiple simpler layers, missing systems may actually be chains of
    subsystems:

        B = Bn * Bn-1 * ... * B2 * B1

    SVD Decomposition Approach:
        B = U * Σ * V^T

    Where:
    - U: Left singular vectors (output space basis)
    - Σ: Singular values (importance of each component)
    - V^T: Right singular vectors (input space basis)

    Number of significant singular values indicates number of subsystems.

    Example (Wolf System Decomposition):
        B_wolf = B3 * B2 * B1
        B1 = Wolf predation (primary mechanism)
        B2 = Landscape of fear (behavioral cascade)
        B3 = Ecosystem restructuring (tertiary effects)
    """

    def __init__(self, threshold: float = 0.1, verbose: bool = False):
        """
        Args:
            threshold: Minimum normalized singular value to count as layer
            verbose: Print detailed analysis
        """
        self.threshold = threshold
        self.verbose = verbose

    def detect(self,
               system_a: GraphSystem,
               system_c: GraphSystem,
               interaction: Optional[SystemInteraction] = None) -> Dict[str, Any]:
        """
        Detect if missing system is multi-layer and decompose.

        Returns:
            Dictionary containing:
            - num_subsystems: Number of layers detected
            - subsystems: List of subsystem descriptions
            - singular_values: Importance of each layer
            - decomposition_method: SVD details
        """
        # First solve for composite B
        solver = MissingSystemSolver(verbose=self.verbose)
        result = solver.solve(system_a, system_c, interaction)
        B = np.array(result['transformation_matrix'])

        if self.verbose:
            print("\n=== Multi-Layer Decomposition ===")
            print(f"Analyzing transformation matrix B ({B.shape[0]}x{B.shape[1]})")

        # SVD decomposition
        U, S, Vt = np.linalg.svd(B, full_matrices=False)

        # Normalize singular values
        S_norm = S / S[0] if S[0] > 0 else S

        # Count significant layers
        num_layers = int(np.sum(S_norm > self.threshold))

        if self.verbose:
            print(f"Singular values (normalized): {S_norm[:5]}")
            print(f"Number of subsystems detected: {num_layers}")

        # Decompose based on number of layers
        if num_layers == 1:
            subsystems = self._single_layer_interpretation(U, S, Vt, system_a, system_c)
        elif num_layers == 2:
            subsystems = self._two_layer_decomposition(U, S, Vt, system_a, system_c)
        else:
            subsystems = self._multilayer_decomposition(U, S, Vt, num_layers, system_a, system_c)

        return {
            "num_subsystems": num_layers,
            "subsystems": subsystems,
            "singular_values": S.tolist(),
            "singular_values_normalized": S_norm.tolist(),
            "threshold": self.threshold,
            "decomposition_method": "SVD",
            "confidence": self._layer_confidence(S_norm, num_layers),
            "original_solution": result
        }

    def _single_layer_interpretation(self,
                                    U: np.ndarray,
                                    S: np.ndarray,
                                    Vt: np.ndarray,
                                    system_a: GraphSystem,
                                    system_c: GraphSystem) -> List[Dict[str, Any]]:
        """Interpret single dominant mechanism"""
        return [{
            "id": "B1",
            "name": "Primary_Mechanism",
            "rank": 1,
            "description": "Single dominant mechanism linking systems",
            "strength": float(S[0]),
            "characteristics": [
                "Direct transformation",
                "No intermediate cascades",
                "Simple regulatory mechanism"
            ],
            "matrix_summary": {
                "type": "rank-1 approximation",
                "dominant_singular_value": float(S[0])
            }
        }]

    def _two_layer_decomposition(self,
                                 U: np.ndarray,
                                 S: np.ndarray,
                                 Vt: np.ndarray,
                                 system_a: GraphSystem,
                                 system_c: GraphSystem) -> List[Dict[str, Any]]:
        """
        Decompose into two subsystems: B = B2 * B1

        Using SVD: B = U * Σ * V^T
        We can write: B = (U * √Σ) * (√Σ * V^T)
                       = B2 * B1
        """
        sqrt_S = np.sqrt(np.diag(S))

        B1 = U @ sqrt_S  # Primary mechanism (U-side)
        B2 = sqrt_S @ Vt  # Secondary cascade (V-side)

        return [
            {
                "id": "B1",
                "name": "Primary_Mechanism",
                "rank": 1,
                "description": "First-order effect (direct interaction)",
                "strength": float(S[0]),
                "characteristics": self._interpret_layer_characteristics(B1, "primary"),
                "matrix_summary": {
                    "type": "left singular vectors (U * √Σ)",
                    "dominant_components": self._get_dominant_components(B1, system_a.nodes, top_k=3)
                }
            },
            {
                "id": "B2",
                "name": "Secondary_Cascade",
                "rank": 2,
                "description": "Second-order effect (cascading consequences)",
                "strength": float(S[1]) if len(S) > 1 else 0.0,
                "characteristics": self._interpret_layer_characteristics(B2, "secondary"),
                "matrix_summary": {
                    "type": "right singular vectors (√Σ * V^T)",
                    "dominant_components": self._get_dominant_components(B2, system_c.nodes, top_k=3)
                }
            }
        ]

    def _multilayer_decomposition(self,
                                  U: np.ndarray,
                                  S: np.ndarray,
                                  Vt: np.ndarray,
                                  num_layers: int,
                                  system_a: GraphSystem,
                                  system_c: GraphSystem) -> List[Dict[str, Any]]:
        """Decompose into multiple subsystems"""
        subsystems = []

        for i in range(num_layers):
            layer_strength = float(S[i])
            layer_importance = float(S[i] / S[0])

            subsystems.append({
                "id": f"B{i+1}",
                "name": f"Layer_{i+1}",
                "rank": i + 1,
                "description": f"Subsystem {i+1} in transformation chain",
                "strength": layer_strength,
                "importance": layer_importance,
                "characteristics": [
                    f"Singular value: {layer_strength:.3f}",
                    f"Relative importance: {layer_importance:.1%}",
                    f"Cumulative variance: {float(np.sum(S[:i+1]**2) / np.sum(S**2)):.1%}"
                ],
                "matrix_summary": {
                    "type": f"singular vector {i+1}",
                    "singular_value": layer_strength
                }
            })

        return subsystems

    def _interpret_layer_characteristics(self,
                                        matrix: np.ndarray,
                                        layer_type: str) -> List[str]:
        """Interpret characteristics of a subsystem layer"""
        characteristics = []

        # Sparsity
        sparsity = np.sum(np.abs(matrix) > 0.01) / matrix.size
        if sparsity < 0.3:
            characteristics.append("Targeted/selective mechanism")
        elif sparsity > 0.7:
            characteristics.append("Broad/distributed mechanism")
        else:
            characteristics.append("Moderate selectivity")

        # Magnitude
        max_val = np.max(np.abs(matrix))
        if max_val > 2.0:
            characteristics.append("Strong amplification")
        elif max_val < 0.5:
            characteristics.append("Dampening/regulation")

        # Structure
        is_diagonal_dominant = np.trace(np.abs(matrix)) / np.sum(np.abs(matrix)) > 0.5
        if is_diagonal_dominant:
            characteristics.append("Self-regulation dominant")
        else:
            characteristics.append("Cross-system interactions dominant")

        return characteristics

    def _get_dominant_components(self,
                                matrix: np.ndarray,
                                node_names: List[str],
                                top_k: int = 3) -> List[str]:
        """Identify most important components in transformation"""
        # Sum absolute values across rows to get component importance
        importance = np.sum(np.abs(matrix), axis=1)
        top_indices = np.argsort(importance)[-top_k:][::-1]

        # Map to node names if available
        if len(node_names) >= len(importance):
            return [node_names[i] for i in top_indices if i < len(node_names)]
        else:
            return [f"Component_{i}" for i in top_indices]

    def _layer_confidence(self, S_norm: np.ndarray, num_layers: int) -> Dict[str, Any]:
        """Calculate confidence in layer decomposition"""
        # Gap between significant and insignificant singular values
        if num_layers < len(S_norm):
            gap = S_norm[num_layers - 1] - S_norm[num_layers]
        else:
            gap = S_norm[-1]

        # Cumulative energy in detected layers
        energy = float(np.sum(S_norm[:num_layers]**2) / np.sum(S_norm**2))

        # Overall confidence
        overall = (gap + energy) / 2.0

        return {
            "overall": float(overall),
            "singular_value_gap": float(gap),
            "cumulative_energy": energy,
            "interpretation": self._interpret_layer_confidence(overall)
        }

    def _interpret_layer_confidence(self, score: float) -> str:
        """Human-readable confidence for layer detection"""
        if score >= 0.8:
            return "HIGH - Clear layer separation"
        elif score >= 0.6:
            return "MEDIUM - Likely multi-layer structure"
        elif score >= 0.4:
            return "LOW - Ambiguous layer boundaries"
        else:
            return "VERY_LOW - Poorly separated layers"


def detect_missing_systems(graph_a_path: Path,
                           graph_c_path: Path,
                           output_path: Optional[Path] = None,
                           format_type: str = "json",
                           multilayer: bool = True,
                           verbose: bool = False) -> Dict[str, Any]:
    """
    Main analysis function: Detect missing intermediate systems.

    Args:
        graph_a_path: Path to first system graph
        graph_c_path: Path to second system graph
        output_path: Optional output file path
        format_type: Output format ("json" or "text")
        multilayer: Use multi-layer decomposition
        verbose: Print detailed analysis

    Returns:
        Analysis results dictionary
    """
    # Load systems
    if verbose:
        print(f"Loading systems...")
        print(f"  System A: {graph_a_path}")
        print(f"  System C: {graph_c_path}")

    system_a = GraphSystem.from_json(graph_a_path)
    system_c = GraphSystem.from_json(graph_c_path)

    # Run analysis
    if multilayer:
        detector = MultiLayerGapDetector(verbose=verbose)
        results = detector.detect(system_a, system_c)
    else:
        solver = MissingSystemSolver(verbose=verbose)
        results = solver.solve(system_a, system_c)

    # Add metadata
    results['analysis_metadata'] = {
        "timestamp": datetime.now().isoformat(),
        "system_a": {
            "name": system_a.name,
            "path": str(graph_a_path),
            "nodes": system_a.n
        },
        "system_c": {
            "name": system_c.name,
            "path": str(graph_c_path),
            "nodes": system_c.n
        },
        "analysis_type": "multilayer" if multilayer else "single_layer",
        "tool": "matrix_gap_detection.py",
        "version": "1.0.0"
    }

    # Output results
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        if verbose:
            print(f"\nResults written to: {output_path}")

    # Format output
    if format_type == "text":
        print_text_output(results, system_a, system_c)
    elif format_type == "json":
        print(json.dumps(results, indent=2))

    return results


def print_text_output(results: Dict[str, Any],
                     system_a: GraphSystem,
                     system_c: GraphSystem):
    """Print human-readable text output"""
    print("\n" + "="*80)
    print("MATRIX-BASED GAP DETECTION ANALYSIS")
    print("="*80)

    metadata = results.get('analysis_metadata', {})
    print(f"\nTimestamp: {metadata.get('timestamp', 'N/A')}")
    print(f"Analysis Type: {metadata.get('analysis_type', 'N/A')}")

    print(f"\n{'-'*80}")
    print("INPUT SYSTEMS")
    print(f"{'-'*80}")
    print(f"System A: {system_a.name}")
    print(f"  Nodes: {system_a.n}")
    print(f"  Type: {system_a.metadata.get('framework', 'unknown')}")

    print(f"\nSystem C: {system_c.name}")
    print(f"  Nodes: {system_c.n}")
    print(f"  Type: {system_c.metadata.get('framework', 'unknown')}")

    # Multi-layer results
    if 'num_subsystems' in results:
        print(f"\n{'-'*80}")
        print(f"MISSING SYSTEM DECOMPOSITION: {results['num_subsystems']} Subsystems Detected")
        print(f"{'-'*80}")

        confidence = results.get('confidence', {})
        print(f"\nConfidence: {confidence.get('overall', 0):.2f} - {confidence.get('interpretation', 'N/A')}")
        print(f"  Singular Value Gap: {confidence.get('singular_value_gap', 0):.3f}")
        print(f"  Cumulative Energy: {confidence.get('cumulative_energy', 0):.1%}")

        subsystems = results.get('subsystems', [])
        for i, subsystem in enumerate(subsystems, 1):
            print(f"\n  [{i}] {subsystem.get('name', 'Unknown')}")
            print(f"      Strength: {subsystem.get('strength', 0):.3f}")
            print(f"      Description: {subsystem.get('description', 'N/A')}")

            chars = subsystem.get('characteristics', [])
            if chars:
                print(f"      Characteristics:")
                for char in chars:
                    print(f"        - {char}")

    # Single-layer results
    else:
        print(f"\n{'-'*80}")
        print("MISSING SYSTEM SOLUTION")
        print(f"{'-'*80}")

        props = results.get('properties', {})
        print(f"\nMatrix Properties:")
        print(f"  Rank: {props.get('rank', 'N/A')}")
        print(f"  Sparsity: {props.get('sparsity', 0):.1%}")
        print(f"  Dominant Eigenvalue: {props.get('dominant_eigenvalue', 0):.3f}")

        confidence = results.get('confidence', {})
        print(f"\nConfidence: {confidence.get('overall', 0):.2f} - {confidence.get('interpretation', 'N/A')}")

        hypotheses = results.get('hypotheses', [])
        if hypotheses:
            print(f"\nHypotheses ({len(hypotheses)}):")
            for hyp in hypotheses:
                print(f"  - {hyp.get('type', 'Unknown')} (conf: {hyp.get('confidence', 0):.2f})")
                print(f"    {hyp.get('description', 'N/A')}")

    print(f"\n{'='*80}\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Matrix-based gap detection for missing intermediate systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect missing system between two graphs
  python3 matrix_gap_detection.py system_a.json system_c.json

  # Multi-layer decomposition with JSON output
  python3 matrix_gap_detection.py sys_a.json sys_c.json --multilayer --format json

  # Save results to file
  python3 matrix_gap_detection.py sys_a.json sys_c.json --output missing_system.json

  # Single-layer analysis (no decomposition)
  python3 matrix_gap_detection.py sys_a.json sys_c.json --no-multilayer
        """
    )

    parser.add_argument('system_a', type=Path,
                       help='Path to first system graph (JSON)')
    parser.add_argument('system_c', type=Path,
                       help='Path to second system graph (JSON)')
    parser.add_argument('--output', '-o', type=Path,
                       help='Output file path (optional)')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--multilayer', dest='multilayer', action='store_true',
                       help='Use multi-layer decomposition (default)')
    parser.add_argument('--no-multilayer', dest='multilayer', action='store_false',
                       help='Disable multi-layer decomposition')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    parser.set_defaults(multilayer=True)

    args = parser.parse_args()

    # Validate inputs
    if not args.system_a.exists():
        print(f"Error: System A file not found: {args.system_a}", file=sys.stderr)
        sys.exit(1)

    if not args.system_c.exists():
        print(f"Error: System C file not found: {args.system_c}", file=sys.stderr)
        sys.exit(1)

    try:
        results = detect_missing_systems(
            args.system_a,
            args.system_c,
            output_path=args.output,
            format_type=args.format,
            multilayer=args.multilayer,
            verbose=args.verbose
        )

        # Exit successfully
        sys.exit(0)

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
