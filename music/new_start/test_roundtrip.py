#!/usr/bin/env python3
"""
Round-Trip Test: MIDI → WAV → MIDI

Tests the complete audio transcription pipeline by:
1. Converting MIDI to WAV (synthesis)
2. Transcribing WAV back to MIDI (our system)
3. Comparing the results

Usage:
    python test_roundtrip.py input.mid [options]
"""

import argparse
import sys
from pathlib import Path
import mido

from midi_to_wav_simple import midi_to_wav
from audio_to_midi_pipeline import transcribe


def compare_midi_files(original_path: str, transcribed_path: str, verbose: bool = False):
    """
    Compare two MIDI files and report similarities/differences.

    Args:
        original_path: Path to original MIDI file
        transcribed_path: Path to transcribed MIDI file
        verbose: Print detailed comparison

    Returns:
        Dictionary with comparison metrics
    """
    # Load both MIDI files
    original = mido.MidiFile(original_path)
    transcribed = mido.MidiFile(transcribed_path)

    # Extract note events from original
    original_notes = []
    for track in original.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                original_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    # Extract note events from transcribed
    transcribed_notes = []
    for track in transcribed.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                transcribed_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    # Compute statistics
    metrics = {
        'original_notes': len(original_notes),
        'transcribed_notes': len(transcribed_notes),
        'detection_rate': len(transcribed_notes) / max(1, len(original_notes)),
    }

    # Count pitch matches (within reasonable time window)
    time_tolerance_ticks = 100  # Allow some timing variance
    pitch_matches = 0

    for orig_note in original_notes:
        for trans_note in transcribed_notes:
            if orig_note['note'] == trans_note['note']:
                time_diff = abs(orig_note['time'] - trans_note['time'])
                if time_diff <= time_tolerance_ticks:
                    pitch_matches += 1
                    break

    metrics['pitch_accuracy'] = pitch_matches / max(1, len(original_notes))

    if verbose:
        print(f"\nComparison Results:")
        print(f"  Original notes:     {metrics['original_notes']}")
        print(f"  Transcribed notes:  {metrics['transcribed_notes']}")
        print(f"  Detection rate:     {metrics['detection_rate']:.2%}")
        print(f"  Pitch accuracy:     {metrics['pitch_accuracy']:.2%}")

        if metrics['original_notes'] > 0:
            if metrics['detection_rate'] < 0.5:
                print(f"\n  ⚠ Low detection rate - try adjusting thresholds")
            elif metrics['pitch_accuracy'] > 0.7:
                print(f"\n  ✓ Good pitch accuracy!")

    return metrics


def roundtrip_test(midi_path: str,
                   wav_path: str = None,
                   output_midi_path: str = None,
                   intensity_threshold: float = 0.02,
                   confidence_threshold: float = 0.15,
                   verbose: bool = False):
    """
    Perform round-trip test: MIDI → WAV → MIDI.

    Args:
        midi_path: Input MIDI file
        wav_path: Intermediate WAV file (default: auto-generated)
        output_midi_path: Output MIDI file (default: auto-generated)
        intensity_threshold: Graph intensity threshold
        confidence_threshold: Fundamental confidence threshold
        verbose: Print progress

    Returns:
        Dictionary with test results and metrics
    """
    midi_path_obj = Path(midi_path)

    # Set default paths
    if wav_path is None:
        wav_path = str(midi_path_obj.with_suffix('.roundtrip.wav'))
    if output_midi_path is None:
        output_midi_path = str(midi_path_obj.with_suffix('.roundtrip.mid'))

    if verbose:
        print(f"{'='*60}")
        print(f"Round-Trip Test: MIDI → WAV → MIDI")
        print(f"{'='*60}")
        print(f"Input MIDI:  {midi_path}")
        print(f"Temp WAV:    {wav_path}")
        print(f"Output MIDI: {output_midi_path}")
        print()

    # Step 1: MIDI → WAV
    if verbose:
        print(f"[1/3] Converting MIDI to WAV...")

    try:
        midi_to_wav(midi_path, wav_path, verbose=verbose)
    except Exception as e:
        raise RuntimeError(f"MIDI→WAV conversion failed: {e}")

    # Step 2: WAV → MIDI
    if verbose:
        print(f"\n[2/3] Transcribing WAV to MIDI...")

    try:
        transcribe(
            wav_path=wav_path,
            output_path=output_midi_path,
            intensity_threshold=intensity_threshold,
            confidence_threshold=confidence_threshold,
            verbose=verbose
        )
    except Exception as e:
        raise RuntimeError(f"WAV→MIDI transcription failed: {e}")

    # Step 3: Compare MIDI files
    if verbose:
        print(f"\n[3/3] Comparing MIDI files...")

    metrics = compare_midi_files(midi_path, output_midi_path, verbose=verbose)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Round-Trip Test Complete")
        print(f"{'='*60}\n")

    return {
        'midi_path': midi_path,
        'wav_path': wav_path,
        'output_midi_path': output_midi_path,
        'metrics': metrics
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test MIDI→WAV→MIDI round-trip transcription"
    )

    parser.add_argument('input', help='Input MIDI file')
    parser.add_argument('--wav-output', help='Intermediate WAV file path')
    parser.add_argument('--midi-output', help='Output MIDI file path')

    parser.add_argument('--intensity-threshold', type=float, default=0.02,
                        help='Graph intensity threshold (default: 0.02)')
    parser.add_argument('--confidence', type=float, default=0.15,
                        help='Fundamental confidence threshold (default: 0.15)')

    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    try:
        results = roundtrip_test(
            midi_path=args.input,
            wav_path=args.wav_output,
            output_midi_path=args.midi_output,
            intensity_threshold=args.intensity_threshold,
            confidence_threshold=args.confidence,
            verbose=args.verbose
        )

        if not args.verbose:
            metrics = results['metrics']
            print(f"✓ Round-trip test complete:")
            print(f"  Detection rate: {metrics['detection_rate']:.1%}")
            print(f"  Pitch accuracy: {metrics['pitch_accuracy']:.1%}")

        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
