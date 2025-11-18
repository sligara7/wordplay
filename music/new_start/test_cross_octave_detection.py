"""
Test Cross-Octave Chord Detection

Tests whether octave-4 PSF templates can detect chords in other octaves.

This answers the question: "Do we need PSF templates for every octave?"

Test strategy:
1. Generate PSF templates for octave 4 (our current set)
2. Generate test chords in octaves 2, 3, 4, 5, 6
3. Check detection accuracy across octaves

If octave-4 templates can detect chords in other octaves → We're done!
If not → We need to generate multi-octave templates.
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


def test_cross_octave_detection(verbose=True):
    """
    Test cross-octave detection capability.

    Returns:
        dict with results broken down by template octave vs test octave
    """
    print("=" * 80)
    print("CROSS-OCTAVE DETECTION TEST")
    print("=" * 80)

    sample_rate = 44100
    cycles = 4

    # Test parameters
    test_octaves = [2, 3, 4, 5, 6]  # Octaves to test
    template_octave = 4              # Templates are generated for octave 4
    test_chord_types = ['major', 'minor', 'dim']  # Subset for speed
    test_roots = ['C', 'E', 'G']     # Subset for speed

    print(f"\nConfiguration:")
    print(f"  Template octave: {template_octave}")
    print(f"  Test octaves: {test_octaves}")
    print(f"  Chord types: {test_chord_types}")
    print(f"  Root notes: {test_roots}")
    print(f"  Total tests: {len(test_octaves) * len(test_chord_types) * len(test_roots)}")

    # Step 1: Build PSF templates for octave 4
    print(f"\n1. Building PSF templates (octave {template_octave})...")
    psf_templates, frequencies = build_all_chord_psfs(
        sample_rate=sample_rate,
        cycles=cycles,
        octave=template_octave,
        chord_types=test_chord_types,
        root_notes=test_roots
    )

    print(f"   Templates generated: {len(psf_templates)}")

    # Step 2: Initialize detector
    print(f"\n2. Initializing detector...")
    detector = FastMHTChordDetector(
        psf_templates,
        threshold=6.5,
        use_outlier_removal=False
    )

    # Step 3: Initialize spectral analyzer
    print(f"\n3. Initializing spectral analyzer...")
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Step 4: Test across octaves
    print(f"\n4. Testing chords across octaves...")
    print("-" * 80)

    results = []
    results_by_octave = {octave: [] for octave in test_octaves}

    for test_octave in test_octaves:
        print(f"\n--- Testing Octave {test_octave} ---")

        for chord_type in test_chord_types:
            if verbose:
                print(f"\n{chord_type.upper()}:")

            for root_note in test_roots:
                # Generate test audio in test_octave
                test_audio = generate_pure_chord_audio(
                    root_note, chord_type,
                    octave=test_octave,  # Test in different octave!
                    duration_sec=cycles / (440.0 / 16),
                    sample_rate=sample_rate,
                    amplitude=0.5
                )

                # Analyze
                spectral_data = analyzer.dotop(test_audio)
                mid_time = spectral_data.shape[1] // 2
                spectrum = spectral_data[:, mid_time]

                # Detect (using octave-4 templates!)
                result = detector.detect(spectrum)

                # Expected chord (template is in octave 4)
                template_chord = f"{root_note}_{chord_type}"
                detected_chord = result['chord'] if result['detected'] else None
                snr = result['snr']

                # Check correctness
                # IMPORTANT: We expect the detector to identify the CHORD TYPE and ROOT,
                # but the template is from octave 4 while test is in test_octave
                correct = (detected_chord == template_chord)
                status = "✓" if correct else "✗"

                if verbose:
                    print(f"{status} {root_note}_{chord_type} (octave {test_octave}) → "
                          f"Detected: {detected_chord or 'None':15s} SNR={snr:7.2f}")

                # Store results
                result_dict = {
                    'template_octave': template_octave,
                    'test_octave': test_octave,
                    'octave_diff': test_octave - template_octave,
                    'root_note': root_note,
                    'chord_type': chord_type,
                    'expected': template_chord,
                    'detected': detected_chord,
                    'detected_flag': result['detected'],
                    'correct': correct,
                    'snr': snr
                }

                results.append(result_dict)
                results_by_octave[test_octave].append(result_dict)

    # Step 5: Analyze results
    print("\n" + "=" * 80)
    print("RESULTS BY OCTAVE")
    print("=" * 80)

    print(f"\n{'Octave':>8s} {'Δ Octave':>10s} {'Total':>8s} {'Detected':>10s} "
          f"{'Correct':>10s} {'Accuracy':>10s} {'Avg SNR':>10s}")
    print("-" * 80)

    octave_summaries = []

    for test_octave in test_octaves:
        octave_results = results_by_octave[test_octave]
        total = len(octave_results)
        detected = sum(1 for r in octave_results if r['detected_flag'])
        correct = sum(1 for r in octave_results if r['correct'])
        accuracy = 100 * correct / total if total > 0 else 0
        avg_snr = np.mean([r['snr'] for r in octave_results])
        octave_diff = test_octave - template_octave

        print(f"{test_octave:8d} {octave_diff:+10d} {total:8d} {detected:10d} "
              f"{correct:10d} {accuracy:9.1f}% {avg_snr:10.2f}")

        octave_summaries.append({
            'octave': test_octave,
            'octave_diff': octave_diff,
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

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    same_octave = [s for s in octave_summaries if s['octave_diff'] == 0]
    different_octave = [s for s in octave_summaries if s['octave_diff'] != 0]

    if same_octave:
        same_octave_acc = same_octave[0]['accuracy']
        print(f"\nSame octave (test=template=4): {same_octave_acc:.1f}% accuracy")

    if different_octave:
        diff_octave_acc = np.mean([s['accuracy'] for s in different_octave])
        print(f"Different octave (test≠template): {diff_octave_acc:.1f}% accuracy")

    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if overall_accuracy >= 95:
        print("\n✓ Cross-octave detection WORKS!")
        print("  → Octave-4 templates can detect chords in other octaves")
        print("  → We do NOT need PSF templates for every octave")
        print("  → Current 132 templates are sufficient")
    elif overall_accuracy >= 50:
        print("\n⚠ Partial cross-octave detection")
        print("  → Some octaves work, others don't")
        print("  → May need templates for adjacent octaves (3, 4, 5)")
    else:
        print("\n✗ Cross-octave detection FAILS!")
        print("  → Octave-4 templates cannot detect chords in other octaves")
        print("  → We NEED PSF templates for multiple octaves")
        print("  → Recommend generating templates for octaves 2-6")

    # Visualize results
    print("\n5. Generating visualizations...")
    visualize_cross_octave_results(octave_summaries)

    print("\n" + "=" * 80)

    return {
        'results': results,
        'octave_summaries': octave_summaries,
        'overall_accuracy': overall_accuracy,
        'same_octave_accuracy': same_octave_acc if same_octave else None,
        'cross_octave_accuracy': diff_octave_acc if different_octave else None
    }


def visualize_cross_octave_results(octave_summaries):
    """
    Visualize cross-octave detection results.
    """
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    octaves = [s['octave'] for s in octave_summaries]
    accuracies = [s['accuracy'] for s in octave_summaries]
    snrs = [s['avg_snr'] for s in octave_summaries]
    octave_diffs = [s['octave_diff'] for s in octave_summaries]

    # Color based on octave difference
    colors = ['green' if diff == 0 else 'orange' if abs(diff) == 1 else 'red'
              for diff in octave_diffs]

    # Plot 1: Accuracy by octave
    bars1 = ax1.bar(octaves, accuracies, color=colors, alpha=0.7)
    ax1.set_xlabel('Test Octave')
    ax1.set_ylabel('Accuracy (%)')
    ax1.set_title('Cross-Octave Detection Accuracy\n(Template Octave = 4)')
    ax1.axhline(y=95, color='green', linestyle='--', linewidth=2, label='95% threshold')
    ax1.axhline(y=50, color='orange', linestyle='--', linewidth=2, label='50% threshold')
    ax1.set_ylim([0, 105])
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_xticks(octaves)

    # Add octave difference labels
    for i, (bar, diff) in enumerate(zip(bars1, octave_diffs)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'Δ={diff:+d}', ha='center', va='bottom', fontsize=9)

    # Plot 2: SNR by octave
    ax2.plot(octaves, snrs, 'bo-', linewidth=2, markersize=10, label='Avg SNR')
    ax2.set_xlabel('Test Octave')
    ax2.set_ylabel('Average SNR')
    ax2.set_title('Cross-Octave Detection SNR\n(Template Octave = 4)')
    ax2.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Detection threshold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(octaves)

    # Add value labels
    for octave, snr in zip(octaves, snrs):
        ax2.text(octave, snr + 0.5, f'{snr:.1f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig('cross_octave_detection_results.png', dpi=150)
    print("   ✓ Saved visualization to: cross_octave_detection_results.png")


if __name__ == "__main__":
    print("\nTesting cross-octave detection capability...\n")

    results = test_cross_octave_detection(verbose=True)

    print("\n✓ Test complete!")
    print(f"\nKey result: {results['overall_accuracy']:.1f}% overall accuracy across all octaves")

    if results['cross_octave_accuracy'] is not None:
        print(f"Cross-octave accuracy: {results['cross_octave_accuracy']:.1f}%")
