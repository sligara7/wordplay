# Narrative DAG Module
# Tools for creating, analyzing, and generating book/novel plot structures

from .narrative_dag import (
    NodeType,
    EdgeType,
    PlotNode,
    NarrativeDAG,
    NarrativeMetrics,
)
from .genre_templates import GenreTemplate, GENRE_TEMPLATES, get_template, list_templates
from .analyzers import NarrativeAnalyzer, StructuralDiagnosis, compare_narratives
from .gap_discovery import (
    LinkingStrategy,
    NarrativeGap,
    CharacterGel,
    SpinoffSeed,
    NarrativeGapDetector,
    CharacterGelAnalyzer,
    SpinoffGenerator,
    NarrativeMerger,
    suggest_gap_closure,
)
from .reflow_integration import (
    ReflowExporter,
    ReflowImporter,
    export_narrative_to_reflow,
    import_narrative_from_reflow,
    analyze_narrative_with_reflow,
)
from .functional_analysis import (
    NarrativeFunctionType,
    NarrativeRequirement,
    AtomicFunction,
    ChapterAllocation,
    AllocationStrategy,
    FunctionalFlow,
    NarrativeFunctionalAnalyzer,
    create_narrative_from_premise,
)

__all__ = [
    # Core data structures
    "NodeType",
    "EdgeType",
    "PlotNode",
    "NarrativeDAG",
    "NarrativeMetrics",
    # Templates
    "GenreTemplate",
    "GENRE_TEMPLATES",
    "get_template",
    "list_templates",
    # Analysis
    "NarrativeAnalyzer",
    "StructuralDiagnosis",
    "compare_narratives",
    # Gap Discovery & Resolution
    "LinkingStrategy",
    "NarrativeGap",
    "CharacterGel",
    "SpinoffSeed",
    "NarrativeGapDetector",
    "CharacterGelAnalyzer",
    "SpinoffGenerator",
    "NarrativeMerger",
    "suggest_gap_closure",
    # Reflow Integration
    "ReflowExporter",
    "ReflowImporter",
    "export_narrative_to_reflow",
    "import_narrative_from_reflow",
    "analyze_narrative_with_reflow",
    # Functional Analysis
    "NarrativeFunctionType",
    "NarrativeRequirement",
    "AtomicFunction",
    "ChapterAllocation",
    "AllocationStrategy",
    "FunctionalFlow",
    "NarrativeFunctionalAnalyzer",
    "create_narrative_from_premise",
]
