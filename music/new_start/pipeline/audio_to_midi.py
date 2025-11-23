#!/usr/bin/env python3
"""
Audio-to-MIDI Transcription Pipeline

Integrates Phase 1 (Timing & Dynamics) and Phase 2 (Melody Extraction)
to create complete audio-to-MIDI transcription.

Usage:
    python audio_to_midi.py input.wav output.mid
"""

import sys
import numpy as np
from pathlib import Path
from scipy.io import wavfile
import mido

from onset_detector import OnsetDetector, VelocityEstimator
from pitch_detector import PitchDetector, freq_to_midi, midi_to_note_name


class AudioToMIDITranscriber:
    """
    Complete audio-to-MIDI transcription pipeline.

    Combines:
    - Onset detection (Phase 1)
    - Velocity estimation (Phase 1)
    - Pitch detection (Phase 2)
    - MIDI file generation
    """

    def __init__(self, sample_rate=44100, onset_threshold=0.25):
        """
        Initialize transcriber.

        Args:
            sample_rate: Audio sample rate (Hz)
            onset_threshold: Threshold for onset detection
        """
        self.sample_rate = sample_rate

        # Initialize Phase 1 components
        self.onset_detector = OnsetDetector(
            sample_rate=sample_rate,
            onset_threshold=onset_threshold
        )
        self.velocity_estimator = VelocityEstimator(
            sample_rate=sample_rate
        )

        # Initialize Phase 2 component
        self.pitch_detector = PitchDetector(
            sample_rate=sample_rate,
            use_spectral_analyzer=False  # Use hybrid FFT+autocorrelation
        )

    def load_audio(self, audio_path):
        """
        Load and preprocess audio file.

        Args:
            audio_path: Path to WAV file

        Returns:
            Audio signal (mono, float32, normalized)
        """
        sample_rate, audio = wavfile.read(audio_path)

        # Store original dtype
        original_dtype = audio.dtype

        # Convert to mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Normalize to -1.0 to 1.0 range
        if original_dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif original_dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        elif audio.dtype in [np.float32, np.float64]:
            if np.max(np.abs(audio)) > 2.0:
                audio = audio.astype(np.float32) / 32768.0
            else:
                audio = audio.astype(np.float32)

        if sample_rate != self.sample_rate:
            print(f"Warning: Audio sample rate ({sample_rate}) differs from expected ({self.sample_rate})")

        return audio

    def transcribe(self, audio_path, output_midi_path=None, verbose=True):
        """
        Transcribe audio file to MIDI.

        Args:
            audio_path: Path to input WAV file
            output_midi_path: Path for output MIDI file (optional)
            verbose: Print progress

        Returns:
            Dict with transcription results
        """
        audio_path = Path(audio_path)

        if output_midi_path is None:
            output_midi_path = audio_path.with_suffix('.mid')
        else:
            output_midi_path = Path(output_midi_path)

        if verbose:
            print("="*80)
            print("AUDIO-TO-MIDI TRANSCRIPTION")
            print("="*80)
            print(f"Input:  {audio_path}")
            print(f"Output: {output_midi_path}")
            print()

        # Step 1: Load audio
        if verbose:
            print("[1/4] Loading audio...")

        audio = self.load_audio(audio_path)
        duration = len(audio) / self.sample_rate

        if verbose:
            print(f"  Duration: {duration:.2f}s")
            print(f"  Sample rate: {self.sample_rate} Hz")
            print()

        # Step 2: Detect onsets
        if verbose:
            print("[2/4] Detecting note onsets...")

        onset_times = self.onset_detector.detect_onsets_combined(audio)

        if verbose:
            print(f"  Detected {len(onset_times)} onsets")
            print()

        # Step 3: Detect pitch and velocity for each onset
        if verbose:
            print("[3/4] Detecting pitch and velocity...")

        notes = []
        for i, onset_time in enumerate(onset_times):
            # Detect pitch
            pitch_hz = self.pitch_detector.detect_pitch(audio, onset_time)

            # Estimate velocity
            velocity = self.velocity_estimator.estimate_velocity(audio, onset_time)

            # Only add notes with valid pitch
            if pitch_hz > 0:
                midi_note = freq_to_midi(pitch_hz)
                note_name = midi_to_note_name(midi_note)

                notes.append({
                    'time': onset_time,
                    'pitch_hz': pitch_hz,
                    'midi_note': midi_note,
                    'note_name': note_name,
                    'velocity': velocity
                })

                if verbose and len(notes) <= 10:  # Show first 10
                    print(f"  Note {i+1}: {note_name:4s} (MIDI {midi_note:3d}) "
                          f"at {onset_time:.3f}s, vel={velocity}")

        if verbose:
            if len(notes) > 10:
                print(f"  ... and {len(notes) - 10} more notes")
            print(f"  Total notes: {len(notes)} (from {len(onset_times)} onsets)")
            print()

        # Step 4: Create MIDI file
        if verbose:
            print("[4/4] Creating MIDI file...")

        self.create_midi_file(notes, output_midi_path)

        if verbose:
            print(f"  ✓ Saved: {output_midi_path}")
            print()
            print("="*80)
            print(f"Transcription complete: {len(notes)} notes")
            print("="*80)

        return {
            'audio_path': str(audio_path),
            'midi_path': str(output_midi_path),
            'duration': duration,
            'num_onsets': len(onset_times),
            'num_notes': len(notes),
            'notes': notes
        }

    def create_midi_file(self, notes, output_path, tempo_bpm=120, default_duration=0.5):
        """
        Create MIDI file from detected notes.

        Args:
            notes: List of note dicts with 'time', 'midi_note', 'velocity'
            output_path: Output MIDI file path
            tempo_bpm: Tempo in beats per minute (default 120)
            default_duration: Default note duration in seconds (default 0.5)
        """
        # Create MIDI file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo
        tempo_microseconds = mido.bpm2tempo(tempo_bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo_microseconds))

        # Convert notes to MIDI events
        # We need to create note_on and note_off pairs

        events = []

        for i, note in enumerate(notes):
            note_on_time = note['time']
            midi_note = note['midi_note']
            velocity = note['velocity']

            # Determine note duration
            # Use time until next onset, or default duration if last note
            if i + 1 < len(notes):
                duration = notes[i + 1]['time'] - note_on_time
                # Limit duration to reasonable range
                duration = min(duration, 2.0)  # Max 2 seconds
            else:
                duration = default_duration

            note_off_time = note_on_time + duration

            # Add events
            events.append(('note_on', note_on_time, midi_note, velocity))
            events.append(('note_off', note_off_time, midi_note, 0))

        # Sort events by time
        events.sort(key=lambda x: x[1])

        # Convert absolute times to delta times and add to track
        current_time = 0.0

        for event_type, event_time, midi_note, velocity in events:
            # Calculate delta time in ticks
            delta_seconds = event_time - current_time
            delta_ticks = int(mido.second2tick(delta_seconds, mid.ticks_per_beat, tempo_microseconds))
            delta_ticks = max(0, delta_ticks)  # Ensure non-negative

            # Add MIDI message
            if event_type == 'note_on':
                track.append(mido.Message('note_on', note=midi_note, velocity=velocity, time=delta_ticks))
            else:  # note_off
                track.append(mido.Message('note_off', note=midi_note, velocity=0, time=delta_ticks))

            current_time = event_time

        # Save MIDI file
        mid.save(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python audio_to_midi.py INPUT.wav [OUTPUT.mid]")
        print()
        print("Example:")
        print("  python audio_to_midi.py recording.wav transcription.mid")
        sys.exit(1)

    input_wav = sys.argv[1]
    output_mid = sys.argv[2] if len(sys.argv) > 2 else None

    # Create transcriber
    transcriber = AudioToMIDITranscriber(sample_rate=44100, onset_threshold=0.25)

    # Transcribe
    result = transcriber.transcribe(input_wav, output_mid, verbose=True)
