#!/usr/bin/env python3
"""
Evaluation Framework for Phase 1: Timing & Dynamics

Measures:
1. Onset Detection F-measure (precision, recall)
2. Velocity Correlation (Pearson r)

Goals:
- Onset F-measure > 0.85
- Velocity correlation > 0.70
"""

import sys
import json
import numpy as np
from pathlib import Path
from scipy.io import wavfile
from scipy.stats import pearsonr

# Import our implementations
from onset_detector import OnsetDetector, VelocityEstimator
from reco_enhanced import midi_to_wav


def load_ground_truth(json_path):
    """Load ground truth from JSON file."""
    with open(json_path, 'r') as f:
        gt = json.load(f)
    return gt


def evaluate_onset_detection(detected_onsets, ground_truth_onsets, tolerance=0.05):
    """
    Evaluate onset detection with tolerance window.

    Args:
        detected_onsets: Array of detected onset times (seconds)
        ground_truth_onsets: Array of ground truth onset times (seconds)
        tolerance: Time window in seconds (default 50ms)

    Returns:
        Dict with precision, recall, f_measure, and timing errors
    """
    if len(detected_onsets) == 0:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f_measure': 0.0,
            'num_detected': 0,
            'num_ground_truth': len(ground_truth_onsets),
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': len(ground_truth_onsets),
            'timing_errors_ms': []
        }

    # Match detected to ground truth within tolerance
    matched_gt = set()
    timing_errors = []

    true_positives = 0

    for det_onset in detected_onsets:
        # Find closest ground truth onset
        distances = np.abs(ground_truth_onsets - det_onset)
        min_dist = np.min(distances)
        min_idx = np.argmin(distances)

        if min_dist < tolerance and min_idx not in matched_gt:
            # True positive
            true_positives += 1
            matched_gt.add(min_idx)
            timing_errors.append(min_dist * 1000)  # Convert to ms

    false_positives = len(detected_onsets) - true_positives
    false_negatives = len(ground_truth_onsets) - true_positives

    # Calculate metrics
    precision = true_positives / len(detected_onsets) if len(detected_onsets) > 0 else 0.0
    recall = true_positives / len(ground_truth_onsets) if len(ground_truth_onsets) > 0 else 0.0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f_measure': f_measure,
        'num_detected': len(detected_onsets),
        'num_ground_truth': len(ground_truth_onsets),
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'timing_errors_ms': timing_errors,
        'mean_timing_error_ms': np.mean(timing_errors) if timing_errors else 0.0,
        'std_timing_error_ms': np.std(timing_errors) if timing_errors else 0.0
    }


def evaluate_velocity_estimation(detected_velocities, ground_truth_velocities):
    """
    Evaluate velocity estimation using Pearson correlation.

    Args:
        detected_velocities: Array of detected velocities
        ground_truth_velocities: Array of ground truth velocities

    Returns:
        Dict with correlation, MAE, RMSE
    """
    if len(detected_velocities) == 0 or len(ground_truth_velocities) == 0:
        return {
            'correlation': 0.0,
            'mae': 0.0,
            'rmse': 0.0
        }

    # Ensure same length (match by onset detection)
    n = min(len(detected_velocities), len(ground_truth_velocities))
    det_vel = np.array(detected_velocities[:n])
    gt_vel = np.array(ground_truth_velocities[:n])

    # Pearson correlation
    if np.std(det_vel) > 0 and np.std(gt_vel) > 0:
        correlation, p_value = pearsonr(det_vel, gt_vel)
    else:
        correlation = 0.0

    # Mean absolute error
    mae = np.mean(np.abs(det_vel - gt_vel))

    # Root mean squared error
    rmse = np.sqrt(np.mean((det_vel - gt_vel)**2))

    return {
        'correlation': correlation,
        'mae': mae,
        'rmse': rmse,
        'num_samples': n
    }


def test_single_file(midi_path, ground_truth_path, output_dir, method='combined'):
    """
    Test onset detection and velocity estimation on a single MIDI file.

    Args:
        midi_path: Path to MIDI file
        ground_truth_path: Path to ground truth JSON
        output_dir: Directory for output files
        method: Onset detection method ('energy', 'spectral', 'combined')

    Returns:
        Dict with evaluation results
    """
    midi_path = Path(midi_path)
    gt_path = Path(ground_truth_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print(f"TESTING: {midi_path.name}")
    print("="*80)
    print(f"Method: {method}")
    print()

    # Load ground truth
    gt = load_ground_truth(gt_path)

    print(f"Ground truth:")
    print(f"  Onsets: {len(gt['onset_times'])}")
    print(f"  Velocity range: {min(gt['velocities'])}-{max(gt['velocities'])}")
    print()

    # Synthesize MIDI to audio
    print("[1/3] Synthesizing MIDI to audio...")
    wav_path = output_dir / (midi_path.stem + "_synth.wav")
    midi_to_wav(str(midi_path), str(wav_path), verbose=False)
    print(f"  ✓ {wav_path.name}")
    print()

    # Load audio
    sample_rate, audio = wavfile.read(wav_path)

    # Convert to mono float32
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0

    # Detect onsets
    print(f"[2/3] Detecting onsets ({method} method)...")
    detector = OnsetDetector(sample_rate=sample_rate, onset_threshold=0.2)

    if method == 'energy':
        detected_onsets = detector.detect_onsets_energy(audio)
    elif method == 'spectral':
        detected_onsets = detector.detect_onsets_spectral_flux(audio)
    else:  # combined
        detected_onsets = detector.detect_onsets_combined(audio)

    print(f"  ✓ Detected {len(detected_onsets)} onsets")
    print()

    # Estimate velocities
    print("[3/3] Estimating velocities...")
    estimator = VelocityEstimator(sample_rate=sample_rate)
    detected_velocities = estimator.estimate_velocities(audio, detected_onsets)
    print(f"  ✓ Estimated velocities for {len(detected_velocities)} onsets")
    print()

    # Evaluate onset detection
    print("-" * 80)
    print("ONSET DETECTION EVALUATION")
    print("-" * 80)

    gt_onset_times = np.array(gt['onset_times'])
    onset_eval = evaluate_onset_detection(detected_onsets, gt_onset_times, tolerance=0.05)

    print(f"Precision:    {onset_eval['precision']:.3f}")
    print(f"Recall:       {onset_eval['recall']:.3f}")
    print(f"F-measure:    {onset_eval['f_measure']:.3f} {'✓ PASS' if onset_eval['f_measure'] > 0.85 else '✗ FAIL'} (goal: > 0.85)")
    print()
    print(f"True positives:  {onset_eval['true_positives']}")
    print(f"False positives: {onset_eval['false_positives']}")
    print(f"False negatives: {onset_eval['false_negatives']}")
    print()
    if onset_eval['timing_errors_ms']:
        print(f"Timing error:  {onset_eval['mean_timing_error_ms']:.1f} ± {onset_eval['std_timing_error_ms']:.1f} ms")
        print(f"               {'✓ PASS' if onset_eval['mean_timing_error_ms'] < 50 else '✗ FAIL'} (goal: < 50ms)")
    print()

    # Evaluate velocity estimation (match by onset)
    print("-" * 80)
    print("VELOCITY ESTIMATION EVALUATION")
    print("-" * 80)

    # Match detected onsets to ground truth to get corresponding velocities
    matched_velocities = []
    gt_velocities_matched = []

    for det_onset, det_vel in zip(detected_onsets, detected_velocities):
        # Find closest ground truth onset
        distances = np.abs(gt_onset_times - det_onset)
        min_dist = np.min(distances)
        min_idx = np.argmin(distances)

        if min_dist < 0.05:  # Within 50ms
            matched_velocities.append(det_vel)
            gt_velocities_matched.append(gt['velocities'][min_idx])

    if len(matched_velocities) > 0:
        velocity_eval = evaluate_velocity_estimation(matched_velocities, gt_velocities_matched)

        print(f"Correlation:  {velocity_eval['correlation']:.3f} {'✓ PASS' if velocity_eval['correlation'] > 0.70 else '✗ FAIL'} (goal: > 0.70)")
        print(f"MAE:          {velocity_eval['mae']:.1f}")
        print(f"RMSE:         {velocity_eval['rmse']:.1f}")
        print(f"Samples:      {velocity_eval['num_samples']}")
    else:
        print("No matched onsets for velocity evaluation!")
        velocity_eval = {'correlation': 0.0, 'mae': 0.0, 'rmse': 0.0, 'num_samples': 0}

    print()
    print("="*80)

    return {
        'onset_eval': onset_eval,
        'velocity_eval': velocity_eval,
        'detected_onsets': detected_onsets.tolist(),
        'detected_velocities': detected_velocities.tolist()
    }


def test_all_phase1_data(test_data_dir, output_dir, method='combined'):
    """
    Test all Phase 1 test files.

    Args:
        test_data_dir: Directory with test MIDI and JSON files
        output_dir: Directory for output files
        method: Onset detection method

    Returns:
        Dict with all evaluation results
    """
    test_data_dir = Path(test_data_dir)
    output_dir = Path(output_dir)

    # Find all test files
    midi_files = list(test_data_dir.glob("test_*.mid"))

    if not midi_files:
        print(f"ERROR: No test files found in {test_data_dir}")
        return None

    print()
    print("="*80)
    print(f"PHASE 1 EVALUATION: {len(midi_files)} TEST FILES")
    print("="*80)
    print()

    results = {}

    for midi_path in sorted(midi_files):
        gt_path = midi_path.with_suffix('.json')

        if not gt_path.exists():
            print(f"WARNING: Ground truth not found for {midi_path.name}")
            continue

        result = test_single_file(midi_path, gt_path, output_dir, method=method)
        results[midi_path.stem] = result

        print()
        print()

    # Summary
    print("="*80)
    print("PHASE 1 EVALUATION SUMMARY")
    print("="*80)
    print()

    print(f"{'Test':<30} {'Onset F':<10} {'Timing':<12} {'Velocity r':<12} {'Status':<10}")
    print("-" * 80)

    all_onset_f = []
    all_velocity_r = []

    for name, result in results.items():
        onset_f = result['onset_eval']['f_measure']
        timing_ms = result['onset_eval']['mean_timing_error_ms']
        velocity_r = result['velocity_eval']['correlation']

        all_onset_f.append(onset_f)
        all_velocity_r.append(velocity_r)

        onset_pass = "✓" if onset_f > 0.85 else "✗"
        timing_pass = "✓" if timing_ms < 50 else "✗"
        velocity_pass = "✓" if velocity_r > 0.70 else "✗"

        status = "PASS" if (onset_f > 0.85 and velocity_r > 0.70) else "FAIL"

        print(f"{name:<30} {onset_f:>6.3f} {onset_pass}  {timing_ms:>6.1f}ms {timing_pass}  {velocity_r:>8.3f} {velocity_pass}  {status}")

    print()
    print(f"Average Onset F-measure:  {np.mean(all_onset_f):.3f}")
    print(f"Average Velocity Correlation: {np.mean(all_velocity_r):.3f}")
    print()

    overall_pass = np.mean(all_onset_f) > 0.85 and np.mean(all_velocity_r) > 0.70

    if overall_pass:
        print("✓ PHASE 1 GOALS ACHIEVED!")
    else:
        print("✗ Phase 1 goals not yet met. Continue tuning...")

    print("="*80)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python evaluate_phase1.py TEST_DATA_DIR [OUTPUT_DIR] [METHOD]")
        print()
        print("Methods: combined (default), energy, spectral")
        print()
        print("Example:")
        print("  python evaluate_phase1.py ../working_files/test_data ../working_files combined")
        sys.exit(1)

    test_data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "../working_files/phase1_eval"
    method = sys.argv[3] if len(sys.argv) > 3 else "combined"

    test_all_phase1_data(test_data_dir, output_dir, method=method)
