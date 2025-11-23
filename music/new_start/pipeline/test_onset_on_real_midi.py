#!/usr/bin/env python3
"""
Test Onset Detection on Real MIDI Files

Extracts ground truth onset times from MIDI, synthesizes audio,
detects onsets, and compares.

This tests Phase 1 on realistic music instead of synthetic test data.
"""

import sys
import mido
import numpy as np
from pathlib import Path
from scipy.io import wavfile
from scipy.stats import pearsonr

from onset_detector import OnsetDetector, VelocityEstimator
from reco_enhanced import midi_to_wav


def extract_ground_truth_from_midi(midi_path):
    """
    Extract ground truth onset times and velocities from MIDI file.

    Args:
        midi_path: Path to MIDI file

    Returns:
        Dict with onset_times, velocities, midi_notes
    """
    mid = mido.MidiFile(midi_path)

    # Track note events
    note_events = []
    current_time = 0.0
    tempo = 500000  # Default tempo (120 BPM)
    ticks_per_beat = mid.ticks_per_beat

    # Process all tracks
    for track in mid.tracks:
        track_time = 0.0

        for msg in track:
            # Update time
            delta_ticks = msg.time
            delta_seconds = mido.tick2second(delta_ticks, ticks_per_beat, tempo)
            track_time += delta_seconds
            current_time = max(current_time, track_time)

            # Handle note on events
            if msg.type == 'note_on' and msg.velocity > 0:
                note_events.append({
                    'time': track_time,
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'channel': msg.channel
                })

            # Handle tempo changes
            elif msg.type == 'set_tempo':
                tempo = msg.tempo

    # Sort by time
    note_events.sort(key=lambda x: x['time'])

    # Extract arrays
    onset_times = np.array([note['time'] for note in note_events])
    velocities = np.array([note['velocity'] for note in note_events])
    midi_notes = np.array([note['note'] for note in note_events])

    return {
        'onset_times': onset_times,
        'velocities': velocities,
        'midi_notes': midi_notes,
        'num_notes': len(note_events),
        'duration': current_time
    }


def evaluate_onset_detection(detected_onsets, ground_truth_onsets, tolerance=0.05):
    """Evaluate onset detection with tolerance window."""
    if len(detected_onsets) == 0:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f_measure': 0.0,
            'tp': 0,
            'fp': 0,
            'fn': len(ground_truth_onsets),
            'timing_errors_ms': []
        }

    matched_gt = set()
    timing_errors = []
    tp = 0

    for det_onset in detected_onsets:
        distances = np.abs(ground_truth_onsets - det_onset)
        min_dist = np.min(distances)
        min_idx = np.argmin(distances)

        if min_dist < tolerance and min_idx not in matched_gt:
            tp += 1
            matched_gt.add(min_idx)
            timing_errors.append(min_dist * 1000)  # ms

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
        'fn': fn,
        'timing_errors_ms': timing_errors,
        'mean_timing_error_ms': np.mean(timing_errors) if timing_errors else 0.0,
        'std_timing_error_ms': np.std(timing_errors) if timing_errors else 0.0
    }


def test_onset_on_real_midi(midi_path, output_dir, method='combined', verbose=True):
    """
    Test onset detection on a real MIDI file.

    Args:
        midi_path: Path to MIDI file
        output_dir: Output directory
        method: Onset detection method
        verbose: Print detailed output

    Returns:
        Evaluation results dict
    """
    midi_path = Path(midi_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("="*80)
        print(f"TESTING ONSET DETECTION ON REAL MIDI: {midi_path.name}")
        print("="*80)
        print(f"Method: {method}")
        print()

    # Step 1: Extract ground truth from MIDI
    if verbose:
        print("[1/4] Extracting ground truth from MIDI...")

    gt = extract_ground_truth_from_midi(midi_path)

    if verbose:
        print(f"  Ground truth notes: {gt['num_notes']}")
        print(f"  Duration: {gt['duration']:.2f}s")
        print(f"  Velocity range: {gt['velocities'].min()}-{gt['velocities'].max()}")
        print()

    # Step 2: Synthesize to audio
    if verbose:
        print("[2/4] Synthesizing MIDI to audio...")

    wav_path = output_dir / (midi_path.stem + "_synth.wav")
    midi_to_wav(str(midi_path), str(wav_path), verbose=False)

    if verbose:
        print(f"  ✓ {wav_path.name}")
        print()

    # Step 3: Load audio
    sample_rate, audio = wavfile.read(wav_path)

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0

    # Step 4: Detect onsets
    if verbose:
        print(f"[3/4] Detecting onsets ({method} method)...")

    detector = OnsetDetector(sample_rate=sample_rate, onset_threshold=0.2)

    if method == 'energy':
        detected_onsets = detector.detect_onsets_energy(audio)
    elif method == 'spectral':
        detected_onsets = detector.detect_onsets_spectral_flux(audio)
    else:  # combined
        detected_onsets = detector.detect_onsets_combined(audio)

    if verbose:
        print(f"  Ground truth onsets: {len(gt['onset_times'])}")
        print(f"  Detected onsets: {len(detected_onsets)}")
        print()

    # Step 5: Evaluate onset detection
    if verbose:
        print("[4/4] Evaluating onset detection...")
        print()

    onset_eval = evaluate_onset_detection(detected_onsets, gt['onset_times'], tolerance=0.05)

    if verbose:
        print("-" * 80)
        print("ONSET DETECTION RESULTS")
        print("-" * 80)
        print(f"Precision:        {onset_eval['precision']:.3f}")
        print(f"Recall:           {onset_eval['recall']:.3f}")
        print(f"F-measure:        {onset_eval['f_measure']:.3f} {'✓ PASS' if onset_eval['f_measure'] > 0.85 else '✗ FAIL'} (goal: > 0.85)")
        print()
        print(f"True positives:   {onset_eval['tp']}/{len(gt['onset_times'])}")
        print(f"False positives:  {onset_eval['fp']}")
        print(f"False negatives:  {onset_eval['fn']}")
        print()
        if onset_eval['timing_errors_ms']:
            print(f"Timing error:     {onset_eval['mean_timing_error_ms']:.1f} ± {onset_eval['std_timing_error_ms']:.1f} ms")
            print(f"                  {'✓ PASS' if onset_eval['mean_timing_error_ms'] < 50 else '✗ FAIL'} (goal: < 50ms)")
        print()

    # Step 6: Evaluate velocity estimation (for matched onsets)
    if verbose:
        print("-" * 80)
        print("VELOCITY ESTIMATION RESULTS")
        print("-" * 80)

    estimator = VelocityEstimator(sample_rate=sample_rate)
    detected_velocities = estimator.estimate_velocities(audio, detected_onsets)

    # Match detected onsets to ground truth
    matched_det_velocities = []
    matched_gt_velocities = []

    for det_onset, det_vel in zip(detected_onsets, detected_velocities):
        distances = np.abs(gt['onset_times'] - det_onset)
        min_dist = np.min(distances)
        min_idx = np.argmin(distances)

        if min_dist < 0.05:  # Within 50ms
            matched_det_velocities.append(det_vel)
            matched_gt_velocities.append(gt['velocities'][min_idx])

    if len(matched_det_velocities) > 1:
        # Pearson correlation
        if np.std(matched_det_velocities) > 0 and np.std(matched_gt_velocities) > 0:
            correlation, p_value = pearsonr(matched_det_velocities, matched_gt_velocities)
        else:
            correlation = 0.0

        # MAE
        mae = np.mean(np.abs(np.array(matched_det_velocities) - np.array(matched_gt_velocities)))

        # RMSE
        rmse = np.sqrt(np.mean((np.array(matched_det_velocities) - np.array(matched_gt_velocities))**2))

        if verbose:
            print(f"Matched onsets:   {len(matched_det_velocities)}/{len(gt['onset_times'])}")
            print(f"Correlation:      {correlation:.3f} {'✓ PASS' if correlation > 0.70 else '✗ FAIL'} (goal: > 0.70)")
            print(f"MAE:              {mae:.1f}")
            print(f"RMSE:             {rmse:.1f}")
    else:
        if verbose:
            print("Not enough matched onsets for velocity evaluation")
        correlation = 0.0
        mae = 0.0
        rmse = 0.0

    if verbose:
        print()
        print("="*80)

        # Overall status
        onset_pass = onset_eval['f_measure'] > 0.85
        velocity_pass = correlation > 0.70

        if onset_pass and velocity_pass:
            print("✓ PHASE 1 GOALS ACHIEVED ON REAL MIDI!")
        elif onset_pass:
            print("✓ Onset detection goal achieved!")
            print("✗ Velocity estimation needs improvement")
        elif velocity_pass:
            print("✗ Onset detection needs improvement")
            print("✓ Velocity estimation goal achieved!")
        else:
            print("✗ Both onset and velocity need improvement")
            print()
            print("Insights:")
            print(f"  - Onset recall: {onset_eval['recall']:.1%} (finding real onsets)")
            print(f"  - Onset precision: {onset_eval['precision']:.1%} (avoiding false positives)")
            if onset_eval['recall'] > 0.85 and onset_eval['precision'] < 0.85:
                print("  → High recall, low precision: Too many false positives")
                print("  → Consider: Increase threshold, stricter peak detection")
            elif onset_eval['recall'] < 0.85 and onset_eval['precision'] > 0.85:
                print("  → Low recall, high precision: Missing real onsets")
                print("  → Consider: Decrease threshold, more sensitive detection")

        print("="*80)

    return {
        'onset_eval': onset_eval,
        'velocity_correlation': correlation,
        'velocity_mae': mae,
        'velocity_rmse': rmse,
        'num_matched': len(matched_det_velocities),
        'ground_truth': gt,
        'detected_onsets': detected_onsets,
        'detected_velocities': detected_velocities
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_onset_on_real_midi.py MIDI_FILE [OUTPUT_DIR] [METHOD]")
        print()
        print("Methods: combined (default), energy, spectral")
        print()
        print("Example:")
        print("  python test_onset_on_real_midi.py ../midi_files/CdL.mid ../working_files/real_midi_test")
        sys.exit(1)

    midi_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "../working_files/real_midi_test"
    method = sys.argv[3] if len(sys.argv) > 3 else "combined"

    test_onset_on_real_midi(midi_path, output_dir, method=method, verbose=True)
