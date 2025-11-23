"""
Instrument Engine Module

Responsibility: Generate sound for individual notes

Input: MIDI note number, velocity, duration, instrument program
Output: Audio waveform for that note
"""

import numpy as np
from typing import Optional
import sys
from pathlib import Path

# Import synthesizers if available
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'new_start' / 'midi_to_wav'))
    from synthesize_instruments import (
        PercussionSynthesizer,
        BrassSynthesizer,
        StringInstrumentSynthesizer,
    )
    SYNTH_AVAILABLE = True
except ImportError:
    SYNTH_AVAILABLE = False


class InstrumentEngine:
    """
    Generate audio for individual notes based on instrument.

    Supports:
    - General MIDI program numbers (0-127)
    - Randomized harmonics (like reco.py)
    - Physics-based models (inharmonicity for piano)
    - Family-specific characteristics
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize instrument engine.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.max_value = 32767

        # Initialize external synthesizers if available
        if SYNTH_AVAILABLE:
            self.percussion = PercussionSynthesizer(sample_rate, self.max_value)
            self.brass = BrassSynthesizer(sample_rate, self.max_value)
            self.strings = StringInstrumentSynthesizer(sample_rate, self.max_value)
        else:
            self.percussion = None
            self.brass = None
            self.strings = None

        # GM program to family mapping
        self.program_families = self._build_program_families()

        # Cache for randomized harmonic structures (like reco.py)
        self.harmonic_cache = {}

    def _build_program_families(self) -> dict:
        """Map GM program numbers to instrument families."""
        families = {}
        for p in range(0, 8): families[p] = 'piano'
        for p in range(8, 16): families[p] = 'chromatic_percussion'
        for p in range(16, 24): families[p] = 'organ'
        for p in range(24, 32): families[p] = 'guitar'
        for p in range(32, 40): families[p] = 'bass'
        for p in range(40, 48): families[p] = 'strings'
        for p in range(48, 56): families[p] = 'ensemble'
        for p in range(56, 64): families[p] = 'brass'
        for p in range(64, 72): families[p] = 'reed'
        for p in range(72, 80): families[p] = 'pipe'
        for p in range(80, 88): families[p] = 'synth_lead'
        for p in range(88, 96): families[p] = 'synth_pad'
        for p in range(96, 104): families[p] = 'synth_fx'
        for p in range(104, 112): families[p] = 'ethnic'
        for p in range(112, 120): families[p] = 'percussive'
        for p in range(120, 128): families[p] = 'sound_fx'
        return families

    def synthesize_note(self, midi_note: float, velocity: int,
                       duration: float, program: int = 0,
                       channel: int = 0) -> np.ndarray:
        """
        Synthesize a single note.

        Args:
            midi_note: MIDI note number (can be fractional for pitch bend)
            velocity: Velocity (0-127)
            duration: Duration in seconds
            program: MIDI program number (0-127)
            channel: MIDI channel (0-15), channel 9 = percussion

        Returns:
            Audio waveform as float32 array [-1.0, 1.0]
        """
        # Channel 9 is always percussion in GM
        if channel == 9:
            audio = self._synthesize_percussion(int(midi_note), velocity, duration)
        else:
            # Get instrument family
            family = self.program_families.get(program, 'piano')

            # Use external synthesizers if available
            if family == 'brass' and self.brass is not None:
                audio = self._synth_brass(midi_note, velocity, duration, program)

            elif family in ['strings', 'guitar', 'bass'] and self.strings is not None:
                audio = self._synth_strings(midi_note, velocity, duration)

            elif family == 'piano':
                audio = self._synth_piano(midi_note, velocity, duration)

            elif family == 'organ':
                audio = self._synth_organ(midi_note, velocity, duration)

            elif family in ['reed', 'pipe']:
                audio = self._synth_woodwind(midi_note, velocity, duration)

            elif family in ['synth_lead', 'synth_pad']:
                audio = self._synth_synth(midi_note, velocity, duration, family)

            else:
                # Fallback: generic harmonic synthesis
                audio = self._synth_generic(midi_note, velocity, duration)

        # Ensure output is within [-1.0, 1.0]
        peak = np.max(np.abs(audio))
        if peak > 1.0:
            audio = audio / peak

        return audio

    def _synthesize_percussion(self, midi_note: int, velocity: int,
                              duration: float) -> np.ndarray:
        """Synthesize percussion note."""
        if self.percussion is not None:
            audio_int16 = self.percussion.synthesize_midi_percussion(
                midi_note, velocity, duration
            )
            return audio_int16.astype(np.float32) / self.max_value
        else:
            # Fallback: simple noise burst
            samples = int(duration * self.sample_rate)
            noise = np.random.uniform(-1, 1, samples)
            envelope = np.exp(-10 * np.arange(samples) / self.sample_rate)
            return noise * envelope * (velocity / 127.0)

    def _synth_brass(self, midi_note: float, velocity: int,
                    duration: float, program: int) -> np.ndarray:
        """Synthesize brass using external synthesizer."""
        try:
            base_note = int(round(midi_note))
            audio_int16 = self.brass.synthesize_note(base_note, velocity, duration, program)
            audio = audio_int16.astype(np.float32) / self.max_value

            # Apply pitch shift if needed (for pitch bend)
            if abs(midi_note - base_note) > 0.01:
                ratio = 2 ** ((midi_note - base_note) / 12.0)
                audio = self._pitch_shift(audio, ratio)

            return audio
        except (AttributeError, TypeError):
            # Fallback to generic synthesis if external synth doesn't work
            return self._synth_generic(midi_note, velocity, duration)

    def _synth_strings(self, midi_note: float, velocity: int,
                      duration: float) -> np.ndarray:
        """Synthesize strings using external synthesizer."""
        try:
            base_note = int(round(midi_note))
            audio_int16 = self.strings.synthesize_note(base_note, velocity, duration)
            audio = audio_int16.astype(np.float32) / self.max_value

            # Apply pitch shift if needed
            if abs(midi_note - base_note) > 0.01:
                ratio = 2 ** ((midi_note - base_note) / 12.0)
                audio = self._pitch_shift(audio, ratio)

            return audio
        except (AttributeError, TypeError):
            # Fallback to generic synthesis if external synth doesn't work
            return self._synth_generic(midi_note, velocity, duration)

    def _synth_piano(self, midi_note: float, velocity: int,
                    duration: float) -> np.ndarray:
        """
        Synthesize piano with physical modeling (inharmonicity).

        Uses randomized harmonics like reco.py + inharmonicity.
        """
        freq = 440.0 * 2**((midi_note - 69) / 12.0)
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate
        amp = velocity / 127.0

        # Get or create randomized harmonic structure
        note_int = int(round(midi_note))
        if note_int not in self.harmonic_cache:
            self.harmonic_cache[note_int] = self._generate_random_harmonics()

        coefs, phases, h_nums = self.harmonic_cache[note_int]

        # Inharmonicity coefficient (higher for lower notes)
        B = 0.0001 * (88 - note_int) / 88.0 + 0.00005

        # Generate harmonics
        audio = np.zeros(samples, dtype=np.float32)

        for i, (coef, phase, h) in enumerate(zip(coefs, phases, h_nums)):
            # Inharmonic frequency
            f_h = freq * h * np.sqrt(1 + B * h**2)

            # Add harmonic
            audio += amp * coef * np.sin(2 * np.pi * f_h * t + phase)

        # Piano envelope
        envelope = self._piano_envelope(samples, velocity, note_int)
        audio *= envelope

        return audio

    def _synth_organ(self, midi_note: float, velocity: int,
                    duration: float) -> np.ndarray:
        """Synthesize organ with strong octaves."""
        freq = 440.0 * 2**((midi_note - 69) / 12.0)
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate
        amp = velocity / 127.0

        # Organ harmonics: strong fundamental and octaves
        audio = np.zeros(samples, dtype=np.float32)
        harmonics = [1, 2, 4, 8]
        weights = [1.0, 0.8, 0.6, 0.4]

        for h, w in zip(harmonics, weights):
            audio += amp * w * np.sin(2 * np.pi * freq * h * t)

        # Organ envelope: instant attack, sustained, quick release
        envelope = np.ones(samples)
        release_samples = int(0.05 * self.sample_rate)
        if release_samples > 0 and samples > release_samples:
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)

        audio *= envelope

        return audio

    def _synth_woodwind(self, midi_note: float, velocity: int,
                       duration: float) -> np.ndarray:
        """Synthesize woodwinds with odd harmonics."""
        freq = 440.0 * 2**((midi_note - 69) / 12.0)
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate
        amp = velocity / 127.0

        # Woodwinds: odd harmonics dominant
        audio = np.zeros(samples, dtype=np.float32)
        harmonics = [1, 3, 5, 7, 9]
        weights = [1.0, 0.5, 0.3, 0.2, 0.1]

        for h, w in zip(harmonics, weights):
            audio += amp * w * np.sin(2 * np.pi * freq * h * t)

        # ADSR envelope
        envelope = self._adsr_envelope(samples, 0.02, 0.1, 0.7, 0.2, duration)
        audio *= envelope

        return audio

    def _synth_synth(self, midi_note: float, velocity: int,
                    duration: float, family: str) -> np.ndarray:
        """Synthesize synth lead/pad with many harmonics."""
        freq = 440.0 * 2**((midi_note - 69) / 12.0)
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate
        amp = velocity / 127.0

        # Synth: bright with many harmonics
        audio = np.zeros(samples, dtype=np.float32)
        num_harmonics = 12

        for h in range(1, num_harmonics + 1):
            weight = 1.0 / (h * 0.8)
            audio += amp * weight * np.sin(2 * np.pi * freq * h * t)

        # Envelope varies by family
        if family == 'synth_pad':
            # Pad: slow attack, long sustain
            envelope = self._adsr_envelope(samples, 0.1, 0.2, 0.9, 0.5, duration)
        else:
            # Lead: fast attack, moderate sustain
            envelope = self._adsr_envelope(samples, 0.01, 0.05, 0.7, 0.1, duration)

        audio *= envelope

        return audio

    def _synth_generic(self, midi_note: float, velocity: int,
                      duration: float) -> np.ndarray:
        """Generic harmonic synthesis fallback."""
        freq = 440.0 * 2**((midi_note - 69) / 12.0)
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate
        amp = velocity / 127.0

        audio = np.zeros(samples, dtype=np.float32)

        for h in range(1, 9):
            audio += amp / h * np.sin(2 * np.pi * freq * h * t)

        envelope = self._adsr_envelope(samples, 0.02, 0.1, 0.7, 0.2, duration)
        audio *= envelope

        return audio

    def _generate_random_harmonics(self, max_harm: int = 11):
        """
        Generate randomized harmonic structure (like reco.py).

        Returns:
            (coefficients, phases, harmonic_numbers)
        """
        r = np.random.randint(2, max_harm + 1)
        x = np.arange(0, max_harm + 1)
        y = -0.81 * x / max_harm + 1
        h = np.random.uniform(-0.97, 0.97, max_harm)
        y[1:] = y[1:] * h
        coef = y[:r]
        phase = np.random.uniform(-np.pi/2, np.pi/2, r)
        f = (x[:r] + 1)

        return coef, phase, f

    def _piano_envelope(self, samples: int, velocity: int, midi_note: int) -> np.ndarray:
        """Piano-specific envelope."""
        sr = self.sample_rate

        # Attack varies with velocity
        attack_time = 0.001 + (127 - velocity) / 127.0 * 0.01
        attack_samples = int(attack_time * sr)

        # Decay varies with note
        decay_rate = 2.0 + (midi_note - 21) / 88.0 * 3.0

        envelope = np.zeros(samples)

        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        decay_samples = samples - attack_samples
        if decay_samples > 0:
            t_decay = np.arange(decay_samples) / sr
            envelope[attack_samples:] = np.exp(-decay_rate * t_decay)

        return envelope

    def _adsr_envelope(self, samples: int, attack: float, decay: float,
                      sustain: float, release: float, duration: float) -> np.ndarray:
        """ADSR envelope."""
        sr = self.sample_rate
        attack_samples = int(attack * sr)
        decay_samples = int(decay * sr)
        release_samples = int(release * sr)
        sustain_samples = samples - attack_samples - decay_samples - release_samples

        if sustain_samples < 0:
            sustain_samples = 0

        parts = []
        if attack_samples > 0:
            parts.append(np.linspace(0, 1, attack_samples))
        if decay_samples > 0:
            parts.append(np.linspace(1, sustain, decay_samples))
        if sustain_samples > 0:
            parts.append(np.ones(sustain_samples) * sustain)
        if release_samples > 0:
            parts.append(np.linspace(sustain, 0, release_samples))

        envelope = np.concatenate(parts) if parts else np.array([])

        if len(envelope) > samples:
            envelope = envelope[:samples]
        elif len(envelope) < samples:
            envelope = np.pad(envelope, (0, samples - len(envelope)))

        return envelope

    def _pitch_shift(self, audio: np.ndarray, ratio: float) -> np.ndarray:
        """Pitch shift via resampling."""
        if abs(ratio - 1.0) < 0.001:
            return audio

        num_samples = int(len(audio) / ratio)
        indices = np.linspace(0, len(audio) - 1, num_samples)
        shifted = np.interp(indices, np.arange(len(audio)), audio)

        if len(shifted) > len(audio):
            shifted = shifted[:len(audio)]
        elif len(shifted) < len(audio):
            shifted = np.pad(shifted, (0, len(audio) - len(shifted)))

        return shifted
