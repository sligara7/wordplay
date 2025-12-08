"""
Functional Analysis for Narratives - Systems Engineering Approach to Plot Design.

Inspired by reflow's functional analysis workflows (FA-01 through FA-07), this
module treats storytelling through a systems engineering lens:

- Narrative Functions: What the story needs to accomplish (like functional requirements)
- Plot Events: Atomic functions that perform one specific story task
- Chapters: Allocation units where functions are grouped (like services)
- Character Arcs: Workflows that span multiple chapters
- Subplots: Domains that organize related functions

This enables:
1. Requirements-driven plot development (what must the story do?)
2. Functional decomposition (break big story goals into atomic events)
3. Chapter allocation (which events go in which chapters?)
4. Flow analysis (how do events connect?)
5. Gap detection (what's missing to meet story requirements?)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any
import json
from pathlib import Path

from .narrative_dag import NarrativeDAG, PlotNode, NodeType, EdgeType


class NarrativeFunctionType(Enum):
    """Types of narrative functions (what the story needs to do)."""

    # Character functions
    INTRODUCE_CHARACTER = auto()  # Make reader care about a character
    DEVELOP_CHARACTER = auto()  # Show character growth/change
    REVEAL_BACKSTORY = auto()  # Provide character history
    ESTABLISH_MOTIVATION = auto()  # Show why character acts

    # Plot functions
    ESTABLISH_STAKES = auto()  # Show what's at risk
    RAISE_TENSION = auto()  # Increase conflict/suspense
    PROVIDE_OBSTACLE = auto()  # Create challenge for protagonist
    DELIVER_TWIST = auto()  # Subvert expectations
    RESOLVE_CONFLICT = auto()  # Close a narrative thread

    # Information functions
    PLANT_CLUE = auto()  # Set up future revelation
    DELIVER_EXPOSITION = auto()  # Provide necessary context
    CREATE_MYSTERY = auto()  # Raise questions
    ANSWER_QUESTION = auto()  # Resolve mystery

    # Emotional functions
    CREATE_SYMPATHY = auto()  # Make reader feel for character
    BUILD_DREAD = auto()  # Create sense of impending doom
    PROVIDE_RELIEF = auto()  # Release tension
    DELIVER_CATHARSIS = auto()  # Emotional payoff

    # Structural functions
    ESTABLISH_SETTING = auto()  # Create world/atmosphere
    TRANSITION_TIME = auto()  # Move story forward in time
    CONNECT_SUBPLOTS = auto()  # Link different storylines
    FORESHADOW_ENDING = auto()  # Prepare reader for conclusion


@dataclass
class NarrativeRequirement:
    """
    A functional requirement for the narrative.

    Like a systems engineering requirement (FR-001), this specifies
    WHAT the story must accomplish without specifying HOW.
    """

    id: str  # e.g., "NR-001"
    description: str  # What must be accomplished
    function_type: NarrativeFunctionType
    priority: int = 1  # 1=critical, 2=important, 3=nice-to-have
    source: str = ""  # Where this requirement came from (premise, genre, etc.)
    success_criteria: list[str] = field(default_factory=list)  # How we know it's met
    allocated_to: Optional[str] = None  # Which chapter/scene addresses this
    satisfied: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "function_type": self.function_type.name,
            "priority": self.priority,
            "source": self.source,
            "success_criteria": self.success_criteria,
            "allocated_to": self.allocated_to,
            "satisfied": self.satisfied,
        }


@dataclass
class AtomicFunction:
    """
    An atomic story function - the smallest unit of narrative work.

    Following reflow's principle: "Smallest reusable unit of functionality
    that performs ONE specific task."

    Each atomic function:
    - Has a single responsibility
    - Takes inputs (prior story state)
    - Produces outputs (new story state)
    - Can be allocated to a chapter
    """

    id: str  # e.g., "F-001"
    name: str  # Verb + Object: "Reveal Villain's Motivation"
    description: str
    function_type: NarrativeFunctionType
    inputs: list[str] = field(default_factory=list)  # Required prior state
    outputs: list[str] = field(default_factory=list)  # Resulting state
    characters_involved: list[str] = field(default_factory=list)
    requirements_satisfied: list[str] = field(default_factory=list)  # NR-xxx IDs
    allocated_chapter: Optional[int] = None
    estimated_pages: float = 1.0  # Rough size estimate

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "function_type": self.function_type.name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "characters_involved": self.characters_involved,
            "requirements_satisfied": self.requirements_satisfied,
            "allocated_chapter": self.allocated_chapter,
            "estimated_pages": self.estimated_pages,
        }


@dataclass
class ChapterAllocation:
    """
    A chapter as an allocation unit for narrative functions.

    Like a service in systems engineering, chapters group related
    functions and manage their coordination.
    """

    chapter_number: int
    title: str = ""
    pov_character: Optional[str] = None
    subplot: str = "main"
    allocated_functions: list[str] = field(default_factory=list)  # Function IDs
    target_pages: int = 20
    emotional_arc: str = ""  # e.g., "tension_rising", "relief", "climax"

    def to_dict(self) -> dict:
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "pov_character": self.pov_character,
            "subplot": self.subplot,
            "allocated_functions": self.allocated_functions,
            "target_pages": self.target_pages,
            "emotional_arc": self.emotional_arc,
        }


class AllocationStrategy(Enum):
    """Strategies for allocating functions to chapters (like service organization)."""

    CHRONOLOGICAL = auto()  # Events in time order
    POV_BASED = auto()  # Group by point-of-view character
    SUBPLOT_BASED = auto()  # Group by storyline
    EMOTIONAL_ARC = auto()  # Group by emotional beats
    HYBRID = auto()  # Mix strategies as needed


@dataclass
class FunctionalFlow:
    """
    A flow of connected functions representing a narrative thread.

    Like reflow's functional flows, this maps how functions connect:
    - Process flows: Sequential events
    - Decision flows: Branching paths
    - Data flows: Information transfer
    - Error flows: Recovery/failure paths
    """

    id: str
    name: str
    flow_type: str  # "process", "decision", "character_arc", "mystery"
    functions: list[str]  # Ordered function IDs
    entry_point: str  # Starting function
    exit_points: list[str]  # Ending functions
    decision_points: list[dict] = field(default_factory=list)  # Branching logic

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "flow_type": self.flow_type,
            "functions": self.functions,
            "entry_point": self.entry_point,
            "exit_points": self.exit_points,
            "decision_points": self.decision_points,
        }


class NarrativeFunctionalAnalyzer:
    """
    Performs functional analysis on narrative structures.

    Workflow inspired by reflow's FA-01 through FA-07:
    1. Extract functional requirements from premise/genre
    2. Decompose into atomic functions
    3. Analyze functional flows
    4. Allocate to chapters
    5. Validate coverage
    6. Iterate and refine
    """

    def __init__(self):
        self.requirements: dict[str, NarrativeRequirement] = {}
        self.functions: dict[str, AtomicFunction] = {}
        self.chapters: dict[int, ChapterAllocation] = {}
        self.flows: dict[str, FunctionalFlow] = {}
        self._req_counter = 0
        self._func_counter = 0
        self._flow_counter = 0

    # ========== Phase 1: Requirements Extraction ==========

    def add_requirement(
        self,
        description: str,
        function_type: NarrativeFunctionType,
        priority: int = 1,
        source: str = "",
        success_criteria: list[str] | None = None,
    ) -> NarrativeRequirement:
        """Add a narrative requirement."""
        self._req_counter += 1
        req_id = f"NR-{self._req_counter:03d}"

        req = NarrativeRequirement(
            id=req_id,
            description=description,
            function_type=function_type,
            priority=priority,
            source=source,
            success_criteria=success_criteria or [],
        )
        self.requirements[req_id] = req
        return req

    def extract_requirements_from_genre(self, genre: str) -> list[NarrativeRequirement]:
        """Extract standard requirements based on genre conventions."""
        genre_requirements = {
            "mystery": [
                (NarrativeFunctionType.CREATE_MYSTERY, "Establish central mystery/crime", 1),
                (NarrativeFunctionType.PLANT_CLUE, "Plant at least 5 discoverable clues", 1),
                (NarrativeFunctionType.DELIVER_TWIST, "Include at least one red herring", 2),
                (NarrativeFunctionType.ANSWER_QUESTION, "Reveal solution that reader could deduce", 1),
                (NarrativeFunctionType.INTRODUCE_CHARACTER, "Introduce detective/investigator", 1),
            ],
            "thriller": [
                (NarrativeFunctionType.ESTABLISH_STAKES, "Establish life-or-death stakes", 1),
                (NarrativeFunctionType.RAISE_TENSION, "Escalate tension through 3+ levels", 1),
                (NarrativeFunctionType.BUILD_DREAD, "Create ticking clock pressure", 1),
                (NarrativeFunctionType.PROVIDE_OBSTACLE, "Include 3+ major obstacles", 1),
                (NarrativeFunctionType.RESOLVE_CONFLICT, "Climactic confrontation", 1),
            ],
            "romance": [
                (NarrativeFunctionType.INTRODUCE_CHARACTER, "Establish both romantic leads", 1),
                (NarrativeFunctionType.CREATE_SYMPATHY, "Make reader root for the couple", 1),
                (NarrativeFunctionType.PROVIDE_OBSTACLE, "Create compelling obstacles to union", 1),
                (NarrativeFunctionType.DEVELOP_CHARACTER, "Show character growth in both leads", 1),
                (NarrativeFunctionType.DELIVER_CATHARSIS, "Satisfying romantic resolution", 1),
            ],
            "epic_fantasy": [
                (NarrativeFunctionType.ESTABLISH_SETTING, "Create rich fantasy world", 1),
                (NarrativeFunctionType.INTRODUCE_CHARACTER, "Establish hero's ordinary world", 1),
                (NarrativeFunctionType.ESTABLISH_MOTIVATION, "Give hero compelling reason to act", 1),
                (NarrativeFunctionType.DEVELOP_CHARACTER, "Show hero's transformation", 1),
                (NarrativeFunctionType.RESOLVE_CONFLICT, "Epic final confrontation", 1),
                (NarrativeFunctionType.FORESHADOW_ENDING, "Plant seeds of ending early", 2),
            ],
            "literary_fiction": [
                (NarrativeFunctionType.DEVELOP_CHARACTER, "Deep character exploration", 1),
                (NarrativeFunctionType.REVEAL_BACKSTORY, "Meaningful backstory integration", 1),
                (NarrativeFunctionType.CREATE_SYMPATHY, "Complex, sympathetic protagonist", 1),
                (NarrativeFunctionType.DELIVER_CATHARSIS, "Thematic resolution (may be ambiguous)", 1),
            ],
        }

        reqs = []
        for func_type, desc, priority in genre_requirements.get(genre, []):
            req = self.add_requirement(
                description=desc,
                function_type=func_type,
                priority=priority,
                source=f"genre:{genre}",
            )
            reqs.append(req)

        return reqs

    # ========== Phase 2: Functional Decomposition ==========

    def add_function(
        self,
        name: str,
        description: str,
        function_type: NarrativeFunctionType,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        characters: list[str] | None = None,
        satisfies: list[str] | None = None,
    ) -> AtomicFunction:
        """Add an atomic narrative function."""
        self._func_counter += 1
        func_id = f"F-{self._func_counter:03d}"

        func = AtomicFunction(
            id=func_id,
            name=name,
            description=description,
            function_type=function_type,
            inputs=inputs or [],
            outputs=outputs or [],
            characters_involved=characters or [],
            requirements_satisfied=satisfies or [],
        )
        self.functions[func_id] = func

        # Mark requirements as having allocation
        for req_id in func.requirements_satisfied:
            if req_id in self.requirements:
                self.requirements[req_id].satisfied = True

        return func

    def decompose_requirement(self, req_id: str) -> list[AtomicFunction]:
        """Decompose a requirement into atomic functions."""
        if req_id not in self.requirements:
            return []

        req = self.requirements[req_id]
        functions = []

        # Generate appropriate functions based on requirement type
        decomposition_patterns = {
            NarrativeFunctionType.INTRODUCE_CHARACTER: [
                ("Establish Character Context", "Show character in their world"),
                ("Reveal Character Trait", "Demonstrate key personality trait"),
                ("Create Character Connection", "Give reader reason to care"),
            ],
            NarrativeFunctionType.ESTABLISH_STAKES: [
                ("Show Normal State", "What could be lost"),
                ("Introduce Threat", "What endangers the normal state"),
                ("Personalize Stakes", "Connect stakes to specific character"),
            ],
            NarrativeFunctionType.CREATE_MYSTERY: [
                ("Present Anomaly", "Something doesn't fit"),
                ("Raise Question", "Why did this happen?"),
                ("Hint at Depth", "Suggest larger implications"),
            ],
            NarrativeFunctionType.DELIVER_TWIST: [
                ("Setup Expectation", "Lead reader to assume X"),
                ("Maintain Misdirection", "Reinforce wrong assumption"),
                ("Reveal Truth", "Subvert expectation with Y"),
            ],
        }

        pattern = decomposition_patterns.get(req.function_type, [
            ("Execute " + req.description, req.description),
        ])

        for name, desc in pattern:
            func = self.add_function(
                name=name,
                description=desc,
                function_type=req.function_type,
                satisfies=[req_id],
            )
            functions.append(func)

        return functions

    # ========== Phase 3: Flow Analysis ==========

    def add_flow(
        self,
        name: str,
        flow_type: str,
        functions: list[str],
        decision_points: list[dict] | None = None,
    ) -> FunctionalFlow:
        """Add a functional flow connecting functions."""
        self._flow_counter += 1
        flow_id = f"FL-{self._flow_counter:03d}"

        flow = FunctionalFlow(
            id=flow_id,
            name=name,
            flow_type=flow_type,
            functions=functions,
            entry_point=functions[0] if functions else "",
            exit_points=[functions[-1]] if functions else [],
            decision_points=decision_points or [],
        )
        self.flows[flow_id] = flow
        return flow

    def create_character_arc_flow(self, character: str) -> Optional[FunctionalFlow]:
        """Create a flow representing a character's arc."""
        char_functions = [
            f_id
            for f_id, f in self.functions.items()
            if character in f.characters_involved
        ]

        if not char_functions:
            return None

        return self.add_flow(
            name=f"{character}'s Arc",
            flow_type="character_arc",
            functions=char_functions,
        )

    # ========== Phase 4: Chapter Allocation ==========

    def add_chapter(
        self,
        chapter_number: int,
        title: str = "",
        pov_character: str | None = None,
        subplot: str = "main",
        target_pages: int = 20,
        emotional_arc: str = "",
    ) -> ChapterAllocation:
        """Add a chapter allocation unit."""
        chapter = ChapterAllocation(
            chapter_number=chapter_number,
            title=title,
            pov_character=pov_character,
            subplot=subplot,
            target_pages=target_pages,
            emotional_arc=emotional_arc,
        )
        self.chapters[chapter_number] = chapter
        return chapter

    def allocate_function_to_chapter(self, func_id: str, chapter_number: int) -> bool:
        """Allocate a function to a specific chapter."""
        if func_id not in self.functions:
            return False
        if chapter_number not in self.chapters:
            self.add_chapter(chapter_number)

        self.functions[func_id].allocated_chapter = chapter_number
        if func_id not in self.chapters[chapter_number].allocated_functions:
            self.chapters[chapter_number].allocated_functions.append(func_id)

        return True

    def auto_allocate(self, strategy: AllocationStrategy = AllocationStrategy.CHRONOLOGICAL) -> None:
        """Automatically allocate functions to chapters based on strategy."""
        unallocated = [f for f in self.functions.values() if f.allocated_chapter is None]

        if strategy == AllocationStrategy.CHRONOLOGICAL:
            # Simple: distribute evenly across chapters
            num_chapters = max(len(self.chapters), len(unallocated) // 3, 1)
            for i, func in enumerate(unallocated):
                chapter_num = (i % num_chapters) + 1
                self.allocate_function_to_chapter(func.id, chapter_num)

        elif strategy == AllocationStrategy.POV_BASED:
            # Group by character
            char_groups: dict[str, list[AtomicFunction]] = {}
            for func in unallocated:
                char = func.characters_involved[0] if func.characters_involved else "narrator"
                if char not in char_groups:
                    char_groups[char] = []
                char_groups[char].append(func)

            chapter_num = 1
            for char, funcs in char_groups.items():
                for func in funcs:
                    self.allocate_function_to_chapter(func.id, chapter_num)
                chapter_num += 1

    # ========== Phase 5: Validation ==========

    def validate_coverage(self) -> dict[str, Any]:
        """Validate that all requirements are covered by allocated functions."""
        uncovered = []
        partially_covered = []
        fully_covered = []

        for req_id, req in self.requirements.items():
            # Find functions that satisfy this requirement
            satisfying = [
                f for f in self.functions.values() if req_id in f.requirements_satisfied
            ]

            if not satisfying:
                uncovered.append(req)
            elif all(f.allocated_chapter is not None for f in satisfying):
                fully_covered.append(req)
            else:
                partially_covered.append(req)

        return {
            "total_requirements": len(self.requirements),
            "uncovered": [r.to_dict() for r in uncovered],
            "partially_covered": [r.to_dict() for r in partially_covered],
            "fully_covered": [r.to_dict() for r in fully_covered],
            "coverage_percentage": len(fully_covered) / len(self.requirements) * 100
            if self.requirements
            else 100,
        }

    def validate_allocation(self) -> dict[str, Any]:
        """Validate chapter allocations for balance and completeness."""
        issues = []

        # Check for unallocated functions
        unallocated = [f for f in self.functions.values() if f.allocated_chapter is None]
        if unallocated:
            issues.append({
                "type": "unallocated_functions",
                "count": len(unallocated),
                "functions": [f.id for f in unallocated],
            })

        # Check for empty chapters
        empty_chapters = [
            ch for ch in self.chapters.values() if not ch.allocated_functions
        ]
        if empty_chapters:
            issues.append({
                "type": "empty_chapters",
                "chapters": [ch.chapter_number for ch in empty_chapters],
            })

        # Check for overloaded chapters
        avg_functions = len(self.functions) / len(self.chapters) if self.chapters else 0
        overloaded = [
            ch
            for ch in self.chapters.values()
            if len(ch.allocated_functions) > avg_functions * 2
        ]
        if overloaded:
            issues.append({
                "type": "overloaded_chapters",
                "chapters": [ch.chapter_number for ch in overloaded],
            })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "statistics": {
                "total_functions": len(self.functions),
                "total_chapters": len(self.chapters),
                "avg_functions_per_chapter": avg_functions,
            },
        }

    # ========== Conversion ==========

    def to_narrative_dag(self, title: str = "Generated Narrative") -> NarrativeDAG:
        """Convert functional analysis to a NarrativeDAG."""
        dag = NarrativeDAG(title=title)

        # Convert functions to plot nodes
        func_type_to_node_type = {
            NarrativeFunctionType.INTRODUCE_CHARACTER: NodeType.SETUP,
            NarrativeFunctionType.DEVELOP_CHARACTER: NodeType.CONSEQUENCE,
            NarrativeFunctionType.REVEAL_BACKSTORY: NodeType.FLASHBACK,
            NarrativeFunctionType.ESTABLISH_MOTIVATION: NodeType.SETUP,
            NarrativeFunctionType.ESTABLISH_STAKES: NodeType.SETUP,
            NarrativeFunctionType.RAISE_TENSION: NodeType.COMPLICATION,
            NarrativeFunctionType.PROVIDE_OBSTACLE: NodeType.COMPLICATION,
            NarrativeFunctionType.DELIVER_TWIST: NodeType.REVELATION,
            NarrativeFunctionType.RESOLVE_CONFLICT: NodeType.RESOLUTION,
            NarrativeFunctionType.PLANT_CLUE: NodeType.FORESHADOWING,
            NarrativeFunctionType.DELIVER_EXPOSITION: NodeType.SETUP,
            NarrativeFunctionType.CREATE_MYSTERY: NodeType.CATALYST,
            NarrativeFunctionType.ANSWER_QUESTION: NodeType.REVELATION,
            NarrativeFunctionType.CREATE_SYMPATHY: NodeType.SETUP,
            NarrativeFunctionType.BUILD_DREAD: NodeType.COMPLICATION,
            NarrativeFunctionType.PROVIDE_RELIEF: NodeType.CONSEQUENCE,
            NarrativeFunctionType.DELIVER_CATHARSIS: NodeType.RESOLUTION,
            NarrativeFunctionType.ESTABLISH_SETTING: NodeType.SETUP,
            NarrativeFunctionType.TRANSITION_TIME: NodeType.CONSEQUENCE,
            NarrativeFunctionType.CONNECT_SUBPLOTS: NodeType.CONSEQUENCE,
            NarrativeFunctionType.FORESHADOW_ENDING: NodeType.FORESHADOWING,
        }

        # Add nodes
        for func in self.functions.values():
            node_type = func_type_to_node_type.get(
                func.function_type, NodeType.CONSEQUENCE
            )

            # Determine subplot from chapter
            subplot = None
            if func.allocated_chapter and func.allocated_chapter in self.chapters:
                subplot = self.chapters[func.allocated_chapter].subplot

            node = PlotNode(
                id=func.id,
                node_type=node_type,
                description=f"{func.name}: {func.description}",
                chapter=func.allocated_chapter,
                character=func.characters_involved[0] if func.characters_involved else None,
                subplot=subplot,
                is_twist=func.function_type == NarrativeFunctionType.DELIVER_TWIST,
            )
            dag.add_node(node)

        # Add edges based on input/output dependencies
        for func in self.functions.values():
            for input_ref in func.inputs:
                # Find function that produces this output
                for other_func in self.functions.values():
                    if input_ref in other_func.outputs:
                        dag.add_edge(other_func.id, func.id, EdgeType.ENABLES)

        # Add edges based on chapter order (functions in same chapter connect)
        for chapter in self.chapters.values():
            funcs = chapter.allocated_functions
            for i in range(len(funcs) - 1):
                if funcs[i] in dag._nodes and funcs[i + 1] in dag._nodes:
                    # Only add if edge doesn't exist
                    if not dag.graph.has_edge(funcs[i], funcs[i + 1]):
                        dag.add_edge(funcs[i], funcs[i + 1], EdgeType.CAUSES)

        return dag

    def export_to_reflow(self) -> dict[str, Any]:
        """Export in reflow-compatible format for systems engineering tools."""
        return {
            "metadata": {
                "type": "narrative_functional_analysis",
                "version": "1.0",
                "total_requirements": len(self.requirements),
                "total_functions": len(self.functions),
                "total_chapters": len(self.chapters),
            },
            "requirements": [r.to_dict() for r in self.requirements.values()],
            "functions": [f.to_dict() for f in self.functions.values()],
            "chapters": [c.to_dict() for c in self.chapters.values()],
            "flows": [f.to_dict() for f in self.flows.values()],
            "validation": {
                "coverage": self.validate_coverage(),
                "allocation": self.validate_allocation(),
            },
        }

    def save(self, path: str | Path) -> None:
        """Save functional analysis to JSON file."""
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.export_to_reflow(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "NarrativeFunctionalAnalyzer":
        """Load functional analysis from JSON file."""
        path = Path(path)
        with open(path) as f:
            data = json.load(f)

        analyzer = cls()

        # Restore requirements
        for req_data in data.get("requirements", []):
            req = NarrativeRequirement(
                id=req_data["id"],
                description=req_data["description"],
                function_type=NarrativeFunctionType[req_data["function_type"]],
                priority=req_data.get("priority", 1),
                source=req_data.get("source", ""),
                success_criteria=req_data.get("success_criteria", []),
                allocated_to=req_data.get("allocated_to"),
                satisfied=req_data.get("satisfied", False),
            )
            analyzer.requirements[req.id] = req

        # Restore functions
        for func_data in data.get("functions", []):
            func = AtomicFunction(
                id=func_data["id"],
                name=func_data["name"],
                description=func_data["description"],
                function_type=NarrativeFunctionType[func_data["function_type"]],
                inputs=func_data.get("inputs", []),
                outputs=func_data.get("outputs", []),
                characters_involved=func_data.get("characters_involved", []),
                requirements_satisfied=func_data.get("requirements_satisfied", []),
                allocated_chapter=func_data.get("allocated_chapter"),
                estimated_pages=func_data.get("estimated_pages", 1.0),
            )
            analyzer.functions[func.id] = func

        # Restore chapters
        for ch_data in data.get("chapters", []):
            ch = ChapterAllocation(
                chapter_number=ch_data["chapter_number"],
                title=ch_data.get("title", ""),
                pov_character=ch_data.get("pov_character"),
                subplot=ch_data.get("subplot", "main"),
                allocated_functions=ch_data.get("allocated_functions", []),
                target_pages=ch_data.get("target_pages", 20),
                emotional_arc=ch_data.get("emotional_arc", ""),
            )
            analyzer.chapters[ch.chapter_number] = ch

        # Restore flows
        for flow_data in data.get("flows", []):
            flow = FunctionalFlow(
                id=flow_data["id"],
                name=flow_data["name"],
                flow_type=flow_data["flow_type"],
                functions=flow_data["functions"],
                entry_point=flow_data["entry_point"],
                exit_points=flow_data["exit_points"],
                decision_points=flow_data.get("decision_points", []),
            )
            analyzer.flows[flow.id] = flow

        return analyzer


def create_narrative_from_premise(
    premise: str, genre: str, num_chapters: int = 20
) -> tuple[NarrativeFunctionalAnalyzer, NarrativeDAG]:
    """
    High-level function to create a narrative from a premise using functional analysis.

    This follows the full systems engineering workflow:
    1. Extract requirements from genre and premise
    2. Decompose requirements into atomic functions
    3. Allocate functions to chapters
    4. Convert to NarrativeDAG
    """
    analyzer = NarrativeFunctionalAnalyzer()

    # Step 1: Extract genre requirements
    analyzer.extract_requirements_from_genre(genre)

    # Step 2: Add premise-specific requirement
    analyzer.add_requirement(
        description=f"Deliver on premise: {premise}",
        function_type=NarrativeFunctionType.RESOLVE_CONFLICT,
        priority=1,
        source="premise",
    )

    # Step 3: Decompose all requirements
    for req_id in list(analyzer.requirements.keys()):
        analyzer.decompose_requirement(req_id)

    # Step 4: Create chapters
    for i in range(1, num_chapters + 1):
        analyzer.add_chapter(i, title=f"Chapter {i}")

    # Step 5: Auto-allocate functions to chapters
    analyzer.auto_allocate(AllocationStrategy.CHRONOLOGICAL)

    # Step 6: Convert to DAG
    dag = analyzer.to_narrative_dag(title=premise[:50])

    return analyzer, dag
