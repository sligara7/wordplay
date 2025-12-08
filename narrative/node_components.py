"""
Rich Node Components for Narrative DAGs

This module defines the hierarchical components that compose a PlotNode.
A node is not just an "event" - it's a complete story beat with:

- Characters (who's there, what roles they play)
- Setting (where and when)
- Situation (the dramatic context)
- Action (what happens)
- Consequences (what changes)

This richer model supports:
- Multiple characters per scene with distinct roles
- Detailed settings that can recur
- Tracking of information flow (who knows what)
- Object/prop tracking across scenes
- Emotional arcs for each character present
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from datetime import time


# =========================================================
# CHARACTER COMPONENTS
# =========================================================

class CharacterRole(Enum):
    """Role a character plays in a specific scene."""
    PROTAGONIST = auto()      # Driving the scene's action
    ANTAGONIST = auto()       # Opposing the protagonist
    ALLY = auto()             # Supporting the protagonist
    WITNESS = auto()          # Present but not actively involved
    VICTIM = auto()           # Affected by the action
    CATALYST = auto()         # Triggers events but not central
    MENTOR = auto()           # Providing guidance
    TRICKSTER = auto()        # Disrupting expectations
    MESSENGER = auto()        # Delivering information
    OBSERVER_POV = auto()     # The POV character (may differ from protagonist)


class EmotionalState(Enum):
    """Character's emotional state during a scene."""
    CALM = auto()
    ANXIOUS = auto()
    ANGRY = auto()
    FEARFUL = auto()
    HOPEFUL = auto()
    DESPAIRING = auto()
    CONFLICTED = auto()
    DETERMINED = auto()
    GRIEF = auto()
    JOY = auto()
    SUSPICIOUS = auto()
    TRUSTING = auto()
    CONFUSED = auto()
    ENLIGHTENED = auto()


@dataclass
class CharacterPresence:
    """
    A character's presence and state in a specific scene.

    The same character will have different CharacterPresence
    instances across different nodes, tracking their arc.
    """
    character_id: str
    character_name: str
    role: CharacterRole

    # Emotional journey in this scene
    entering_state: EmotionalState
    exiting_state: Optional[EmotionalState] = None  # If changed

    # What they want in this scene
    scene_goal: Optional[str] = None
    goal_achieved: Optional[bool] = None

    # Knowledge state
    learns_information: list[str] = field(default_factory=list)
    reveals_information: list[str] = field(default_factory=list)
    secrets_kept: list[str] = field(default_factory=list)

    # Dialogue/action summary
    key_dialogue: Optional[str] = None  # Most important line
    key_action: Optional[str] = None    # Most important action

    # Relationship changes
    relationship_changes: dict[str, str] = field(default_factory=dict)
    # e.g., {"other_char_id": "trust decreased"}


@dataclass
class Character:
    """
    Master character definition (not scene-specific).

    This is the "template" - CharacterPresence tracks per-scene state.
    """
    id: str
    name: str

    # Core identity
    role_in_story: str  # "protagonist", "antagonist", "mentor", etc.
    description: str

    # Character dimensions
    want: str           # External goal
    need: str           # Internal/thematic need
    flaw: str           # What holds them back
    ghost: Optional[str] = None  # Past trauma/backstory

    # Arc tracking
    arc_type: str = "change"  # "change", "flat", "fall", "rise"
    starting_state: Optional[str] = None
    ending_state: Optional[str] = None

    # Relationships
    relationships: dict[str, str] = field(default_factory=dict)
    # e.g., {"char_id": "brother", "char_id2": "rival"}


# =========================================================
# SETTING COMPONENTS
# =========================================================

class TimeOfDay(Enum):
    """When the scene takes place."""
    DAWN = auto()
    MORNING = auto()
    MIDDAY = auto()
    AFTERNOON = auto()
    DUSK = auto()
    EVENING = auto()
    NIGHT = auto()
    LATE_NIGHT = auto()
    UNSPECIFIED = auto()


class SettingMood(Enum):
    """Atmospheric mood of the setting."""
    OMINOUS = auto()
    PEACEFUL = auto()
    TENSE = auto()
    CHAOTIC = auto()
    INTIMATE = auto()
    EXPOSED = auto()
    CLAUSTROPHOBIC = auto()
    VAST = auto()
    FAMILIAR = auto()
    ALIEN = auto()
    SACRED = auto()
    PROFANE = auto()


@dataclass
class Setting:
    """
    A location where scenes can take place.

    Settings are reusable - multiple nodes can reference the same setting.
    This allows tracking of "this location has significance because X happened here."
    """
    id: str
    name: str
    description: str

    # Location hierarchy
    parent_location: Optional[str] = None  # e.g., "castle" is parent of "throne_room"

    # Characteristics
    is_public: bool = True
    is_safe: bool = True  # For the protagonist
    mood: SettingMood = SettingMood.FAMILIAR

    # Sensory details (for consistency)
    visual_details: list[str] = field(default_factory=list)
    sounds: list[str] = field(default_factory=list)
    smells: list[str] = field(default_factory=list)

    # Narrative significance
    first_appearance_chapter: Optional[int] = None
    significance: Optional[str] = None  # Why this place matters to the story

    # Associated props/objects that "live" here
    permanent_props: list[str] = field(default_factory=list)


@dataclass
class SceneSetting:
    """
    Setting configuration for a specific scene.

    References a Setting but adds scene-specific details.
    """
    setting_id: str

    # Time
    time_of_day: TimeOfDay = TimeOfDay.UNSPECIFIED
    duration_minutes: Optional[int] = None  # How long does scene span?

    # Scene-specific mood (may override setting default)
    mood_override: Optional[SettingMood] = None

    # Weather/atmosphere (if relevant)
    weather: Optional[str] = None

    # What's different about the setting in THIS scene?
    temporary_elements: list[str] = field(default_factory=list)
    # e.g., ["crime scene tape", "broken window"]


# =========================================================
# PROP/OBJECT TRACKING
# =========================================================

class PropSignificance(Enum):
    """How important is this object to the narrative?"""
    BACKGROUND = auto()      # Atmosphere only
    MENTIONED = auto()       # Referenced but not used
    USED = auto()            # Actively used in scene
    PLOT_DEVICE = auto()     # Critical to plot
    SYMBOL = auto()          # Thematic significance
    CHEKHOV = auto()         # Planted for later payoff


@dataclass
class Prop:
    """
    An object that appears in the story.

    Props can recur, be passed between characters, or serve as
    Chekhov's guns that must fire later.
    """
    id: str
    name: str
    description: str

    significance: PropSignificance = PropSignificance.BACKGROUND

    # Tracking
    introduced_in_node: Optional[str] = None
    current_owner: Optional[str] = None  # Character ID
    current_location: Optional[str] = None  # Setting ID

    # Chekhov tracking
    is_planted: bool = False
    planted_in_node: Optional[str] = None
    fires_in_node: Optional[str] = None  # When it pays off

    # Symbolic meaning
    symbolizes: Optional[str] = None


@dataclass
class PropUsage:
    """How a prop is used in a specific scene."""
    prop_id: str
    action: str  # "picked up", "hidden", "revealed", "destroyed", etc.
    by_character: Optional[str] = None
    significance_in_scene: PropSignificance = PropSignificance.USED


# =========================================================
# SITUATION / DRAMATIC CONTEXT
# =========================================================

class ConflictType(Enum):
    """Type of conflict in the scene."""
    PERSON_VS_PERSON = auto()
    PERSON_VS_SELF = auto()
    PERSON_VS_NATURE = auto()
    PERSON_VS_SOCIETY = auto()
    PERSON_VS_TECHNOLOGY = auto()
    PERSON_VS_FATE = auto()
    NONE = auto()  # Purely expository


class TensionLevel(Enum):
    """Narrative tension level."""
    RELEASE = auto()      # Tension release / breather
    LOW = auto()          # Calm before storm
    BUILDING = auto()     # Rising tension
    HIGH = auto()         # Peak tension
    EXPLOSIVE = auto()    # Crisis point


@dataclass
class Situation:
    """
    The dramatic context of a scene.

    What's at stake, what's the conflict, what must be decided?
    """
    # Conflict
    conflict_type: ConflictType = ConflictType.NONE
    conflict_description: Optional[str] = None

    # Stakes
    stakes_description: str = ""
    stakes_level: int = 5  # 1-10
    stakes_personal: bool = True   # Does it affect protagonist personally?
    stakes_global: bool = False    # Does it affect the world?

    # Tension
    tension_level: TensionLevel = TensionLevel.LOW

    # Dramatic question
    scene_question: Optional[str] = None  # "Will X succeed in doing Y?"
    question_answered: Optional[bool] = None

    # Ticking clock
    has_deadline: bool = False
    deadline_description: Optional[str] = None

    # Reversals
    contains_reversal: bool = False
    reversal_description: Optional[str] = None


# =========================================================
# INFORMATION TRACKING
# =========================================================

@dataclass
class InformationPiece:
    """
    A piece of information that can be known, revealed, or hidden.

    Tracking information flow is critical for mysteries and any
    plot with secrets, lies, or revelations.
    """
    id: str
    content: str  # What the information IS

    # Truth value
    is_true: bool = True  # False for red herrings, lies, mistaken beliefs

    # Revelation tracking
    first_hinted_node: Optional[str] = None
    fully_revealed_node: Optional[str] = None

    # Who knows this?
    known_by: list[str] = field(default_factory=list)  # Character IDs
    reader_knows: bool = False  # Does the reader know this yet?

    # Plot significance
    is_crucial: bool = False  # Must be known for plot to resolve
    contradicts: list[str] = field(default_factory=list)  # Other info piece IDs


@dataclass
class InformationExchange:
    """Information flow in a specific scene."""
    info_id: str

    # Flow direction
    revealer: Optional[str] = None  # Who reveals it (None if discovered)
    recipients: list[str] = field(default_factory=list)

    # How it's revealed
    method: str = "dialogue"  # "dialogue", "action", "discovery", "flashback"

    # Impact
    is_surprise: bool = False  # Was this unexpected?
    changes_understanding: bool = False  # Does it reframe prior events?


# =========================================================
# THE RICH PLOT NODE
# =========================================================

@dataclass
class RichPlotNode:
    """
    A fully-specified story beat with all components.

    This replaces the flat PlotNode with a hierarchical structure
    that captures the full richness of a scene.
    """
    # Identity
    id: str
    title: str  # Short title for the beat

    # Classification (from original PlotNode)
    node_type: str  # "SETUP", "CATALYST", etc. - using string for flexibility

    # Narrative position
    chapter: Optional[int] = None
    act: Optional[int] = None
    sequence: Optional[int] = None  # Order within chapter
    subplot: Optional[str] = None

    # === COMPONENTS ===

    # Characters
    characters: list[CharacterPresence] = field(default_factory=list)
    pov_character: Optional[str] = None  # Whose perspective is this?

    # Setting
    setting: Optional[SceneSetting] = None

    # Situation
    situation: Optional[Situation] = None

    # Props
    props_used: list[PropUsage] = field(default_factory=list)

    # Information
    info_exchanges: list[InformationExchange] = field(default_factory=list)

    # === NARRATIVE METADATA ===

    # Summary
    description: str = ""  # Prose description of what happens
    one_liner: str = ""    # Tweet-length summary

    # Emotional
    emotional_valence: float = 0.0  # -1 to +1 overall

    # Structural
    is_twist: bool = False
    is_cliffhanger: bool = False
    is_obligatory_scene: bool = False  # Genre-required scene

    # Reader experience
    reader_emotion_target: Optional[str] = None  # What should reader feel?
    dramatic_irony: bool = False  # Does reader know more than characters?

    # === CONNECTIONS (for DAG) ===

    # These help determine edge types
    causes: list[str] = field(default_factory=list)      # Node IDs this leads to
    caused_by: list[str] = field(default_factory=list)   # Node IDs leading here
    foreshadows: list[str] = field(default_factory=list)
    parallels: list[str] = field(default_factory=list)

    # === AUTHORING METADATA ===

    status: str = "draft"  # "idea", "draft", "revised", "final"
    author_notes: str = ""
    version: int = 1

    def get_character_ids(self) -> list[str]:
        """Get all character IDs in this scene."""
        return [c.character_id for c in self.characters]

    def get_protagonist(self) -> Optional[CharacterPresence]:
        """Get the protagonist's presence in this scene."""
        for c in self.characters:
            if c.role == CharacterRole.PROTAGONIST:
                return c
        return None

    def get_info_learned_by(self, character_id: str) -> list[str]:
        """Get all information learned by a character in this scene."""
        for c in self.characters:
            if c.character_id == character_id:
                return c.learns_information
        return []

    def summary(self) -> str:
        """Generate a summary of this beat."""
        lines = [f"[{self.id}] {self.title}"]

        if self.chapter:
            lines.append(f"  Chapter {self.chapter}" +
                        (f", Act {self.act}" if self.act else ""))

        lines.append(f"  Type: {self.node_type}")

        if self.characters:
            char_summary = ", ".join(
                f"{c.character_name} ({c.role.name})"
                for c in self.characters[:3]
            )
            if len(self.characters) > 3:
                char_summary += f" +{len(self.characters) - 3} more"
            lines.append(f"  Characters: {char_summary}")

        if self.setting:
            lines.append(f"  Setting: {self.setting.setting_id}")

        if self.situation:
            lines.append(f"  Tension: {self.situation.tension_level.name}")
            lines.append(f"  Stakes: {self.situation.stakes_level}/10")

        if self.one_liner:
            lines.append(f"  Summary: {self.one_liner}")

        return "\n".join(lines)


# =========================================================
# STORY WORLD (Container for reusable elements)
# =========================================================

@dataclass
class StoryWorld:
    """
    Container for all reusable story elements.

    Characters, settings, props, and information pieces are defined
    once here and referenced by ID in individual nodes.
    """
    # Master definitions
    characters: dict[str, Character] = field(default_factory=dict)
    settings: dict[str, Setting] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
    information: dict[str, InformationPiece] = field(default_factory=dict)

    # Story metadata
    title: str = ""
    genre: str = ""
    themes: list[str] = field(default_factory=list)

    # Timeline
    story_duration: Optional[str] = None  # "3 days", "10 years", etc.

    def add_character(self, char: Character) -> None:
        self.characters[char.id] = char

    def add_setting(self, setting: Setting) -> None:
        self.settings[setting.id] = setting

    def add_prop(self, prop: Prop) -> None:
        self.props[prop.id] = prop

    def add_information(self, info: InformationPiece) -> None:
        self.information[info.id] = info

    def get_character(self, char_id: str) -> Optional[Character]:
        return self.characters.get(char_id)

    def get_setting(self, setting_id: str) -> Optional[Setting]:
        return self.settings.get(setting_id)

    def validate_node(self, node: RichPlotNode) -> list[str]:
        """
        Validate that a node's references exist in the world.
        Returns list of errors.
        """
        errors = []

        # Check character references
        for char in node.characters:
            if char.character_id not in self.characters:
                errors.append(f"Unknown character: {char.character_id}")

        # Check setting reference
        if node.setting and node.setting.setting_id not in self.settings:
            errors.append(f"Unknown setting: {node.setting.setting_id}")

        # Check prop references
        for prop_usage in node.props_used:
            if prop_usage.prop_id not in self.props:
                errors.append(f"Unknown prop: {prop_usage.prop_id}")

        # Check information references
        for info_ex in node.info_exchanges:
            if info_ex.info_id not in self.information:
                errors.append(f"Unknown information: {info_ex.info_id}")

        return errors
