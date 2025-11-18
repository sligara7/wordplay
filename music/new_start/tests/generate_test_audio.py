"""
Test Audio Generator - Creates synthetic WAV files for testing

Generates simple test audio files with known properties for testing
the audio-to-MIDI transcription pipeline.
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path
from typing import List, Tuple


def generate_sine_wave(frequency: float, duration_seconds: float,
                       sample_rate: int = 44100,
                       amplitude: float = 0.5) -> np.ndarray:
    """
    Generate a pure sine wave at a specific frequency.

    Args:
        frequency: Frequency in Hz (e.g., 440.0 for A4)
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz (default: 44100)
        amplitude: Amplitude [0, 1] (default: 0.5)

    Returns:
        Audio samples as numpy array
    """
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    wave = amplitude * np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit PCM
    wave_int16 = np.int16(wave * 32767)

    return wave_int16


def generate_chord(frequencies: List[float], duration_seconds: float,
                   sample_rate: int = 44100,
                   amplitude: float = 0.3) -> np.ndarray:
    """
    Generate a chord (multiple simultaneous frequencies).

    Args:
        frequencies: List of frequencies in Hz
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz (default: 44100)
        amplitude: Amplitude per note [0, 1] (default: 0.3)

    Returns:
        Audio samples as numpy array
    """
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))

    # Sum all frequencies
    wave = np.zeros_like(t)
    for freq in frequencies:
        wave += amplitude * np.sin(2 * np.pi * freq * t)

    # Normalize to prevent clipping
    wave = wave / len(frequencies)

    # Convert to 16-bit PCM
    wave_int16 = np.int16(wave * 32767)

    return wave_int16


def generate_sequence(notes: List[Tuple[float, float]], sample_rate: int = 44100,
                      amplitude: float = 0.5) -> np.ndarray:
    """
    Generate a sequence of notes.

    Args:
        notes: List of (frequency, duration_seconds) tuples
        sample_rate: Sample rate in Hz (default: 44100)
        amplitude: Amplitude [0, 1] (default: 0.5)

    Returns:
        Audio samples as numpy array
    """
    segments = []

    for frequency, duration in notes:
        segment = generate_sine_wave(frequency, duration, sample_rate, amplitude)
        segments.append(segment)

    # Concatenate all segments
    wave = np.concatenate(segments)

    return wave


def save_test_audio(filename: str, audio_data: np.ndarray,
                    sample_rate: int = 44100):
    """
    Save audio data to WAV file.

    Args:
        filename: Output file path
        audio_data: Audio samples
        sample_rate: Sample rate in Hz (default: 44100)
    """
    wavfile.write(filename, sample_rate, audio_data)


def create_standard_test_files(output_dir: str = "tests/test_audio"):
    """
    Create standard test audio files for testing.

    Creates:
    - single_note_A4.wav: Pure A4 (440 Hz) for 1 second
    - c_major_chord.wav: C-E-G chord (C4 major) for 2 seconds
    - simple_melody.wav: C4-D4-E4-F4-G4 sequence
    - two_notes.wav: C4 for 0.5s, then E4 for 0.5s

    Args:
        output_dir: Directory to save test files (default: tests/test_audio)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating test audio files in {output_dir}/...")

    # 1. Single note - A4 (440 Hz)
    print("  - single_note_A4.wav")
    single_note = generate_sine_wave(440.0, 1.0)
    save_test_audio(str(output_path / "single_note_A4.wav"), single_note)

    # 2. C major chord (C4, E4, G4)
    print("  - c_major_chord.wav")
    c_major_freqs = [261.63, 329.63, 392.00]  # C4, E4, G4
    chord = generate_chord(c_major_freqs, 2.0)
    save_test_audio(str(output_path / "c_major_chord.wav"), chord)

    # 3. Simple melody - C4 D4 E4 F4 G4
    print("  - simple_melody.wav")
    melody_notes = [
        (261.63, 0.5),  # C4
        (293.66, 0.5),  # D4
        (329.63, 0.5),  # E4
        (349.23, 0.5),  # F4
        (392.00, 0.5),  # G4
    ]
    melody = generate_sequence(melody_notes)
    save_test_audio(str(output_path / "simple_melody.wav"), melody)

    # 4. Two notes - C4 then E4
    print("  - two_notes.wav")
    two_notes_seq = [
        (261.63, 0.5),  # C4
        (329.63, 0.5),  # E4
    ]
    two_notes = generate_sequence(two_notes_seq)
    save_test_audio(str(output_path / "two_notes.wav"), two_notes)

    print(f"\n✓ Generated 4 test audio files in {output_dir}/")


if __name__ == '__main__':
    create_standard_test_files()
