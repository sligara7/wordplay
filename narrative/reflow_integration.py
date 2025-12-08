"""
Reflow Integration - Export narrative DAGs to system_of_systems_graph format.

This module bridges the narrative module with reflow's analysis tools by
converting plot events (nodes) and narrative dependencies (edges) into the
standard system_of_systems_graph.json format.

Mapping:
- PlotNode → System/Component node
- Edge → Interface/dependency connection
- Character → Subsystem grouping
- Chapter → Tier/layer
- Subplot → Framework

This enables using all of reflow's analysis tools on narrative structures:
- analyze_integration_gaps.py for finding plot holes
- link_architectures.py for merging storylines
- matrix_gap_detection.py for finding missing scenes
"""

import json
from typing import Any
from pathlib import Path

from .narrative_dag import NarrativeDAG, PlotNode, NodeType, EdgeType


# Mapping narrative node types to system_of_systems_graph types
NODE_TYPE_MAPPING = {
    NodeType.SETUP: "foundation",
    NodeType.CATALYST: "trigger",
    NodeType.COMPLICATION: "obstacle",
    NodeType.REVELATION: "information_source",
    NodeType.DECISION: "decision_point",
    NodeType.CONSEQUENCE: "outcome",
    NodeType.CONFRONTATION: "conflict_handler",
    NodeType.RESOLUTION: "resolution_service",
    NodeType.CLIFFHANGER: "suspense_generator",
    NodeType.FLASHBACK: "context_provider",
    NodeType.FORESHADOWING: "hint_system",
}

# Mapping narrative edge types to system_of_systems_graph interaction types
EDGE_TYPE_MAPPING = {
    EdgeType.CAUSES: "triggers",
    EdgeType.ENABLES: "enables",
    EdgeType.REVEALS: "provides_context",
    EdgeType.FORESHADOWS: "hints_at",
    EdgeType.CONTRASTS: "contrasts_with",
    EdgeType.PARALLELS: "mirrors",
    EdgeType.REQUIRES: "depends_on",
    EdgeType.INTERRUPTS: "interrupts",
    EdgeType.RESOLVES: "resolves",
}


def plot_node_to_system(node: PlotNode) -> dict[str, Any]:
    """
    Convert a PlotNode to a system_of_systems_graph node.

    Maps narrative concepts to architecture concepts:
    - description → functions (what the event does in the story)
    - character → interfaces (who is involved)
    - chapter → tier (when it happens)
    - subplot → framework_id (which storyline)
    """
    return {
        "id": node.id,
        "name": node.description[:50] + "..." if len(node.description) > 50 else node.description,
        "type": NODE_TYPE_MAPPING.get(node.node_type, "event"),
        "functions": [
            f"Advance {node.subplot or 'main'} plot",
            f"Stakes level: {node.stakes_level}/10",
            node.node_type.name.lower().replace("_", " ").title(),
        ],
        "interfaces": [node.character] if node.character else [],
        "dependencies": [],  # Filled in from edges
        "tier": node.chapter or 0,
        "framework_id": node.subplot or "main",
        "raw": {
            "node_type": node.node_type.name,
            "chapter": node.chapter,
            "character": node.character,
            "subplot": node.subplot,
            "emotional_valence": node.emotional_valence,
            "stakes_level": node.stakes_level,
            "is_twist": node.is_twist,
        },
    }


def narrative_edge_to_connection(
    source_id: str, target_id: str, edge_type: str, weight: float = 1.0
) -> dict[str, Any]:
    """
    Convert a narrative edge to a system_of_systems_graph edge.

    Maps narrative dependencies to architecture connections:
    - CAUSES → triggers (direct causation)
    - ENABLES → enables (makes possible)
    - REVEALS → provides_context (information flow)
    - etc.
    """
    edge_enum = EdgeType[edge_type] if isinstance(edge_type, str) else edge_type

    return {
        "source": source_id,
        "target": target_id,
        "type": "narrative_dependency",
        "interaction_type": EDGE_TYPE_MAPPING.get(edge_enum, "connects"),
        "interface_name": edge_type if isinstance(edge_type, str) else edge_type.name,
        "direction": "directed",
        "weight": weight,
        "raw": {
            "edge_type": edge_type if isinstance(edge_type, str) else edge_type.name,
            "narrative_role": _describe_edge_role(edge_enum),
        },
    }


def _describe_edge_role(edge_type: EdgeType) -> str:
    """Provide a human-readable description of the edge's narrative role."""
    descriptions = {
        EdgeType.CAUSES: "This event directly causes the next event to occur",
        EdgeType.ENABLES: "This event makes the next event possible (but doesn't guarantee it)",
        EdgeType.REVEALS: "This event provides context that reframes understanding of the next",
        EdgeType.FORESHADOWS: "This event hints at the next (reader may not notice initially)",
        EdgeType.CONTRASTS: "These events are thematically opposed",
        EdgeType.PARALLELS: "These events mirror each other structurally",
        EdgeType.REQUIRES: "The next event cannot happen without this one",
        EdgeType.INTERRUPTS: "This event breaks the expected flow",
        EdgeType.RESOLVES: "This event provides closure for a prior setup",
    }
    return descriptions.get(edge_type, "Narrative connection")


class ReflowExporter:
    """
    Exports NarrativeDAG to system_of_systems_graph.json format.

    This enables using reflow's analysis tools on narrative structures:
    - Gap detection finds plot holes
    - Architecture linking merges storylines
    - Validation tools check structural integrity
    """

    def __init__(self, dag: NarrativeDAG):
        self.dag = dag

    def to_system_of_systems_graph(self) -> dict[str, Any]:
        """
        Convert the entire NarrativeDAG to system_of_systems_graph format.

        Returns a dictionary that can be serialized to JSON and used
        with all reflow analysis tools.
        """
        # Convert nodes
        nodes = []
        for node in self.dag._nodes.values():
            system_node = plot_node_to_system(node)
            nodes.append(system_node)

        # Convert edges and update dependencies
        edges = []
        dependency_map: dict[str, list[str]] = {}

        for source, target, data in self.dag.graph.edges(data=True):
            edge = narrative_edge_to_connection(
                source, target, data.get("edge_type", "CAUSES"), data.get("weight", 1.0)
            )
            edges.append(edge)

            # Track dependencies for each node
            if target not in dependency_map:
                dependency_map[target] = []
            dependency_map[target].append(source)

        # Update node dependencies
        for node in nodes:
            node["dependencies"] = dependency_map.get(node["id"], [])

        # Build the full graph structure
        graph = {
            "metadata": {
                "title": self.dag.title,
                "author": self.dag.author,
                "type": "narrative_dag",
                "chapter_count": self.dag._chapter_count,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "framework": "narrative",
                "version": "1.0",
            },
            "nodes": nodes,
            "edges": edges,
            "tiers": self._build_tier_structure(),
            "frameworks": self._build_framework_structure(),
        }

        return graph

    def _build_tier_structure(self) -> list[dict[str, Any]]:
        """Build tier (chapter) structure for hierarchical organization."""
        chapters: dict[int, list[str]] = {}
        for node in self.dag._nodes.values():
            ch = node.chapter or 0
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(node.id)

        return [
            {"tier": ch, "name": f"Chapter {ch}", "nodes": node_ids}
            for ch, node_ids in sorted(chapters.items())
        ]

    def _build_framework_structure(self) -> list[dict[str, Any]]:
        """Build framework (subplot) structure for grouping."""
        subplots: dict[str, list[str]] = {}
        for node in self.dag._nodes.values():
            subplot = node.subplot or "main"
            if subplot not in subplots:
                subplots[subplot] = []
            subplots[subplot].append(node.id)

        return [
            {"framework_id": subplot, "name": subplot.title(), "nodes": node_ids}
            for subplot, node_ids in subplots.items()
        ]

    def export_json(self, path: str | Path) -> None:
        """Export to a JSON file."""
        graph = self.to_system_of_systems_graph()
        path = Path(path)
        with open(path, "w") as f:
            json.dump(graph, f, indent=2)

    def export_for_gap_analysis(self) -> dict[str, Any]:
        """
        Export in format optimized for analyze_integration_gaps.py.

        Adds explicit interface contracts and requirements for
        compatibility with reflow's gap detection.
        """
        graph = self.to_system_of_systems_graph()

        # Add explicit provides/requires for interface matching
        for node in graph["nodes"]:
            raw = node.get("raw", {})
            node_type = raw.get("node_type", "")

            # Setups and catalysts "provide" story elements
            if node_type in ["SETUP", "CATALYST", "REVELATION"]:
                node["provides"] = [
                    {"interface": f"{node['id']}_output", "type": "story_element"}
                ]

            # Resolutions and consequences "require" prior elements
            if node_type in ["RESOLUTION", "CONSEQUENCE", "CONFRONTATION"]:
                node["requires"] = [
                    {"interface": dep, "type": "story_element"}
                    for dep in node.get("dependencies", [])
                ]

        return graph

    def export_for_linking(self) -> dict[str, Any]:
        """
        Export in format optimized for link_architectures.py.

        Adds metadata for cross-narrative linking (e.g., shared universe,
        sequel connections, character crossovers).
        """
        graph = self.to_system_of_systems_graph()

        # Add linking metadata
        graph["metadata"]["linkable"] = True
        graph["metadata"]["link_points"] = []

        # Characters that appear are potential link points
        characters = set()
        for node in self.dag._nodes.values():
            if node.character:
                characters.add(node.character)

        graph["metadata"]["link_points"].extend(
            [{"type": "character", "name": char} for char in characters]
        )

        # Unresolved threads are link points for sequels
        from .analyzers import NarrativeAnalyzer

        analyzer = NarrativeAnalyzer(self.dag)
        diagnosis = analyzer.diagnose()

        for dangling in diagnosis.dangling_setups:
            graph["metadata"]["link_points"].append(
                {"type": "unresolved_thread", "node_id": dangling.id, "description": dangling.description}
            )

        return graph


class ReflowImporter:
    """
    Import system_of_systems_graph.json back into NarrativeDAG.

    Useful for:
    - Loading narratives that were analyzed/modified by reflow tools
    - Converting other domain graphs into narrative structures
    - Round-trip editing (export → reflow analysis → import)
    """

    @staticmethod
    def from_system_of_systems_graph(graph: dict[str, Any]) -> NarrativeDAG:
        """
        Convert a system_of_systems_graph back to NarrativeDAG.

        Attempts to recover narrative-specific metadata from the 'raw' field,
        falling back to sensible defaults if not present.
        """
        metadata = graph.get("metadata", {})
        dag = NarrativeDAG(
            title=metadata.get("title", "Imported Narrative"),
            author=metadata.get("author", "Unknown"),
        )

        # Import nodes
        for node_data in graph.get("nodes", []):
            raw = node_data.get("raw", {})

            # Recover node type
            node_type_str = raw.get("node_type", _infer_node_type(node_data.get("type", "")))
            try:
                node_type = NodeType[node_type_str]
            except KeyError:
                node_type = NodeType.CONSEQUENCE  # Default

            node = PlotNode(
                id=node_data["id"],
                node_type=node_type,
                description=node_data.get("name", node_data["id"]),
                chapter=raw.get("chapter") or node_data.get("tier"),
                character=raw.get("character") or (node_data.get("interfaces", [None])[0] if node_data.get("interfaces") else None),
                subplot=raw.get("subplot") or node_data.get("framework_id"),
                emotional_valence=raw.get("emotional_valence", 0.0),
                stakes_level=raw.get("stakes_level", 5),
                is_twist=raw.get("is_twist", False),
            )
            dag.add_node(node)

        # Import edges
        for edge_data in graph.get("edges", []):
            raw = edge_data.get("raw", {})

            # Recover edge type
            edge_type_str = raw.get("edge_type", _infer_edge_type(edge_data.get("interaction_type", "")))
            try:
                edge_type = EdgeType[edge_type_str]
            except KeyError:
                edge_type = EdgeType.CAUSES  # Default

            try:
                dag.add_edge(
                    edge_data["source"],
                    edge_data["target"],
                    edge_type,
                    edge_data.get("weight", 1.0),
                )
            except ValueError:
                # Skip edges with missing nodes
                pass

        return dag

    @staticmethod
    def from_json(path: str | Path) -> NarrativeDAG:
        """Load a NarrativeDAG from a system_of_systems_graph.json file."""
        path = Path(path)
        with open(path) as f:
            graph = json.load(f)
        return ReflowImporter.from_system_of_systems_graph(graph)


def _infer_node_type(system_type: str) -> str:
    """Infer narrative node type from system_of_systems_graph type."""
    reverse_mapping = {v: k.name for k, v in NODE_TYPE_MAPPING.items()}
    return reverse_mapping.get(system_type, "CONSEQUENCE")


def _infer_edge_type(interaction_type: str) -> str:
    """Infer narrative edge type from system_of_systems_graph interaction type."""
    reverse_mapping = {v: k.name for k, v in EDGE_TYPE_MAPPING.items()}
    return reverse_mapping.get(interaction_type, "CAUSES")


# Convenience functions
def export_narrative_to_reflow(dag: NarrativeDAG, path: str | Path) -> None:
    """Export a NarrativeDAG to system_of_systems_graph.json format."""
    exporter = ReflowExporter(dag)
    exporter.export_json(path)


def import_narrative_from_reflow(path: str | Path) -> NarrativeDAG:
    """Import a NarrativeDAG from system_of_systems_graph.json format."""
    return ReflowImporter.from_json(path)


def analyze_narrative_with_reflow(dag: NarrativeDAG) -> dict[str, Any]:
    """
    Prepare narrative for analysis with reflow tools.

    Returns a dict containing:
    - graph: The system_of_systems_graph format
    - gap_analysis_ready: Format for analyze_integration_gaps.py
    - linking_ready: Format for link_architectures.py
    - suggested_tools: List of recommended reflow tools to run
    """
    exporter = ReflowExporter(dag)

    # Determine which tools would be most useful
    from .analyzers import NarrativeAnalyzer

    analyzer = NarrativeAnalyzer(dag)
    diagnosis = analyzer.diagnose()

    suggested_tools = []

    if diagnosis.dangling_setups or diagnosis.orphan_nodes:
        suggested_tools.append({
            "tool": "analyze_integration_gaps.py",
            "reason": f"Found {len(diagnosis.dangling_setups)} dangling setups and {len(diagnosis.orphan_nodes)} orphan nodes",
        })

    if diagnosis.pacing_issues:
        suggested_tools.append({
            "tool": "analyze_workflow_complexity.py",
            "reason": "Pacing issues detected - analyze flow complexity",
        })

    metrics = dag.calculate_metrics()
    if metrics.subplot_count > 1:
        suggested_tools.append({
            "tool": "link_architectures.py",
            "reason": f"Multiple subplots ({metrics.subplot_count}) could benefit from explicit linking",
        })

    return {
        "graph": exporter.to_system_of_systems_graph(),
        "gap_analysis_ready": exporter.export_for_gap_analysis(),
        "linking_ready": exporter.export_for_linking(),
        "suggested_tools": suggested_tools,
        "diagnosis_summary": diagnosis.summary() if diagnosis.has_issues else "No structural issues detected",
    }
