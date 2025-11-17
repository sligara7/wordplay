#!/usr/bin/env python3
"""
Audio-to-MIDI Transcription Pipeline

End-to-end pipeline that transcribes WAV audio files to MIDI using
graph-based spectral analysis, harmonic detection, and onset detection.

Usage:
    python audio_to_midi_pipeline.py input.wav [OPTIONS]
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple, Optional
from scipy.io import wavfile

from spectral_analyzer import SpectralAnalyzer
from audio_graph_builder import AudioGraphBuilder
from harmonic_analyzer import HarmonicAnalyzer
from onset_detector import OnsetDetector
from midi_generator import MidiGenerator


def validate_wav_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate that input file is a valid WAV file.

    Args:
        file_path: Path to file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file exists
    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"

    if not path.is_file():
        return False, f"Not a file: {file_path}"

    # Check file extension
    if path.suffix.lower() not in ['.wav', '.wave']:
        return False, f"Not a WAV file (extension: {path.suffix})"

    # Try to read with scipy
    try:
        sample_rate, audio_data = wavfile.read(file_path)
    except Exception as e:
        return False, f"Failed to read WAV file: {e}"

    # Check sample rate is supported
    supported_rates = [44100, 48000, 22050, 96000]
    if sample_rate not in supported_rates:
        return False, (
            f"Unsupported sample rate: {sample_rate} Hz. "
            f"Supported rates: {supported_rates}"
        )

    return True, ""


def transcribe(wav_path: str, output_path: str,
               intensity_threshold: float = 0.05,
               confidence_threshold: float = 0.3,
               min_duration_samples: int = 3,
               tempo: int = 120,
               verbose: bool = False) -> str:
    """
    Main transcription function coordinating all components.

    Transcribes a WAV audio file to MIDI using graph-based analysis.

    Args:
        wav_path: Path to input WAV file
        output_path: Path for output MIDI file
        intensity_threshold: Minimum intensity for graph nodes (default: 0.05)
        confidence_threshold: Minimum confidence for fundamentals (default: 0.3)
        min_duration_samples: Minimum sustained duration (default: 3)
        tempo: Tempo in BPM for MIDI file (default: 120)
        verbose: Print progress messages (default: False)

    Returns:
        Path to created MIDI file

    Raises:
        ValueError: If input file is invalid
        RuntimeError: If transcription fails
    """
    if verbose:
        print(f"\n{'='*60}")
        print("Audio-to-MIDI Transcription Pipeline")
        print(f"{'='*60}\n")

    # Step 1: Validate input file
    if verbose:
        print(f"[1/6] Validating input file: {wav_path}")

    is_valid, error_msg = validate_wav_file(wav_path)
    if not is_valid:
        raise ValueError(f"Invalid input file: {error_msg}")

    # Step 2: Load and analyze audio
    if verbose:
        print("[2/6] Performing spectral analysis...")

    try:
        sample_rate, audio_data = wavfile.read(wav_path)

        # Extract left channel if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        # Create SpectralAnalyzer
        # Standard musical range: A0 (27.5 Hz) to C8 (4186 Hz)
        analyzer = SpectralAnalyzer(
            samplefreq=sample_rate,
            cycles=2,  # 2 cycles per window for good frequency resolution
            standard_A4=440.0,
            note_begin=21,  # A0
            note_end=108,   # C8
            increments=1    # Semitone resolution
        )

        # Run spectral analysis
        spectral_data = analyzer.dotop(audio_data)

        if verbose:
            print(f"   Spectral data shape: {spectral_data.shape}")

    except Exception as e:
        raise RuntimeError(f"Spectral analysis failed: {e}")

    # Step 3: Build audio graph
    if verbose:
        print("[3/6] Building audio graph...")

    try:
        graph_builder = AudioGraphBuilder(
            spectral_data=spectral_data,
            frequencies=analyzer.note_freqs,
            sample_rate=sample_rate,
            window_length=analyzer.window_length,
            intensity_threshold=intensity_threshold
        )

        # Build graph with temporal and harmonic edges
        graph = graph_builder.build_graph()

        if verbose:
            print(f"   Graph nodes: {graph.number_of_nodes()}")
            print(f"   Graph edges: {graph.number_of_edges()}")

    except Exception as e:
        raise RuntimeError(f"Graph construction failed: {e}")

    # Step 4: Analyze harmonics
    if verbose:
        print("[4/6] Detecting fundamental frequencies...")

    try:
        harmonic_analyzer = HarmonicAnalyzer(graph)

        # Detect fundamentals across all time samples
        fundamentals_by_time = harmonic_analyzer.analyze_all_time_samples()

        # Filter noise
        filtered_fundamentals = harmonic_analyzer.filter_noise(
            confidence_threshold=confidence_threshold,
            min_duration_samples=min_duration_samples
        )

        if verbose:
            print(f"   Detected {len(filtered_fundamentals)} fundamental notes")

    except Exception as e:
        raise RuntimeError(f"Harmonic analysis failed: {e}")

    # Step 5: Detect onsets
    if verbose:
        print("[5/6] Detecting note onsets...")

    try:
        onset_detector = OnsetDetector(
            graph=graph,
            onset_threshold=0.3,
            min_onset_gap_seconds=0.05
        )

        # Detect onsets from fundamentals
        note_events = onset_detector.detect_onsets(filtered_fundamentals)

        if verbose:
            print(f"   Detected {len(note_events)} note events")

    except Exception as e:
        raise RuntimeError(f"Onset detection failed: {e}")

    # Check if we got any notes
    if not note_events:
        if verbose:
            print("\n   WARNING: No notes detected!")
            print("   Try adjusting thresholds:")
            print("   - Lower --intensity-threshold (current: {:.3f})".format(
                intensity_threshold))
            print("   - Lower --confidence (current: {:.2f})".format(
                confidence_threshold))

    # Step 6: Generate MIDI
    if verbose:
        print(f"[6/6] Generating MIDI file: {output_path}")

    try:
        midi_generator = MidiGenerator(tempo=tempo)

        # Generate MIDI file
        midi_path = midi_generator.generate_midi(
            note_events=note_events,
            output_path=output_path
        )

        if verbose:
            print(f"\n{'='*60}")
            print("✓ Transcription complete!")
            print(f"{'='*60}")
            print(f"Output: {midi_path}")
            print(f"Notes: {len(note_events)}")
            print(f"Tempo: {tempo} BPM")
            print(f"{'='*60}\n")

        return midi_path

    except Exception as e:
        raise RuntimeError(f"MIDI generation failed: {e}")


def main():
    """
    CLI entry point using argparse.

    Parses command-line arguments and calls transcribe() function.
    """
    parser = argparse.ArgumentParser(
        description="Transcribe WAV audio files to MIDI using graph-based analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audio_to_midi_pipeline.py input.wav
  python audio_to_midi_pipeline.py input.wav --output output.mid
  python audio_to_midi_pipeline.py input.wav --intensity-threshold 0.1
  python audio_to_midi_pipeline.py input.wav --tempo 140 --verbose

Parameters Guide:
  --intensity-threshold: Higher = fewer notes (stricter filtering)
  --confidence: Higher = only confident fundamentals (fewer false positives)
  --min-duration: Higher = filter out very short notes
        """
    )

    # Required arguments
    parser.add_argument('input', type=str,
                        help='Input WAV file path')

    # Optional arguments
    parser.add_argument('--output', '-o', type=str,
                        help='Output MIDI file path (default: INPUT.mid)')

    parser.add_argument('--intensity-threshold', type=float, default=0.05,
                        help='Minimum intensity for graph nodes (default: 0.05)')

    parser.add_argument('--confidence', type=float, default=0.3,
                        help='Minimum confidence for fundamentals (default: 0.3)')

    parser.add_argument('--min-duration', type=int, default=3,
                        help='Minimum sustained samples (default: 3)')

    parser.add_argument('--tempo', type=int, default=120,
                        help='MIDI tempo in BPM (default: 120)')

    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    # Parse arguments
    args = parser.parse_args()

    # Set output path default if not provided
    if args.output is None:
        input_path = Path(args.input)
        args.output = str(input_path.with_suffix('.mid'))

    # Call transcription function
    try:
        midi_path = transcribe(
            wav_path=args.input,
            output_path=args.output,
            intensity_threshold=args.intensity_threshold,
            confidence_threshold=args.confidence,
            min_duration_samples=args.min_duration,
            tempo=args.tempo,
            verbose=args.verbose
        )

        if not args.verbose:
            print(f"✓ Transcription complete: {midi_path}")

        sys.exit(0)

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
