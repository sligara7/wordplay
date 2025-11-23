#!/usr/bin/env python3
"""
Test Onset Detection on Real Piano Recordings

Tests Phase 1 onset detection on actual piano samples with known dynamics.

Each WAV file contains a single piano note, so:
- Ground truth: 1 onset per file
- Success: Detect exactly 1 onset
- Dynamics: ff (loud) to p (soft)
"""

import sys
import numpy as np
from pathlib import Path
from scipy.io import wavfile
import random

from onset_detector import OnsetDetector, VelocityEstimator


def parse_piano_filename(filename):
    """
    Parse piano sample filename to extract metadata.

    Format 1: {number}_mcg_{dynamic}_{midi_note}.wav
    Format 2: {number}_mcg_e_lc_{dynamic}.wav (some special samples)

    Returns:
        Dict with number, dynamic, midi_note (or None)
    """
    stem = Path(filename).stem
    parts = stem.split('_')

    # Check format
    if len(parts) >= 4 and parts[3].isdigit():
        # Format 1: standard with MIDI note
        return {
            'number': int(parts[0]),
            'dynamic': parts[2],
            'midi_note': int(parts[3]),
            'filename': filename
        }
    elif len(parts) >= 5 and parts[2] == 'e' and parts[3] == 'lc':
        # Format 2: special samples with "e_lc"
        return {
            'number': int(parts[0]),
            'dynamic': parts[4],  # Dynamic is at the end
            'midi_note': None,
            'filename': filename
        }
    else:
        # Unknown format - use defaults
        return {
            'number': int(parts[0]) if parts[0].isdigit() else 0,
            'dynamic': 'mf',  # Default
            'midi_note': None,
            'filename': filename
        }


def test_single_piano_sample(wav_path, detector, estimator, verbose=False):
    """
    Test onset detection on a single piano sample.

    Args:
        wav_path: Path to piano WAV file
        detector: OnsetDetector instance
        estimator: VelocityEstimator instance
        verbose: Print details

    Returns:
        Dict with results
    """
    # Load audio
    sample_rate, audio = wavfile.read(wav_path)

    # Convert to mono float32
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0

    # Detect onsets (use first_onset_only for single-note piano samples)
    detected_onsets = detector.detect_onsets_combined(audio, first_onset_only=True)
    num_detected = len(detected_onsets)

    # Estimate velocity for first onset (if detected)
    velocity = 0
    if num_detected > 0:
        velocity = estimator.estimate_velocity(audio, detected_onsets[0])

    # Parse metadata
    metadata = parse_piano_filename(wav_path)

    # Evaluate
    ground_truth = 1  # Each file has exactly 1 note
    correct = (num_detected == 1)

    if verbose:
        status = "✓" if correct else "✗"
        midi_str = f"{metadata['midi_note']:3d}" if metadata['midi_note'] is not None else "N/A"
        print(f"{status} {metadata['dynamic']:3s} MIDI{midi_str}: "
              f"detected={num_detected}, velocity={velocity}")

    return {
        'filename': Path(wav_path).name,
        'dynamic': metadata['dynamic'],
        'midi_note': metadata['midi_note'],
        'num_detected': num_detected,
        'velocity': velocity,
        'correct': correct,
        'onset_time': detected_onsets[0] if num_detected > 0 else None
    }


def test_piano_samples_by_dynamic(piano_dir, samples_per_dynamic=10, method='combined'):
    """
    Test onset detection on piano samples, sampling from each dynamic level.

    Args:
        piano_dir: Directory with piano WAV files
        samples_per_dynamic: Number of samples to test per dynamic
        method: Onset detection method

    Returns:
        Results dict
    """
    piano_dir = Path(piano_dir)

    print("="*80)
    print("TESTING ONSET DETECTION ON REAL PIANO RECORDINGS")
    print("="*80)
    print(f"Piano samples: {piano_dir}")
    print(f"Method: {method}")
    print(f"Samples per dynamic: {samples_per_dynamic}")
    print()

    # Find all piano samples
    all_files = list(piano_dir.glob("*.wav"))

    if not all_files:
        print(f"ERROR: No WAV files found in {piano_dir}")
        return None

    print(f"Total piano samples available: {len(all_files)}")
    print()

    # Group by dynamic
    by_dynamic = {}
    for f in all_files:
        metadata = parse_piano_filename(f)
        dynamic = metadata['dynamic']
        if dynamic not in by_dynamic:
            by_dynamic[dynamic] = []
        by_dynamic[dynamic].append(f)

    print("Dynamics available:")
    for dynamic in sorted(by_dynamic.keys()):
        print(f"  {dynamic}: {len(by_dynamic[dynamic])} samples")
    print()

    # Initialize detector and estimator
    # Use threshold 0.25 for real piano (more selective than synthetic tests)
    detector = OnsetDetector(sample_rate=44100, onset_threshold=0.25)
    estimator = VelocityEstimator(sample_rate=44100)

    # Test samples from each dynamic
    all_results = []

    for dynamic in sorted(by_dynamic.keys()):
        files = by_dynamic[dynamic]

        # Sample random files
        num_to_test = min(samples_per_dynamic, len(files))
        sampled_files = random.sample(files, num_to_test)

        print(f"Testing {dynamic} (n={num_to_test}):")
        print("-" * 80)

        dynamic_results = []

        for wav_path in sampled_files:
            result = test_single_piano_sample(wav_path, detector, estimator, verbose=True)
            result['dynamic'] = dynamic
            dynamic_results.append(result)
            all_results.append(result)

        # Summarize this dynamic
        num_correct = sum(1 for r in dynamic_results if r['correct'])
        accuracy = num_correct / len(dynamic_results)
        avg_velocity = np.mean([r['velocity'] for r in dynamic_results])

        print()
        print(f"  Accuracy: {num_correct}/{len(dynamic_results)} = {accuracy:.1%}")
        print(f"  Avg velocity: {avg_velocity:.1f}")
        print()

    # Overall summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    # Accuracy by dynamic
    print("Accuracy by dynamic level:")
    print(f"{'Dynamic':<10} {'Correct':<10} {'Total':<10} {'Accuracy':<12} {'Avg Velocity':<15} {'Status'}")
    print("-" * 80)

    dynamics_order = ['ff', 'f', 'mf', 'mp', 'p']  # Loud to soft
    dynamic_stats = {}

    for dynamic in dynamics_order:
        if dynamic not in by_dynamic:
            continue

        dynamic_results = [r for r in all_results if r['dynamic'] == dynamic]
        num_correct = sum(1 for r in dynamic_results if r['correct'])
        accuracy = num_correct / len(dynamic_results) if dynamic_results else 0
        avg_velocity = np.mean([r['velocity'] for r in dynamic_results])

        status = "✓ PASS" if accuracy > 0.85 else "✗ FAIL"

        print(f"{dynamic:<10} {num_correct:<10} {len(dynamic_results):<10} "
              f"{accuracy:<12.1%} {avg_velocity:<15.1f} {status}")

        dynamic_stats[dynamic] = {
            'accuracy': accuracy,
            'avg_velocity': avg_velocity,
            'num_samples': len(dynamic_results)
        }

    print()

    # Overall statistics
    total_correct = sum(1 for r in all_results if r['correct'])
    total_tested = len(all_results)
    overall_accuracy = total_correct / total_tested

    print(f"Overall accuracy: {total_correct}/{total_tested} = {overall_accuracy:.1%}")
    print()

    # Detection patterns
    num_zero = sum(1 for r in all_results if r['num_detected'] == 0)
    num_one = sum(1 for r in all_results if r['num_detected'] == 1)
    num_multiple = sum(1 for r in all_results if r['num_detected'] > 1)

    print("Detection patterns:")
    print(f"  0 onsets (missed): {num_zero} ({100*num_zero/total_tested:.1f}%)")
    print(f"  1 onset (correct): {num_one} ({100*num_one/total_tested:.1f}%)")
    print(f"  >1 onsets (false positives): {num_multiple} ({100*num_multiple/total_tested:.1f}%)")
    print()

    # Velocity correlation with dynamic
    print("Velocity estimation:")
    dynamic_to_expected_velocity = {
        'ff': 127,
        'f': 100,
        'mf': 80,
        'mp': 60,
        'p': 40
    }

    detected_velocities = []
    expected_velocities = []

    for dynamic in dynamics_order:
        if dynamic in dynamic_stats:
            detected_velocities.append(dynamic_stats[dynamic]['avg_velocity'])
            expected_velocities.append(dynamic_to_expected_velocity[dynamic])

    # Check if velocity decreases with dynamic (ff → p should decrease)
    velocity_decreasing = all(detected_velocities[i] >= detected_velocities[i+1]
                              for i in range(len(detected_velocities)-1))

    print(f"  Velocity trend: {'Decreasing (correct)' if velocity_decreasing else 'Not decreasing'}")
    print(f"  ff avg velocity: {dynamic_stats.get('ff', {}).get('avg_velocity', 0):.1f}")
    print(f"  p avg velocity: {dynamic_stats.get('p', {}).get('avg_velocity', 0):.1f}")
    print()

    # Final assessment
    print("="*80)

    if overall_accuracy > 0.85:
        print("✓ PHASE 1 ONSET DETECTION GOAL ACHIEVED ON REAL PIANO!")
        print(f"  Accuracy: {overall_accuracy:.1%} > 85%")
    else:
        print("✗ Onset detection accuracy not yet at goal")
        print(f"  Current: {overall_accuracy:.1%}")
        print(f"  Goal: > 85%")
        print()
        print("Main issues:")
        if num_zero > num_multiple:
            print("  - Missing onsets (too insensitive)")
            print("  → Try: Lower threshold, more sensitive detection")
        elif num_multiple > num_zero:
            print("  - Too many false positives (too sensitive)")
            print("  → Try: Higher threshold, stricter peak detection")

    print("="*80)

    return {
        'overall_accuracy': overall_accuracy,
        'dynamic_stats': dynamic_stats,
        'all_results': all_results,
        'num_zero': num_zero,
        'num_one': num_one,
        'num_multiple': num_multiple
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_onset_on_real_piano.py PIANO_DIR [SAMPLES_PER_DYNAMIC] [METHOD]")
        print()
        print("Methods: combined (default), energy, spectral")
        print()
        print("Example:")
        print("  python test_onset_on_real_piano.py /home/ajs7/Downloads/grand_piano/cg2 20")
        sys.exit(1)

    piano_dir = sys.argv[1]
    samples_per_dynamic = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    method = sys.argv[3] if len(sys.argv) > 3 else "combined"

    test_piano_samples_by_dynamic(piano_dir, samples_per_dynamic=samples_per_dynamic, method=method)
