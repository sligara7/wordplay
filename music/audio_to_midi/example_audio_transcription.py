#!/usr/bin/env python3
"""
Example: Audio-to-MIDI Transcription Using Graph Theory

This script demonstrates how to use the audio graph analyzer to transcribe
audio files (.wav) into MIDI files using graph-based analysis.

Usage:
    python examples/example_audio_transcription.py

Requirements:
    - Specialized Fourier transform implementation (see audio_graph_analyzer.py)
    - Or use the dummy data generator provided below for testing

See AUDIO_TRANSCRIPTION.md for methodology details.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from audio_graph_analyzer import (
    AudioGraphAnalyzer,
    A0_FREQUENCY,
    specialized_fourier_transform,
)


def generate_test_data(
    duration_seconds: float = 5.0,
    sample_rate: float = 22050,
    num_sub_notes: int = 4,
) -> tuple:
    """
    Generate synthetic frequency-time-intensity data for testing.

    This simulates the output of a specialized Fourier transform with
    a simple melody: C4 - E4 - G4 - C5 (C major arpeggio)

    Args:
        duration_seconds: Total duration of the audio
        sample_rate: Sample rate (Hz)
        num_sub_notes: Sub-divisions per note

    Returns:
        Tuple of (frequency_time_matrix, frequencies, time_samples)
    """
    print("Generating synthetic test data (C major arpeggio)...")

    # Frequency axis: 82 notes × num_sub_notes
    num_frequencies = 82 * num_sub_notes
    frequencies = A0_FREQUENCY * (2 ** (np.arange(num_frequencies) / (12 * num_sub_notes)))

    # Time axis: samples based on 5 cycles of 27.5 Hz
    cycles_per_sample = 5
    sample_duration = cycles_per_sample / A0_FREQUENCY  # ~182ms
    num_time_samples = int(duration_seconds / sample_duration)
    time_samples = np.arange(num_time_samples) * sample_duration

    # Initialize intensity matrix
    frequency_time_matrix = np.zeros((num_frequencies, num_time_samples))

    # Add background noise
    noise_level = 0.05
    frequency_time_matrix += np.random.rand(num_frequencies, num_time_samples) * noise_level

    # Define melody: C4 - E4 - G4 - C5
    melody_notes = [
        ('C4', 261.63),  # Middle C
        ('E4', 329.63),  # E
        ('G4', 392.00),  # G
        ('C5', 523.25),  # High C
    ]

    # Each note lasts 1 second
    note_duration = 1.0
    samples_per_note = int(note_duration / sample_duration)

    for i, (note_name, fundamental_freq) in enumerate(melody_notes):
        # Time range for this note
        start_sample = i * samples_per_note
        end_sample = min(start_sample + samples_per_note, num_time_samples)

        if start_sample >= num_time_samples:
            break

        # Find closest frequency index
        freq_idx = np.argmin(np.abs(frequencies - fundamental_freq))

        # Add fundamental with onset and decay
        for t in range(start_sample, end_sample):
            # Exponential decay envelope
            time_offset = (t - start_sample) * sample_duration
            envelope = np.exp(-time_offset / 0.5)  # Decay constant

            # Fundamental
            frequency_time_matrix[freq_idx, t] = 0.8 * envelope

            # Add harmonics (2f, 3f, 4f)
            for harmonic in [2, 3, 4]:
                harmonic_freq = fundamental_freq * harmonic
                harmonic_idx = np.argmin(np.abs(frequencies - harmonic_freq))

                # Harmonics are weaker
                harmonic_strength = 0.5 / harmonic
                frequency_time_matrix[harmonic_idx, t] = harmonic_strength * envelope

    print(f"Generated {num_frequencies} frequencies × {num_time_samples} time samples")
    print(f"Melody: {' → '.join(note for note, _ in melody_notes)}")

    return frequency_time_matrix, frequencies, time_samples


def example_basic_transcription():
    """
    Example 1: Basic transcription with synthetic data.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Audio Transcription")
    print("="*70 + "\n")

    # Generate test data
    frequency_time_matrix, frequencies, time_samples = generate_test_data(
        duration_seconds=5.0,
        sample_rate=22050,
        num_sub_notes=4,
    )

    # Create analyzer
    analyzer = AudioGraphAnalyzer(
        frequency_time_matrix=frequency_time_matrix,
        sample_rate_hz=22050,
        frequencies=frequencies,
        time_samples=time_samples,
        intensity_threshold=0.1,
        onset_threshold=0.15,
    )

    # Run analysis
    result = analyzer.analyze()

    # Create output directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Export MIDI
    midi_path = output_dir / "example_transcription.mid"
    analyzer.export_midi(str(midi_path), result.notes, tempo_bpm=120)

    # Export graph
    graph_path = output_dir / "example_audio_graph.json"
    analyzer.export_graph_json(str(graph_path))

    # Print results
    print("\n" + "-"*70)
    print("RESULTS:")
    print("-"*70)
    print(f"Detected key: {result.key_signature}")
    print(f"Number of notes: {len(result.notes)}")
    print(f"\nFirst 5 notes:")
    for i, note in enumerate(result.notes[:5], 1):
        print(f"  {i}. {note['note_name']}: "
              f"onset={note['onset_time']:.2f}s, "
              f"duration={note['duration']:.2f}s, "
              f"velocity={note['velocity']}")

    print(f"\nOutputs:")
    print(f"  MIDI: {midi_path}")
    print(f"  Graph: {graph_path}")
    print()


def example_real_audio_file():
    """
    Example 2: Transcribe a real audio file (requires Fourier transform implementation).
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Real Audio File Transcription")
    print("="*70 + "\n")

    audio_file = "music/song.wav"  # Replace with actual file

    try:
        # Apply specialized Fourier transform (user must implement)
        frequency_time_matrix, frequencies, time_samples = specialized_fourier_transform(
            audio_file,
            num_sub_notes=4,
            sample_duration_cycles=5,
        )

        # Create analyzer
        analyzer = AudioGraphAnalyzer(
            frequency_time_matrix=frequency_time_matrix,
            sample_rate_hz=22050,
            frequencies=frequencies,
            time_samples=time_samples,
        )

        # Run analysis
        result = analyzer.analyze()

        # Export
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)

        analyzer.export_midi(
            str(output_dir / "real_audio_transcription.mid"),
            result.notes
        )
        analyzer.export_graph_json(
            str(output_dir / "real_audio_graph.json")
        )

        print(f"Successfully transcribed {audio_file}")

    except NotImplementedError:
        print("⚠️  Specialized Fourier transform not implemented yet.")
        print("   Please implement specialized_fourier_transform() in audio_graph_analyzer.py")
        print("   Or provide the 2D frequency-time-intensity array directly.")
    except FileNotFoundError:
        print(f"⚠️  Audio file not found: {audio_file}")


def example_graph_analysis_integration():
    """
    Example 3: Integrate with existing wordplay graph analysis tools.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Integration with Wordplay Graph Tools")
    print("="*70 + "\n")

    # Generate test data
    frequency_time_matrix, frequencies, time_samples = generate_test_data()

    # Transcribe
    analyzer = AudioGraphAnalyzer(
        frequency_time_matrix=frequency_time_matrix,
        sample_rate_hz=22050,
        frequencies=frequencies,
        time_samples=time_samples,
    )
    result = analyzer.analyze()

    # Export graph in system_of_systems format
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    graph_path = output_dir / "audio_system_graph.json"
    analyzer.export_graph_json(str(graph_path))

    print(f"\n✓ Graph exported to {graph_path}")
    print("\nThis graph can now be analyzed with wordplay tools:")
    print("  - analyze_word_graph.py: Compute centrality, communities, cycles")
    print("  - batch_graph_merger.py: Compare with other audio transcriptions")
    print("  - graph_query.py: Query note patterns")
    print("\nExample commands:")
    print(f"  python src/analyze_word_graph.py {graph_path}")
    print()


def example_parameter_tuning():
    """
    Example 4: Demonstrate effect of different analysis parameters.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Parameter Tuning")
    print("="*70 + "\n")

    # Generate test data
    frequency_time_matrix, frequencies, time_samples = generate_test_data()

    # Try different threshold combinations
    parameter_sets = [
        {'intensity_threshold': 0.05, 'onset_threshold': 0.1, 'name': 'Sensitive'},
        {'intensity_threshold': 0.15, 'onset_threshold': 0.2, 'name': 'Balanced'},
        {'intensity_threshold': 0.25, 'onset_threshold': 0.3, 'name': 'Conservative'},
    ]

    print("Comparing different threshold settings:\n")

    for params in parameter_sets:
        analyzer = AudioGraphAnalyzer(
            frequency_time_matrix=frequency_time_matrix,
            sample_rate_hz=22050,
            frequencies=frequencies,
            time_samples=time_samples,
            intensity_threshold=params['intensity_threshold'],
            onset_threshold=params['onset_threshold'],
        )

        result = analyzer.analyze()

        print(f"{params['name']} settings:")
        print(f"  Intensity threshold: {params['intensity_threshold']}")
        print(f"  Onset threshold: {params['onset_threshold']}")
        print(f"  → Detected {len(result.notes)} notes")
        print(f"  → {len(result.fundamentals)} fundamentals, "
              f"{len(result.harmonics)} harmonics")
        print()

    print("💡 Tip: Adjust thresholds based on:")
    print("   - Lower thresholds → More sensitive (detects quiet notes, more noise)")
    print("   - Higher thresholds → More conservative (misses quiet notes, less noise)")
    print()


def main():
    """Run all examples."""
    # Example 1: Basic transcription (always works)
    example_basic_transcription()

    # Example 2: Real audio (requires implementation)
    # example_real_audio_file()

    # Example 3: Integration with wordplay tools
    example_graph_analysis_integration()

    # Example 4: Parameter tuning
    example_parameter_tuning()

    print("="*70)
    print("All examples completed!")
    print("="*70)
    print("\nNext steps:")
    print("1. Implement specialized_fourier_transform() for real audio files")
    print("2. Provide your 2D frequency-time-intensity array")
    print("3. Experiment with different thresholds for your data")
    print("4. Compare transcriptions with existing MIDI using wordplay tools")
    print("\nSee AUDIO_TRANSCRIPTION.md for methodology details.")
    print()


if __name__ == "__main__":
    main()
