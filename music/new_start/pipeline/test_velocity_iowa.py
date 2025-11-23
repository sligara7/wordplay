#!/usr/bin/env python3
"""
Test Velocity Estimation on Iowa Piano Samples

Tests velocity estimation on real piano recordings with true amplitude differences.

Iowa samples have three dynamics:
- pp (pianissimo - very soft)
- mf (mezzo-forte - medium)
- ff (fortissimo - very loud)

Each file contains a single piano note, so:
- Ground truth: 1 onset per file
- Velocity should correlate with dynamic marking
"""

import sys
import numpy as np
from pathlib import Path
from scipy.io import wavfile
from scipy.stats import pearsonr
import random

from onset_detector import OnsetDetector, VelocityEstimator


def parse_iowa_filename(filename):
    """
    Parse Iowa piano sample filename.

    Format: Piano.{dynamic}.{note}.aiff.wav
    Example: Piano.ff.C4.aiff.wav

    Returns:
        Dict with dynamic, note
    """
    stem = Path(filename).stem  # Remove .wav
    parts = stem.split('.')

    if len(parts) >= 3 and parts[0] == 'Piano':
        return {
            'dynamic': parts[1],  # pp, mf, ff
            'note': parts[2],     # C4, A3, etc.
            'filename': filename
        }
    else:
        return {
            'dynamic': 'unknown',
            'note': 'unknown',
            'filename': filename
        }


def dynamic_to_expected_velocity(dynamic):
    """
    Map dynamic marking to expected MIDI velocity range.

    Args:
        dynamic: pp, mf, or ff

    Returns:
        Expected MIDI velocity (approximate center of range)
    """
    mapping = {
        'pp': 30,   # Very soft: 20-40
        'mf': 80,   # Medium: 60-100
        'ff': 110   # Very loud: 100-120
    }
    return mapping.get(dynamic, 64)


def test_single_iowa_sample(wav_path, detector, estimator, verbose=False):
    """
    Test velocity estimation on a single Iowa piano sample.

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

    # Store original dtype before any conversions
    original_dtype = audio.dtype

    # Convert to mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    # Normalize to -1.0 to 1.0 range
    # Check original dtype since .mean() converts int to float
    if original_dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif original_dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype in [np.float32, np.float64]:
        # Check if float is in int16 range (not normalized)
        if np.max(np.abs(audio)) > 2.0:
            # Likely unnormalized float in int16 range
            audio = audio.astype(np.float32) / 32768.0
        else:
            # Already normalized
            audio = audio.astype(np.float32)

    # Detect onset (use first_onset_only for single-note samples)
    detected_onsets = detector.detect_onsets_combined(audio, first_onset_only=True)

    # Estimate velocity
    velocity = 0
    onset_detected = len(detected_onsets) > 0

    if onset_detected:
        velocity = estimator.estimate_velocity(audio, detected_onsets[0])

    # Parse metadata
    metadata = parse_iowa_filename(wav_path)

    # Get expected velocity
    expected_velocity = dynamic_to_expected_velocity(metadata['dynamic'])

    if verbose:
        status = "✓" if onset_detected else "✗"
        print(f"{status} {metadata['dynamic']:3s} {metadata['note']:5s}: "
              f"velocity={velocity:3d} (expected ~{expected_velocity:3d})")

    return {
        'filename': Path(wav_path).name,
        'dynamic': metadata['dynamic'],
        'note': metadata['note'],
        'onset_detected': onset_detected,
        'velocity': velocity,
        'expected_velocity': expected_velocity
    }


def test_velocity_on_iowa_samples(iowa_dir, samples_per_dynamic=20):
    """
    Test velocity estimation on Iowa piano samples.

    Args:
        iowa_dir: Directory with Iowa piano WAV files
        samples_per_dynamic: Number of samples to test per dynamic

    Returns:
        Results dict
    """
    iowa_dir = Path(iowa_dir)

    print("="*80)
    print("TESTING VELOCITY ESTIMATION ON IOWA PIANO SAMPLES")
    print("="*80)
    print(f"Iowa samples: {iowa_dir}")
    print(f"Samples per dynamic: {samples_per_dynamic}")
    print()

    # Find all piano samples
    all_files = list(iowa_dir.glob("Piano.*.wav"))

    if not all_files:
        print(f"ERROR: No WAV files found in {iowa_dir}")
        return None

    print(f"Total Iowa samples available: {len(all_files)}")
    print()

    # Group by dynamic
    by_dynamic = {}
    for f in all_files:
        metadata = parse_iowa_filename(f)
        dynamic = metadata['dynamic']
        if dynamic not in by_dynamic:
            by_dynamic[dynamic] = []
        by_dynamic[dynamic].append(f)

    print("Dynamics available:")
    for dynamic in sorted(by_dynamic.keys()):
        print(f"  {dynamic}: {len(by_dynamic[dynamic])} samples")
    print()

    # Initialize detector and estimator
    detector = OnsetDetector(sample_rate=44100, onset_threshold=0.25)
    estimator = VelocityEstimator(sample_rate=44100)

    # Test samples from each dynamic
    all_results = []

    dynamics_order = ['pp', 'mf', 'ff']  # Soft to loud

    for dynamic in dynamics_order:
        if dynamic not in by_dynamic:
            continue

        files = by_dynamic[dynamic]

        # Sample random files
        num_to_test = min(samples_per_dynamic, len(files))
        sampled_files = random.sample(files, num_to_test)

        print(f"Testing {dynamic} (n={num_to_test}):")
        print("-" * 80)

        dynamic_results = []

        for wav_path in sampled_files:
            result = test_single_iowa_sample(wav_path, detector, estimator, verbose=True)
            dynamic_results.append(result)
            all_results.append(result)

        # Summarize this dynamic
        num_detected = sum(1 for r in dynamic_results if r['onset_detected'])
        avg_velocity = np.mean([r['velocity'] for r in dynamic_results if r['onset_detected']])
        expected_velocity = dynamic_results[0]['expected_velocity']

        print()
        print(f"  Onset detection: {num_detected}/{len(dynamic_results)}")
        print(f"  Avg velocity: {avg_velocity:.1f} (expected ~{expected_velocity})")
        print()

    # Overall analysis
    print("="*80)
    print("VELOCITY ESTIMATION ANALYSIS")
    print("="*80)
    print()

    # Calculate statistics per dynamic
    print("Velocity by dynamic level:")
    print(f"{'Dynamic':<10} {'N':<6} {'Avg Vel':<10} {'Std':<10} {'Expected':<10} {'Status'}")
    print("-" * 80)

    dynamic_stats = {}

    for dynamic in dynamics_order:
        dynamic_results = [r for r in all_results if r['dynamic'] == dynamic and r['onset_detected']]

        if not dynamic_results:
            continue

        velocities = [r['velocity'] for r in dynamic_results]
        avg_velocity = np.mean(velocities)
        std_velocity = np.std(velocities)
        expected = dynamic_results[0]['expected_velocity']

        # Check if velocity is in reasonable range
        status = "✓" if abs(avg_velocity - expected) < 30 else "~"

        print(f"{dynamic:<10} {len(velocities):<6} {avg_velocity:<10.1f} {std_velocity:<10.1f} "
              f"{expected:<10} {status}")

        dynamic_stats[dynamic] = {
            'avg_velocity': avg_velocity,
            'std_velocity': std_velocity,
            'n': len(velocities),
            'velocities': velocities
        }

    print()

    # Check if velocity increases with dynamic level
    print("Velocity progression:")
    velocities_ordered = []
    for dynamic in dynamics_order:
        if dynamic in dynamic_stats:
            avg = dynamic_stats[dynamic]['avg_velocity']
            velocities_ordered.append(avg)
            print(f"  {dynamic}: {avg:.1f}")

    if len(velocities_ordered) >= 3:
        increasing = velocities_ordered[0] < velocities_ordered[1] < velocities_ordered[2]
        print()
        if increasing:
            print(f"  ✓ Velocity increases: pp < mf < ff")
        else:
            print(f"  ✗ Velocity does NOT increase monotonically")
    print()

    # Correlation analysis
    print("-" * 80)
    print("CORRELATION ANALYSIS")
    print("-" * 80)
    print()

    # Prepare data for correlation
    detected_velocities = []
    expected_velocities = []

    for result in all_results:
        if result['onset_detected']:
            detected_velocities.append(result['velocity'])
            expected_velocities.append(result['expected_velocity'])

    if len(detected_velocities) >= 10:
        # Pearson correlation
        if np.std(detected_velocities) > 0 and np.std(expected_velocities) > 0:
            correlation, p_value = pearsonr(detected_velocities, expected_velocities)

            print(f"Detected velocities: {len(detected_velocities)} samples")
            print(f"Pearson correlation: {correlation:.3f}")
            print(f"P-value: {p_value:.6f}")
            print()

            # MAE
            mae = np.mean(np.abs(np.array(detected_velocities) - np.array(expected_velocities)))
            print(f"Mean absolute error: {mae:.1f}")
            print()

            # Goal assessment
            if correlation > 0.70:
                print("✓ VELOCITY CORRELATION > 0.70 - PHASE 1 GOAL ACHIEVED!")
            else:
                print(f"✗ Velocity correlation not yet at goal")
                print(f"  Current: {correlation:.3f}")
                print(f"  Goal: > 0.70")
        else:
            print("Insufficient variation in velocities for correlation")
            correlation = 0.0
    else:
        print("Not enough samples for correlation analysis")
        correlation = 0.0

    print()
    print("="*80)

    return {
        'dynamic_stats': dynamic_stats,
        'all_results': all_results,
        'correlation': correlation if len(detected_velocities) >= 10 else 0.0,
        'num_samples': len(detected_velocities)
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_velocity_iowa.py IOWA_DIR [SAMPLES_PER_DYNAMIC]")
        print()
        print("Example:")
        print("  python test_velocity_iowa.py /home/ajs7/Downloads/iowawav 20")
        sys.exit(1)

    iowa_dir = sys.argv[1]
    samples_per_dynamic = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    test_velocity_on_iowa_samples(iowa_dir, samples_per_dynamic=samples_per_dynamic)
