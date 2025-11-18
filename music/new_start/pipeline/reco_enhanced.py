"""
Enhanced MIDI-to-WAV Synthesis using Realistic Instrument Models

Integrates synthesize_instruments into reco.py architecture:
- Keeps reco.py's time-placement and scaling framework
- Replaces Fourier synthesis with realistic instrument synthesis
- Supports: strings, brass, woodwinds, percussion

Architecture:
1. Parse MIDI → notes, timing, velocity (reco.py parser)
2. Generate instrument-specific signals (synthesize_instruments)
3. Scale by velocity (reco.py approach)
4. Place in time (reco.py approach)
5. Sum all signals (reco.py approach)
"""

import numpy as np
import mido
import sys
import os

# Add paths for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
midi_to_wav_dir = os.path.join(parent_dir, 'midi_to_wav')
synth_dir = os.path.join(midi_to_wav_dir, 'synthesize_instruments')

sys.path.insert(0, midi_to_wav_dir)
sys.path.insert(0, synth_dir)

try:
    from synthesize_string_instruments import StringInstrumentSynthesizer
    from synthesize_brass import BrassSynthesizer
    from synthesize_woodwind import WoodwindSynthesizer
    from synthesize_common_percussion import PercussionSynthesizer
    SYNTH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import synthesize_instruments: {e}")
    print(f"Falling back to simple synthesis only")
    SYNTH_AVAILABLE = False
    # Define dummy classes
    class StringInstrumentSynthesizer:
        def __init__(self, **kwargs): pass
        def is_string_instrument(self, program): return False
    class BrassSynthesizer:
        def __init__(self, **kwargs): pass
    class WoodwindSynthesizer:
        def __init__(self, **kwargs): pass
    class PercussionSynthesizer:
        def __init__(self, **kwargs): pass


class InstrumentSynthesizer:
    """
    Unified interface for all instrument synthesizers.
    Routes MIDI program numbers to appropriate synthesizer.
    """

    def __init__(self, sample_rate=44100):
        """Initialize all instrument synthesizers."""
        self.sample_rate = sample_rate
        self.synth_available = SYNTH_AVAILABLE

        # Initialize synthesizers
        if SYNTH_AVAILABLE:
            self.string_synth = StringInstrumentSynthesizer(sample_rate=sample_rate)
            self.brass_synth = BrassSynthesizer(sample_rate=sample_rate)
            self.woodwind_synth = WoodwindSynthesizer(sample_rate=sample_rate)
            self.percussion_synth = PercussionSynthesizer(sample_rate=sample_rate)
        else:
            # Use dummy instances
            self.string_synth = None
            self.brass_synth = None
            self.woodwind_synth = None
            self.percussion_synth = None

        # MIDI program number ranges (GM standard)
        self.program_map = {
            'piano': range(1, 9),       # 1-8: Pianos
            'chromatic': range(9, 17),  # 9-16: Chromatic Percussion
            'organ': range(17, 25),     # 17-24: Organs
            'guitar': range(25, 33),    # 25-32: Guitars
            'bass': range(33, 41),      # 33-40: Bass
            'strings': range(41, 49),   # 41-48: Strings
            'ensemble': range(49, 57),  # 49-56: Ensemble
            'brass': range(57, 65),     # 57-64: Brass
            'reed': range(65, 73),      # 65-72: Reed (woodwinds)
            'pipe': range(73, 81),      # 73-80: Pipe (woodwinds)
            'synth_lead': range(81, 89),   # 81-88: Synth Lead
            'synth_pad': range(89, 97),    # 89-96: Synth Pad
            'synth_effects': range(97, 105),  # 97-104: Synth Effects
            'ethnic': range(105, 113),  # 105-112: Ethnic
            'percussive': range(113, 121),  # 113-120: Percussive
            'sound_effects': range(121, 129),  # 121-128: Sound Effects
        }

    def get_synthesizer_for_program(self, program):
        """
        Determine which synthesizer to use for a given MIDI program.

        Args:
            program: MIDI program number (1-128)

        Returns:
            (synthesizer, fallback_to_simple)
        """
        # If synthesizers not available, always use fallback
        if not self.synth_available:
            return None, True

        # Check specific synthesizers
        if self.string_synth and self.string_synth.is_string_instrument(program):
            return self.string_synth, False

        if self.brass_synth and hasattr(self.brass_synth, 'is_brass_instrument') and self.brass_synth.is_brass_instrument(program):
            return self.brass_synth, False

        if self.woodwind_synth and hasattr(self.woodwind_synth, 'is_woodwind_instrument') and self.woodwind_synth.is_woodwind_instrument(program):
            return self.woodwind_synth, False

        # For now, use simple sine synthesis for other instruments
        # This maintains compatibility while we expand instrument coverage
        return None, True

    def generate_note(self, program, midi_note, velocity, duration):
        """
        Generate audio for a single note using appropriate synthesizer.

        Args:
            program: MIDI program number
            midi_note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
            duration: Duration in seconds

        Returns:
            numpy array of audio samples (float32, normalized to [-1, 1])
        """
        synth, use_fallback = self.get_synthesizer_for_program(program)

        if use_fallback:
            # Simple sine wave fallback (like original reco.py)
            return self._generate_simple_note(midi_note, velocity, duration)

        # Use instrument-specific synthesizer
        try:
            if synth == self.string_synth:
                signal = synth.create_string_note(
                    instrument=program,
                    note=midi_note,
                    velocity=velocity,
                    duration=duration
                )
            elif synth == self.brass_synth:
                signal = synth.create_brass_note(
                    instrument=program,
                    note=midi_note,
                    velocity=velocity,
                    duration=duration
                )
            elif synth == self.woodwind_synth:
                signal = synth.create_woodwind_note(
                    instrument=program,
                    note=midi_note,
                    velocity=velocity,
                    duration=duration
                )
            else:
                # Should not reach here
                signal = self._generate_simple_note(midi_note, velocity, duration)

            # Convert from int16 to float32 normalized
            signal = signal.astype(np.float32) / 32767.0

            return signal

        except Exception as e:
            print(f"Warning: Synthesis failed for program {program}, using fallback. Error: {e}")
            return self._generate_simple_note(midi_note, velocity, duration)

    def _generate_simple_note(self, midi_note, velocity, duration):
        """
        Simple sine wave synthesis (fallback for unsupported instruments).

        Mimics original reco.py Fourier synthesis.
        """
        # Calculate frequency
        frequency = 440.0 * 2 ** ((midi_note - 69) / 12.0)

        # Generate time array
        num_samples = int(duration * self.sample_rate)

        # Handle very short or zero duration
        if num_samples <= 0:
            return np.zeros(1, dtype=np.float32)

        t = np.arange(num_samples) / self.sample_rate

        # Simple sine wave with harmonics (like original reco.py)
        signal = np.zeros(num_samples, dtype=np.float32)

        # Fundamental + 3 harmonics
        for k in range(1, 5):
            amplitude = 1.0 / k  # Diminishing harmonics
            signal += amplitude * np.sin(2 * np.pi * k * frequency * t)

        # Normalize (only if signal has content)
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val

        # Apply velocity scaling
        signal = signal * (velocity / 127.0)

        # Apply envelope (ADSR-like)
        envelope = np.ones_like(signal)

        # Attack (10ms)
        attack_samples = int(0.01 * self.sample_rate)
        if attack_samples > 0 and attack_samples < len(envelope):
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Release (50ms at end)
        release_samples = int(0.05 * self.sample_rate)
        if release_samples > 0 and release_samples < len(envelope):
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)

        signal = signal * envelope

        return signal


class EnhancedMidiIO:
    """
    Enhanced MIDI-to-audio converter using realistic instrument synthesis.

    Maintains reco.py's time-placement architecture but uses
    synthesize_instruments for sound generation.
    """

    def __init__(self, sample_rate=44100, max_value=32767):
        """
        Initialize enhanced MIDI converter.

        Args:
            sample_rate: Audio sample rate in Hz
            max_value: Maximum amplitude value (for int16 PCM)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value
        self.min_value = -max_value

        # Initialize instrument synthesizer
        self.instrument_synth = InstrumentSynthesizer(sample_rate=sample_rate)

        # MIDI parsing state
        self.notes = []
        self.instruments = {}  # channel -> program mapping
        self.tempo = 500000  # Default tempo (120 BPM)
        self.ticks_per_beat = 480
        self.duration = 0.0

    def parse_midi(self, midi_path):
        """
        Parse MIDI file to extract notes and timing.

        Args:
            midi_path: Path to MIDI file
        """
        mid = mido.MidiFile(midi_path)
        self.ticks_per_beat = mid.ticks_per_beat

        # Track note on/off events
        active_notes = {}  # (channel, note) -> (start_time, velocity)
        current_time = 0.0

        # Default instrument for each channel (0 = piano)
        for ch in range(16):
            self.instruments[ch] = 1  # Acoustic Grand Piano

        # Process all tracks
        for track in mid.tracks:
            track_time = 0

            for msg in track:
                # Update time
                delta_ticks = msg.time
                delta_seconds = mido.tick2second(delta_ticks, self.ticks_per_beat, self.tempo)
                track_time += delta_seconds
                current_time = max(current_time, track_time)

                # Handle messages
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Note start
                    key = (msg.channel, msg.note)
                    active_notes[key] = (track_time, msg.velocity)

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Note end
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        start_time, velocity = active_notes[key]
                        duration = track_time - start_time

                        self.notes.append({
                            'channel': msg.channel,
                            'note': msg.note,
                            'velocity': velocity,
                            'start_time': start_time,
                            'duration': duration,
                            'program': self.instruments[msg.channel]
                        })

                        del active_notes[key]

                elif msg.type == 'program_change':
                    # Instrument change
                    self.instruments[msg.channel] = msg.program + 1  # MIDI programs are 0-127, GM is 1-128

                elif msg.type == 'set_tempo':
                    # Tempo change
                    self.tempo = msg.tempo

        # Calculate total duration
        if self.notes:
            self.duration = max(note['start_time'] + note['duration'] for note in self.notes)
        else:
            self.duration = current_time

        print(f"Parsed MIDI: {len(self.notes)} notes, duration: {self.duration:.2f}s")

    def synthesize(self):
        """
        Synthesize audio from parsed MIDI notes.

        Uses reco.py's approach:
        1. Create output buffer
        2. Generate each note's signal
        3. Place signal at correct time
        4. Sum overlapping signals

        Returns:
            Stereo audio as int16 numpy array (samples, 2)
        """
        # Create output buffer (add 1 second padding)
        num_samples = int((self.duration + 1.0) * self.sample_rate)
        audio = np.zeros(num_samples, dtype=np.float32)

        print(f"Synthesizing {len(self.notes)} notes...")

        # Process each note
        for i, note in enumerate(self.notes):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(self.notes)} notes...")

            # Generate note signal
            signal = self.instrument_synth.generate_note(
                program=note['program'],
                midi_note=note['note'],
                velocity=note['velocity'],
                duration=note['duration']
            )

            # Calculate placement indices
            start_idx = int(note['start_time'] * self.sample_rate)
            end_idx = start_idx + len(signal)

            # Ensure we don't exceed buffer
            if end_idx > len(audio):
                signal = signal[:len(audio) - start_idx]
                end_idx = len(audio)

            # Add to output buffer (mix)
            audio[start_idx:end_idx] += signal

        # Normalize and scale to int16 range (like reco.py)
        audio = self._normalize_and_scale(audio)

        # Convert to stereo
        audio_stereo = np.column_stack([audio, audio])

        return audio_stereo

    def _normalize_and_scale(self, audio):
        """
        Normalize audio and scale to int16 range (reco.py approach).

        Args:
            audio: Float32 audio array

        Returns:
            Int16 audio array
        """
        # Find max absolute value
        max_val = np.max(np.abs(audio))

        if max_val > 0:
            # Normalize to [-1, 1]
            audio = audio / max_val

            # Scale to int16 range with 90% headroom (prevent clipping)
            audio = audio * self.max_value * 0.9

        # Clip and convert to int16
        audio = np.clip(audio, self.min_value, self.max_value)
        audio = audio.astype(np.int16)

        return audio

    def midi_to_audio(self, midi_path):
        """
        Complete MIDI-to-audio conversion.

        Args:
            midi_path: Path to MIDI file

        Returns:
            Stereo audio as int16 numpy array
        """
        self.parse_midi(midi_path)
        audio = self.synthesize()
        return audio


def midi_to_wav(midi_path, wav_path, verbose=False, sample_rate=44100):
    """
    Convert MIDI to WAV using enhanced instrument synthesis.

    Compatible with reco.py API.

    Args:
        midi_path: Input MIDI file path
        wav_path: Output WAV file path
        verbose: Print progress
        sample_rate: Sample rate in Hz

    Returns:
        Path to created WAV file
    """
    from scipy.io.wavfile import write

    if verbose:
        print("="*80)
        print("Enhanced MIDI-to-WAV Conversion")
        print("="*80)
        print(f"Input:  {midi_path}")
        print(f"Output: {wav_path}")
        print()

    # Create converter
    converter = EnhancedMidiIO(sample_rate=sample_rate)

    # Convert
    audio = converter.midi_to_audio(midi_path)

    # Write WAV
    write(wav_path, sample_rate, audio)

    if verbose:
        duration = len(audio) / sample_rate
        print()
        print(f"✓ Conversion complete!")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Channels: 2 (stereo)")
        print("="*80)

    return wav_path


if __name__ == "__main__":
    print("Enhanced MIDI-to-WAV Synthesis")
    print("Uses realistic instrument models from synthesize_instruments")
