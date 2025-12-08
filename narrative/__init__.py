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
]
