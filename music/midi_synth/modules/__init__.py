"""
Modular MIDI Synthesizer Components

Separation of concerns:
- midi_parser.py: MIDI file parsing
- controller_manager.py: MIDI controller state tracking
- instrument_engine.py: Sound synthesis
- effects_processor.py: Audio effects
- audio_mixer.py: Mix notes with timing
- master_processor.py: Final limiting/normalization

Usage:
    from modules import MIDIParser, ControllerManager, InstrumentEngine
    from modules import EffectsProcessor, AudioMixer, MasterProcessor

    # Or use the main orchestrator:
    from modules.synthesizer import MIDISynthesizer
"""

from .midi_parser import MIDIParser
from .controller_manager import ControllerManager
from .instrument_engine import InstrumentEngine
from .effects_processor import EffectsProcessor
from .audio_mixer import AudioMixer
from .master_processor import MasterProcessor

__all__ = [
    'MIDIParser',
    'ControllerManager',
    'InstrumentEngine',
    'EffectsProcessor',
    'AudioMixer',
    'MasterProcessor',
]
