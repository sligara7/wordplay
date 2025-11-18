"""
Comprehensive PSF-Based Chord Detection Test

Tests ALL chord types (including 7th, 9th, 11th) across ALL roots
using PSF templates generated through spectral_analyzer.py

Verifies repeatability with multiple runs.
"""

import numpy as np
from spectral_analyzer import SpectralAnalyzer
from bht_chord_detector_fast import FastMHTChordDetector
from build_chord_psf import (
    build_all_chord_psfs,
    generate_pure_chord_audio,
    CHORD_INTERVALS,
    ROOT_NOTES
)
import time


def test_all_chords_with_psf(num_runs=3, verbose=True):
    """
    Test ALL chord types with PSF templates.

    Tests: 11 chord types × 12 roots × num_runs = 132 × num_runs tests

    Args:
        num_runs: Number of times to repeat each test (for repeatability)
        verbose: Print detailed results

    Returns:
        dict with results
    """
    print("=" * 80)
    print("COMPREHENSIVE PSF-BASED CHORD DETECTION TEST")
    print("=" * 80)

    # Setup
    sample_rate = 44100
    cycles = 4
    all_chord_types = list(CHORD_INTERVALS.keys())
    all_roots = ROOT_NOTES

    print(f"\nConfiguration:")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Cycles: {cycles}")
    print(f"  Chord types: {len(all_chord_types)}")
    print(f"  Root notes: {len(all_roots)}")
    print(f"  Runs per chord: {num_runs}")
    print(f"  Total tests: {len(all_chord_types) * len(all_roots) * num_runs}")

    # Step 1: Build PSF templates for ALL chords
    print(f"\n1. Building PSF templates for ALL chord types...")
    start_time = time.perf_counter()

    psf_templates, frequencies = build_all_chord_psfs(
        sample_rate=sample_rate,
        cycles=cycles,
        octave=4,
        chord_types=all_chord_types,
        root_notes=all_roots
    )

    template_time = time.perf_counter() - start_time
    print(f"\n   Template generation time: {template_time:.2f} seconds")

    # Step 2: Initialize detector
    print(f"\n2. Initializing detector...")
    detector = FastMHTChordDetector(
        psf_templates,
        threshold=6.5,
        use_outlier_removal=False  # Clean signals don't need outlier removal
    )

    # Step 3: Initialize spectral analyzer
    print(f"\n3. Initializing spectral analyzer...")
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Step 4: Test all chords (multiple runs)
    print(f"\n4. Testing all chords ({num_runs} runs each)...")
    print("-" * 80)

    all_results = []
    snr_by_chord_type = {ct: [] for ct in all_chord_types}

    start_test_time = time.perf_counter()

    for run in range(num_runs):
        if num_runs > 1:
            print(f"\n--- Run {run + 1}/{num_runs} ---")

        for chord_type in all_chord_types:
            if verbose:
                print(f"\n{chord_type.upper()}:")

            for root_note in all_roots:
                # Generate test audio (pure sinusoids)
                test_audio = generate_pure_chord_audio(
                    root_note, chord_type,
                    octave=4,
                    duration_sec=cycles / (440.0 / 16),
                    sample_rate=sample_rate,
                    amplitude=0.5
                )

                # Analyze with spectral_analyzer (same as template generation)
                spectral_data = analyzer.dotop(test_audio)

                # Extract middle time slice
                mid_time = spectral_data.shape[1] // 2
                spectrum = spectral_data[:, mid_time]

                # Detect
                result = detector.detect(spectrum)

                # Parse result
                true_chord = f"{root_note}_{chord_type}"
                detected_chord = result['chord'] if result['detected'] else None
                snr = result['snr']

                # Check correctness
                correct = (detected_chord == true_chord)
                status = "✓" if correct else "✗"

                if verbose:
                    print(f"{status} {true_chord:15s} → Detected: {detected_chord or 'None':20s} "
                          f"SNR={snr:7.2f}")

                # Store results
                all_results.append({
                    'run': run,
                    'true_chord': true_chord,
                    'true_root': root_note,
                    'true_type': chord_type,
                    'detected_chord': detected_chord,
                    'detected': result['detected'],
                    'correct': correct,
                    'snr': snr
                })

                # Track SNR by chord type
                snr_by_chord_type[chord_type].append(snr)

    test_time = time.perf_counter() - start_test_time

    # Calculate statistics
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    total_tests = len(all_results)
    detected_count = sum(1 for r in all_results if r['detected'])
    correct_count = sum(1 for r in all_results if r['correct'])

    print(f"\nTotal tests:        {total_tests}")
    print(f"Detected:           {detected_count} ({100*detected_count/total_tests:.1f}%)")
    print(f"Correct:            {correct_count} ({100*correct_count/total_tests:.1f}%)")

    if detected_count > 0:
        accuracy = 100 * correct_count / detected_count
        print(f"Accuracy:           {accuracy:.1f}%")

    print(f"\nTesting time:       {test_time:.2f} seconds")
    print(f"Rate:               {total_tests / test_time:.0f} tests/sec")

    # Per-chord-type breakdown
    print("\n" + "-" * 80)
    print("PER CHORD TYPE ACCURACY:")
    print("-" * 80)
    print(f"{'Chord Type':12s} {'Notes':>6s} {'Total':>7s} {'Correct':>8s} "
          f"{'Accuracy':>10s} {'Avg SNR':>10s} {'SNR Std':>10s}")
    print("-" * 80)

    for chord_type in all_chord_types:
        type_results = [r for r in all_results if r['true_type'] == chord_type]
        type_total = len(type_results)
        type_correct = sum(1 for r in type_results if r['correct'])
        type_accuracy = 100 * type_correct / type_total if type_total > 0 else 0

        # SNR statistics
        snrs = snr_by_chord_type[chord_type]
        avg_snr = np.mean(snrs)
        std_snr = np.std(snrs)

        # Number of notes in chord
        num_notes = len(CHORD_INTERVALS[chord_type])

        print(f"{chord_type:12s} {num_notes:6d} {type_total:7d} {type_correct:8d} "
              f"{type_accuracy:9.1f}% {avg_snr:10.2f} {std_snr:10.2f}")

    print("-" * 80)

    # Repeatability check (if multiple runs)
    if num_runs > 1:
        print("\n" + "-" * 80)
        print("REPEATABILITY CHECK:")
        print("-" * 80)

        # Check if same chord gives same result across runs
        unique_chords = list(set(r['true_chord'] for r in all_results))

        consistent_count = 0
        inconsistent = []

        for chord in unique_chords:
            chord_results = [r for r in all_results if r['true_chord'] == chord]

            # Check if all runs gave same result
            detected_chords = [r['detected_chord'] for r in chord_results]
            all_same = len(set(detected_chords)) == 1

            if all_same:
                consistent_count += 1
            else:
                inconsistent.append((chord, detected_chords))

        print(f"Consistent across runs: {consistent_count}/{len(unique_chords)} "
              f"({100*consistent_count/len(unique_chords):.1f}%)")

        if inconsistent:
            print(f"\nInconsistent detections ({len(inconsistent)}):")
            for chord, results in inconsistent[:10]:  # Show first 10
                print(f"  {chord}: {results}")

    # Failed detections
    failed = [r for r in all_results if not r['correct']]
    if failed:
        print("\n" + "-" * 80)
        print(f"FAILED DETECTIONS ({len(failed)} total):")
        print("-" * 80)

        if len(failed) <= 20:
            for r in failed:
                print(f"  {r['true_chord']:15s} → {r['detected_chord'] or 'None':20s} "
                      f"(SNR={r['snr']:6.2f}, Run {r['run']+1})")
        else:
            print(f"  (Too many to list - showing first 20)")
            for r in failed[:20]:
                print(f"  {r['true_chord']:15s} → {r['detected_chord'] or 'None':20s} "
                      f"(SNR={r['snr']:6.2f}, Run {r['run']+1})")

    print("\n" + "=" * 80)

    # Return summary
    return {
        'total_tests': total_tests,
        'detected': detected_count,
        'correct': correct_count,
        'accuracy': 100 * correct_count / total_tests,
        'test_time': test_time,
        'template_time': template_time,
        'results': all_results,
        'snr_by_type': snr_by_chord_type,
        'num_runs': num_runs,
        'consistent': consistent_count if num_runs > 1 else total_tests
    }


def analyze_snr_patterns(results_summary):
    """
    Analyze SNR patterns across chord complexity.

    Args:
        results_summary: Output from test_all_chords_with_psf
    """
    import matplotlib.pyplot as plt

    snr_by_type = results_summary['snr_by_type']

    # Group by number of notes
    snr_by_complexity = {}

    for chord_type, snrs in snr_by_type.items():
        num_notes = len(CHORD_INTERVALS[chord_type])

        if num_notes not in snr_by_complexity:
            snr_by_complexity[num_notes] = []

        snr_by_complexity[num_notes].extend(snrs)

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: SNR by chord type
    chord_types = list(CHORD_INTERVALS.keys())
    avg_snrs = [np.mean(snr_by_type[ct]) for ct in chord_types]
    std_snrs = [np.std(snr_by_type[ct]) for ct in chord_types]
    num_notes = [len(CHORD_INTERVALS[ct]) for ct in chord_types]

    colors = ['green' if avg > 6.5 else 'red' for avg in avg_snrs]

    bars = ax1.bar(range(len(chord_types)), avg_snrs, yerr=std_snrs,
                   color=colors, alpha=0.7, capsize=5)
    ax1.set_xticks(range(len(chord_types)))
    ax1.set_xticklabels(chord_types, rotation=45, ha='right')
    ax1.set_ylabel('Average SNR')
    ax1.set_title('SNR by Chord Type')
    ax1.axhline(y=6.5, color='black', linestyle='--', linewidth=2, label='Threshold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Add note count labels
    for i, (bar, nn) in enumerate(zip(bars, num_notes)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std_snrs[i] + 0.5,
                f'{nn} notes', ha='center', va='bottom', fontsize=8)

    # Plot 2: SNR vs complexity (number of notes)
    complexities = sorted(snr_by_complexity.keys())
    avg_by_complexity = [np.mean(snr_by_complexity[c]) for c in complexities]
    std_by_complexity = [np.std(snr_by_complexity[c]) for c in complexities]

    ax2.errorbar(complexities, avg_by_complexity, yerr=std_by_complexity,
                fmt='o-', linewidth=2, markersize=10, capsize=5, color='blue')
    ax2.set_xlabel('Number of Notes in Chord')
    ax2.set_ylabel('Average SNR')
    ax2.set_title('SNR vs Chord Complexity')
    ax2.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(complexities)

    plt.tight_layout()
    plt.savefig('psf_snr_analysis.png', dpi=150)
    print("\n✓ Saved SNR analysis to: psf_snr_analysis.png")

    return fig


if __name__ == "__main__":
    # Run comprehensive test with multiple runs for repeatability
    print("\nTesting ALL chord types with PSF templates...\n")

    results = test_all_chords_with_psf(
        num_runs=3,  # Run each test 3 times
        verbose=False  # Set to True to see all individual results
    )

    # Analyze SNR patterns
    print("\nAnalyzing SNR patterns...")
    analyze_snr_patterns(results)

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"✓ Total tests:        {results['total_tests']}")
    print(f"✓ Accuracy:           {results['accuracy']:.1f}%")
    print(f"✓ Consistent:         {results['consistent']}/{results['total_tests']//results['num_runs']} "
          f"({100*results['consistent']/(results['total_tests']//results['num_runs']):.1f}%)")
    print(f"✓ Template gen time:  {results['template_time']:.2f} sec")
    print(f"✓ Testing time:       {results['test_time']:.2f} sec")
    print(f"✓ Rate:               {results['total_tests'] / results['test_time']:.0f} tests/sec")
    print("=" * 80)

    if results['accuracy'] == 100.0:
        print("\n🎉 PERFECT! 100% accuracy achieved! 🎉")
    elif results['accuracy'] >= 95.0:
        print(f"\n✓ Excellent! {results['accuracy']:.1f}% accuracy")
    elif results['accuracy'] >= 80.0:
        print(f"\n✓ Good! {results['accuracy']:.1f}% accuracy")
    else:
        print(f"\n⚠ Needs improvement: {results['accuracy']:.1f}% accuracy")

    print("\n✓ Test complete!")
