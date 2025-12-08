"""
Narrative DAG - Core data structures for modeling book/novel plot structures.

This module provides the fundamental building blocks for representing
story structures as Directed Acyclic Graphs.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import networkx as nx


class NodeType(Enum):
    """Types of plot elements in a narrative DAG."""

    SETUP = auto()  # Establishing information (world, character, stakes)
    CATALYST = auto()  # Inciting incident that starts the journey
    COMPLICATION = auto()  # Obstacle or twist that raises stakes
    REVELATION = auto()  # Information that changes understanding
    DECISION = auto()  # Character choice that affects trajectory
    CONSEQUENCE = auto()  # Result of prior actions
    CONFRONTATION = auto()  # Direct conflict or challenge
    RESOLUTION = auto()  # Closure of a thread
    CLIFFHANGER = auto()  # Unresolved tension (chapter/act boundaries)
    FLASHBACK = auto()  # Past event providing context
    FORESHADOWING = auto()  # Hint at future events


class EdgeType(Enum):
    """Types of narrative dependencies between plot elements."""

    CAUSES = auto()  # A directly causes B
    ENABLES = auto()  # A makes B possible (but doesn't guarantee it)
    REVEALS = auto()  # A provides context that reframes B
    FORESHADOWS = auto()  # A hints at future B (reader may not notice)
    CONTRASTS = auto()  # A and B are thematically opposed
    PARALLELS = auto()  # A and B mirror each other structurally
    REQUIRES = auto()  # B cannot happen without A
    INTERRUPTS = auto()  # B breaks the flow from A
    RESOLVES = auto()  # B closes the thread opened by A


@dataclass
class PlotNode:
    """A single plot element in a narrative DAG."""

    id: str
    node_type: NodeType
    description: str
    chapter: Optional[int] = None
    character: Optional[str] = None  # Primary character involved
    subplot: Optional[str] = None  # Which storyline this belongs to
    emotional_valence: float = 0.0  # -1 (negative) to +1 (positive)
    stakes_level: int = 1  # 1-10 scale
    is_twist: bool = False  # Major revelation that recontextualizes prior events

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "node_type": self.node_type.name,
            "description": self.description,
            "chapter": self.chapter,
            "character": self.character,
            "subplot": self.subplot,
            "emotional_valence": self.emotional_valence,
            "stakes_level": self.stakes_level,
            "is_twist": self.is_twist,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlotNode":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            node_type=NodeType[data["node_type"]],
            description=data["description"],
            chapter=data.get("chapter"),
            character=data.get("character"),
            subplot=data.get("subplot"),
            emotional_valence=data.get("emotional_valence", 0.0),
            stakes_level=data.get("stakes_level", 1),
            is_twist=data.get("is_twist", False),
        )


@dataclass
class NarrativeMetrics:
    """Metrics for analyzing narrative DAG structure quality."""

    # Pacing metrics
    chapter_density: float = 0.0  # Nodes per chapter
    revelation_spacing: float = 0.0  # Average chapters between revelations
    cliffhanger_frequency: float = 0.0  # Proportion of chapters ending in cliffhanger

    # Coherence metrics
    dangling_threads: int = 0  # Setup nodes without resolution
    orphan_nodes: int = 0  # Events without causal connection
    causal_depth: int = 0  # Longest dependency chain
    resolution_rate: float = 0.0  # Proportion of setups that resolve

    # Tension metrics
    complication_gradient: float = 0.0  # Rate of obstacle introduction
    stakes_escalation: float = 0.0  # How quickly stakes increase
    peak_stakes_position: float = 0.0  # Where climax falls (0-1)

    # Character metrics
    arc_completeness: float = 0.0  # Percentage of character arcs resolved
    agency_ratio: float = 0.0  # Character decisions vs. external events
    pov_balance: float = 0.0  # Balance across POV characters (0=unbalanced, 1=equal)

    # Structural metrics
    twist_count: int = 0  # Number of major revelations
    subplot_count: int = 0  # Number of parallel storylines
    convergence_point: Optional[float] = None  # When threads merge (0-1)

    def summary(self) -> str:
        """Return human-readable summary of metrics."""
        lines = [
            "=== Narrative DAG Metrics ===",
            "",
            "PACING:",
            f"  Chapter density: {self.chapter_density:.2f} nodes/chapter",
            f"  Revelation spacing: {self.revelation_spacing:.1f} chapters",
            f"  Cliffhanger frequency: {self.cliffhanger_frequency:.1%}",
            "",
            "COHERENCE:",
            f"  Dangling threads: {self.dangling_threads}",
            f"  Orphan nodes: {self.orphan_nodes}",
            f"  Causal depth: {self.causal_depth}",
            f"  Resolution rate: {self.resolution_rate:.1%}",
            "",
            "TENSION:",
            f"  Complication gradient: {self.complication_gradient:.2f}",
            f"  Stakes escalation: {self.stakes_escalation:.2f}",
            f"  Peak stakes position: {self.peak_stakes_position:.1%}",
            "",
            "CHARACTER:",
            f"  Arc completeness: {self.arc_completeness:.1%}",
            f"  Agency ratio: {self.agency_ratio:.1%}",
            f"  POV balance: {self.pov_balance:.2f}",
            "",
            "STRUCTURE:",
            f"  Twist count: {self.twist_count}",
            f"  Subplot count: {self.subplot_count}",
            f"  Convergence point: {self.convergence_point:.1%}"
            if self.convergence_point
            else "  Convergence point: N/A",
        ]
        return "\n".join(lines)


class NarrativeDAG:
    """
    A Directed Acyclic Graph representing a novel's plot structure.

    Nodes represent plot elements (setup, complication, revelation, etc.)
    Edges represent narrative dependencies (causes, enables, reveals, etc.)
    """

    def __init__(self, title: str = "Untitled", author: str = "Unknown"):
        self.title = title
        self.author = author
        self.graph = nx.DiGraph()
        self._nodes: dict[str, PlotNode] = {}
        self._chapter_count = 0

    def add_node(self, node: PlotNode) -> None:
        """Add a plot node to the narrative."""
        self._nodes[node.id] = node
        self.graph.add_node(node.id, **node.to_dict())
        if node.chapter and node.chapter > self._chapter_count:
            self._chapter_count = node.chapter

    def add_edge(
        self, source_id: str, target_id: str, edge_type: EdgeType, weight: float = 1.0
    ) -> None:
        """Add a narrative dependency between plot elements."""
        if source_id not in self._nodes:
            raise ValueError(f"Source node '{source_id}' not found")
        if target_id not in self._nodes:
            raise ValueError(f"Target node '{target_id}' not found")

        self.graph.add_edge(
            source_id, target_id, edge_type=edge_type.name, weight=weight
        )

    def get_node(self, node_id: str) -> Optional[PlotNode]:
        """Get a plot node by ID."""
        return self._nodes.get(node_id)

    def get_chapter_nodes(self, chapter: int) -> list[PlotNode]:
        """Get all nodes in a specific chapter."""
        return [n for n in self._nodes.values() if n.chapter == chapter]

    def get_character_arc(self, character: str) -> list[PlotNode]:
        """Get all nodes involving a specific character, in chapter order."""
        nodes = [n for n in self._nodes.values() if n.character == character]
        return sorted(nodes, key=lambda n: n.chapter or 0)

    def get_subplot_nodes(self, subplot: str) -> list[PlotNode]:
        """Get all nodes in a specific subplot."""
        return [n for n in self._nodes.values() if n.subplot == subplot]

    def is_valid_dag(self) -> bool:
        """Check if the graph is a valid DAG (no cycles)."""
        return nx.is_directed_acyclic_graph(self.graph)

    def get_causal_chain(self, node_id: str) -> list[str]:
        """Get all ancestors of a node (everything that led to it)."""
        return list(nx.ancestors(self.graph, node_id))

    def get_consequences(self, node_id: str) -> list[str]:
        """Get all descendants of a node (everything it affects)."""
        return list(nx.descendants(self.graph, node_id))

    def find_dangling_setups(self) -> list[PlotNode]:
        """Find setup nodes that never get resolved."""
        dangling = []
        for node in self._nodes.values():
            if node.node_type == NodeType.SETUP:
                descendants = self.get_consequences(node.id)
                has_resolution = any(
                    self._nodes[d].node_type == NodeType.RESOLUTION for d in descendants
                )
                if not has_resolution:
                    dangling.append(node)
        return dangling

    def find_orphan_nodes(self) -> list[PlotNode]:
        """Find nodes with no incoming edges (except valid starting points)."""
        orphans = []
        for node_id in self.graph.nodes():
            if self.graph.in_degree(node_id) == 0:
                node = self._nodes[node_id]
                # Starting setups and catalysts are allowed to be orphans
                if node.node_type not in [NodeType.SETUP, NodeType.CATALYST]:
                    orphans.append(node)
        return orphans

    def find_unfired_foreshadowing(self) -> list[tuple[PlotNode, str]]:
        """Find foreshadowing that never pays off."""
        unfired = []
        for source, target, data in self.graph.edges(data=True):
            if data.get("edge_type") == EdgeType.FORESHADOWS.name:
                # Check if the foreshadowed event actually happens
                target_node = self._nodes[target]
                if target_node.node_type == NodeType.FORESHADOWING:
                    # This is just hinting, check if it connects to real event
                    if self.graph.out_degree(target) == 0:
                        unfired.append((self._nodes[source], target))
        return unfired

    def calculate_metrics(self) -> NarrativeMetrics:
        """Calculate comprehensive metrics for this narrative DAG."""
        metrics = NarrativeMetrics()

        if not self._nodes:
            return metrics

        # Chapter density
        if self._chapter_count > 0:
            metrics.chapter_density = len(self._nodes) / self._chapter_count

        # Revelation spacing
        revelations = [
            n for n in self._nodes.values() if n.node_type == NodeType.REVELATION
        ]
        if len(revelations) > 1:
            chapters = sorted([r.chapter for r in revelations if r.chapter])
            if len(chapters) > 1:
                gaps = [chapters[i + 1] - chapters[i] for i in range(len(chapters) - 1)]
                metrics.revelation_spacing = sum(gaps) / len(gaps)

        # Cliffhanger frequency
        if self._chapter_count > 0:
            cliffhangers = sum(
                1
                for n in self._nodes.values()
                if n.node_type == NodeType.CLIFFHANGER
            )
            metrics.cliffhanger_frequency = cliffhangers / self._chapter_count

        # Dangling threads
        metrics.dangling_threads = len(self.find_dangling_setups())

        # Orphan nodes
        metrics.orphan_nodes = len(self.find_orphan_nodes())

        # Causal depth
        if self.is_valid_dag():
            metrics.causal_depth = nx.dag_longest_path_length(self.graph)

        # Resolution rate
        setups = [n for n in self._nodes.values() if n.node_type == NodeType.SETUP]
        if setups:
            resolved = len(setups) - metrics.dangling_threads
            metrics.resolution_rate = resolved / len(setups)

        # Stakes escalation
        stakes_by_chapter: dict[int, list[int]] = {}
        for node in self._nodes.values():
            if node.chapter:
                if node.chapter not in stakes_by_chapter:
                    stakes_by_chapter[node.chapter] = []
                stakes_by_chapter[node.chapter].append(node.stakes_level)

        if len(stakes_by_chapter) > 1:
            avg_stakes = {ch: sum(s) / len(s) for ch, s in stakes_by_chapter.items()}
            chapters = sorted(avg_stakes.keys())
            if len(chapters) > 1:
                escalation = [
                    avg_stakes[chapters[i + 1]] - avg_stakes[chapters[i]]
                    for i in range(len(chapters) - 1)
                ]
                metrics.stakes_escalation = sum(escalation) / len(escalation)

        # Peak stakes position
        if stakes_by_chapter:
            max_chapter = max(stakes_by_chapter.keys(), key=lambda c: max(stakes_by_chapter[c]))
            metrics.peak_stakes_position = max_chapter / self._chapter_count

        # Twist count
        metrics.twist_count = sum(1 for n in self._nodes.values() if n.is_twist)

        # Subplot count
        subplots = set(n.subplot for n in self._nodes.values() if n.subplot)
        metrics.subplot_count = len(subplots)

        # Character metrics
        characters = set(n.character for n in self._nodes.values() if n.character)
        if characters:
            # POV balance
            char_counts = {}
            for n in self._nodes.values():
                if n.character:
                    char_counts[n.character] = char_counts.get(n.character, 0) + 1
            if char_counts:
                counts = list(char_counts.values())
                avg = sum(counts) / len(counts)
                variance = sum((c - avg) ** 2 for c in counts) / len(counts)
                max_variance = avg**2  # Maximum possible variance
                metrics.pov_balance = (
                    1 - (variance / max_variance) if max_variance > 0 else 1
                )

            # Agency ratio
            decisions = sum(
                1 for n in self._nodes.values() if n.node_type == NodeType.DECISION
            )
            external = sum(
                1
                for n in self._nodes.values()
                if n.node_type in [NodeType.COMPLICATION, NodeType.CONSEQUENCE]
            )
            if decisions + external > 0:
                metrics.agency_ratio = decisions / (decisions + external)

        return metrics

    def to_dict(self) -> dict:
        """Serialize the narrative DAG to a dictionary."""
        return {
            "title": self.title,
            "author": self.author,
            "chapter_count": self._chapter_count,
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "edge_type": d.get("edge_type"),
                    "weight": d.get("weight", 1.0),
                }
                for u, v, d in self.graph.edges(data=True)
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeDAG":
        """Deserialize from a dictionary."""
        dag = cls(title=data.get("title", "Untitled"), author=data.get("author", "Unknown"))

        for node_data in data.get("nodes", []):
            dag.add_node(PlotNode.from_dict(node_data))

        for edge_data in data.get("edges", []):
            dag.add_edge(
                edge_data["source"],
                edge_data["target"],
                EdgeType[edge_data["edge_type"]],
                edge_data.get("weight", 1.0),
            )

        return dag

    def __repr__(self) -> str:
        return (
            f"NarrativeDAG(title='{self.title}', "
            f"nodes={len(self._nodes)}, "
            f"edges={self.graph.number_of_edges()}, "
            f"chapters={self._chapter_count})"
        )
