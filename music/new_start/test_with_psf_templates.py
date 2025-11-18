"""
Test Chord Detection with PSF Templates

Uses templates generated from actual spectral_analyzer.py
instead of synthetic Gaussians.
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


def test_psf_based_detection():
    """
    Test chord detection using PSF templates.

    This is the CORRECT approach:
    1. Generate PSF templates using spectral_analyzer
    2. Generate test audio (pure sinusoids)
    3. Analyze test audio using spectral_analyzer
    4. Detect using MHT with PSF templates
    """
    print("=" * 80)
    print("CHORD DETECTION WITH PSF TEMPLATES")
    print("=" * 80)

    # Setup
    sample_rate = 44100
    cycles = 4

    # Step 1: Build PSF templates
    print("\n1. Building PSF templates...")
    psf_templates, frequencies = build_all_chord_psfs(
        sample_rate=sample_rate,
        cycles=cycles,
        octave=4,
        chord_types=['major', 'minor', 'dim'],
        root_notes=['C', 'D', 'E', 'F', 'G', 'A', 'B']
    )

    print(f"   Templates: {len(psf_templates)}")
    print(f"   Frequency bins: {len(frequencies)}")

    # Step 2: Initialize detector
    print("\n2. Initializing detector...")
    detector = FastMHTChordDetector(
        psf_templates,
        threshold=6.5,
        use_outlier_removal=False  # Disable for clean test signals
    )

    # Step 3: Initialize spectral analyzer
    print("\n3. Initializing spectral analyzer...")
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Step 4: Test all chords
    print("\n4. Testing chord detection...")
    print("-" * 80)

    results = []

    for chord_type in ['major', 'minor', 'dim']:
        print(f"\n{chord_type.upper()}:")

        for root_note in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
            # Generate test audio
            test_audio = generate_pure_chord_audio(
                root_note, chord_type,
                octave=4,
                duration_sec=cycles / (440.0 / 16),
                sample_rate=sample_rate,
                amplitude=0.5
            )

            # Analyze with spectral_analyzer
            spectral_data = analyzer.dotop(test_audio)

            # Extract single time slice (middle of the signal)
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

            print(f"{status} {true_chord:10s} → Detected: {detected_chord or 'None':15s} "
                  f"SNR={snr:7.2f}")

            results.append({
                'true': true_chord,
                'detected': detected_chord,
                'correct': correct,
                'snr': snr
            })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    detected = sum(1 for r in results if r['detected'] is not None)
    correct = sum(1 for r in results if r['correct'])

    print(f"\nTotal tests:     {total}")
    print(f"Detected:        {detected} ({100*detected/total:.1f}%)")
    print(f"Correct:         {correct} ({100*correct/total:.1f}%)")

    if detected > 0:
        accuracy = 100 * correct / detected
        print(f"Accuracy (of detected): {accuracy:.1f}%")

    # Per-chord-type breakdown
    print("\n" + "-" * 80)
    print("PER CHORD TYPE:")
    print("-" * 80)

    for chord_type in ['major', 'minor', 'dim']:
        type_results = [r for r in results if chord_type in r['true']]
        type_total = len(type_results)
        type_correct = sum(1 for r in type_results if r['correct'])

        print(f"{chord_type:10s}: {type_correct}/{type_total} correct "
              f"({100*type_correct/type_total:.1f}%)")

    print("=" * 80)

    return results


def compare_psf_vs_gaussian():
    """
    Compare PSF-based templates vs Gaussian templates.
    """
    print("\n" + "=" * 80)
    print("COMPARISON: PSF vs GAUSSIAN TEMPLATES")
    print("=" * 80)

    sample_rate = 44100
    cycles = 4

    # Build PSF templates
    print("\n1. Building PSF templates (using spectral_analyzer)...")
    psf_templates, psf_frequencies = build_all_chord_psfs(
        sample_rate=sample_rate,
        cycles=cycles,
        octave=4,
        chord_types=['major'],
        root_notes=['C']
    )

    # Build Gaussian templates (old method)
    print("\n2. Building Gaussian templates (old method)...")
    from bht_chord_detector import build_chord_templates

    # Match frequency bins to PSF
    gaussian_templates = build_chord_templates(
        psf_frequencies,
        chord_types=['major'],
        template_type='gaussian',
        sigma_hz=10.0
    )

    # Compare C_major templates
    psf_C = psf_templates['C_major']
    gaussian_C = gaussian_templates['C_major']

    print("\n3. Comparing C_major templates...")
    print("-" * 80)
    print(f"{'Metric':30s} {'PSF':>15s} {'Gaussian':>15s}")
    print("-" * 80)
    print(f"{'Norm':30s} {np.linalg.norm(psf_C):15.4f} {np.linalg.norm(gaussian_C):15.4f}")
    print(f"{'Max value':30s} {np.max(psf_C):15.4f} {np.max(gaussian_C):15.4f}")
    print(f"{'Non-zero bins':30s} {np.sum(psf_C > 0.01):15.0f} {np.sum(gaussian_C > 0.01):15.0f}")
    print(f"{'Energy in 200-500 Hz':30s} {np.sum(psf_C[np.where((psf_frequencies > 200) & (psf_frequencies < 500))[0]]):15.4f} "
          f"{np.sum(gaussian_C[np.where((psf_frequencies > 200) & (psf_frequencies < 500))[0]]):15.4f}")

    # Correlation between templates
    correlation = np.dot(psf_C, gaussian_C)
    print(f"{'Correlation (PSF · Gaussian)':30s} {correlation:15.4f}")

    print("-" * 80)

    # Visualize comparison
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

    # Zoom to relevant range
    mask = (psf_frequencies >= 200) & (psf_frequencies <= 500)

    # Plot 1: PSF template
    ax1.plot(psf_frequencies[mask], psf_C[mask], 'b-', linewidth=2, label='PSF (from spectral_analyzer)')
    ax1.set_ylabel('Amplitude')
    ax1.set_title('PSF Template (Generated via Spectral Analyzer)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axvline(261.63, color='r', linestyle='--', alpha=0.5, label='C4')
    ax1.axvline(329.63, color='g', linestyle='--', alpha=0.5, label='E4')
    ax1.axvline(392.00, color='b', linestyle='--', alpha=0.5, label='G4')

    # Plot 2: Gaussian template
    ax2.plot(psf_frequencies[mask], gaussian_C[mask], 'r-', linewidth=2, label='Gaussian (synthetic)')
    ax2.set_ylabel('Amplitude')
    ax2.set_title('Gaussian Template (Synthetic)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axvline(261.63, color='r', linestyle='--', alpha=0.5)
    ax2.axvline(329.63, color='g', linestyle='--', alpha=0.5)
    ax2.axvline(392.00, color='b', linestyle='--', alpha=0.5)

    # Plot 3: Overlay
    ax3.plot(psf_frequencies[mask], psf_C[mask], 'b-', linewidth=2, label='PSF', alpha=0.7)
    ax3.plot(psf_frequencies[mask], gaussian_C[mask], 'r--', linewidth=2, label='Gaussian', alpha=0.7)
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('Amplitude')
    ax3.set_title('Overlay Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('psf_vs_gaussian_comparison.png', dpi=150)
    print("\n✓ Saved comparison to: psf_vs_gaussian_comparison.png")

    return psf_C, gaussian_C


if __name__ == "__main__":
    # Test 1: PSF-based detection
    results = test_psf_based_detection()

    # Test 2: Compare PSF vs Gaussian
    psf_C, gaussian_C = compare_psf_vs_gaussian()

    print("\n✓ All tests complete!")
