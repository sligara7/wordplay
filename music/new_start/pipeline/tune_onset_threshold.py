#!/usr/bin/env python3
"""
Tune Onset Detection Threshold

Tests multiple threshold values to find optimal balance between
precision and recall.

Goal: F-measure > 0.85
"""

import sys
import json
import numpy as np
from pathlib import Path
from scipy.io import wavfile
import matplotlib.pyplot as plt

from onset_detector import OnsetDetector
from reco_enhanced import midi_to_wav


def evaluate_onset_detection(detected_onsets, ground_truth_onsets, tolerance=0.05):
    """Evaluate onset detection (same as evaluate_phase1.py)."""
    if len(detected_onsets) == 0:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f_measure': 0.0,
            'tp': 0,
            'fp': 0,
            'fn': len(ground_truth_onsets)
        }

    matched_gt = set()
    tp = 0

    for det_onset in detected_onsets:
        distances = np.abs(ground_truth_onsets - det_onset)
        min_dist = np.min(distances)
        min_idx = np.argmin(distances)

        if min_dist < tolerance and min_idx not in matched_gt:
            tp += 1
            matched_gt.add(min_idx)

    fp = len(detected_onsets) - tp
    fn = len(ground_truth_onsets) - tp

    precision = tp / len(detected_onsets) if len(detected_onsets) > 0 else 0.0
    recall = tp / len(ground_truth_onsets) if len(ground_truth_onsets) > 0 else 0.0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f_measure': f_measure,
        'tp': tp,
        'fp': fp,
        'fn': fn
    }


def test_threshold_on_file(audio, ground_truth, threshold, method='combined'):
    """Test a single threshold value on audio."""
    detector = OnsetDetector(sample_rate=44100, onset_threshold=threshold)

    if method == 'energy':
        detected_onsets = detector.detect_onsets_energy(audio)
    elif method == 'spectral':
        detected_onsets = detector.detect_onsets_spectral_flux(audio)
    else:  # combined
        detected_onsets = detector.detect_onsets_combined(audio)

    gt_onset_times = np.array(ground_truth['onset_times'])
    eval_result = evaluate_onset_detection(detected_onsets, gt_onset_times)

    return {
        'threshold': threshold,
        'num_detected': len(detected_onsets),
        'num_ground_truth': len(gt_onset_times),
        **eval_result
    }


def tune_threshold_single_file(midi_path, ground_truth_path, output_dir,
                                thresholds=None, method='combined'):
    """
    Tune threshold on a single test file.

    Args:
        midi_path: Path to MIDI file
        ground_truth_path: Path to ground truth JSON
        output_dir: Directory for outputs
        thresholds: List of thresholds to test (default: 0.1 to 0.9)
        method: Onset detection method

    Returns:
        Results dict with best threshold
    """
    if thresholds is None:
        thresholds = np.arange(0.1, 1.0, 0.05)

    midi_path = Path(midi_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print(f"THRESHOLD TUNING: {midi_path.name}")
    print("="*80)
    print(f"Method: {method}")
    print(f"Testing {len(thresholds)} threshold values: {thresholds[0]:.2f} - {thresholds[-1]:.2f}")
    print()

    # Load ground truth
    with open(ground_truth_path, 'r') as f:
        gt = json.load(f)

    # Synthesize MIDI to audio
    print("[1/2] Synthesizing audio...")
    wav_path = output_dir / (midi_path.stem + "_synth.wav")
    if not wav_path.exists():
        midi_to_wav(str(midi_path), str(wav_path), verbose=False)
    print(f"  ✓ {wav_path.name}")

    # Load audio
    sample_rate, audio = wavfile.read(wav_path)
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0

    # Test each threshold
    print()
    print("[2/2] Testing thresholds...")
    results = []

    for threshold in thresholds:
        result = test_threshold_on_file(audio, gt, threshold, method=method)
        results.append(result)

    # Find best threshold (maximize F-measure)
    best_result = max(results, key=lambda x: x['f_measure'])

    print()
    print("-" * 80)
    print("RESULTS")
    print("-" * 80)
    print()
    print(f"{'Threshold':<12} {'Detected':<10} {'Precision':<12} {'Recall':<12} {'F-measure':<12} {'Status'}")
    print("-" * 80)

    for r in results:
        status = ""
        if r['f_measure'] == best_result['f_measure']:
            status = "← BEST"
        elif r['f_measure'] > 0.85:
            status = "✓ PASS"

        print(f"{r['threshold']:<12.2f} {r['num_detected']:<10d} "
              f"{r['precision']:<12.3f} {r['recall']:<12.3f} "
              f"{r['f_measure']:<12.3f} {status}")

    print()
    print(f"Best threshold: {best_result['threshold']:.2f}")
    print(f"  Precision: {best_result['precision']:.3f}")
    print(f"  Recall:    {best_result['recall']:.3f}")
    print(f"  F-measure: {best_result['f_measure']:.3f} {'✓ PASS' if best_result['f_measure'] > 0.85 else '✗ FAIL'}")
    print()

    return {
        'file': midi_path.name,
        'best_threshold': best_result['threshold'],
        'best_f_measure': best_result['f_measure'],
        'all_results': results
    }


def tune_threshold_all_files(test_data_dir, output_dir, method='combined'):
    """
    Tune threshold across all test files and find optimal global threshold.

    Args:
        test_data_dir: Directory with test data
        output_dir: Output directory
        method: Onset detection method

    Returns:
        Optimal threshold and results
    """
    test_data_dir = Path(test_data_dir)
    output_dir = Path(output_dir)

    midi_files = list(test_data_dir.glob("test_*.mid"))

    if not midi_files:
        print(f"ERROR: No test files found in {test_data_dir}")
        return None

    print()
    print("="*80)
    print(f"THRESHOLD TUNING: {len(midi_files)} FILES")
    print("="*80)
    print()

    all_file_results = []
    thresholds = np.arange(0.1, 1.0, 0.05)

    for midi_path in sorted(midi_files):
        gt_path = midi_path.with_suffix('.json')
        if not gt_path.exists():
            continue

        result = tune_threshold_single_file(
            midi_path, gt_path, output_dir,
            thresholds=thresholds, method=method
        )
        all_file_results.append(result)
        print()

    # Aggregate results: average F-measure across all files for each threshold
    print("="*80)
    print("AGGREGATE RESULTS")
    print("="*80)
    print()

    threshold_aggregates = {}
    for threshold in thresholds:
        f_measures = []
        precisions = []
        recalls = []

        for file_result in all_file_results:
            for r in file_result['all_results']:
                if abs(r['threshold'] - threshold) < 0.001:  # Float comparison
                    f_measures.append(r['f_measure'])
                    precisions.append(r['precision'])
                    recalls.append(r['recall'])

        if f_measures:
            threshold_aggregates[threshold] = {
                'avg_f_measure': np.mean(f_measures),
                'avg_precision': np.mean(precisions),
                'avg_recall': np.mean(recalls),
                'min_f_measure': np.min(f_measures),
                'max_f_measure': np.max(f_measures)
            }

    # Find optimal threshold
    best_threshold = max(threshold_aggregates.items(),
                        key=lambda x: x[1]['avg_f_measure'])

    print(f"{'Threshold':<12} {'Avg F':<10} {'Avg P':<10} {'Avg R':<10} {'Min F':<10} {'Max F':<10} {'Status'}")
    print("-" * 80)

    for threshold, agg in sorted(threshold_aggregates.items()):
        status = ""
        if threshold == best_threshold[0]:
            status = "← BEST"
        elif agg['avg_f_measure'] > 0.85:
            status = "✓ PASS"

        print(f"{threshold:<12.2f} {agg['avg_f_measure']:<10.3f} "
              f"{agg['avg_precision']:<10.3f} {agg['avg_recall']:<10.3f} "
              f"{agg['min_f_measure']:<10.3f} {agg['max_f_measure']:<10.3f} {status}")

    print()
    print("="*80)
    print("OPTIMAL THRESHOLD")
    print("="*80)
    print(f"Threshold: {best_threshold[0]:.2f}")
    print(f"Average F-measure: {best_threshold[1]['avg_f_measure']:.3f} "
          f"{'✓ PASS' if best_threshold[1]['avg_f_measure'] > 0.85 else '✗ FAIL'} (goal: > 0.85)")
    print(f"Average Precision: {best_threshold[1]['avg_precision']:.3f}")
    print(f"Average Recall:    {best_threshold[1]['avg_recall']:.3f}")
    print(f"F-measure range:   {best_threshold[1]['min_f_measure']:.3f} - {best_threshold[1]['max_f_measure']:.3f}")
    print()

    if best_threshold[1]['avg_f_measure'] > 0.85:
        print("✓ PHASE 1 ONSET DETECTION GOAL ACHIEVED!")
        print(f"  Update onset_detector.py: onset_threshold={best_threshold[0]:.2f}")
    else:
        print("✗ Goal not yet met. Consider:")
        print("  - Adjusting smoothing window size")
        print("  - Using different onset detection method")
        print("  - Combining multiple methods with voting")

    print("="*80)

    return {
        'optimal_threshold': best_threshold[0],
        'optimal_metrics': best_threshold[1],
        'all_thresholds': threshold_aggregates,
        'file_results': all_file_results
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tune_onset_threshold.py TEST_DATA_DIR [OUTPUT_DIR] [METHOD]")
        print()
        print("Methods: combined (default), energy, spectral")
        print()
        print("Example:")
        print("  python tune_onset_threshold.py ../working_files/test_data ../working_files/threshold_tuning")
        sys.exit(1)

    test_data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "../working_files/threshold_tuning"
    method = sys.argv[3] if len(sys.argv) > 3 else "combined"

    tune_threshold_all_files(test_data_dir, output_dir, method=method)
