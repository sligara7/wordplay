"""
Narrative Analyzers - Tools for analyzing narrative DAG structures.

Provides diagnostics, comparisons, and structural health checks
for novel plot structures.
"""

from dataclasses import dataclass
from typing import Optional
import networkx as nx

from .narrative_dag import NarrativeDAG, PlotNode, NodeType, EdgeType, NarrativeMetrics


@dataclass
class StructuralDiagnosis:
    """Results of analyzing a narrative DAG for structural issues."""

    dangling_setups: list[PlotNode]
    orphan_nodes: list[PlotNode]
    unfired_foreshadowing: list[tuple[PlotNode, str]]
    rushed_arcs: list[str]  # Character names with too-short arcs
    sagging_chapters: list[int]  # Chapters with low density
    deus_ex_machina: list[PlotNode]  # Resolutions without proper setup
    pacing_issues: list[str]  # Descriptive pacing problems

    @property
    def has_issues(self) -> bool:
        """Check if any structural issues were found."""
        return bool(
            self.dangling_setups
            or self.orphan_nodes
            or self.unfired_foreshadowing
            or self.rushed_arcs
            or self.sagging_chapters
            or self.deus_ex_machina
            or self.pacing_issues
        )

    def summary(self) -> str:
        """Return human-readable summary of issues."""
        if not self.has_issues:
            return "No structural issues detected."

        lines = ["=== Structural Diagnosis ===", ""]

        if self.dangling_setups:
            lines.append(f"DANGLING SETUPS ({len(self.dangling_setups)}):")
            for node in self.dangling_setups:
                lines.append(f"  - [{node.id}] {node.description}")
            lines.append("")

        if self.orphan_nodes:
            lines.append(f"ORPHAN NODES ({len(self.orphan_nodes)}):")
            for node in self.orphan_nodes:
                lines.append(f"  - [{node.id}] {node.description}")
            lines.append("")

        if self.unfired_foreshadowing:
            lines.append(f"UNFIRED FORESHADOWING ({len(self.unfired_foreshadowing)}):")
            for node, target in self.unfired_foreshadowing:
                lines.append(f"  - [{node.id}] foreshadows '{target}' but never pays off")
            lines.append("")

        if self.rushed_arcs:
            lines.append(f"RUSHED CHARACTER ARCS ({len(self.rushed_arcs)}):")
            for char in self.rushed_arcs:
                lines.append(f"  - {char}'s arc has too few beats")
            lines.append("")

        if self.sagging_chapters:
            lines.append(f"SAGGING MIDDLE ({len(self.sagging_chapters)} chapters):")
            lines.append(f"  Chapters with low activity: {self.sagging_chapters}")
            lines.append("")

        if self.deus_ex_machina:
            lines.append(f"DEUS EX MACHINA ({len(self.deus_ex_machina)}):")
            for node in self.deus_ex_machina:
                lines.append(f"  - [{node.id}] resolves without proper causal chain")
            lines.append("")

        if self.pacing_issues:
            lines.append("PACING ISSUES:")
            for issue in self.pacing_issues:
                lines.append(f"  - {issue}")

        return "\n".join(lines)


class NarrativeAnalyzer:
    """Analyzer for narrative DAG structures."""

    def __init__(self, dag: NarrativeDAG):
        self.dag = dag

    def diagnose(self) -> StructuralDiagnosis:
        """Perform comprehensive structural diagnosis."""
        return StructuralDiagnosis(
            dangling_setups=self._find_dangling_setups(),
            orphan_nodes=self._find_orphan_nodes(),
            unfired_foreshadowing=self._find_unfired_foreshadowing(),
            rushed_arcs=self._find_rushed_arcs(),
            sagging_chapters=self._find_sagging_chapters(),
            deus_ex_machina=self._find_deus_ex_machina(),
            pacing_issues=self._analyze_pacing(),
        )

    def _find_dangling_setups(self) -> list[PlotNode]:
        """Find setup nodes that never get resolved."""
        return self.dag.find_dangling_setups()

    def _find_orphan_nodes(self) -> list[PlotNode]:
        """Find nodes without proper causal connection."""
        return self.dag.find_orphan_nodes()

    def _find_unfired_foreshadowing(self) -> list[tuple[PlotNode, str]]:
        """Find foreshadowing that doesn't pay off."""
        return self.dag.find_unfired_foreshadowing()

    def _find_rushed_arcs(self, min_beats: int = 3) -> list[str]:
        """Find character arcs with too few beats."""
        rushed = []
        characters: set[str] = set()

        for node in self.dag._nodes.values():
            if node.character:
                characters.add(node.character)

        for char in characters:
            arc = self.dag.get_character_arc(char)
            if len(arc) < min_beats:
                rushed.append(char)

        return rushed

    def _find_sagging_chapters(self, threshold_ratio: float = 0.5) -> list[int]:
        """Find chapters with below-average node density."""
        if self.dag._chapter_count == 0:
            return []

        chapter_counts: dict[int, int] = {}
        for node in self.dag._nodes.values():
            if node.chapter:
                chapter_counts[node.chapter] = chapter_counts.get(node.chapter, 0) + 1

        if not chapter_counts:
            return []

        avg_density = sum(chapter_counts.values()) / len(chapter_counts)
        threshold = avg_density * threshold_ratio

        # Look for chapters in the middle 50% that are below threshold
        all_chapters = list(range(1, self.dag._chapter_count + 1))
        middle_start = len(all_chapters) // 4
        middle_end = len(all_chapters) * 3 // 4

        sagging = []
        for ch in all_chapters[middle_start:middle_end]:
            if chapter_counts.get(ch, 0) < threshold:
                sagging.append(ch)

        return sagging

    def _find_deus_ex_machina(self) -> list[PlotNode]:
        """Find resolution nodes without proper causal chains."""
        deus_ex = []

        for node in self.dag._nodes.values():
            if node.node_type == NodeType.RESOLUTION:
                # Check if it has causal ancestors
                ancestors = self.dag.get_causal_chain(node.id)
                has_proper_setup = False

                for ancestor_id in ancestors:
                    ancestor = self.dag.get_node(ancestor_id)
                    if ancestor and ancestor.node_type in [
                        NodeType.SETUP,
                        NodeType.CATALYST,
                        NodeType.COMPLICATION,
                    ]:
                        # Check edge type
                        path = nx.shortest_path(self.dag.graph, ancestor_id, node.id)
                        for i in range(len(path) - 1):
                            edge_data = self.dag.graph.get_edge_data(path[i], path[i + 1])
                            if edge_data and edge_data.get("edge_type") in [
                                EdgeType.CAUSES.name,
                                EdgeType.ENABLES.name,
                                EdgeType.RESOLVES.name,
                            ]:
                                has_proper_setup = True
                                break
                    if has_proper_setup:
                        break

                if not has_proper_setup and len(ancestors) < 2:
                    deus_ex.append(node)

        return deus_ex

    def _analyze_pacing(self) -> list[str]:
        """Analyze pacing issues in the narrative."""
        issues = []
        metrics = self.dag.calculate_metrics()

        # Check revelation spacing
        if metrics.revelation_spacing > 0:
            if metrics.revelation_spacing > 10:
                issues.append(
                    f"Revelations too sparse ({metrics.revelation_spacing:.1f} chapters apart) - "
                    "reader may lose engagement"
                )
            elif metrics.revelation_spacing < 2:
                issues.append(
                    f"Revelations too frequent ({metrics.revelation_spacing:.1f} chapters apart) - "
                    "may overwhelm reader"
                )

        # Check stakes escalation
        if metrics.stakes_escalation < 0:
            issues.append("Stakes decrease over time - tension may deflate")

        # Check peak position
        if metrics.peak_stakes_position < 0.6:
            issues.append(
                f"Climax too early ({metrics.peak_stakes_position:.0%} through story) - "
                "ending may feel anticlimactic"
            )
        elif metrics.peak_stakes_position > 0.95:
            issues.append(
                f"Climax too late ({metrics.peak_stakes_position:.0%} through story) - "
                "insufficient resolution time"
            )

        # Check chapter density
        if metrics.chapter_density < 1:
            issues.append("Very sparse chapters - pacing may feel slow")
        elif metrics.chapter_density > 5:
            issues.append("Very dense chapters - may overwhelm reader")

        return issues

    def compare_to_genre(self, genre_name: str) -> dict:
        """Compare this narrative's structure to a genre template."""
        from .genre_templates import get_template

        template = get_template(genre_name)
        template_dag = template.create_skeleton()
        template_metrics = template_dag.calculate_metrics()
        our_metrics = self.dag.calculate_metrics()

        comparison = {
            "genre": genre_name,
            "matches": [],
            "deviations": [],
            "recommendations": [],
        }

        # Compare key metrics
        if abs(our_metrics.chapter_density - template_metrics.chapter_density) < 0.5:
            comparison["matches"].append("Chapter density matches genre expectations")
        else:
            if our_metrics.chapter_density < template_metrics.chapter_density:
                comparison["deviations"].append("Pacing slower than typical for genre")
                comparison["recommendations"].append("Consider adding more plot beats per chapter")
            else:
                comparison["deviations"].append("Pacing faster than typical for genre")
                comparison["recommendations"].append("Consider spreading events across more chapters")

        # Compare twist count
        if our_metrics.twist_count >= template_metrics.twist_count:
            comparison["matches"].append("Sufficient plot twists for genre")
        else:
            comparison["deviations"].append(
                f"Fewer twists ({our_metrics.twist_count}) than genre typical "
                f"({template_metrics.twist_count})"
            )
            comparison["recommendations"].append("Consider adding revelation/twist moments")

        # Compare subplot count
        if our_metrics.subplot_count >= template.typical_subplot_count[0]:
            comparison["matches"].append("Subplot count appropriate for genre")
        else:
            comparison["deviations"].append("Fewer subplots than typical for genre")

        # Check required node types
        our_node_types = {n.node_type for n in self.dag._nodes.values()}
        missing_types = set(template.required_node_types) - our_node_types
        if not missing_types:
            comparison["matches"].append("All required narrative elements present")
        else:
            comparison["deviations"].append(
                f"Missing expected elements: {[t.name for t in missing_types]}"
            )

        return comparison

    def extract_structural_signature(self) -> dict:
        """
        Extract a structural signature compatible with the Structural Rorschach framework.

        This allows narrative DAGs to be compared with other domains (music, images, etc.)
        """
        metrics = self.dag.calculate_metrics()
        graph = self.dag.graph

        # Basic graph metrics
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        # Degree distribution
        in_degrees = [d for _, d in graph.in_degree()]
        out_degrees = [d for _, d in graph.out_degree()]

        avg_in_degree = sum(in_degrees) / node_count if node_count else 0
        avg_out_degree = sum(out_degrees) / node_count if node_count else 0
        max_in_degree = max(in_degrees) if in_degrees else 0
        max_out_degree = max(out_degrees) if out_degrees else 0

        # Hub detection (nodes with high connectivity)
        hub_threshold = avg_out_degree * 2
        hub_count = sum(1 for d in out_degrees if d > hub_threshold)

        # Chain detection (sequential paths)
        chain_nodes = sum(1 for i, o in zip(in_degrees, out_degrees) if i == 1 and o == 1)

        # Convergence points (multiple inputs, single output)
        funnel_nodes = sum(1 for i, o in zip(in_degrees, out_degrees) if i > 1 and o <= 1)

        # Fork points (single input, multiple outputs)
        fork_nodes = sum(1 for i, o in zip(in_degrees, out_degrees) if i <= 1 and o > 1)

        return {
            "domain": "narrative",
            "source": self.dag.title,
            "scale": {
                "nodes": node_count,
                "edges": edge_count,
                "chapters": self.dag._chapter_count,
            },
            "degree": {
                "avg_in": avg_in_degree,
                "avg_out": avg_out_degree,
                "max_in": max_in_degree,
                "max_out": max_out_degree,
            },
            "motifs": {
                "hub_count": hub_count,
                "chain_nodes": chain_nodes,
                "funnel_nodes": funnel_nodes,
                "fork_nodes": fork_nodes,
                "hub_ratio": hub_count / node_count if node_count else 0,
                "chain_ratio": chain_nodes / node_count if node_count else 0,
            },
            "flow": {
                "is_dag": self.dag.is_valid_dag(),
                "causal_depth": metrics.causal_depth,
                "resolution_rate": metrics.resolution_rate,
            },
            "narrative_specific": {
                "twist_count": metrics.twist_count,
                "subplot_count": metrics.subplot_count,
                "stakes_escalation": metrics.stakes_escalation,
                "revelation_spacing": metrics.revelation_spacing,
            },
        }


def compare_narratives(dag1: NarrativeDAG, dag2: NarrativeDAG) -> dict:
    """Compare two narrative DAGs structurally."""
    sig1 = NarrativeAnalyzer(dag1).extract_structural_signature()
    sig2 = NarrativeAnalyzer(dag2).extract_structural_signature()

    # Calculate similarity scores
    motif_similarity = _cosine_similarity(
        [
            sig1["motifs"]["hub_ratio"],
            sig1["motifs"]["chain_ratio"],
            sig1["flow"]["causal_depth"] / 20,  # Normalize
            sig1["flow"]["resolution_rate"],
        ],
        [
            sig2["motifs"]["hub_ratio"],
            sig2["motifs"]["chain_ratio"],
            sig2["flow"]["causal_depth"] / 20,
            sig2["flow"]["resolution_rate"],
        ],
    )

    scale_ratio = min(sig1["scale"]["nodes"], sig2["scale"]["nodes"]) / max(
        sig1["scale"]["nodes"], sig2["scale"]["nodes"], 1
    )

    return {
        "narrative_1": sig1["source"],
        "narrative_2": sig2["source"],
        "motif_similarity": motif_similarity,
        "scale_ratio": scale_ratio,
        "structural_differences": {
            "causal_depth_diff": abs(
                sig1["flow"]["causal_depth"] - sig2["flow"]["causal_depth"]
            ),
            "twist_count_diff": abs(
                sig1["narrative_specific"]["twist_count"]
                - sig2["narrative_specific"]["twist_count"]
            ),
            "subplot_count_diff": abs(
                sig1["narrative_specific"]["subplot_count"]
                - sig2["narrative_specific"]["subplot_count"]
            ),
        },
    }


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
