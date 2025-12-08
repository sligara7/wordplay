"""
Genre Templates - Pre-built DAG structures for common narrative patterns.

Each template provides a skeleton structure that can be populated
with specific plot details while maintaining genre-appropriate pacing
and structural expectations.
"""

from dataclasses import dataclass, field
from typing import Callable
from .narrative_dag import NarrativeDAG, PlotNode, NodeType, EdgeType


@dataclass
class GenreTemplate:
    """A template for generating genre-specific narrative DAGs."""

    name: str
    description: str
    typical_chapter_count: tuple[int, int]  # (min, max)
    key_structural_features: list[str]
    required_node_types: list[NodeType]
    typical_subplot_count: tuple[int, int]
    build_skeleton: Callable[[NarrativeDAG], None]  # Function to build base structure

    def create_skeleton(self, title: str = "Untitled", author: str = "Unknown") -> NarrativeDAG:
        """Create a new narrative DAG with the genre's skeletal structure."""
        dag = NarrativeDAG(title=title, author=author)
        self.build_skeleton(dag)
        return dag


def _build_mystery_skeleton(dag: NarrativeDAG) -> None:
    """Build the skeleton for a mystery novel."""
    # Act 1: Setup and Crime
    dag.add_node(PlotNode(
        id="world_setup", node_type=NodeType.SETUP,
        description="Establish setting and introduce detective/protagonist",
        chapter=1, stakes_level=1
    ))
    dag.add_node(PlotNode(
        id="crime_occurs", node_type=NodeType.CATALYST,
        description="The central crime/mystery is introduced",
        chapter=2, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="detective_engaged", node_type=NodeType.DECISION,
        description="Protagonist decides to investigate",
        chapter=2, stakes_level=3
    ))

    # Act 2: Investigation
    dag.add_node(PlotNode(
        id="clue_1", node_type=NodeType.REVELATION,
        description="First significant clue discovered",
        chapter=4, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="suspect_1", node_type=NodeType.SETUP,
        description="First suspect introduced",
        chapter=5, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="red_herring_1", node_type=NodeType.COMPLICATION,
        description="Misleading clue or false lead",
        chapter=6, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="clue_2", node_type=NodeType.REVELATION,
        description="Second significant clue",
        chapter=8, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="suspect_2", node_type=NodeType.SETUP,
        description="Second suspect introduced or first cleared",
        chapter=9, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="midpoint_revelation", node_type=NodeType.REVELATION,
        description="Major revelation that shifts the investigation",
        chapter=12, stakes_level=6, is_twist=True
    ))

    # Act 3: Escalation
    dag.add_node(PlotNode(
        id="stakes_raise", node_type=NodeType.COMPLICATION,
        description="Second crime or threat to protagonist",
        chapter=15, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="clue_3", node_type=NodeType.REVELATION,
        description="Crucial clue that points to truth",
        chapter=17, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="false_solution", node_type=NodeType.DECISION,
        description="Protagonist thinks they've solved it (wrong)",
        chapter=19, stakes_level=7
    ))

    # Act 4: Resolution
    dag.add_node(PlotNode(
        id="true_revelation", node_type=NodeType.REVELATION,
        description="The real solution is discovered",
        chapter=22, stakes_level=9, is_twist=True
    ))
    dag.add_node(PlotNode(
        id="confrontation", node_type=NodeType.CONFRONTATION,
        description="Protagonist confronts the true culprit",
        chapter=23, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="resolution", node_type=NodeType.RESOLUTION,
        description="Justice served, loose ends tied",
        chapter=24, stakes_level=3
    ))

    # Build the edges
    dag.add_edge("world_setup", "crime_occurs", EdgeType.ENABLES)
    dag.add_edge("crime_occurs", "detective_engaged", EdgeType.CAUSES)
    dag.add_edge("detective_engaged", "clue_1", EdgeType.ENABLES)
    dag.add_edge("clue_1", "suspect_1", EdgeType.REVEALS)
    dag.add_edge("suspect_1", "red_herring_1", EdgeType.ENABLES)
    dag.add_edge("clue_1", "clue_2", EdgeType.ENABLES)
    dag.add_edge("clue_2", "suspect_2", EdgeType.REVEALS)
    dag.add_edge("red_herring_1", "midpoint_revelation", EdgeType.CONTRASTS)
    dag.add_edge("suspect_2", "midpoint_revelation", EdgeType.ENABLES)
    dag.add_edge("midpoint_revelation", "stakes_raise", EdgeType.CAUSES)
    dag.add_edge("stakes_raise", "clue_3", EdgeType.ENABLES)
    dag.add_edge("clue_3", "false_solution", EdgeType.ENABLES)
    dag.add_edge("false_solution", "true_revelation", EdgeType.CONTRASTS)
    dag.add_edge("clue_1", "true_revelation", EdgeType.FORESHADOWS)
    dag.add_edge("clue_2", "true_revelation", EdgeType.FORESHADOWS)
    dag.add_edge("clue_3", "true_revelation", EdgeType.REVEALS)
    dag.add_edge("true_revelation", "confrontation", EdgeType.CAUSES)
    dag.add_edge("confrontation", "resolution", EdgeType.RESOLVES)
    dag.add_edge("crime_occurs", "resolution", EdgeType.RESOLVES)


def _build_thriller_skeleton(dag: NarrativeDAG) -> None:
    """Build the skeleton for a thriller novel."""
    # Act 1: Ordinary World Shattered
    dag.add_node(PlotNode(
        id="ordinary_world", node_type=NodeType.SETUP,
        description="Protagonist's normal life established",
        chapter=1, stakes_level=1
    ))
    dag.add_node(PlotNode(
        id="inciting_threat", node_type=NodeType.CATALYST,
        description="Sudden threat disrupts protagonist's world",
        chapter=2, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="clock_starts", node_type=NodeType.SETUP,
        description="Time pressure established",
        chapter=3, stakes_level=6
    ))

    # Act 2: Chase and Escalation
    dag.add_node(PlotNode(
        id="first_escape", node_type=NodeType.DECISION,
        description="Protagonist narrowly escapes first danger",
        chapter=5, stakes_level=6
    ))
    dag.add_node(PlotNode(
        id="stakes_rise_1", node_type=NodeType.COMPLICATION,
        description="Threat expands - more at risk",
        chapter=7, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="ally_introduced", node_type=NodeType.SETUP,
        description="Potential ally appears",
        chapter=8, stakes_level=6
    ))
    dag.add_node(PlotNode(
        id="caught_moment", node_type=NodeType.COMPLICATION,
        description="Protagonist is caught/cornered",
        chapter=10, stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="second_escape", node_type=NodeType.DECISION,
        description="Desperate escape with cost",
        chapter=11, stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="midpoint_twist", node_type=NodeType.REVELATION,
        description="Major revelation changes everything",
        chapter=13, stakes_level=8, is_twist=True
    ))

    # Act 3: Desperate Measures
    dag.add_node(PlotNode(
        id="stakes_rise_2", node_type=NodeType.COMPLICATION,
        description="Personal cost - loved one threatened",
        chapter=16, stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="ally_betrayal_or_death", node_type=NodeType.CONSEQUENCE,
        description="Ally betrays or is lost",
        chapter=18, stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="clock_final", node_type=NodeType.CLIFFHANGER,
        description="Time almost up",
        chapter=20, stakes_level=10
    ))

    # Act 4: Final Confrontation
    dag.add_node(PlotNode(
        id="final_gambit", node_type=NodeType.DECISION,
        description="Protagonist's desperate final plan",
        chapter=22, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="sacrifice", node_type=NodeType.CONSEQUENCE,
        description="Something must be given up",
        chapter=23, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="climax", node_type=NodeType.CONFRONTATION,
        description="Final confrontation with antagonist",
        chapter=24, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="resolution", node_type=NodeType.RESOLUTION,
        description="Threat neutralized, cost counted",
        chapter=25, stakes_level=4
    ))

    # Build edges - everything escalates
    dag.add_edge("ordinary_world", "inciting_threat", EdgeType.CONTRASTS)
    dag.add_edge("inciting_threat", "clock_starts", EdgeType.CAUSES)
    dag.add_edge("inciting_threat", "first_escape", EdgeType.CAUSES)
    dag.add_edge("first_escape", "stakes_rise_1", EdgeType.CAUSES)
    dag.add_edge("clock_starts", "stakes_rise_1", EdgeType.ENABLES)
    dag.add_edge("stakes_rise_1", "ally_introduced", EdgeType.ENABLES)
    dag.add_edge("stakes_rise_1", "caught_moment", EdgeType.CAUSES)
    dag.add_edge("caught_moment", "second_escape", EdgeType.CAUSES)
    dag.add_edge("ally_introduced", "second_escape", EdgeType.ENABLES)
    dag.add_edge("second_escape", "midpoint_twist", EdgeType.ENABLES)
    dag.add_edge("midpoint_twist", "stakes_rise_2", EdgeType.CAUSES)
    dag.add_edge("ally_introduced", "ally_betrayal_or_death", EdgeType.ENABLES)
    dag.add_edge("stakes_rise_2", "ally_betrayal_or_death", EdgeType.CAUSES)
    dag.add_edge("ally_betrayal_or_death", "clock_final", EdgeType.CAUSES)
    dag.add_edge("clock_final", "final_gambit", EdgeType.CAUSES)
    dag.add_edge("final_gambit", "sacrifice", EdgeType.REQUIRES)
    dag.add_edge("sacrifice", "climax", EdgeType.ENABLES)
    dag.add_edge("climax", "resolution", EdgeType.RESOLVES)
    dag.add_edge("inciting_threat", "resolution", EdgeType.RESOLVES)


def _build_romance_skeleton(dag: NarrativeDAG) -> None:
    """Build the skeleton for a romance novel."""
    # Act 1: Meeting
    dag.add_node(PlotNode(
        id="char_a_intro", node_type=NodeType.SETUP,
        description="Character A's world and desires established",
        chapter=1, character="A", stakes_level=2
    ))
    dag.add_node(PlotNode(
        id="char_b_intro", node_type=NodeType.SETUP,
        description="Character B's world and desires established",
        chapter=2, character="B", stakes_level=2
    ))
    dag.add_node(PlotNode(
        id="meet_cute", node_type=NodeType.CATALYST,
        description="A and B meet in memorable circumstances",
        chapter=3, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="first_conflict", node_type=NodeType.COMPLICATION,
        description="Initial friction or misunderstanding",
        chapter=4, stakes_level=4
    ))

    # Act 2: Growing Connection
    dag.add_node(PlotNode(
        id="forced_proximity", node_type=NodeType.SETUP,
        description="Circumstances force A and B together",
        chapter=6, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="a_vulnerability", node_type=NodeType.REVELATION,
        description="A reveals something vulnerable",
        chapter=8, character="A", stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="b_vulnerability", node_type=NodeType.REVELATION,
        description="B reveals something vulnerable",
        chapter=9, character="B", stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="growing_feelings", node_type=NodeType.CONSEQUENCE,
        description="Both begin to fall for each other",
        chapter=11, stakes_level=6
    ))
    dag.add_node(PlotNode(
        id="first_kiss", node_type=NodeType.DECISION,
        description="First romantic milestone",
        chapter=13, stakes_level=7
    ))

    # Act 3: Complication
    dag.add_node(PlotNode(
        id="external_obstacle", node_type=NodeType.COMPLICATION,
        description="External force threatens relationship",
        chapter=15, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="misunderstanding", node_type=NodeType.COMPLICATION,
        description="Major misunderstanding or secret revealed",
        chapter=17, stakes_level=8, is_twist=True
    ))
    dag.add_node(PlotNode(
        id="breakup", node_type=NodeType.CONSEQUENCE,
        description="A and B separate",
        chapter=19, stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="dark_moment", node_type=NodeType.CONSEQUENCE,
        description="Both realize what they've lost",
        chapter=20, stakes_level=9
    ))

    # Act 4: Resolution
    dag.add_node(PlotNode(
        id="a_growth", node_type=NodeType.DECISION,
        description="A confronts their flaw/fear",
        chapter=22, character="A", stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="b_growth", node_type=NodeType.DECISION,
        description="B confronts their flaw/fear",
        chapter=22, character="B", stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="grand_gesture", node_type=NodeType.DECISION,
        description="One makes grand romantic gesture",
        chapter=24, stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="reunion", node_type=NodeType.RESOLUTION,
        description="A and B reunite",
        chapter=25, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="happy_ending", node_type=NodeType.RESOLUTION,
        description="Happily ever after established",
        chapter=26, stakes_level=3
    ))

    # Build edges - the oscillating connection
    dag.add_edge("char_a_intro", "meet_cute", EdgeType.ENABLES)
    dag.add_edge("char_b_intro", "meet_cute", EdgeType.ENABLES)
    dag.add_edge("meet_cute", "first_conflict", EdgeType.CAUSES)
    dag.add_edge("first_conflict", "forced_proximity", EdgeType.ENABLES)
    dag.add_edge("forced_proximity", "a_vulnerability", EdgeType.ENABLES)
    dag.add_edge("forced_proximity", "b_vulnerability", EdgeType.ENABLES)
    dag.add_edge("a_vulnerability", "growing_feelings", EdgeType.CAUSES)
    dag.add_edge("b_vulnerability", "growing_feelings", EdgeType.CAUSES)
    dag.add_edge("growing_feelings", "first_kiss", EdgeType.ENABLES)
    dag.add_edge("first_kiss", "external_obstacle", EdgeType.ENABLES)
    dag.add_edge("external_obstacle", "misunderstanding", EdgeType.CAUSES)
    dag.add_edge("misunderstanding", "breakup", EdgeType.CAUSES)
    dag.add_edge("breakup", "dark_moment", EdgeType.CAUSES)
    dag.add_edge("dark_moment", "a_growth", EdgeType.CAUSES)
    dag.add_edge("dark_moment", "b_growth", EdgeType.CAUSES)
    dag.add_edge("a_growth", "grand_gesture", EdgeType.ENABLES)
    dag.add_edge("b_growth", "grand_gesture", EdgeType.ENABLES)
    dag.add_edge("grand_gesture", "reunion", EdgeType.CAUSES)
    dag.add_edge("reunion", "happy_ending", EdgeType.CAUSES)
    dag.add_edge("first_conflict", "happy_ending", EdgeType.RESOLVES)
    dag.add_edge("misunderstanding", "reunion", EdgeType.RESOLVES)


def _build_epic_fantasy_skeleton(dag: NarrativeDAG) -> None:
    """Build the skeleton for an epic fantasy novel."""
    # Act 1: The Ordinary World
    dag.add_node(PlotNode(
        id="world_building", node_type=NodeType.SETUP,
        description="Fantasy world established with its rules",
        chapter=1, stakes_level=1
    ))
    dag.add_node(PlotNode(
        id="hero_ordinary", node_type=NodeType.SETUP,
        description="Hero in their ordinary circumstances",
        chapter=1, character="Hero", subplot="Main", stakes_level=1
    ))
    dag.add_node(PlotNode(
        id="mentor_intro", node_type=NodeType.SETUP,
        description="Mentor figure introduced",
        chapter=2, character="Mentor", subplot="Main", stakes_level=2
    ))
    dag.add_node(PlotNode(
        id="dark_force_hint", node_type=NodeType.FORESHADOWING,
        description="First hints of the antagonist/dark force",
        chapter=2, subplot="Villain", stakes_level=3
    ))
    dag.add_node(PlotNode(
        id="call_to_adventure", node_type=NodeType.CATALYST,
        description="Hero's world disrupted, adventure calls",
        chapter=4, character="Hero", subplot="Main", stakes_level=5
    ))

    # Act 2: Crossing the Threshold
    dag.add_node(PlotNode(
        id="refusal_then_acceptance", node_type=NodeType.DECISION,
        description="Hero initially refuses, then accepts call",
        chapter=5, character="Hero", subplot="Main", stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="companions_gather", node_type=NodeType.SETUP,
        description="Hero gathers companions for the journey",
        chapter=7, subplot="Main", stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="training_begins", node_type=NodeType.SETUP,
        description="Hero begins learning/training",
        chapter=8, character="Hero", subplot="Main", stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="first_trial", node_type=NodeType.COMPLICATION,
        description="First major challenge tests the hero",
        chapter=10, character="Hero", subplot="Main", stakes_level=6
    ))
    dag.add_node(PlotNode(
        id="villain_moves", node_type=NodeType.COMPLICATION,
        description="Antagonist makes significant move",
        chapter=11, subplot="Villain", stakes_level=6
    ))

    # Midpoint: The Ordeal
    dag.add_node(PlotNode(
        id="mentor_sacrifice", node_type=NodeType.CONSEQUENCE,
        description="Mentor dies or is lost",
        chapter=15, character="Mentor", subplot="Main", stakes_level=8, is_twist=True
    ))
    dag.add_node(PlotNode(
        id="hero_crisis", node_type=NodeType.CONSEQUENCE,
        description="Hero faces dark night of the soul",
        chapter=16, character="Hero", subplot="Main", stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="hidden_truth", node_type=NodeType.REVELATION,
        description="Major revelation about hero's nature/destiny",
        chapter=17, character="Hero", subplot="Main", stakes_level=8, is_twist=True
    ))

    # Act 3: The Road Back
    dag.add_node(PlotNode(
        id="hero_transforms", node_type=NodeType.DECISION,
        description="Hero accepts their destiny fully",
        chapter=20, character="Hero", subplot="Main", stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="allies_rally", node_type=NodeType.SETUP,
        description="Forces of good unite",
        chapter=22, subplot="Main", stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="villain_power", node_type=NodeType.COMPLICATION,
        description="Villain at height of power",
        chapter=23, subplot="Villain", stakes_level=9
    ))

    # Act 4: The Climax
    dag.add_node(PlotNode(
        id="final_battle", node_type=NodeType.CONFRONTATION,
        description="Epic final confrontation",
        chapter=27, stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="sacrifice_moment", node_type=NodeType.DECISION,
        description="Hero makes ultimate sacrifice/choice",
        chapter=28, character="Hero", stakes_level=10
    ))
    dag.add_node(PlotNode(
        id="villain_defeated", node_type=NodeType.CONSEQUENCE,
        description="Antagonist is defeated",
        chapter=29, subplot="Villain", stakes_level=9
    ))
    dag.add_node(PlotNode(
        id="new_world", node_type=NodeType.RESOLUTION,
        description="New world order established",
        chapter=30, stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="hero_return", node_type=NodeType.RESOLUTION,
        description="Hero returns transformed",
        chapter=30, character="Hero", subplot="Main", stakes_level=3
    ))

    # Build edges
    dag.add_edge("world_building", "hero_ordinary", EdgeType.ENABLES)
    dag.add_edge("hero_ordinary", "mentor_intro", EdgeType.ENABLES)
    dag.add_edge("world_building", "dark_force_hint", EdgeType.ENABLES)
    dag.add_edge("dark_force_hint", "call_to_adventure", EdgeType.CAUSES)
    dag.add_edge("mentor_intro", "call_to_adventure", EdgeType.ENABLES)
    dag.add_edge("call_to_adventure", "refusal_then_acceptance", EdgeType.CAUSES)
    dag.add_edge("refusal_then_acceptance", "companions_gather", EdgeType.ENABLES)
    dag.add_edge("mentor_intro", "training_begins", EdgeType.ENABLES)
    dag.add_edge("refusal_then_acceptance", "training_begins", EdgeType.ENABLES)
    dag.add_edge("training_begins", "first_trial", EdgeType.ENABLES)
    dag.add_edge("dark_force_hint", "villain_moves", EdgeType.ENABLES)
    dag.add_edge("first_trial", "villain_moves", EdgeType.PARALLELS)
    dag.add_edge("villain_moves", "mentor_sacrifice", EdgeType.CAUSES)
    dag.add_edge("mentor_sacrifice", "hero_crisis", EdgeType.CAUSES)
    dag.add_edge("hero_crisis", "hidden_truth", EdgeType.ENABLES)
    dag.add_edge("hidden_truth", "hero_transforms", EdgeType.CAUSES)
    dag.add_edge("hero_transforms", "allies_rally", EdgeType.ENABLES)
    dag.add_edge("villain_moves", "villain_power", EdgeType.ENABLES)
    dag.add_edge("allies_rally", "final_battle", EdgeType.ENABLES)
    dag.add_edge("villain_power", "final_battle", EdgeType.ENABLES)
    dag.add_edge("final_battle", "sacrifice_moment", EdgeType.CAUSES)
    dag.add_edge("sacrifice_moment", "villain_defeated", EdgeType.CAUSES)
    dag.add_edge("villain_defeated", "new_world", EdgeType.CAUSES)
    dag.add_edge("new_world", "hero_return", EdgeType.ENABLES)
    dag.add_edge("hero_ordinary", "hero_return", EdgeType.CONTRASTS)
    dag.add_edge("dark_force_hint", "villain_defeated", EdgeType.RESOLVES)


def _build_literary_fiction_skeleton(dag: NarrativeDAG) -> None:
    """Build the skeleton for literary fiction (character-driven)."""
    # Non-linear structure with internal/external interplay
    dag.add_node(PlotNode(
        id="present_moment", node_type=NodeType.SETUP,
        description="Character at a crossroads in present",
        chapter=1, character="Protagonist", stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="memory_1", node_type=NodeType.FLASHBACK,
        description="Formative memory surfaces",
        chapter=2, character="Protagonist", stakes_level=3
    ))
    dag.add_node(PlotNode(
        id="external_catalyst", node_type=NodeType.CATALYST,
        description="External event forces engagement",
        chapter=3, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="relationship_tension", node_type=NodeType.COMPLICATION,
        description="Key relationship under strain",
        chapter=4, stakes_level=5
    ))
    dag.add_node(PlotNode(
        id="memory_2", node_type=NodeType.FLASHBACK,
        description="Deeper memory reveals pattern",
        chapter=6, character="Protagonist", stakes_level=4
    ))
    dag.add_node(PlotNode(
        id="internal_recognition", node_type=NodeType.REVELATION,
        description="Character begins to see themselves clearly",
        chapter=8, character="Protagonist", stakes_level=6
    ))
    dag.add_node(PlotNode(
        id="external_pressure", node_type=NodeType.COMPLICATION,
        description="External circumstances intensify",
        chapter=10, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="confrontation_other", node_type=NodeType.CONFRONTATION,
        description="Confrontation with key person",
        chapter=12, stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="memory_3", node_type=NodeType.FLASHBACK,
        description="Final piece of past clicks into place",
        chapter=14, character="Protagonist", stakes_level=6, is_twist=True
    ))
    dag.add_node(PlotNode(
        id="internal_shift", node_type=NodeType.DECISION,
        description="Internal transformation occurs",
        chapter=16, character="Protagonist", stakes_level=8
    ))
    dag.add_node(PlotNode(
        id="action_from_growth", node_type=NodeType.CONSEQUENCE,
        description="Character acts differently than before",
        chapter=18, character="Protagonist", stakes_level=7
    ))
    dag.add_node(PlotNode(
        id="ambiguous_resolution", node_type=NodeType.RESOLUTION,
        description="Open-ended but meaningful conclusion",
        chapter=20, stakes_level=5
    ))

    # Edges - internal and external intertwined
    dag.add_edge("present_moment", "memory_1", EdgeType.REVEALS)
    dag.add_edge("present_moment", "external_catalyst", EdgeType.ENABLES)
    dag.add_edge("external_catalyst", "relationship_tension", EdgeType.CAUSES)
    dag.add_edge("memory_1", "memory_2", EdgeType.REVEALS)
    dag.add_edge("relationship_tension", "memory_2", EdgeType.CAUSES)
    dag.add_edge("memory_2", "internal_recognition", EdgeType.REVEALS)
    dag.add_edge("internal_recognition", "external_pressure", EdgeType.PARALLELS)
    dag.add_edge("external_pressure", "confrontation_other", EdgeType.CAUSES)
    dag.add_edge("confrontation_other", "memory_3", EdgeType.REVEALS)
    dag.add_edge("memory_1", "memory_3", EdgeType.FORESHADOWS)
    dag.add_edge("memory_3", "internal_shift", EdgeType.CAUSES)
    dag.add_edge("internal_recognition", "internal_shift", EdgeType.ENABLES)
    dag.add_edge("internal_shift", "action_from_growth", EdgeType.CAUSES)
    dag.add_edge("action_from_growth", "ambiguous_resolution", EdgeType.CAUSES)
    dag.add_edge("present_moment", "ambiguous_resolution", EdgeType.CONTRASTS)


def _build_riddle_novel_skeleton(dag: NarrativeDAG) -> None:
    """
    Build the skeleton for a riddle-novel.

    The entire plot functions as a riddle for the reader to solve.
    Uses misdirection, hidden answers in plain sight, and a perspective
    shift that recontextualizes everything.
    """
    # ACT 1: THE FRAME (Chapters 1-6)
    # Establish what the reader THINKS the story is about

    dag.add_node(PlotNode(
        id="opening_question",
        node_type=NodeType.SETUP,
        description="Opening scene poses implicit question. Sets false frame",
        chapter=1,
        stakes_level=3,
    ))

    dag.add_node(PlotNode(
        id="frame_establishment",
        node_type=NodeType.SETUP,
        description="World/situation established. Reader forms assumptions",
        chapter=2,
        stakes_level=3,
    ))

    dag.add_node(PlotNode(
        id="protagonist_goal",
        node_type=NodeType.CATALYST,
        description="Protagonist's apparent goal introduced. Seems straightforward",
        chapter=3,
        character="Protagonist",
        stakes_level=4,
    ))

    dag.add_node(PlotNode(
        id="answer_planted_1",
        node_type=NodeType.FORESHADOWING,
        description="THE ANSWER appears in plain sight, disguised as ordinary detail",
        chapter=4,
        stakes_level=2,
    ))

    dag.add_node(PlotNode(
        id="decoy_clue_1",
        node_type=NodeType.COMPLICATION,
        description="First misdirection - points toward false answer",
        chapter=5,
        stakes_level=4,
    ))

    dag.add_node(PlotNode(
        id="supporting_cast",
        node_type=NodeType.SETUP,
        description="Characters introduced who seem to fit expected roles",
        chapter=6,
        stakes_level=3,
    ))

    # ACT 2A: DEEPENING THE FRAME (Chapters 7-12)
    # Make the false frame feel real while planting more hidden truth

    dag.add_node(PlotNode(
        id="false_progress",
        node_type=NodeType.CONSEQUENCE,
        description="Protagonist makes progress toward apparent goal",
        chapter=7,
        character="Protagonist",
        stakes_level=5,
    ))

    dag.add_node(PlotNode(
        id="decoy_clue_2",
        node_type=NodeType.COMPLICATION,
        description="Second misdirection - stronger false path",
        chapter=8,
        stakes_level=5,
    ))

    dag.add_node(PlotNode(
        id="answer_planted_2",
        node_type=NodeType.FORESHADOWING,
        description="More truth hidden in plain sight. Pattern if reader looks",
        chapter=9,
        stakes_level=3,
    ))

    dag.add_node(PlotNode(
        id="false_revelation",
        node_type=NodeType.REVELATION,
        description="'Revelation' that fits the false frame perfectly",
        chapter=10,
        stakes_level=6,
        is_twist=True,  # Feels like a twist but isn't the real one
    ))

    dag.add_node(PlotNode(
        id="decoy_climax",
        node_type=NodeType.CONFRONTATION,
        description="Confrontation that seems climactic but isn't",
        chapter=11,
        stakes_level=7,
    ))

    dag.add_node(PlotNode(
        id="hollow_victory",
        node_type=NodeType.CONSEQUENCE,
        description="'Victory' that feels wrong. Something doesn't fit",
        chapter=12,
        stakes_level=6,
    ))

    # ACT 2B: THE PARADOX (Chapters 13-18)
    # Things stop making sense in the false frame

    dag.add_node(PlotNode(
        id="first_crack",
        node_type=NodeType.COMPLICATION,
        description="First event that doesn't fit the frame. Dismissed",
        chapter=13,
        stakes_level=6,
    ))

    dag.add_node(PlotNode(
        id="answer_planted_3",
        node_type=NodeType.FORESHADOWING,
        description="Third planting of truth. Pattern now visible if looking",
        chapter=14,
        stakes_level=4,
    ))

    dag.add_node(PlotNode(
        id="second_crack",
        node_type=NodeType.COMPLICATION,
        description="Second contradiction. Harder to dismiss",
        chapter=15,
        stakes_level=7,
    ))

    dag.add_node(PlotNode(
        id="protagonist_doubt",
        node_type=NodeType.DECISION,
        description="Protagonist begins questioning assumptions",
        chapter=16,
        character="Protagonist",
        stakes_level=7,
    ))

    dag.add_node(PlotNode(
        id="paradox_moment",
        node_type=NodeType.COMPLICATION,
        description="Event that is IMPOSSIBLE in the false frame",
        chapter=17,
        stakes_level=8,
    ))

    dag.add_node(PlotNode(
        id="stuck_point",
        node_type=NodeType.CONSEQUENCE,
        description="Complete confusion. Old understanding broken",
        chapter=18,
        stakes_level=8,
        emotional_valence=-0.5,
    ))

    # ACT 3: THE SHIFT (Chapters 19-24)
    # Perspective changes, everything recontextualizes

    dag.add_node(PlotNode(
        id="shift_trigger",
        node_type=NodeType.REVELATION,
        description="Single detail that triggers the perspective shift",
        chapter=19,
        stakes_level=9,
    ))

    dag.add_node(PlotNode(
        id="perspective_shift",
        node_type=NodeType.REVELATION,
        description="THE SHIFT - reader/protagonist sees truth",
        chapter=20,
        stakes_level=10,
        is_twist=True,  # The REAL twist
    ))

    dag.add_node(PlotNode(
        id="reframe_cascade",
        node_type=NodeType.CONSEQUENCE,
        description="Everything clicks. Earlier events gain new meaning",
        chapter=21,
        stakes_level=9,
        emotional_valence=0.7,
    ))

    dag.add_node(PlotNode(
        id="true_confrontation",
        node_type=NodeType.CONFRONTATION,
        description="Real confrontation now that truth is known",
        chapter=22,
        stakes_level=10,
    ))

    dag.add_node(PlotNode(
        id="real_resolution",
        node_type=NodeType.RESOLUTION,
        description="Resolution that satisfies both frame and truth",
        chapter=23,
        stakes_level=7,
    ))

    dag.add_node(PlotNode(
        id="retrospective_clarity",
        node_type=NodeType.RESOLUTION,
        description="Final image that rewards re-reading",
        chapter=24,
        stakes_level=5,
        emotional_valence=0.6,
    ))

    # BUILD EDGES

    # Frame establishment chain
    dag.add_edge("opening_question", "frame_establishment", EdgeType.ENABLES)
    dag.add_edge("frame_establishment", "protagonist_goal", EdgeType.ENABLES)
    dag.add_edge("protagonist_goal", "supporting_cast", EdgeType.ENABLES)

    # Hidden answers (all point to final revelation)
    dag.add_edge("answer_planted_1", "perspective_shift", EdgeType.FORESHADOWS)
    dag.add_edge("answer_planted_2", "perspective_shift", EdgeType.FORESHADOWS)
    dag.add_edge("answer_planted_3", "perspective_shift", EdgeType.FORESHADOWS)

    # Decoy chain (misdirection)
    dag.add_edge("frame_establishment", "decoy_clue_1", EdgeType.ENABLES)
    dag.add_edge("decoy_clue_1", "false_progress", EdgeType.CAUSES)
    dag.add_edge("false_progress", "decoy_clue_2", EdgeType.ENABLES)
    dag.add_edge("decoy_clue_2", "false_revelation", EdgeType.CAUSES)
    dag.add_edge("false_revelation", "decoy_climax", EdgeType.CAUSES)
    dag.add_edge("decoy_climax", "hollow_victory", EdgeType.CAUSES)

    # Contrast: false path vs real truth
    dag.add_edge("false_revelation", "perspective_shift", EdgeType.CONTRASTS)
    dag.add_edge("decoy_climax", "true_confrontation", EdgeType.CONTRASTS)

    # Paradox build-up
    dag.add_edge("hollow_victory", "first_crack", EdgeType.CAUSES)
    dag.add_edge("first_crack", "second_crack", EdgeType.ENABLES)
    dag.add_edge("second_crack", "protagonist_doubt", EdgeType.CAUSES)
    dag.add_edge("protagonist_doubt", "paradox_moment", EdgeType.ENABLES)
    dag.add_edge("paradox_moment", "stuck_point", EdgeType.CAUSES)

    # The shift sequence
    dag.add_edge("stuck_point", "shift_trigger", EdgeType.ENABLES)
    dag.add_edge("shift_trigger", "perspective_shift", EdgeType.CAUSES)
    dag.add_edge("perspective_shift", "reframe_cascade", EdgeType.CAUSES)

    # Reframe connects back to early events
    dag.add_edge("answer_planted_1", "reframe_cascade", EdgeType.REVEALS)
    dag.add_edge("answer_planted_2", "reframe_cascade", EdgeType.REVEALS)
    dag.add_edge("answer_planted_3", "reframe_cascade", EdgeType.REVEALS)

    # Resolution
    dag.add_edge("reframe_cascade", "true_confrontation", EdgeType.ENABLES)
    dag.add_edge("true_confrontation", "real_resolution", EdgeType.CAUSES)
    dag.add_edge("real_resolution", "retrospective_clarity", EdgeType.ENABLES)

    # Full circle
    dag.add_edge("opening_question", "retrospective_clarity", EdgeType.RESOLVES)
    dag.add_edge("protagonist_goal", "real_resolution", EdgeType.RESOLVES)


# Define the genre templates
GENRE_TEMPLATES: dict[str, GenreTemplate] = {
    "mystery": GenreTemplate(
        name="Mystery/Detective",
        description="Convergent structure where scattered clues funnel toward revelation",
        typical_chapter_count=(20, 30),
        key_structural_features=[
            "Clue distribution across chapters",
            "Red herrings that mislead",
            "Multiple suspects introduced and eliminated",
            "Final revelation recontextualizes clues",
        ],
        required_node_types=[
            NodeType.CATALYST,  # The crime
            NodeType.REVELATION,  # Clues
            NodeType.COMPLICATION,  # Red herrings
            NodeType.RESOLUTION,  # Solution
        ],
        typical_subplot_count=(1, 3),
        build_skeleton=_build_mystery_skeleton,
    ),
    "thriller": GenreTemplate(
        name="Thriller",
        description="Escalating cascade with relentless forward momentum and time pressure",
        typical_chapter_count=(25, 35),
        key_structural_features=[
            "Ticking clock pressure",
            "Escalating stakes",
            "Chase sequences",
            "Escape/capture cycles",
            "High-stakes climax",
        ],
        required_node_types=[
            NodeType.CATALYST,  # Inciting threat
            NodeType.COMPLICATION,  # Escalations
            NodeType.DECISION,  # Escapes
            NodeType.CONFRONTATION,  # Final battle
        ],
        typical_subplot_count=(1, 2),
        build_skeleton=_build_thriller_skeleton,
    ),
    "romance": GenreTemplate(
        name="Romance",
        description="Intertwining helix where two characters approach, diverge, and merge",
        typical_chapter_count=(20, 30),
        key_structural_features=[
            "Meet cute",
            "Oscillating connection/separation",
            "Vulnerability reveals",
            "Dark moment",
            "Grand gesture",
            "Happily ever after",
        ],
        required_node_types=[
            NodeType.CATALYST,  # Meet cute
            NodeType.REVELATION,  # Vulnerabilities
            NodeType.COMPLICATION,  # Misunderstanding
            NodeType.RESOLUTION,  # Union
        ],
        typical_subplot_count=(0, 2),
        build_skeleton=_build_romance_skeleton,
    ),
    "epic_fantasy": GenreTemplate(
        name="Epic Fantasy",
        description="Hero's journey with multiple threads converging toward climactic battle",
        typical_chapter_count=(30, 50),
        key_structural_features=[
            "World building",
            "Mentor relationship",
            "Quest structure",
            "Training/growth arc",
            "Parallel villain arc",
            "Epic final confrontation",
        ],
        required_node_types=[
            NodeType.SETUP,  # World building
            NodeType.CATALYST,  # Call to adventure
            NodeType.COMPLICATION,  # Trials
            NodeType.REVELATION,  # Hidden truth
            NodeType.CONFRONTATION,  # Final battle
        ],
        typical_subplot_count=(2, 5),
        build_skeleton=_build_epic_fantasy_skeleton,
    ),
    "literary_fiction": GenreTemplate(
        name="Literary Fiction",
        description="Character-driven with non-linear time and internal/external interplay",
        typical_chapter_count=(15, 25),
        key_structural_features=[
            "Non-linear timeline",
            "Flashback integration",
            "Internal monologue",
            "Subtle external events",
            "Ambiguous resolution",
            "Thematic resonance",
        ],
        required_node_types=[
            NodeType.SETUP,  # Present moment
            NodeType.FLASHBACK,  # Memories
            NodeType.REVELATION,  # Internal recognition
            NodeType.DECISION,  # Internal shift
        ],
        typical_subplot_count=(1, 3),
        build_skeleton=_build_literary_fiction_skeleton,
    ),
    "riddle_novel": GenreTemplate(
        name="Riddle-Novel",
        description="The entire plot IS a riddle - reader solves it through perspective shift",
        typical_chapter_count=(20, 28),
        key_structural_features=[
            "False frame that seems like the real story",
            "Answer hidden in plain sight (planted 3+ times)",
            "Compelling decoy clues and false climax",
            "Paradox that breaks the false frame",
            "Perspective shift that recontextualizes everything",
            "Retrospective clarity on re-read",
        ],
        required_node_types=[
            NodeType.SETUP,  # Frame establishment
            NodeType.FORESHADOWING,  # Hidden answers
            NodeType.COMPLICATION,  # Decoys and paradox
            NodeType.REVELATION,  # The shift
            NodeType.RESOLUTION,  # True resolution
        ],
        typical_subplot_count=(1, 2),
        build_skeleton=_build_riddle_novel_skeleton,
    ),
}


def list_templates() -> list[str]:
    """Return list of available genre template names."""
    return list(GENRE_TEMPLATES.keys())


def get_template(genre: str) -> GenreTemplate:
    """Get a genre template by name."""
    if genre not in GENRE_TEMPLATES:
        raise ValueError(f"Unknown genre: {genre}. Available: {list_templates()}")
    return GENRE_TEMPLATES[genre]
