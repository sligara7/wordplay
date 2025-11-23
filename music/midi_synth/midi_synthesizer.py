#!/usr/bin/env python3
"""
MIDI to WAV Synthesizer for Pipeline2

Synthesizes MIDI files to WAV audio using the synthesize_instruments package.
This provides clean, controlled audio with known ground truth for MHT validation.

Unlike reco.py which uses external percussion samples, this uses pure synthesis.
"""

import sys
import numpy as np
import mido
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy.io import wavfile

# Import synthesizers from the synthesize_instruments package
sys.path.insert(0, str(Path(__file__).parent.parent / 'midi_to_wav'))
from synthesize_instruments import (
    PercussionSynthesizer,
    BrassSynthesizer,
    StringInstrumentSynthesizer,
    # WoodwindSynthesizer,  # Add when needed
)


class MIDISynthesizer:
    """
    Synthesize MIDI files to WAV audio using pure synthesis.

    Uses the synthesize_instruments package for all instruments:
    - Percussion: PercussionSynthesizer
    - Brass: BrassSynthesizer
    - Strings: StringInstrumentSynthesizer
    - Woodwinds: WoodwindSynthesizer (TODO)
    - Piano/Keys: Simple harmonic synthesis (TODO)
    """

    def __init__(self, sample_rate=44100, max_value=32767):
        """
        Initialize MIDI synthesizer.

        Args:
            sample_rate: Audio sample rate in Hz
            max_value: Maximum amplitude value (16-bit PCM)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value

        # Initialize instrument synthesizers
        self.percussion = PercussionSynthesizer(sample_rate, max_value)
        self.brass = BrassSynthesizer(sample_rate, max_value)
        self.strings = StringInstrumentSynthesizer(sample_rate, max_value)
        # self.woodwinds = WoodwindSynthesizer(sample_rate, max_value)

        # MIDI program to instrument family mapping
        # Based on General MIDI specification
        self.program_families = self._build_program_families()

    def _build_program_families(self) -> Dict[int, str]:
        """Build mapping from MIDI program number to instrument family."""
        families = {}

        # Programs 0-7: Piano
        for p in range(0, 8):
            families[p] = 'piano'

        # Programs 8-15: Chromatic Percussion
        for p in range(8, 16):
            families[p] = 'chromatic_percussion'

        # Programs 16-23: Organ
        for p in range(16, 24):
            families[p] = 'organ'

        # Programs 24-31: Guitar
        for p in range(24, 32):
            families[p] = 'guitar'

        # Programs 32-39: Bass
        for p in range(32, 40):
            families[p] = 'bass'

        # Programs 40-47: Strings
        for p in range(40, 48):
            families[p] = 'strings'

        # Programs 48-55: Ensemble
        for p in range(48, 56):
            families[p] = 'ensemble'

        # Programs 56-63: Brass
        for p in range(56, 64):
            families[p] = 'brass'

        # Programs 64-71: Reed (Woodwinds)
        for p in range(64, 72):
            families[p] = 'reed'

        # Programs 72-79: Pipe (Woodwinds)
        for p in range(72, 80):
            families[p] = 'pipe'

        # Programs 80-87: Synth Lead
        for p in range(80, 88):
            families[p] = 'synth_lead'

        # Programs 88-95: Synth Pad
        for p in range(88, 96):
            families[p] = 'synth_pad'

        # Programs 96-103: Synth Effects
        for p in range(96, 104):
            families[p] = 'synth_fx'

        # Programs 104-111: Ethnic
        for p in range(104, 112):
            families[p] = 'ethnic'

        # Programs 112-119: Percussive
        for p in range(112, 120):
            families[p] = 'percussive'

        # Programs 120-127: Sound Effects
        for p in range(120, 128):
            families[p] = 'sound_fx'

        return families

    def synthesize_from_file(self, midi_path: str,
                           output_wav: Optional[str] = None,
                           verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Synthesize MIDI file to WAV audio.

        Args:
            midi_path: Path to MIDI file
            output_wav: Optional path to save WAV file
            verbose: Print progress

        Returns:
            (audio, midi_data) where:
                audio: Synthesized audio as float32 array [-1.0, 1.0]
                midi_data: Dict with MIDI information (notes, timing, chords)
        """
        midi_path = Path(midi_path)

        if verbose:
            print("=" * 80)
            print("MIDI TO WAV SYNTHESIS (Pipeline2)")
            print("=" * 80)
            print(f"Input:  {midi_path}")
            if output_wav:
                print(f"Output: {output_wav}")
            print()

        # Parse MIDI file
        if verbose:
            print("[1/3] Parsing MIDI file...")

        midi_data = self._parse_midi(midi_path)

        if verbose:
            print(f"  Duration: {midi_data['duration']:.2f}s")
            print(f"  Tempo: {midi_data['tempo_bpm']:.1f} BPM")
            print(f"  Total notes: {len(midi_data['notes'])}")
            print(f"  Tracks: {len(midi_data['tracks'])}")
            print()

        # Synthesize audio
        if verbose:
            print("[2/3] Synthesizing audio...")

        audio = self._synthesize_notes(midi_data['notes'], midi_data['duration'], verbose)

        if verbose:
            print(f"  Audio shape: {audio.shape}")
            print(f"  Sample rate: {self.sample_rate} Hz")
            print(f"  Max amplitude: {np.max(np.abs(audio)):.3f}")
            print()

        # Save to WAV if requested
        if output_wav:
            if verbose:
                print("[3/3] Saving WAV file...")

            self._save_wav(audio, output_wav)

            if verbose:
                print(f"  ✓ Saved: {output_wav}")
                print()

        if verbose:
            print("=" * 80)
            print(f"Synthesis complete: {len(midi_data['notes'])} notes → audio")
            print("=" * 80)

        return audio, midi_data

    def _parse_midi(self, midi_path: Path) -> Dict:
        """
        Parse MIDI file and extract note information.

        Returns:
            Dict with keys:
                - notes: List of note dicts with (channel, note, velocity, start, duration)
                - duration: Total duration in seconds
                - tempo_bpm: Tempo in beats per minute
                - tracks: List of track information
                - chords: Detected chords from MIDI (ground truth)
        """
        mid = mido.MidiFile(midi_path)

        # Extract tempo
        tempo_microseconds = 500000  # Default: 120 BPM
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo_microseconds = msg.tempo
                    break

        tempo_bpm = mido.tempo2bpm(tempo_microseconds)
        ticks_per_beat = mid.ticks_per_beat

        # Parse all note events
        notes = []
        active_notes = {}  # Track note_on events waiting for note_off

        for track_idx, track in enumerate(mid.tracks):
            current_time = 0  # Time in ticks

            for msg in track:
                current_time += msg.time

                # Convert ticks to seconds
                time_seconds = mido.tick2second(
                    current_time, ticks_per_beat, tempo_microseconds
                )

                if msg.type == 'note_on' and msg.velocity > 0:
                    # Note on event
                    key = (msg.channel, msg.note)
                    active_notes[key] = {
                        'channel': msg.channel,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'start': time_seconds,
                        'track': track_idx
                    }

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Note off event
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        note_info = active_notes.pop(key)
                        duration = time_seconds - note_info['start']
                        note_info['duration'] = duration
                        notes.append(note_info)

        # Calculate total duration
        duration = max((n['start'] + n['duration'] for n in notes), default=0.0)

        # Extract chord information (ground truth for validation)
        chords = self._extract_chords_from_notes(notes)

        return {
            'notes': notes,
            'duration': duration,
            'tempo_bpm': tempo_bpm,
            'tempo_microseconds': tempo_microseconds,
            'ticks_per_beat': ticks_per_beat,
            'tracks': list(range(len(mid.tracks))),
            'chords': chords
        }

    def _extract_chords_from_notes(self, notes: List[Dict],
                                   window_ms: float = 100.0) -> List[Dict]:
        """
        Extract chords from MIDI notes by grouping simultaneous notes.

        Args:
            notes: List of note dicts
            window_ms: Time window in milliseconds for grouping notes

        Returns:
            List of chord dicts with (time, notes, chord_name)
        """
        # Group notes by time windows
        window_sec = window_ms / 1000.0
        chords = []

        # Sort notes by start time
        sorted_notes = sorted(notes, key=lambda n: n['start'])

        i = 0
        while i < len(sorted_notes):
            # Get notes starting in current window
            window_start = sorted_notes[i]['start']
            window_notes = []

            while i < len(sorted_notes) and sorted_notes[i]['start'] < window_start + window_sec:
                window_notes.append(sorted_notes[i])
                i += 1

            # If multiple notes, it's a chord
            if len(window_notes) >= 2:
                # Get unique pitch classes
                pitch_classes = sorted(set(n['note'] % 12 for n in window_notes))

                # Attempt to identify chord type
                chord_name = self._identify_chord(pitch_classes)

                chords.append({
                    'time': window_start,
                    'notes': window_notes,
                    'pitch_classes': pitch_classes,
                    'chord_name': chord_name
                })

        return chords

    def _identify_chord(self, pitch_classes: List[int]) -> str:
        """
        Identify chord type from pitch classes.

        Args:
            pitch_classes: List of pitch classes (0-11)

        Returns:
            Chord name (e.g., 'C_major', 'D_minor')
        """
        if len(pitch_classes) < 2:
            return 'single_note'

        # Calculate intervals from root
        root = pitch_classes[0]
        intervals = [(pc - root) % 12 for pc in pitch_classes]
        intervals_set = set(intervals)

        # Note names
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        root_name = note_names[root]

        # Chord templates (from bht_chord_detector.py)
        if intervals_set == {0, 4, 7}:
            return f"{root_name}_major"
        elif intervals_set == {0, 3, 7}:
            return f"{root_name}_minor"
        elif intervals_set == {0, 3, 6}:
            return f"{root_name}_dim"
        elif intervals_set == {0, 4, 8}:
            return f"{root_name}_aug"
        elif intervals_set == {0, 2, 7}:
            return f"{root_name}_sus2"
        elif intervals_set == {0, 5, 7}:
            return f"{root_name}_sus4"
        elif intervals_set == {0, 4, 7, 11}:
            return f"{root_name}_maj7"
        elif intervals_set == {0, 3, 7, 10}:
            return f"{root_name}_min7"
        elif intervals_set == {0, 4, 7, 10}:
            return f"{root_name}_dom7"
        else:
            return f"{root_name}_unknown"

    def _synthesize_notes(self, notes: List[Dict], duration: float,
                         verbose: bool = True) -> np.ndarray:
        """
        Synthesize all notes to audio.

        Args:
            notes: List of note dicts
            duration: Total duration in seconds
            verbose: Print progress

        Returns:
            Audio as float32 array [-1.0, 1.0]
        """
        # Create output buffer
        samples = int(np.ceil(duration * self.sample_rate)) + self.sample_rate  # Extra buffer
        audio = np.zeros(samples, dtype=np.float32)

        # Track instrument programs per channel
        channel_programs = {}  # channel -> program number

        # Synthesize each note
        for idx, note in enumerate(notes):
            if verbose and idx % 100 == 0 and idx > 0:
                print(f"  Synthesizing note {idx}/{len(notes)}...")

            channel = note['channel']
            midi_note = note['note']
            velocity = note['velocity']
            start = note['start']
            dur = note['duration']

            # Get instrument program for this channel
            # Channel 9 (index 9) is percussion in MIDI
            if channel == 9:
                # Percussion
                note_audio = self._synthesize_percussion(midi_note, velocity, dur)
            else:
                # Get program (assume program 0 = piano if not specified)
                program = channel_programs.get(channel, 0)
                note_audio = self._synthesize_melodic(program, midi_note, velocity, dur)

            # Mix into output buffer
            start_sample = int(start * self.sample_rate)
            end_sample = min(start_sample + len(note_audio), len(audio))
            length = end_sample - start_sample

            audio[start_sample:end_sample] += note_audio[:length]

        # Normalize to prevent clipping
        max_amplitude = np.max(np.abs(audio))
        if max_amplitude > 1.0:
            audio = audio / max_amplitude * 0.95  # Leave headroom

        return audio

    def _synthesize_percussion(self, midi_note: int, velocity: int,
                              duration: float) -> np.ndarray:
        """Synthesize percussion note."""
        # Use PercussionSynthesizer
        audio_int16 = self.percussion.synthesize_midi_percussion(
            midi_note, velocity, duration
        )

        # Convert to float32 [-1.0, 1.0]
        audio_float = audio_int16.astype(np.float32) / self.max_value

        return audio_float

    def _synthesize_melodic(self, program: int, midi_note: int,
                           velocity: int, duration: float) -> np.ndarray:
        """Synthesize melodic instrument note."""
        # Determine instrument family
        family = self.program_families.get(program, 'piano')

        # Synthesize based on family
        if family == 'brass':
            return self._synthesize_brass(program, midi_note, velocity, duration)
        elif family in ['strings', 'guitar', 'bass']:
            return self._synthesize_strings(program, midi_note, velocity, duration)
        # elif family in ['reed', 'pipe']:
        #     return self._synthesize_woodwind(program, midi_note, velocity, duration)
        else:
            # Default: Simple harmonic synthesis (piano-like)
            return self._synthesize_simple_harmonic(midi_note, velocity, duration)

    def _synthesize_brass(self, program: int, midi_note: int,
                         velocity: int, duration: float) -> np.ndarray:
        """Synthesize brass instrument using BrassSynthesizer."""
        audio_int16 = self.brass.synthesize_note(midi_note, velocity, duration, program)
        return audio_int16.astype(np.float32) / self.max_value

    def _synthesize_strings(self, program: int, midi_note: int,
                           velocity: int, duration: float) -> np.ndarray:
        """Synthesize string instrument using StringInstrumentSynthesizer."""
        audio_int16 = self.strings.synthesize_note(midi_note, velocity, duration)
        return audio_int16.astype(np.float32) / self.max_value

    def _synthesize_simple_harmonic(self, midi_note: int, velocity: int,
                                   duration: float, num_harmonics: int = 8) -> np.ndarray:
        """
        Simple harmonic synthesis for piano/organ sounds.

        Args:
            midi_note: MIDI note number
            velocity: MIDI velocity (0-127)
            duration: Note duration in seconds
            num_harmonics: Number of harmonics to include

        Returns:
            Audio as float32 array
        """
        # Calculate frequency from MIDI note
        freq = 440.0 * 2**((midi_note - 69) / 12.0)

        # Generate time array
        samples = int(duration * self.sample_rate)
        t = np.arange(samples) / self.sample_rate

        # Amplitude from velocity
        amp = velocity / 127.0

        # Generate harmonics with decreasing amplitude
        audio = np.zeros(samples, dtype=np.float32)
        for h in range(1, num_harmonics + 1):
            harmonic_amp = amp / h  # Decrease amplitude for higher harmonics
            audio += harmonic_amp * np.sin(2 * np.pi * freq * h * t)

        # Apply ADSR envelope
        audio *= self._adsr_envelope(samples,
                                     attack=0.02, decay=0.1,
                                     sustain=0.7, release=0.3,
                                     duration=duration)

        return audio

    def _adsr_envelope(self, samples: int, attack: float, decay: float,
                      sustain: float, release: float, duration: float) -> np.ndarray:
        """
        Generate ADSR envelope.

        Args:
            samples: Number of samples
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain: Sustain level (0-1)
            release: Release time in seconds
            duration: Total duration in seconds

        Returns:
            Envelope as numpy array
        """
        sr = self.sample_rate

        attack_samples = int(attack * sr)
        decay_samples = int(decay * sr)
        release_samples = int(release * sr)
        sustain_samples = samples - attack_samples - decay_samples - release_samples

        if sustain_samples < 0:
            sustain_samples = 0

        # Attack: 0 → 1
        attack_env = np.linspace(0, 1, attack_samples)

        # Decay: 1 → sustain level
        decay_env = np.linspace(1, sustain, decay_samples)

        # Sustain: constant
        sustain_env = np.ones(sustain_samples) * sustain

        # Release: sustain → 0
        release_env = np.linspace(sustain, 0, release_samples)

        # Concatenate
        envelope = np.concatenate([attack_env, decay_env, sustain_env, release_env])

        # Ensure correct length
        if len(envelope) > samples:
            envelope = envelope[:samples]
        elif len(envelope) < samples:
            envelope = np.pad(envelope, (0, samples - len(envelope)))

        return envelope

    def _save_wav(self, audio: np.ndarray, output_path: str):
        """
        Save audio to WAV file.

        Args:
            audio: Audio as float32 array [-1.0, 1.0]
            output_path: Path to save WAV file
        """
        # Convert to int16
        audio_int16 = (audio * self.max_value).astype(np.int16)

        # Save
        wavfile.write(output_path, self.sample_rate, audio_int16)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python midi_synthesizer.py INPUT.mid [OUTPUT.wav]")
        print()
        print("Example:")
        print("  python midi_synthesizer.py song.mid song.wav")
        sys.exit(1)

    input_midi = sys.argv[1]
    output_wav = sys.argv[2] if len(sys.argv) > 2 else None

    # Create synthesizer
    synth = MIDISynthesizer(sample_rate=44100)

    # Synthesize
    audio, midi_data = synth.synthesize_from_file(input_midi, output_wav, verbose=True)

    # Print MIDI ground truth
    print("\nGround Truth Chords (from MIDI):")
    for chord in midi_data['chords'][:10]:
        print(f"  {chord['time']:.2f}s: {chord['chord_name']} - {chord['pitch_classes']}")
    if len(midi_data['chords']) > 10:
        print(f"  ... and {len(midi_data['chords']) - 10} more chords")
