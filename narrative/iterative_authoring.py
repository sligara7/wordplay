"""
Iterative Authoring System for Narrative DAGs

This module supports the messy, non-linear process of actual story creation:
- Authors don't have complete stories upfront
- Characters get added/removed mid-process
- Side-stories emerge and merge with main plot
- One change can ripple through the entire structure
- The DAG must stay coherent through all modifications

Key Concepts:
- ChangeEvent: Records any modification for undo/redo and impact analysis
- DynamicNarrativeDAG: Extends NarrativeDAG with change tracking
- ImpactAnalyzer: Determines what's affected when something changes
- SubplotManager: Handles parallel storylines and merge points
- CoherenceValidator: Ensures DAG integrity after modifications
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional
from collections import defaultdict
import json
from pathlib import Path
import copy

from .narrative_dag import (
    NarrativeDAG,
    PlotNode,
    NodeType,
    EdgeType,
    NarrativeEdge,
)


class ChangeType(Enum):
    """Types of changes that can occur in the DAG."""
    ADD_NODE = "add_node"
    REMOVE_NODE = "remove_node"
    MODIFY_NODE = "modify_node"
    ADD_EDGE = "add_edge"
    REMOVE_EDGE = "remove_edge"
    MODIFY_EDGE = "modify_edge"
    ADD_SUBPLOT = "add_subplot"
    MERGE_SUBPLOT = "merge_subplot"
    REORDER_CHAPTERS = "reorder_chapters"
    BATCH_UPDATE = "batch_update"


@dataclass
class ChangeEvent:
    """Records a single change to the DAG for history/undo."""
    change_type: ChangeType
    timestamp: datetime
    description: str
    # Store before/after state for undo
    before_state: dict = field(default_factory=dict)
    after_state: dict = field(default_factory=dict)
    # Which nodes/edges are affected
    affected_nodes: list[str] = field(default_factory=list)
    affected_edges: list[tuple[str, str]] = field(default_factory=list)
    # Author notes about why change was made
    author_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "affected_nodes": self.affected_nodes,
            "affected_edges": self.affected_edges,
            "author_notes": self.author_notes,
        }


@dataclass
class ImpactReport:
    """Report of how a change affects the rest of the DAG."""
    change_description: str
    # Direct impacts
    orphaned_nodes: list[str] = field(default_factory=list)
    broken_edges: list[tuple[str, str, str]] = field(default_factory=list)  # (from, to, reason)
    # Ripple effects
    timeline_conflicts: list[str] = field(default_factory=list)
    character_arc_gaps: list[str] = field(default_factory=list)
    subplot_disconnections: list[str] = field(default_factory=list)
    # Structural issues
    unreachable_nodes: list[str] = field(default_factory=list)
    dead_end_nodes: list[str] = field(default_factory=list)
    # Suggestions for resolution
    suggested_fixes: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(
            self.orphaned_nodes or
            self.broken_edges or
            self.timeline_conflicts or
            self.character_arc_gaps or
            self.subplot_disconnections or
            self.unreachable_nodes or
            self.dead_end_nodes
        )

    def summary(self) -> str:
        lines = [f"Impact Report: {self.change_description}"]
        lines.append("-" * 50)

        if not self.has_issues:
            lines.append("✓ No issues detected. DAG remains coherent.")
            return "\n".join(lines)

        if self.orphaned_nodes:
            lines.append(f"\n⚠ Orphaned Nodes ({len(self.orphaned_nodes)}):")
            for node in self.orphaned_nodes:
                lines.append(f"  - {node}")

        if self.broken_edges:
            lines.append(f"\n⚠ Broken Edges ({len(self.broken_edges)}):")
            for from_n, to_n, reason in self.broken_edges:
                lines.append(f"  - {from_n} → {to_n}: {reason}")

        if self.timeline_conflicts:
            lines.append(f"\n⚠ Timeline Conflicts ({len(self.timeline_conflicts)}):")
            for conflict in self.timeline_conflicts:
                lines.append(f"  - {conflict}")

        if self.character_arc_gaps:
            lines.append(f"\n⚠ Character Arc Gaps ({len(self.character_arc_gaps)}):")
            for gap in self.character_arc_gaps:
                lines.append(f"  - {gap}")

        if self.subplot_disconnections:
            lines.append(f"\n⚠ Subplot Disconnections ({len(self.subplot_disconnections)}):")
            for disc in self.subplot_disconnections:
                lines.append(f"  - {disc}")

        if self.suggested_fixes:
            lines.append(f"\n💡 Suggested Fixes:")
            for fix in self.suggested_fixes:
                lines.append(f"  → {fix}")

        return "\n".join(lines)


@dataclass
class Subplot:
    """Represents a parallel storyline that may merge with main plot."""
    id: str
    name: str
    description: str
    # Nodes belonging to this subplot
    node_ids: list[str] = field(default_factory=list)
    # Where this subplot connects to main plot
    merge_points: list[str] = field(default_factory=list)
    # Which character(s) drive this subplot
    primary_characters: list[str] = field(default_factory=list)
    # Status
    is_merged: bool = False
    merge_chapter: Optional[int] = None


class DynamicNarrativeDAG(NarrativeDAG):
    """
    Extended NarrativeDAG that supports iterative authoring.

    Features:
    - Change history with undo/redo
    - Impact analysis before/after changes
    - Subplot management
    - Coherence validation
    - Version snapshots
    """

    def __init__(
        self,
        title: str = "Untitled",
        genre: str = "general",
        target_chapters: int = 20,
    ):
        super().__init__(title, genre, target_chapters)

        # Change tracking
        self._change_history: list[ChangeEvent] = []
        self._redo_stack: list[ChangeEvent] = []
        self._change_listeners: list[Callable[[ChangeEvent], None]] = []

        # Subplot management
        self._subplots: dict[str, Subplot] = {}
        self._main_plot_nodes: set[str] = set()

        # Version snapshots
        self._snapshots: dict[str, dict] = {}

        # Validation state
        self._last_validation: Optional[ImpactReport] = None
        self._is_dirty: bool = False

    # =========================================================
    # CHANGE TRACKING
    # =========================================================

    def _record_change(
        self,
        change_type: ChangeType,
        description: str,
        before_state: dict,
        after_state: dict,
        affected_nodes: list[str] = None,
        affected_edges: list[tuple[str, str]] = None,
        author_notes: str = "",
    ) -> ChangeEvent:
        """Record a change for history/undo."""
        event = ChangeEvent(
            change_type=change_type,
            timestamp=datetime.now(),
            description=description,
            before_state=before_state,
            after_state=after_state,
            affected_nodes=affected_nodes or [],
            affected_edges=affected_edges or [],
            author_notes=author_notes,
        )
        self._change_history.append(event)
        self._redo_stack.clear()  # Clear redo on new change
        self._is_dirty = True

        # Notify listeners
        for listener in self._change_listeners:
            listener(event)

        return event

    def add_change_listener(self, listener: Callable[[ChangeEvent], None]) -> None:
        """Register a callback for change events."""
        self._change_listeners.append(listener)

    def get_history(self, limit: int = None) -> list[ChangeEvent]:
        """Get change history, optionally limited."""
        if limit:
            return self._change_history[-limit:]
        return self._change_history.copy()

    def undo(self) -> Optional[ChangeEvent]:
        """Undo the last change."""
        if not self._change_history:
            return None

        event = self._change_history.pop()
        self._redo_stack.append(event)

        # Restore before state based on change type
        self._restore_state(event.before_state, event.change_type)
        self._is_dirty = True

        return event

    def redo(self) -> Optional[ChangeEvent]:
        """Redo the last undone change."""
        if not self._redo_stack:
            return None

        event = self._redo_stack.pop()
        self._change_history.append(event)

        # Apply after state
        self._restore_state(event.after_state, event.change_type)
        self._is_dirty = True

        return event

    def _restore_state(self, state: dict, change_type: ChangeType) -> None:
        """Restore DAG to a previous state."""
        if change_type in (ChangeType.ADD_NODE, ChangeType.REMOVE_NODE, ChangeType.MODIFY_NODE):
            if "node" in state:
                node_data = state["node"]
                if node_data is None:
                    # Node was removed, remove it
                    node_id = state.get("node_id")
                    if node_id and node_id in self.nodes:
                        del self.nodes[node_id]
                else:
                    # Restore node
                    node = PlotNode(**node_data)
                    self.nodes[node.id] = node

        elif change_type in (ChangeType.ADD_EDGE, ChangeType.REMOVE_EDGE):
            if "edge" in state:
                edge_data = state["edge"]
                if edge_data is None:
                    # Edge was removed
                    from_id = state.get("from_id")
                    to_id = state.get("to_id")
                    if from_id and to_id:
                        self.edges = [e for e in self.edges
                                     if not (e.from_node == from_id and e.to_node == to_id)]
                else:
                    # Restore edge
                    edge = NarrativeEdge(
                        from_node=edge_data["from_node"],
                        to_node=edge_data["to_node"],
                        edge_type=EdgeType(edge_data["edge_type"]),
                    )
                    self.edges.append(edge)

    # =========================================================
    # DYNAMIC NODE OPERATIONS
    # =========================================================

    def add_node_dynamic(
        self,
        node: PlotNode,
        author_notes: str = "",
        auto_connect: bool = True,
    ) -> ImpactReport:
        """
        Add a node with full change tracking and impact analysis.

        If auto_connect is True, suggests connections based on:
        - Chapter proximity
        - Character overlap
        - Subplot membership
        """
        before_state = {"node": None, "node_id": node.id}

        # Add the node
        self.add_node(node)

        after_state = {"node": self._node_to_dict(node)}

        self._record_change(
            ChangeType.ADD_NODE,
            f"Added node '{node.id}' at chapter {node.chapter}",
            before_state,
            after_state,
            affected_nodes=[node.id],
            author_notes=author_notes,
        )

        # Generate impact report with suggestions
        report = ImpactReport(change_description=f"Adding node '{node.id}'")

        if auto_connect:
            # Find potential connections
            suggestions = self._suggest_connections_for_node(node)
            report.suggested_fixes = suggestions

        # Check if this creates any issues
        if node.chapter and node.chapter > self.target_chapters:
            report.timeline_conflicts.append(
                f"Node chapter {node.chapter} exceeds target {self.target_chapters}"
            )

        return report

    def remove_node_dynamic(
        self,
        node_id: str,
        author_notes: str = "",
        cascade: bool = False,
    ) -> ImpactReport:
        """
        Remove a node with impact analysis.

        If cascade is True, also removes edges connected to this node.
        If False, returns report of what would break.
        """
        if node_id not in self.nodes:
            report = ImpactReport(change_description=f"Remove node '{node_id}'")
            report.suggested_fixes.append(f"Node '{node_id}' does not exist")
            return report

        node = self.nodes[node_id]
        before_state = {"node": self._node_to_dict(node), "node_id": node_id}

        # Find affected edges
        affected_edges = [
            (e.from_node, e.to_node)
            for e in self.edges
            if e.from_node == node_id or e.to_node == node_id
        ]

        # Build impact report
        report = ImpactReport(change_description=f"Removing node '{node_id}'")

        for from_n, to_n in affected_edges:
            if from_n == node_id:
                report.broken_edges.append((from_n, to_n, "Source node removed"))
                # Check if target becomes orphaned
                incoming = [e for e in self.edges if e.to_node == to_n and e.from_node != node_id]
                if not incoming and to_n != node_id:
                    report.orphaned_nodes.append(to_n)
            else:
                report.broken_edges.append((from_n, to_n, "Target node removed"))
                # Check if source becomes dead-end
                outgoing = [e for e in self.edges if e.from_node == from_n and e.to_node != node_id]
                if not outgoing and from_n != node_id:
                    report.dead_end_nodes.append(from_n)

        # Check subplot impact
        for subplot_id, subplot in self._subplots.items():
            if node_id in subplot.node_ids:
                report.subplot_disconnections.append(
                    f"Node belongs to subplot '{subplot.name}'"
                )
                if node_id in subplot.merge_points:
                    report.subplot_disconnections.append(
                        f"Node is merge point for subplot '{subplot.name}'"
                    )

        # Generate fix suggestions
        if report.orphaned_nodes:
            report.suggested_fixes.append(
                f"Connect orphaned nodes to another source: {report.orphaned_nodes}"
            )
        if report.dead_end_nodes:
            report.suggested_fixes.append(
                f"Connect dead-end nodes to new targets: {report.dead_end_nodes}"
            )

        # Perform removal if cascade or no breaking changes
        if cascade or not report.has_issues:
            # Remove edges first
            self.edges = [e for e in self.edges
                         if e.from_node != node_id and e.to_node != node_id]
            # Remove from subplots
            for subplot in self._subplots.values():
                if node_id in subplot.node_ids:
                    subplot.node_ids.remove(node_id)
                if node_id in subplot.merge_points:
                    subplot.merge_points.remove(node_id)
            # Remove node
            del self.nodes[node_id]

            after_state = {"node": None, "node_id": node_id}
            self._record_change(
                ChangeType.REMOVE_NODE,
                f"Removed node '{node_id}'",
                before_state,
                after_state,
                affected_nodes=[node_id] + report.orphaned_nodes + report.dead_end_nodes,
                affected_edges=affected_edges,
                author_notes=author_notes,
            )

        return report

    def modify_node_dynamic(
        self,
        node_id: str,
        updates: dict,
        author_notes: str = "",
    ) -> ImpactReport:
        """
        Modify a node's properties with impact analysis.

        Updates can include: description, chapter, character, stakes_level, etc.
        """
        if node_id not in self.nodes:
            report = ImpactReport(change_description=f"Modify node '{node_id}'")
            report.suggested_fixes.append(f"Node '{node_id}' does not exist")
            return report

        node = self.nodes[node_id]
        before_state = {"node": self._node_to_dict(node), "node_id": node_id}

        report = ImpactReport(change_description=f"Modifying node '{node_id}'")

        # Check chapter change impact
        old_chapter = node.chapter
        new_chapter = updates.get("chapter", old_chapter)

        if new_chapter != old_chapter:
            # Check timeline consistency
            for edge in self.edges:
                if edge.from_node == node_id:
                    target = self.nodes.get(edge.to_node)
                    if target and target.chapter and new_chapter > target.chapter:
                        if edge.edge_type != EdgeType.FLASHBACK:
                            report.timeline_conflicts.append(
                                f"Node moves to ch.{new_chapter} but causes '{edge.to_node}' in ch.{target.chapter}"
                            )
                elif edge.to_node == node_id:
                    source = self.nodes.get(edge.from_node)
                    if source and source.chapter and new_chapter < source.chapter:
                        if edge.edge_type != EdgeType.FLASHBACK:
                            report.timeline_conflicts.append(
                                f"Node moves to ch.{new_chapter} but follows '{edge.from_node}' in ch.{source.chapter}"
                            )

        # Check character change impact
        old_character = node.character
        new_character = updates.get("character", old_character)

        if new_character != old_character:
            # Check character arc continuity
            char_nodes = [n for n in self.nodes.values()
                         if n.character == old_character and n.id != node_id]
            if char_nodes:
                report.character_arc_gaps.append(
                    f"Character '{old_character}' has {len(char_nodes)} other nodes - verify arc continuity"
                )

        # Apply updates
        for key, value in updates.items():
            if hasattr(node, key):
                setattr(node, key, value)

        after_state = {"node": self._node_to_dict(node), "node_id": node_id}

        self._record_change(
            ChangeType.MODIFY_NODE,
            f"Modified node '{node_id}': {list(updates.keys())}",
            before_state,
            after_state,
            affected_nodes=[node_id],
            author_notes=author_notes,
        )

        # Suggest fixes
        if report.timeline_conflicts:
            report.suggested_fixes.append(
                "Consider adjusting connected nodes' chapters or using FLASHBACK edges"
            )

        return report

    def _node_to_dict(self, node: PlotNode) -> dict:
        """Convert node to dictionary for state storage."""
        return {
            "id": node.id,
            "node_type": node.node_type.value,
            "description": node.description,
            "chapter": node.chapter,
            "character": node.character,
            "subplot": node.subplot,
            "emotional_valence": node.emotional_valence,
            "stakes_level": node.stakes_level,
            "is_twist": node.is_twist,
        }

    def _suggest_connections_for_node(self, node: PlotNode) -> list[str]:
        """Suggest potential connections for a new node."""
        suggestions = []

        # Find nodes in adjacent chapters
        if node.chapter:
            before_chapter = [n for n in self.nodes.values()
                            if n.chapter and n.chapter == node.chapter - 1]
            after_chapter = [n for n in self.nodes.values()
                           if n.chapter and n.chapter == node.chapter + 1]

            if before_chapter:
                suggestions.append(
                    f"Connect from chapter {node.chapter - 1} nodes: {[n.id for n in before_chapter]}"
                )
            if after_chapter:
                suggestions.append(
                    f"Connect to chapter {node.chapter + 1} nodes: {[n.id for n in after_chapter]}"
                )

        # Find nodes with same character
        if node.character:
            same_char = [n for n in self.nodes.values()
                        if n.character == node.character and n.id != node.id]
            if same_char:
                suggestions.append(
                    f"Other '{node.character}' nodes to connect: {[n.id for n in same_char]}"
                )

        # Find nodes in same subplot
        if node.subplot:
            same_subplot = [n for n in self.nodes.values()
                          if n.subplot == node.subplot and n.id != node.id]
            if same_subplot:
                suggestions.append(
                    f"Other subplot '{node.subplot}' nodes: {[n.id for n in same_subplot]}"
                )

        return suggestions

    # =========================================================
    # SUBPLOT MANAGEMENT
    # =========================================================

    def create_subplot(
        self,
        subplot_id: str,
        name: str,
        description: str,
        primary_characters: list[str] = None,
    ) -> Subplot:
        """Create a new subplot/side-story."""
        subplot = Subplot(
            id=subplot_id,
            name=name,
            description=description,
            primary_characters=primary_characters or [],
        )
        self._subplots[subplot_id] = subplot

        self._record_change(
            ChangeType.ADD_SUBPLOT,
            f"Created subplot '{name}'",
            {},
            {"subplot_id": subplot_id, "name": name},
            author_notes=description,
        )

        return subplot

    def add_node_to_subplot(self, node_id: str, subplot_id: str) -> None:
        """Assign a node to a subplot."""
        if subplot_id not in self._subplots:
            raise ValueError(f"Subplot '{subplot_id}' does not exist")
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")

        subplot = self._subplots[subplot_id]
        if node_id not in subplot.node_ids:
            subplot.node_ids.append(node_id)
            self.nodes[node_id].subplot = subplot_id

    def set_merge_point(
        self,
        subplot_id: str,
        node_id: str,
        merge_chapter: int = None,
    ) -> ImpactReport:
        """
        Define where a subplot merges with main plot.

        The merge point is a node that connects subplot to main story.
        """
        if subplot_id not in self._subplots:
            raise ValueError(f"Subplot '{subplot_id}' does not exist")

        subplot = self._subplots[subplot_id]
        report = ImpactReport(
            change_description=f"Setting merge point for subplot '{subplot.name}'"
        )

        # Node can be in subplot or main plot
        if node_id not in self.nodes:
            report.suggested_fixes.append(f"Node '{node_id}' does not exist - create it first")
            return report

        subplot.merge_points.append(node_id)
        if merge_chapter:
            subplot.merge_chapter = merge_chapter

        # Check for connectivity
        subplot_nodes = set(subplot.node_ids)
        merge_node = self.nodes[node_id]

        # Verify subplot nodes can reach merge point
        reachable = self._find_reachable_from(subplot_nodes)
        if node_id not in reachable and node_id not in subplot_nodes:
            report.subplot_disconnections.append(
                f"Subplot nodes cannot reach merge point '{node_id}'"
            )
            report.suggested_fixes.append(
                f"Add edge from subplot node to '{node_id}'"
            )

        self._record_change(
            ChangeType.MERGE_SUBPLOT,
            f"Set merge point '{node_id}' for subplot '{subplot.name}'",
            {},
            {"subplot_id": subplot_id, "merge_node": node_id},
        )

        return report

    def _find_reachable_from(self, start_nodes: set[str]) -> set[str]:
        """Find all nodes reachable from a set of starting nodes."""
        reachable = set(start_nodes)
        frontier = list(start_nodes)

        while frontier:
            current = frontier.pop()
            for edge in self.edges:
                if edge.from_node == current and edge.to_node not in reachable:
                    reachable.add(edge.to_node)
                    frontier.append(edge.to_node)

        return reachable

    def get_subplot_status(self, subplot_id: str) -> dict:
        """Get detailed status of a subplot."""
        if subplot_id not in self._subplots:
            return {"error": f"Subplot '{subplot_id}' not found"}

        subplot = self._subplots[subplot_id]
        nodes = [self.nodes[nid] for nid in subplot.node_ids if nid in self.nodes]

        # Calculate subplot metrics
        chapters = [n.chapter for n in nodes if n.chapter]
        characters = set(n.character for n in nodes if n.character)

        # Check connectivity within subplot
        subplot_edges = [e for e in self.edges
                        if e.from_node in subplot.node_ids and e.to_node in subplot.node_ids]

        return {
            "id": subplot.id,
            "name": subplot.name,
            "description": subplot.description,
            "node_count": len(nodes),
            "chapter_range": (min(chapters), max(chapters)) if chapters else None,
            "characters": list(characters),
            "internal_edges": len(subplot_edges),
            "merge_points": subplot.merge_points,
            "is_merged": subplot.is_merged,
            "merge_chapter": subplot.merge_chapter,
        }

    # =========================================================
    # VERSION SNAPSHOTS
    # =========================================================

    def create_snapshot(self, name: str, description: str = "") -> str:
        """Create a named snapshot of current DAG state."""
        snapshot = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "nodes": {nid: self._node_to_dict(n) for nid, n in self.nodes.items()},
            "edges": [{"from": e.from_node, "to": e.to_node, "type": e.edge_type.value}
                     for e in self.edges],
            "subplots": {sid: {
                "id": s.id, "name": s.name, "description": s.description,
                "node_ids": s.node_ids.copy(), "merge_points": s.merge_points.copy(),
            } for sid, s in self._subplots.items()},
            "change_count": len(self._change_history),
        }
        self._snapshots[name] = snapshot
        return name

    def restore_snapshot(self, name: str) -> bool:
        """Restore DAG to a previous snapshot."""
        if name not in self._snapshots:
            return False

        snapshot = self._snapshots[name]

        # Clear current state
        self.nodes.clear()
        self.edges.clear()
        self._subplots.clear()

        # Restore nodes
        for node_data in snapshot["nodes"].values():
            node = PlotNode(
                id=node_data["id"],
                node_type=NodeType(node_data["node_type"]),
                description=node_data["description"],
                chapter=node_data.get("chapter"),
                character=node_data.get("character"),
                subplot=node_data.get("subplot"),
                emotional_valence=node_data.get("emotional_valence", 0.0),
                stakes_level=node_data.get("stakes_level", 5),
                is_twist=node_data.get("is_twist", False),
            )
            self.nodes[node.id] = node

        # Restore edges
        for edge_data in snapshot["edges"]:
            self.add_edge(
                edge_data["from"],
                edge_data["to"],
                EdgeType(edge_data["type"]),
            )

        # Restore subplots
        for subplot_data in snapshot["subplots"].values():
            subplot = Subplot(
                id=subplot_data["id"],
                name=subplot_data["name"],
                description=subplot_data["description"],
            )
            subplot.node_ids = subplot_data["node_ids"]
            subplot.merge_points = subplot_data["merge_points"]
            self._subplots[subplot.id] = subplot

        self._record_change(
            ChangeType.BATCH_UPDATE,
            f"Restored snapshot '{name}'",
            {},
            {"snapshot_name": name},
        )

        return True

    def list_snapshots(self) -> list[dict]:
        """List all available snapshots."""
        return [
            {
                "name": name,
                "description": snap["description"],
                "timestamp": snap["timestamp"],
                "node_count": len(snap["nodes"]),
            }
            for name, snap in self._snapshots.items()
        ]


class CoherenceValidator:
    """
    Validates narrative DAG coherence after modifications.

    Checks:
    - Structural integrity (no orphans, no unreachable nodes)
    - Timeline consistency (causes before effects)
    - Character arc completeness
    - Subplot integration
    - Genre convention adherence
    """

    def __init__(self, dag: DynamicNarrativeDAG):
        self.dag = dag

    def full_validation(self) -> ImpactReport:
        """Run all validation checks."""
        report = ImpactReport(change_description="Full DAG Validation")

        self._check_structural_integrity(report)
        self._check_timeline_consistency(report)
        self._check_character_arcs(report)
        self._check_subplot_integration(report)
        self._generate_fix_suggestions(report)

        return report

    def _check_structural_integrity(self, report: ImpactReport) -> None:
        """Check for orphans, dead-ends, unreachable nodes."""
        if not self.dag.nodes:
            return

        # Find nodes with no incoming edges (potential entry points)
        entry_points = set(self.dag.nodes.keys())
        for edge in self.dag.edges:
            entry_points.discard(edge.to_node)

        # Find nodes with no outgoing edges (potential endpoints)
        exit_points = set(self.dag.nodes.keys())
        for edge in self.dag.edges:
            exit_points.discard(edge.from_node)

        # Check reachability from entry points
        reachable = set()
        for entry in entry_points:
            reachable.update(self.dag._find_reachable_from({entry}))

        unreachable = set(self.dag.nodes.keys()) - reachable
        report.unreachable_nodes.extend(unreachable)

        # Dead ends that aren't resolution nodes
        for node_id in exit_points:
            node = self.dag.nodes.get(node_id)
            if node and node.node_type not in (NodeType.RESOLUTION, NodeType.CLIFFHANGER):
                report.dead_end_nodes.append(node_id)

    def _check_timeline_consistency(self, report: ImpactReport) -> None:
        """Verify causality flows forward in time (except flashbacks)."""
        for edge in self.dag.edges:
            if edge.edge_type == EdgeType.FLASHBACK:
                continue

            from_node = self.dag.nodes.get(edge.from_node)
            to_node = self.dag.nodes.get(edge.to_node)

            if from_node and to_node and from_node.chapter and to_node.chapter:
                if from_node.chapter > to_node.chapter:
                    report.timeline_conflicts.append(
                        f"'{edge.from_node}' (ch.{from_node.chapter}) → "
                        f"'{edge.to_node}' (ch.{to_node.chapter}): cause after effect"
                    )

    def _check_character_arcs(self, report: ImpactReport) -> None:
        """Verify character arcs have proper progression."""
        # Group nodes by character
        char_nodes: dict[str, list[PlotNode]] = defaultdict(list)
        for node in self.dag.nodes.values():
            if node.character:
                char_nodes[node.character].append(node)

        for character, nodes in char_nodes.items():
            if len(nodes) < 2:
                continue

            # Sort by chapter
            sorted_nodes = sorted(nodes, key=lambda n: n.chapter or 0)

            # Check for large gaps in chapters
            for i in range(len(sorted_nodes) - 1):
                current = sorted_nodes[i]
                next_node = sorted_nodes[i + 1]
                if current.chapter and next_node.chapter:
                    gap = next_node.chapter - current.chapter
                    if gap > 5:  # More than 5 chapters without this character
                        report.character_arc_gaps.append(
                            f"'{character}' absent for {gap} chapters "
                            f"(ch.{current.chapter} to ch.{next_node.chapter})"
                        )

    def _check_subplot_integration(self, report: ImpactReport) -> None:
        """Verify subplots connect to main story."""
        for subplot_id, subplot in self.dag._subplots.items():
            if not subplot.node_ids:
                report.subplot_disconnections.append(
                    f"Subplot '{subplot.name}' has no nodes"
                )
                continue

            if not subplot.merge_points:
                report.subplot_disconnections.append(
                    f"Subplot '{subplot.name}' has no merge points with main plot"
                )

            # Check if subplot nodes connect to merge points
            subplot_nodes = set(subplot.node_ids)
            for merge_point in subplot.merge_points:
                # Find if any subplot node connects to merge point
                connected = False
                for edge in self.dag.edges:
                    if edge.from_node in subplot_nodes and edge.to_node == merge_point:
                        connected = True
                        break
                    if edge.from_node == merge_point and edge.to_node in subplot_nodes:
                        connected = True
                        break

                if not connected and merge_point not in subplot_nodes:
                    report.subplot_disconnections.append(
                        f"Subplot '{subplot.name}' has no edge to merge point '{merge_point}'"
                    )

    def _generate_fix_suggestions(self, report: ImpactReport) -> None:
        """Generate actionable suggestions for fixing issues."""
        if report.unreachable_nodes:
            report.suggested_fixes.append(
                f"Add edges from existing nodes to: {list(report.unreachable_nodes)[:3]}"
            )

        if report.dead_end_nodes:
            report.suggested_fixes.append(
                f"Add continuation edges from: {list(report.dead_end_nodes)[:3]}"
            )

        if report.timeline_conflicts:
            report.suggested_fixes.append(
                "Review chapter assignments or convert edges to FLASHBACK type"
            )

        if report.character_arc_gaps:
            report.suggested_fixes.append(
                "Add intermediate nodes for absent characters or justify absence in plot"
            )

        if report.subplot_disconnections:
            report.suggested_fixes.append(
                "Define merge points and add connecting edges for subplots"
            )


class ImpactAnalyzer:
    """
    Analyzes potential impact of changes before they're made.

    Use this to preview what will break/change before committing.
    """

    def __init__(self, dag: DynamicNarrativeDAG):
        self.dag = dag

    def preview_node_removal(self, node_id: str) -> ImpactReport:
        """Preview impact of removing a node without actually removing it."""
        # Create temporary copy
        temp_dag = copy.deepcopy(self.dag)
        return temp_dag.remove_node_dynamic(node_id, cascade=False)

    def preview_node_modification(self, node_id: str, updates: dict) -> ImpactReport:
        """Preview impact of modifying a node."""
        temp_dag = copy.deepcopy(self.dag)
        return temp_dag.modify_node_dynamic(node_id, updates)

    def preview_chapter_reorder(
        self,
        reorder_map: dict[int, int],
    ) -> ImpactReport:
        """
        Preview impact of reordering chapters.

        reorder_map: {old_chapter: new_chapter}
        """
        report = ImpactReport(
            change_description=f"Reordering chapters: {reorder_map}"
        )

        # Check each edge for timeline violations
        for edge in self.dag.edges:
            if edge.edge_type == EdgeType.FLASHBACK:
                continue

            from_node = self.dag.nodes.get(edge.from_node)
            to_node = self.dag.nodes.get(edge.to_node)

            if from_node and to_node and from_node.chapter and to_node.chapter:
                new_from = reorder_map.get(from_node.chapter, from_node.chapter)
                new_to = reorder_map.get(to_node.chapter, to_node.chapter)

                if new_from > new_to:
                    report.timeline_conflicts.append(
                        f"'{from_node.id}' would move to ch.{new_from}, "
                        f"after '{to_node.id}' at ch.{new_to}"
                    )

        return report

    def find_ripple_effects(self, node_id: str) -> dict:
        """
        Find all nodes that depend on or are affected by a given node.

        Returns dict with:
        - downstream: nodes that this node leads to
        - upstream: nodes that lead to this node
        - same_character: nodes with same character
        - same_subplot: nodes in same subplot
        """
        if node_id not in self.dag.nodes:
            return {"error": f"Node '{node_id}' not found"}

        node = self.dag.nodes[node_id]

        # Find downstream (what this node causes)
        downstream = self.dag._find_reachable_from({node_id}) - {node_id}

        # Find upstream (what leads to this node)
        upstream = set()
        for other_id in self.dag.nodes:
            if other_id != node_id:
                if node_id in self.dag._find_reachable_from({other_id}):
                    upstream.add(other_id)

        # Same character
        same_char = {n.id for n in self.dag.nodes.values()
                    if n.character == node.character and n.id != node_id} if node.character else set()

        # Same subplot
        same_subplot = {n.id for n in self.dag.nodes.values()
                       if n.subplot == node.subplot and n.id != node_id} if node.subplot else set()

        return {
            "node": node_id,
            "downstream": list(downstream),
            "upstream": list(upstream),
            "same_character": list(same_char),
            "same_subplot": list(same_subplot),
            "total_affected": len(downstream | upstream | same_char | same_subplot),
        }


# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================

def create_dynamic_dag(
    title: str,
    genre: str = "general",
    target_chapters: int = 20,
) -> DynamicNarrativeDAG:
    """Create a new dynamic DAG ready for iterative authoring."""
    return DynamicNarrativeDAG(title, genre, target_chapters)


def validate_dag(dag: DynamicNarrativeDAG) -> ImpactReport:
    """Run full validation on a DAG."""
    validator = CoherenceValidator(dag)
    return validator.full_validation()


def analyze_impact(dag: DynamicNarrativeDAG, node_id: str) -> dict:
    """Analyze ripple effects of changes to a node."""
    analyzer = ImpactAnalyzer(dag)
    return analyzer.find_ripple_effects(node_id)
