"""
Structural Rorschach - Cross-Domain Graph Analysis

A system for finding structural resonances across domains (images, music, text)
by comparing graph topologies rather than semantic content.

Inspired by:
- Synesthesia: Cross-sensory perception
- Rorschach inkblot test: Structural interpretation

Core concept: Any structured data can be the "inkblot" that the system
interprets through other domain corpora by matching graph patterns.
"""

from .signature import StructuralSignature, Resonance
from .extractor import SignatureExtractor
from .motifs import MotifDetector

__version__ = "0.1.0"
__all__ = [
    "StructuralSignature",
    "Resonance",
    "SignatureExtractor",
    "MotifDetector",
]
