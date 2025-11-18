"""
Comprehensive Test: All Chord Types × All Root Positions

Tests EVERY chord type from chords.py across ALL 12 root positions
against single 1D time samples (spectral slices).

Validates that MHT detector correctly identifies:
- Chord type (major, minor, dim, etc.)
- Root note (C, C#, D, ..., B)
"""

import numpy as np
from bht_chord_detector_fast import FastMHTChordDetector
from bht_chord_detector import build_chord_templates
import time


# Chord definitions from chords.py
CHORD_TYPES = {
    'major':     [0, 4, 7],      # Root, major 3rd, perfect 5th
    'minor':     [0, 3, 7],      # Root, minor 3rd, perfect 5th
    'dim':       [0, 3, 6],      # Root, minor 3rd, diminished 5th
    'maj7':      [0, 4, 7, 11],  # Major + major 7th
    'min7':      [0, 3, 7, 10],  # Minor + minor 7th
    'dom7':      [0, 4, 7, 10],  # Major + minor 7th
    'sus2':      [0, 2, 7],      # Root, major 2nd, perfect 5th
    'sus4':      [0, 5, 7],      # Root, perfect 4th, perfect 5th
    'aug':       [0, 4, 8],      # Root, major 3rd, augmented 5th
    'dom9':      [0, 4, 7, 10, 14],  # Dom7 + major 9th
    'maj11':     [0, 4, 7, 11, 14, 17],  # Maj7 + 9th + 11th
}

# All 12 chromatic roots
ROOT_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def semitone_to_frequency(semitone_from_A0):
    """Convert semitone number (relative to A0) to frequency in Hz."""
    A0 = 27.5
    return A0 * 2**(semitone_from_A0 / 12.0)


def note_name_to_semitone_offset(note_name):
    """
    Convert note name to semitone offset from A.

    C=3, C#=4, D=5, D#=6, E=7, F=8, F#=9, G=10, G#=11, A=0, A#=1, B=2
    """
    note_to_offset = {
        'C': 3, 'C#': 4, 'D': 5, 'D#': 6, 'E': 7, 'F': 8,
        'F#': 9, 'G': 10, 'G#': 11, 'A': 0, 'A#': 1, 'B': 2
    }
    return note_to_offset[note_name]


def generate_chord_spectrum(frequencies, root_note, chord_type,
                            octave=4, signal_amp=100.0, noise_amp=1.0):
    """
    Generate synthetic spectral data for a specific chord.

    Args:
        frequencies: Array of frequency bins
        root_note: Root note name ('C', 'C#', etc.)
        chord_type: Chord type ('major', 'minor', etc.)
        octave: Octave for root note (default: 4)
        signal_amp: Signal amplitude
        noise_amp: Noise amplitude

    Returns:
        1D array of spectral amplitudes
    """
    spectrum = np.zeros(len(frequencies), dtype=np.float64)

    # Get chord intervals
    intervals = CHORD_TYPES[chord_type]

    # Calculate root frequency
    root_semitone = note_name_to_semitone_offset(root_note)
    root_freq = semitone_to_frequency(octave * 12 + root_semitone)

    # Add Gaussian peak for each note in chord
    # Use wider Gaussian to account for semitone-spaced bins (~15-20 Hz spacing)
    sigma_hz = 20.0  # Wide enough to hit neighboring bins

    for i, interval in enumerate(intervals):
        # Calculate frequency for this interval
        note_freq = root_freq * 2**(interval / 12.0)

        # Add Gaussian peak (decreasing amplitude for higher notes)
        amplitude = signal_amp * (0.8 ** i)
        gaussian = amplitude * np.exp(-(frequencies - note_freq)**2 / (2*sigma_hz**2))
        spectrum += gaussian

    # Add noise
    spectrum += noise_amp * np.abs(np.random.randn(len(frequencies)))

    return spectrum


def test_single_chord(detector, frequencies, true_root, true_type,
                      octave=4, signal_amp=100.0, verbose=False):
    """
    Test detection of a single chord.

    Returns:
        dict with test results
    """
    # Generate spectrum for this chord
    spectrum = generate_chord_spectrum(
        frequencies, true_root, true_type,
        octave, signal_amp, noise_amp=1.0
    )

    # Detect
    result = detector.detect(spectrum)

    # Parse detected chord
    detected = result['detected']
    detected_chord = result['chord']
    snr = result['snr']

    if detected_chord:
        # Split "C_major" → root="C", type="major"
        parts = detected_chord.split('_', 1)
        detected_root = parts[0] if len(parts) > 0 else None
        detected_type = parts[1] if len(parts) > 1 else None
    else:
        detected_root = None
        detected_type = None

    # Check correctness
    root_correct = (detected_root == true_root)
    type_correct = (detected_type == true_type)
    fully_correct = detected and root_correct and type_correct

    if verbose:
        status = "✓" if fully_correct else "✗"
        print(f"{status} {true_root:3s}_{true_type:8s} → "
              f"Detected: {detected_chord or 'None':15s} "
              f"SNR={snr:6.2f}")

    return {
        'true_root': true_root,
        'true_type': true_type,
        'detected': detected,
        'detected_root': detected_root,
        'detected_type': detected_type,
        'snr': snr,
        'root_correct': root_correct,
        'type_correct': type_correct,
        'fully_correct': fully_correct
    }


def test_all_chords(signal_amp=100.0, octave=4, verbose=True):
    """
    Test ALL chord types across ALL root positions.

    Total tests: 11 chord types × 12 roots = 132 tests

    Args:
        signal_amp: Signal amplitude (increase if detection fails)
        octave: Octave for root notes
        verbose: Print individual results

    Returns:
        dict with summary statistics
    """
    print("=" * 80)
    print("COMPREHENSIVE CHORD DETECTION TEST")
    print("=" * 80)

    # Setup
    print("\n1. Initializing detector...")
    A0 = 27.5
    frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)

    # Build ALL templates
    templates = build_chord_templates(
        frequencies,
        chord_types=list(CHORD_TYPES.keys()),
        template_type='gaussian',
        sigma_hz=10.0
    )

    print(f"   Frequencies: {len(frequencies)} bins")
    print(f"   Templates: {len(templates)} total")
    print(f"   Chord types: {len(CHORD_TYPES)}")
    print(f"   Root notes: {len(ROOT_NOTES)}")
    print(f"   Total tests: {len(CHORD_TYPES) * len(ROOT_NOTES)}")

    # Initialize detector
    detector = FastMHTChordDetector(templates, threshold=6.5)

    # Run tests
    print(f"\n2. Testing all chords (signal={signal_amp}, octave={octave})...")
    print("-" * 80)

    results = []
    start_time = time.perf_counter()

    for chord_type in CHORD_TYPES.keys():
        if verbose:
            print(f"\n{chord_type.upper()}:")

        for root_note in ROOT_NOTES:
            result = test_single_chord(
                detector, frequencies, root_note, chord_type,
                octave, signal_amp, verbose=verbose
            )
            results.append(result)

    end_time = time.perf_counter()

    # Calculate statistics
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    total_tests = len(results)
    detected_count = sum(r['detected'] for r in results)
    root_correct_count = sum(r['root_correct'] for r in results if r['detected'])
    type_correct_count = sum(r['type_correct'] for r in results if r['detected'])
    fully_correct_count = sum(r['fully_correct'] for r in results)

    print(f"\nTotal tests:        {total_tests}")
    print(f"Detected:           {detected_count} ({100*detected_count/total_tests:.1f}%)")
    print(f"Fully correct:      {fully_correct_count} ({100*fully_correct_count/total_tests:.1f}%)")

    if detected_count > 0:
        print(f"\nOf detected chords:")
        print(f"  Root correct:     {root_correct_count}/{detected_count} ({100*root_correct_count/detected_count:.1f}%)")
        print(f"  Type correct:     {type_correct_count}/{detected_count} ({100*type_correct_count/detected_count:.1f}%)")

    print(f"\nProcessing time:    {end_time - start_time:.3f} seconds")
    print(f"Rate:               {total_tests / (end_time - start_time):.0f} chords/sec")

    # Per-chord-type breakdown
    print("\n" + "-" * 80)
    print("PER CHORD TYPE ACCURACY:")
    print("-" * 80)
    print(f"{'Chord Type':12s} {'Total':>7s} {'Detected':>9s} {'Correct':>8s} {'Accuracy':>10s}")
    print("-" * 80)

    for chord_type in CHORD_TYPES.keys():
        type_results = [r for r in results if r['true_type'] == chord_type]
        type_total = len(type_results)
        type_detected = sum(r['detected'] for r in type_results)
        type_correct = sum(r['fully_correct'] for r in type_results)
        type_accuracy = 100 * type_correct / type_total if type_total > 0 else 0

        print(f"{chord_type:12s} {type_total:7d} {type_detected:9d} {type_correct:8d} {type_accuracy:9.1f}%")

    print("-" * 80)

    # Failed detections
    failed = [r for r in results if not r['fully_correct']]
    if failed and len(failed) <= 20:
        print(f"\nFAILED DETECTIONS ({len(failed)} total):")
        print("-" * 80)
        for r in failed:
            true_chord = f"{r['true_root']}_{r['true_type']}"
            detected_chord = f"{r['detected_root'] or '?'}_{r['detected_type'] or '?'}" if r['detected'] else "None"
            print(f"  {true_chord:15s} → {detected_chord:15s} (SNR={r['snr']:6.2f})")
    elif failed:
        print(f"\nFAILED DETECTIONS: {len(failed)} total (too many to list)")

    print("\n" + "=" * 80)

    # Return summary
    return {
        'total_tests': total_tests,
        'detected': detected_count,
        'fully_correct': fully_correct_count,
        'accuracy': 100 * fully_correct_count / total_tests,
        'processing_time': end_time - start_time,
        'rate': total_tests / (end_time - start_time),
        'results': results
    }


def test_signal_strength_sweep():
    """
    Test detection accuracy vs signal strength.

    Finds minimum signal amplitude needed for reliable detection.
    """
    print("\n" + "=" * 80)
    print("SIGNAL STRENGTH SWEEP")
    print("=" * 80)

    signal_levels = [20, 30, 50, 75, 100, 150, 200]

    print(f"\n{'Signal':>8s} {'Detected':>10s} {'Correct':>10s} {'Accuracy':>10s}")
    print("-" * 40)

    results_by_signal = []

    for signal_amp in signal_levels:
        summary = test_all_chords(signal_amp=signal_amp, verbose=False)

        print(f"{signal_amp:8.0f} {summary['detected']:10d} "
              f"{summary['fully_correct']:10d} {summary['accuracy']:9.1f}%")

        results_by_signal.append({
            'signal': signal_amp,
            'accuracy': summary['accuracy']
        })

    print("-" * 40)

    # Find threshold for 95% accuracy
    threshold_95 = None
    for r in results_by_signal:
        if r['accuracy'] >= 95.0:
            threshold_95 = r['signal']
            break

    if threshold_95:
        print(f"\n✓ Signal threshold for 95% accuracy: {threshold_95}")
    else:
        print(f"\n✗ 95% accuracy not achieved (max: {max(r['accuracy'] for r in results_by_signal):.1f}%)")

    return results_by_signal


if __name__ == "__main__":
    # Test 1: All chords at default signal level
    summary = test_all_chords(signal_amp=100.0, octave=4, verbose=True)

    # Test 2: Signal strength sweep (optional - uncomment if needed)
    # signal_sweep = test_signal_strength_sweep()

    print("\n✓ Comprehensive test complete!")
    print(f"✓ Overall accuracy: {summary['accuracy']:.1f}%")
