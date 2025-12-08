"""
Gap Discovery and Resolution for Narrative DAGs.

Inspired by chain_reflow's gap detection workflows, this module helps:
- Find missing plot elements between known scenes
- Determine how characters should interact (protagonist/antagonist gel)
- Generate spinoff storylines
- Merge partial plots into coherent wholes

Key Concepts from chain_reflow:
- Homography matrix transformation for finding missing systems
- SVD-based gap detection to identify transformational elements
- Strategy determination for linking orthogonal graphs
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import math

from .narrative_dag import NarrativeDAG, PlotNode, NodeType, EdgeType


class LinkingStrategy(Enum):
    """Strategy for linking narrative fragments together."""

    HIERARCHICAL = auto()  # Clear parent-child (main plot → subplot)
    PAIRWISE = auto()  # Direct connection between two threads
    NETWORK = auto()  # Multiple threads with peer relationships
    PHASED = auto()  # Large story with cluster-first approach
    WITH_INTERMEDIARIES = auto()  # High orthogonality requiring bridge scenes


@dataclass
class NarrativeGap:
    """A detected gap in the narrative structure."""

    gap_type: str  # "causal", "character", "temporal", "thematic"
    source_node: Optional[PlotNode]  # Where we are
    target_node: Optional[PlotNode]  # Where we need to get
    description: str
    severity: int  # 1-5, how critical this gap is
    suggested_bridges: list[str]  # Potential node types to bridge
    confidence: float  # 0-1, confidence in the gap detection


@dataclass
class CharacterGel:
    """Analysis of how two characters should relate."""

    character_a: str
    character_b: str
    suggested_relationship: str  # "protagonist-antagonist", "allies", "rivals", etc.
    connection_strength: float  # 0-1
    suggested_scenes: list[str]  # Scenes that would establish this relationship
    thematic_tension: str  # What drives their dynamic


@dataclass
class SpinoffSeed:
    """A potential spinoff story derived from the main narrative."""

    origin_node: PlotNode
    spinoff_theme: str
    divergence_point: str
    potential_length: str  # "short story", "novella", "novel"
    key_elements: list[str]


class NarrativeGapDetector:
    """
    Detects gaps in narrative structures using techniques inspired
    by chain_reflow's matrix-based gap detection.

    Instead of mathematical matrices, we use narrative "transformation patterns"
    to identify what's missing between known story elements.
    """

    def __init__(self, dag: NarrativeDAG):
        self.dag = dag

    def detect_all_gaps(self) -> list[NarrativeGap]:
        """Run comprehensive gap detection."""
        gaps = []
        gaps.extend(self._detect_causal_gaps())
        gaps.extend(self._detect_character_gaps())
        gaps.extend(self._detect_temporal_gaps())
        gaps.extend(self._detect_thematic_gaps())
        return sorted(gaps, key=lambda g: g.severity, reverse=True)

    def _detect_causal_gaps(self) -> list[NarrativeGap]:
        """
        Find causal chain breaks - events that need intermediary steps.

        Like chain_reflow's homography detection, we look for "transformations"
        between plot states that seem too large for a single step.
        """
        gaps = []

        for node in self.dag._nodes.values():
            # Check for CAUSES edges that skip too many steps
            for successor_id in self.dag.graph.successors(node.id):
                edge_data = self.dag.graph.get_edge_data(node.id, successor_id)
                if edge_data and edge_data.get("edge_type") == EdgeType.CAUSES.name:
                    successor = self.dag.get_node(successor_id)
                    if successor:
                        # Check stakes jump
                        stakes_jump = abs(successor.stakes_level - node.stakes_level)
                        chapter_jump = (
                            abs(successor.chapter - node.chapter)
                            if successor.chapter and node.chapter
                            else 0
                        )

                        # Large jumps suggest missing intermediary
                        if stakes_jump > 3 or chapter_jump > 5:
                            gaps.append(
                                NarrativeGap(
                                    gap_type="causal",
                                    source_node=node,
                                    target_node=successor,
                                    description=f"Large jump from '{node.description}' to '{successor.description}'",
                                    severity=min(5, stakes_jump),
                                    suggested_bridges=self._suggest_causal_bridges(
                                        node, successor
                                    ),
                                    confidence=0.8,
                                )
                            )

        return gaps

    def _suggest_causal_bridges(
        self, source: PlotNode, target: PlotNode
    ) -> list[str]:
        """Suggest node types that could bridge a causal gap."""
        bridges = []

        # If stakes increase dramatically, need escalation steps
        if target.stakes_level > source.stakes_level + 2:
            bridges.append("COMPLICATION - raise stakes gradually")
            bridges.append("REVELATION - provide information that increases tension")

        # If going from setup to confrontation, need development
        if (
            source.node_type == NodeType.SETUP
            and target.node_type == NodeType.CONFRONTATION
        ):
            bridges.append("DECISION - character makes choice that leads to conflict")
            bridges.append("CONSEQUENCE - prior action escalates to confrontation")

        # If resolution comes too fast
        if (
            source.node_type in [NodeType.COMPLICATION, NodeType.CATALYST]
            and target.node_type == NodeType.RESOLUTION
        ):
            bridges.append("CONFRONTATION - dramatic climax before resolution")
            bridges.append("DECISION - character agency in reaching resolution")

        return bridges if bridges else ["CONSEQUENCE - intermediate step"]

    def _detect_character_gaps(self) -> list[NarrativeGap]:
        """
        Find character arc gaps - characters who appear without setup
        or disappear without resolution.
        """
        gaps = []
        characters: dict[str, list[PlotNode]] = {}

        # Group nodes by character
        for node in self.dag._nodes.values():
            if node.character:
                if node.character not in characters:
                    characters[node.character] = []
                characters[node.character].append(node)

        for char, nodes in characters.items():
            sorted_nodes = sorted(nodes, key=lambda n: n.chapter or 0)

            # Check for proper introduction
            first_node = sorted_nodes[0]
            if first_node.node_type not in [NodeType.SETUP, NodeType.CATALYST]:
                gaps.append(
                    NarrativeGap(
                        gap_type="character",
                        source_node=None,
                        target_node=first_node,
                        description=f"Character '{char}' appears without introduction",
                        severity=3,
                        suggested_bridges=["SETUP - introduce character properly"],
                        confidence=0.9,
                    )
                )

            # Check for resolution (if character has significant presence)
            if len(sorted_nodes) >= 3:
                last_node = sorted_nodes[-1]
                if last_node.node_type not in [NodeType.RESOLUTION, NodeType.CONSEQUENCE]:
                    gaps.append(
                        NarrativeGap(
                            gap_type="character",
                            source_node=last_node,
                            target_node=None,
                            description=f"Character '{char}' arc lacks resolution",
                            severity=2,
                            suggested_bridges=[
                                "RESOLUTION - close character arc",
                                "CONSEQUENCE - show outcome of character's journey",
                            ],
                            confidence=0.7,
                        )
                    )

            # Check for gaps in character's timeline
            for i in range(len(sorted_nodes) - 1):
                current = sorted_nodes[i]
                next_node = sorted_nodes[i + 1]
                if current.chapter and next_node.chapter:
                    chapter_gap = next_node.chapter - current.chapter
                    if chapter_gap > 5:
                        gaps.append(
                            NarrativeGap(
                                gap_type="character",
                                source_node=current,
                                target_node=next_node,
                                description=f"Character '{char}' absent for {chapter_gap} chapters",
                                severity=2,
                                suggested_bridges=[
                                    f"Intermediate scene with {char} to maintain presence"
                                ],
                                confidence=0.6,
                            )
                        )

        return gaps

    def _detect_temporal_gaps(self) -> list[NarrativeGap]:
        """Find pacing issues - chapters with no plot advancement."""
        gaps = []

        chapter_nodes: dict[int, list[PlotNode]] = {}
        for node in self.dag._nodes.values():
            if node.chapter:
                if node.chapter not in chapter_nodes:
                    chapter_nodes[node.chapter] = []
                chapter_nodes[node.chapter].append(node)

        if not chapter_nodes:
            return gaps

        max_chapter = max(chapter_nodes.keys())
        avg_density = len(self.dag._nodes) / max_chapter if max_chapter > 0 else 0

        # Find empty or sparse chapters
        for ch in range(1, max_chapter + 1):
            nodes = chapter_nodes.get(ch, [])
            if len(nodes) == 0:
                gaps.append(
                    NarrativeGap(
                        gap_type="temporal",
                        source_node=None,
                        target_node=None,
                        description=f"Chapter {ch} has no plot nodes",
                        severity=4,
                        suggested_bridges=[
                            "Add plot advancement to chapter",
                            "Consider merging with adjacent chapter",
                        ],
                        confidence=1.0,
                    )
                )
            elif len(nodes) < avg_density * 0.3:
                gaps.append(
                    NarrativeGap(
                        gap_type="temporal",
                        source_node=nodes[0] if nodes else None,
                        target_node=None,
                        description=f"Chapter {ch} is sparse ({len(nodes)} nodes vs avg {avg_density:.1f})",
                        severity=2,
                        suggested_bridges=["Add subplot advancement", "Deepen character moment"],
                        confidence=0.7,
                    )
                )

        return gaps

    def _detect_thematic_gaps(self) -> list[NarrativeGap]:
        """Find thematic issues - setups without payoffs, foreshadowing without resolution."""
        gaps = []

        # Find foreshadowing without payoff
        for source, target, data in self.dag.graph.edges(data=True):
            if data.get("edge_type") == EdgeType.FORESHADOWS.name:
                # Check if the foreshadowed element connects to meaningful resolution
                target_node = self.dag.get_node(target)
                if target_node:
                    descendants = self.dag.get_consequences(target)
                    has_payoff = any(
                        self.dag.get_node(d)
                        and self.dag.get_node(d).node_type
                        in [NodeType.REVELATION, NodeType.RESOLUTION, NodeType.CONFRONTATION]
                        for d in descendants
                    )
                    if not has_payoff:
                        source_node = self.dag.get_node(source)
                        gaps.append(
                            NarrativeGap(
                                gap_type="thematic",
                                source_node=source_node,
                                target_node=target_node,
                                description=f"Foreshadowing in '{source_node.description if source_node else source}' never pays off",
                                severity=3,
                                suggested_bridges=[
                                    "REVELATION - pay off the foreshadowing",
                                    "CONSEQUENCE - show result of foreshadowed element",
                                ],
                                confidence=0.8,
                            )
                        )

        return gaps


class CharacterGelAnalyzer:
    """
    Analyzes how characters should interact and "gel" together.

    Uses concepts from chain_reflow's strategy determination to suggest
    how orthogonal character arcs can be linked.
    """

    def __init__(self, dag: NarrativeDAG):
        self.dag = dag
        self.characters = self._extract_characters()

    def _extract_characters(self) -> dict[str, list[PlotNode]]:
        """Extract character presence information."""
        chars: dict[str, list[PlotNode]] = {}
        for node in self.dag._nodes.values():
            if node.character:
                if node.character not in chars:
                    chars[node.character] = []
                chars[node.character].append(node)
        return chars

    def analyze_pair(self, char_a: str, char_b: str) -> Optional[CharacterGel]:
        """Analyze how two characters should relate."""
        if char_a not in self.characters or char_b not in self.characters:
            return None

        nodes_a = self.characters[char_a]
        nodes_b = self.characters[char_b]

        # Calculate orthogonality (how different their arcs are)
        orthogonality = self._calculate_orthogonality(nodes_a, nodes_b)

        # Determine relationship type based on arc characteristics
        relationship = self._suggest_relationship(nodes_a, nodes_b, orthogonality)

        # Find scenes that connect them
        connection_scenes = self._find_connection_scenes(char_a, char_b)

        # Calculate connection strength
        connection_strength = len(connection_scenes) / max(len(nodes_a), len(nodes_b), 1)

        # Suggest scenes to establish relationship
        suggestions = self._suggest_connection_scenes(
            char_a, char_b, nodes_a, nodes_b, relationship
        )

        return CharacterGel(
            character_a=char_a,
            character_b=char_b,
            suggested_relationship=relationship,
            connection_strength=connection_strength,
            suggested_scenes=suggestions,
            thematic_tension=self._identify_tension(nodes_a, nodes_b, relationship),
        )

    def _calculate_orthogonality(
        self, nodes_a: list[PlotNode], nodes_b: list[PlotNode]
    ) -> float:
        """
        Calculate how orthogonal (different) two character arcs are.
        0 = identical arc patterns, 1 = completely different
        """
        # Compare node type distributions
        types_a = [n.node_type for n in nodes_a]
        types_b = [n.node_type for n in nodes_b]

        # Compare chapter overlap
        chapters_a = set(n.chapter for n in nodes_a if n.chapter)
        chapters_b = set(n.chapter for n in nodes_b if n.chapter)

        chapter_overlap = (
            len(chapters_a & chapters_b) / len(chapters_a | chapters_b)
            if chapters_a | chapters_b
            else 0
        )

        # Compare emotional valence patterns
        avg_valence_a = (
            sum(n.emotional_valence for n in nodes_a) / len(nodes_a) if nodes_a else 0
        )
        avg_valence_b = (
            sum(n.emotional_valence for n in nodes_b) / len(nodes_b) if nodes_b else 0
        )
        valence_diff = abs(avg_valence_a - avg_valence_b)

        # Combine factors
        orthogonality = (1 - chapter_overlap) * 0.5 + valence_diff * 0.5
        return min(1.0, orthogonality)

    def _suggest_relationship(
        self, nodes_a: list[PlotNode], nodes_b: list[PlotNode], orthogonality: float
    ) -> str:
        """Suggest relationship type based on arc analysis."""
        # Compare emotional arcs
        avg_valence_a = (
            sum(n.emotional_valence for n in nodes_a) / len(nodes_a) if nodes_a else 0
        )
        avg_valence_b = (
            sum(n.emotional_valence for n in nodes_b) / len(nodes_b) if nodes_b else 0
        )

        # Compare stakes levels
        avg_stakes_a = (
            sum(n.stakes_level for n in nodes_a) / len(nodes_a) if nodes_a else 0
        )
        avg_stakes_b = (
            sum(n.stakes_level for n in nodes_b) / len(nodes_b) if nodes_b else 0
        )

        # High orthogonality with opposite valences = antagonist relationship
        if orthogonality > 0.7 and (avg_valence_a * avg_valence_b < 0):
            return "protagonist-antagonist"

        # High orthogonality with similar valences = parallel journeys
        if orthogonality > 0.7:
            return "parallel-protagonists"

        # Low orthogonality with high shared stakes = allies
        if orthogonality < 0.3 and max(avg_stakes_a, avg_stakes_b) > 5:
            return "allies"

        # Medium orthogonality = rivals or frenemies
        if 0.3 <= orthogonality <= 0.7:
            if avg_valence_a * avg_valence_b > 0:
                return "rivals"
            else:
                return "frenemies"

        return "connected-strangers"

    def _find_connection_scenes(self, char_a: str, char_b: str) -> list[PlotNode]:
        """Find existing scenes where both characters appear."""
        connections = []
        chapters_a = {n.chapter: n for n in self.characters.get(char_a, []) if n.chapter}
        chapters_b = {n.chapter for n in self.characters.get(char_b, []) if n.chapter}

        for chapter, node in chapters_a.items():
            if chapter in chapters_b:
                connections.append(node)

        return connections

    def _suggest_connection_scenes(
        self,
        char_a: str,
        char_b: str,
        nodes_a: list[PlotNode],
        nodes_b: list[PlotNode],
        relationship: str,
    ) -> list[str]:
        """Suggest scenes that would establish the character relationship."""
        suggestions = []

        if relationship == "protagonist-antagonist":
            suggestions.extend(
                [
                    f"Early confrontation where {char_a} and {char_b} establish opposing goals",
                    f"Scene showing {char_b}'s motivation that makes them sympathetic",
                    f"Moment where {char_a} and {char_b} are forced to cooperate briefly",
                    f"Climactic confrontation between {char_a} and {char_b}",
                ]
            )
        elif relationship == "allies":
            suggestions.extend(
                [
                    f"Scene where {char_a} and {char_b} discover shared enemy/goal",
                    f"Trust-building moment under pressure",
                    f"Scene where one saves the other",
                    f"Planning scene where they combine strengths",
                ]
            )
        elif relationship == "rivals":
            suggestions.extend(
                [
                    f"Competition scene between {char_a} and {char_b}",
                    f"Scene showing both want the same thing",
                    f"Moment of grudging respect",
                    f"Scene where rivalry drives both to grow",
                ]
            )
        elif relationship == "parallel-protagonists":
            suggestions.extend(
                [
                    f"Cross-cutting scenes showing parallel challenges",
                    f"Moment where their paths almost cross",
                    f"Scene where one's action unknowingly affects the other",
                    f"Eventual meeting that recontextualizes prior events",
                ]
            )
        else:  # frenemies or connected-strangers
            suggestions.extend(
                [
                    f"Ambiguous scene where allegiances are unclear",
                    f"Scene showing shifting dynamics between {char_a} and {char_b}",
                    f"Moment of unexpected alliance",
                ]
            )

        return suggestions

    def _identify_tension(
        self, nodes_a: list[PlotNode], nodes_b: list[PlotNode], relationship: str
    ) -> str:
        """Identify the thematic tension driving character dynamics."""
        tensions = {
            "protagonist-antagonist": "Order vs. Chaos / Good vs. Evil / Freedom vs. Control",
            "allies": "Trust vs. Self-reliance / Individual vs. Community",
            "rivals": "Pride vs. Humility / Competition vs. Cooperation",
            "parallel-protagonists": "Different paths to same truth / Nature vs. Nurture",
            "frenemies": "Loyalty vs. Self-interest / Past vs. Present",
            "connected-strangers": "Fate vs. Choice / Isolation vs. Connection",
        }
        return tensions.get(relationship, "Unknown tension")


class SpinoffGenerator:
    """
    Generates potential spinoff storylines from a main narrative.

    Uses concepts from chain_reflow's linking strategies to identify
    divergence points and extend them into new narratives.
    """

    def __init__(self, dag: NarrativeDAG):
        self.dag = dag

    def find_spinoff_seeds(self) -> list[SpinoffSeed]:
        """Identify potential spinoff points in the narrative."""
        seeds = []

        for node in self.dag._nodes.values():
            # Decision points with high stakes are natural spinoff points
            if node.node_type == NodeType.DECISION and node.stakes_level >= 6:
                seeds.append(
                    SpinoffSeed(
                        origin_node=node,
                        spinoff_theme=f"What if a different choice was made?",
                        divergence_point=f"Alternative outcome from: {node.description}",
                        potential_length=self._estimate_length(node),
                        key_elements=[
                            "Explore the road not taken",
                            "Same characters, different trajectory",
                            "Thematic parallel to main story",
                        ],
                    )
                )

            # Interesting secondary characters can carry spinoffs
            if (
                node.character
                and node.character not in self._get_main_characters()
                and node.node_type == NodeType.SETUP
            ):
                seeds.append(
                    SpinoffSeed(
                        origin_node=node,
                        spinoff_theme=f"Origin story for {node.character}",
                        divergence_point=f"Background of: {node.description}",
                        potential_length="novella",
                        key_elements=[
                            f"Deep dive into {node.character}'s backstory",
                            "Events before main narrative",
                            "Explain motivations and history",
                        ],
                    )
                )

            # Revelations often hint at larger stories
            if node.node_type == NodeType.REVELATION and node.is_twist:
                seeds.append(
                    SpinoffSeed(
                        origin_node=node,
                        spinoff_theme="Expanded world mystery",
                        divergence_point=f"Deeper exploration of: {node.description}",
                        potential_length="novel",
                        key_elements=[
                            "Expand on the revelation's implications",
                            "New protagonist investigating same mystery",
                            "Connect to broader world-building",
                        ],
                    )
                )

            # Unresolved subplots
            if node.subplot and node.subplot != "Main":
                descendants = self.dag.get_consequences(node.id)
                has_resolution = any(
                    self.dag.get_node(d)
                    and self.dag.get_node(d).node_type == NodeType.RESOLUTION
                    for d in descendants
                )
                if not has_resolution:
                    seeds.append(
                        SpinoffSeed(
                            origin_node=node,
                            spinoff_theme=f"Completing the {node.subplot} storyline",
                            divergence_point=f"Unresolved thread: {node.description}",
                            potential_length="short story",
                            key_elements=[
                                f"Resolve the {node.subplot} subplot fully",
                                "Standalone but connected narrative",
                                "Satisfies readers wanting more",
                            ],
                        )
                    )

        return seeds

    def _get_main_characters(self) -> set[str]:
        """Identify the main characters by frequency."""
        char_counts: dict[str, int] = {}
        for node in self.dag._nodes.values():
            if node.character:
                char_counts[node.character] = char_counts.get(node.character, 0) + 1

        if not char_counts:
            return set()

        # Top 2-3 characters by frequency are "main"
        sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
        threshold = max(c for _, c in sorted_chars) * 0.5
        return {char for char, count in sorted_chars if count >= threshold}

    def _estimate_length(self, node: PlotNode) -> str:
        """Estimate appropriate spinoff length based on node significance."""
        descendants = len(self.dag.get_consequences(node.id))

        if descendants > 10:
            return "novel"
        elif descendants > 5:
            return "novella"
        else:
            return "short story"


class NarrativeMerger:
    """
    Merges multiple narrative fragments into a coherent whole.

    Based on chain_reflow's graph merging workflow, handles:
    - Combining partial plots
    - Integrating character arcs from different fragments
    - Creating intermediary scenes to bridge gaps
    """

    def __init__(self):
        self.fragments: list[NarrativeDAG] = []

    def add_fragment(self, fragment: NarrativeDAG) -> None:
        """Add a narrative fragment to be merged."""
        self.fragments.append(fragment)

    def determine_strategy(self) -> LinkingStrategy:
        """
        Determine the best strategy for merging fragments.

        Based on chain_reflow's strategy determination workflow.
        """
        if len(self.fragments) <= 1:
            return LinkingStrategy.PAIRWISE

        # Check for hierarchical relationships
        has_hierarchy = self._detect_hierarchy()
        if has_hierarchy:
            return LinkingStrategy.HIERARCHICAL

        # Check orthogonality between fragments
        max_orthogonality = self._calculate_max_orthogonality()

        if max_orthogonality > 0.8:
            return LinkingStrategy.WITH_INTERMEDIARIES

        if len(self.fragments) <= 3:
            return LinkingStrategy.PAIRWISE

        if len(self.fragments) > 10:
            return LinkingStrategy.PHASED

        return LinkingStrategy.NETWORK

    def _detect_hierarchy(self) -> bool:
        """Check if fragments have parent-child relationships."""
        # Look for main plot vs subplots
        for frag in self.fragments:
            subplots = set(n.subplot for n in frag._nodes.values() if n.subplot)
            if "Main" in subplots and len(subplots) > 1:
                return True
        return False

    def _calculate_max_orthogonality(self) -> float:
        """Calculate maximum orthogonality between any two fragments."""
        max_orth = 0.0

        for i, frag1 in enumerate(self.fragments):
            for frag2 in self.fragments[i + 1:]:
                orth = self._fragment_orthogonality(frag1, frag2)
                max_orth = max(max_orth, orth)

        return max_orth

    def _fragment_orthogonality(self, frag1: NarrativeDAG, frag2: NarrativeDAG) -> float:
        """Calculate orthogonality between two fragments."""
        # Compare character overlap
        chars1 = set(n.character for n in frag1._nodes.values() if n.character)
        chars2 = set(n.character for n in frag2._nodes.values() if n.character)

        char_overlap = (
            len(chars1 & chars2) / len(chars1 | chars2) if chars1 | chars2 else 0
        )

        # Compare chapter overlap
        chapters1 = set(n.chapter for n in frag1._nodes.values() if n.chapter)
        chapters2 = set(n.chapter for n in frag2._nodes.values() if n.chapter)

        chapter_overlap = (
            len(chapters1 & chapters2) / len(chapters1 | chapters2)
            if chapters1 | chapters2
            else 0
        )

        # Lower overlap = higher orthogonality
        return 1 - (char_overlap * 0.6 + chapter_overlap * 0.4)

    def merge(self, title: str = "Merged Narrative") -> NarrativeDAG:
        """
        Merge all fragments into a single narrative DAG.

        Returns a new NarrativeDAG containing all elements properly connected.
        """
        merged = NarrativeDAG(title=title)
        strategy = self.determine_strategy()

        # Collect all nodes with unique IDs
        node_mapping: dict[str, str] = {}  # old_id -> new_id
        for i, frag in enumerate(self.fragments):
            prefix = f"frag{i}_"
            for node in frag._nodes.values():
                new_id = f"{prefix}{node.id}"
                node_mapping[f"{i}:{node.id}"] = new_id

                new_node = PlotNode(
                    id=new_id,
                    node_type=node.node_type,
                    description=node.description,
                    chapter=node.chapter,
                    character=node.character,
                    subplot=node.subplot or f"Fragment{i}",
                    emotional_valence=node.emotional_valence,
                    stakes_level=node.stakes_level,
                    is_twist=node.is_twist,
                )
                merged.add_node(new_node)

        # Collect all edges
        for i, frag in enumerate(self.fragments):
            prefix = f"frag{i}_"
            for source, target, data in frag.graph.edges(data=True):
                new_source = f"{prefix}{source}"
                new_target = f"{prefix}{target}"
                edge_type = EdgeType[data.get("edge_type", "CAUSES")]
                merged.add_edge(new_source, new_target, edge_type)

        # Create bridge connections based on strategy
        if strategy == LinkingStrategy.WITH_INTERMEDIARIES:
            self._add_intermediary_scenes(merged)
        else:
            self._add_direct_connections(merged)

        return merged

    def _add_intermediary_scenes(self, merged: NarrativeDAG) -> None:
        """Add intermediary scenes to bridge orthogonal fragments."""
        # Find entry and exit points for each fragment
        for i in range(len(self.fragments) - 1):
            # Get last node of current fragment
            frag_nodes = [
                n for n in merged._nodes.values() if n.subplot == f"Fragment{i}"
            ]
            if not frag_nodes:
                continue

            last_node = max(frag_nodes, key=lambda n: n.chapter or 0)

            # Get first node of next fragment
            next_frag_nodes = [
                n for n in merged._nodes.values() if n.subplot == f"Fragment{i + 1}"
            ]
            if not next_frag_nodes:
                continue

            first_node = min(next_frag_nodes, key=lambda n: n.chapter or 0)

            # Create bridge scene
            bridge_id = f"bridge_{i}_{i + 1}"
            bridge_chapter = (
                ((last_node.chapter or 0) + (first_node.chapter or 0)) // 2
                if last_node.chapter and first_node.chapter
                else None
            )

            bridge = PlotNode(
                id=bridge_id,
                node_type=NodeType.CONSEQUENCE,
                description=f"Bridge: Connecting {last_node.subplot} to {first_node.subplot}",
                chapter=bridge_chapter,
                subplot="Bridge",
                stakes_level=(last_node.stakes_level + first_node.stakes_level) // 2,
            )
            merged.add_node(bridge)
            merged.add_edge(last_node.id, bridge_id, EdgeType.ENABLES)
            merged.add_edge(bridge_id, first_node.id, EdgeType.ENABLES)

    def _add_direct_connections(self, merged: NarrativeDAG) -> None:
        """Add direct connections between fragments where characters overlap."""
        # Find shared characters
        char_appearances: dict[str, list[str]] = {}  # char -> [node_ids]
        for node in merged._nodes.values():
            if node.character:
                if node.character not in char_appearances:
                    char_appearances[node.character] = []
                char_appearances[node.character].append(node.id)

        # Create connections for shared characters across fragments
        for char, node_ids in char_appearances.items():
            nodes = [(nid, merged.get_node(nid)) for nid in node_ids]
            nodes = [(nid, n) for nid, n in nodes if n]
            nodes.sort(key=lambda x: x[1].chapter or 0)

            for i in range(len(nodes) - 1):
                current_id, current = nodes[i]
                next_id, next_node = nodes[i + 1]

                # Only connect if in different subplots
                if current.subplot != next_node.subplot:
                    # Check if edge already exists
                    if not merged.graph.has_edge(current_id, next_id):
                        merged.add_edge(current_id, next_id, EdgeType.ENABLES)


def suggest_gap_closure(gap: NarrativeGap) -> PlotNode:
    """
    Suggest a node to close a detected gap.

    Returns a new PlotNode that could bridge the gap.
    """
    # Determine appropriate node type
    if gap.gap_type == "causal":
        node_type = NodeType.CONSEQUENCE
    elif gap.gap_type == "character":
        node_type = NodeType.SETUP if gap.source_node is None else NodeType.RESOLUTION
    elif gap.gap_type == "temporal":
        node_type = NodeType.COMPLICATION
    else:  # thematic
        node_type = NodeType.REVELATION

    # Create bridge node
    source_chapter = gap.source_node.chapter if gap.source_node else 1
    target_chapter = gap.target_node.chapter if gap.target_node else source_chapter + 1

    bridge_chapter = (source_chapter + target_chapter) // 2

    # Get character from surrounding nodes
    character = None
    if gap.source_node and gap.source_node.character:
        character = gap.source_node.character
    elif gap.target_node and gap.target_node.character:
        character = gap.target_node.character

    return PlotNode(
        id=f"bridge_gap_{id(gap)}",
        node_type=node_type,
        description=f"[SUGGESTED] Bridge: {gap.suggested_bridges[0] if gap.suggested_bridges else 'Fill gap'}",
        chapter=bridge_chapter,
        character=character,
        stakes_level=(
            (gap.source_node.stakes_level if gap.source_node else 3)
            + (gap.target_node.stakes_level if gap.target_node else 3)
        )
        // 2,
    )
