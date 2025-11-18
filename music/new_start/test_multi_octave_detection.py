"""
Test Multi-Octave Chord Detection

Verifies that multi-octave PSF templates enable cross-octave chord detection.

This should achieve 100% accuracy across all octaves!
"""

import numpy as np
from spectral_analyzer import SpectralAnalyzer
from bht_chord_detector_fast import FastMHTChordDetector
from build_chord_psf import generate_pure_chord_audio, CHORD_INTERVALS, ROOT_NOTES
from build_multi_octave_psf import load_multi_octave_psfs
import time


def test_multi_octave_detection(template_path="multi_octave_psf_templates.pkl",
                                 verbose=True):
    """
    Test chord detection using multi-octave PSF templates.

    Tests chords in octaves 2-6 using templates that cover all octaves.

    Returns:
        dict with comprehensive results
    """
    print("=" * 80)
    print("MULTI-OCTAVE CHORD DETECTION TEST")
    print("=" * 80)

    # Load multi-octave templates
    print(f"\n1. Loading multi-octave PSF templates...")
    templates, frequencies, metadata = load_multi_octave_psfs(template_path)

    sample_rate = metadata['sample_rate']
    cycles = metadata['cycles']
    template_octaves = metadata['octaves']

    print(f"   Templates loaded: {len(templates)}")
    print(f"   Frequency bins: {len(frequencies)}")

    # Test parameters
    test_octaves = [2, 3, 4, 5, 6]
    test_chord_types = ['major', 'minor', 'dim', 'maj7', 'dom9']
    test_roots = ['C', 'E', 'G', 'A']

    print(f"\n2. Test configuration:")
    print(f"   Test octaves: {test_octaves}")
    print(f"   Chord types: {test_chord_types}")
    print(f"   Root notes: {test_roots}")
    print(f"   Total tests: {len(test_octaves) * len(test_chord_types) * len(test_roots)}")

    # Initialize detector with multi-octave templates
    print(f"\n3. Initializing detector...")
    detector = FastMHTChordDetector(
        templates,
        threshold=6.5,
        use_outlier_removal=False
    )

    # Initialize spectral analyzer
    print(f"\n4. Initializing spectral analyzer...")
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Run tests
    print(f"\n5. Testing chords across octaves...")
    print("-" * 80)

    results = []
    results_by_octave = {octave: [] for octave in test_octaves}

    start_test_time = time.perf_counter()

    for test_octave in test_octaves:
        print(f"\n--- Testing Octave {test_octave} ---")

        for chord_type in test_chord_types:
            if verbose:
                print(f"\n{chord_type.upper()}:")

            for root_note in test_roots:
                # Generate test audio
                test_audio = generate_pure_chord_audio(
                    root_note, chord_type,
                    octave=test_octave,
                    duration_sec=cycles / (440.0 / 16),
                    sample_rate=sample_rate,
                    amplitude=0.5
                )

                # Analyze
                spectral_data = analyzer.dotop(test_audio)
                mid_time = spectral_data.shape[1] // 2
                spectrum = spectral_data[:, mid_time]

                # Detect
                result = detector.detect(spectrum)

                # Parse result
                detected_chord = result['chord'] if result['detected'] else None
                snr = result['snr']

                # Expected: root_type_octN (e.g., "C_major_oct4")
                expected_chord = f"{root_note}_{chord_type}_oct{test_octave}"

                # Check correctness
                correct = (detected_chord == expected_chord)
                status = "✓" if correct else "✗"

                if verbose:
                    print(f"{status} {root_note}_{chord_type} (oct {test_octave}) → "
                          f"Detected: {detected_chord or 'None':20s} SNR={snr:7.2f}")

                # Store results
                result_dict = {
                    'test_octave': test_octave,
                    'root_note': root_note,
                    'chord_type': chord_type,
                    'expected': expected_chord,
                    'detected': detected_chord,
                    'detected_flag': result['detected'],
                    'correct': correct,
                    'snr': snr
                }

                results.append(result_dict)
                results_by_octave[test_octave].append(result_dict)

    test_time = time.perf_counter() - start_test_time

    # Analyze results
    print("\n" + "=" * 80)
    print("RESULTS BY OCTAVE")
    print("=" * 80)

    print(f"\n{'Octave':>8s} {'Total':>8s} {'Detected':>10s} {'Correct':>10s} "
          f"{'Accuracy':>10s} {'Avg SNR':>10s}")
    print("-" * 80)

    octave_summaries = []

    for test_octave in test_octaves:
        octave_results = results_by_octave[test_octave]
        total = len(octave_results)
        detected = sum(1 for r in octave_results if r['detected_flag'])
        correct = sum(1 for r in octave_results if r['correct'])
        accuracy = 100 * correct / total if total > 0 else 0
        avg_snr = np.mean([r['snr'] for r in octave_results])

        print(f"{test_octave:8d} {total:8d} {detected:10d} {correct:10d} "
              f"{accuracy:9.1f}% {avg_snr:10.2f}")

        octave_summaries.append({
            'octave': test_octave,
            'total': total,
            'detected': detected,
            'correct': correct,
            'accuracy': accuracy,
            'avg_snr': avg_snr
        })

    print("-" * 80)

    # Overall summary
    total_tests = len(results)
    total_detected = sum(1 for r in results if r['detected_flag'])
    total_correct = sum(1 for r in results if r['correct'])
    overall_accuracy = 100 * total_correct / total_tests

    print(f"\nOVERALL:")
    print(f"  Total tests: {total_tests}")
    print(f"  Detected: {total_detected} ({100*total_detected/total_tests:.1f}%)")
    print(f"  Correct: {total_correct} ({overall_accuracy:.1f}%)")
    print(f"  Testing time: {test_time:.2f} seconds")
    print(f"  Rate: {total_tests / test_time:.1f} tests/sec")

    # Per chord type breakdown
    print("\n" + "-" * 80)
    print("PER CHORD TYPE:")
    print("-" * 80)

    for chord_type in test_chord_types:
        type_results = [r for r in results if r['chord_type'] == chord_type]
        type_total = len(type_results)
        type_correct = sum(1 for r in type_results if r['correct'])
        type_accuracy = 100 * type_correct / type_total if type_total > 0 else 0
        avg_snr = np.mean([r['snr'] for r in type_results])

        print(f"{chord_type:10s}: {type_correct:3d}/{type_total:3d} correct "
              f"({type_accuracy:5.1f}%) SNR={avg_snr:.2f}")

    # Failed detections
    failed = [r for r in results if not r['correct']]
    if failed:
        print("\n" + "-" * 80)
        print(f"FAILED DETECTIONS ({len(failed)} total):")
        print("-" * 80)

        if len(failed) <= 20:
            for r in failed:
                print(f"  Expected: {r['expected']:25s} → "
                      f"Detected: {r['detected'] or 'None':25s} SNR={r['snr']:6.2f}")
        else:
            print(f"  (Showing first 20 of {len(failed)} failures)")
            for r in failed[:20]:
                print(f"  Expected: {r['expected']:25s} → "
                      f"Detected: {r['detected'] or 'None':25s} SNR={r['snr']:6.2f}")

    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if overall_accuracy == 100:
        print("\n🎉 PERFECT! 100% accuracy across all octaves! 🎉")
        print("  → Multi-octave PSF templates work perfectly!")
        print("  → We now have comprehensive chord detection coverage")
    elif overall_accuracy >= 95:
        print(f"\n✓ Excellent! {overall_accuracy:.1f}% accuracy")
        print("  → Multi-octave detection works well")
    elif overall_accuracy >= 80:
        print(f"\n⚠ Good but needs improvement: {overall_accuracy:.1f}% accuracy")
    else:
        print(f"\n✗ Poor accuracy: {overall_accuracy:.1f}%")
        print("  → Need to investigate failures")

    print("\n" + "=" * 80)

    return {
        'results': results,
        'octave_summaries': octave_summaries,
        'overall_accuracy': overall_accuracy,
        'test_time': test_time
    }


if __name__ == "__main__":
    print("\nTesting multi-octave chord detection...\n")

    results = test_multi_octave_detection(
        template_path="multi_octave_psf_templates.pkl",
        verbose=True
    )

    print("\n✓ Multi-octave detection test complete!")
