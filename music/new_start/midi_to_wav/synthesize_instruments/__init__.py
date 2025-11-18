"""
Instrument Synthesis Package

This package provides synthesizer classes for various instrument families including
percussion, woodwinds, brass, and string instruments.
"""

from .synthesize_common_percussion import PercussionSynthesizer
from .synthesize_woodwind import WoodwindSynthesizer
from .synthesize_brass import BrassSynthesizer  # Assuming this class exists
from .synthesize_string_instruments import StringInstrumentSynthesizer  # Assuming this class exists
from .audio_effects import apply_effects, EffectType  # Assuming these exist

__all__ = [
    'PercussionSynthesizer',
    'WoodwindSynthesizer',
    'BrassSynthesizer',
    'StringInstrumentSynthesizer',
    'apply_effects',
    'EffectType'
]