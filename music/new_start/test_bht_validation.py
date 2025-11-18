"""
Validation script for BHT/MHT chord detection.

Tests with varying SNR levels and visualizes results.
"""

import numpy as np
import matplotlib.pyplot as plt
from bht_chord_detector import (
    BHTChordDetector,
    MHTChordDetector,
    build_chord_templates
)


def generate_chord_spectrum(frequencies,
                            chord_freqs,
                            signal_amplitude=50.0,
                            noise_amplitude=1.0,
                            sigma_hz=5.0):
    """
    Generate synthetic spectral data for a chord.

    Args:
        frequencies: Frequency bins
        chord_freqs: List of frequencies in chord
        signal_amplitude: Peak amplitude of signal
        noise_amplitude: Amplitude of background noise
        sigma_hz: Spread of Gaussian peaks

    Returns:
        1D array of spectral amplitudes
    """
    # Create signal (chord peaks)
    spectrum = np.zeros(len(frequencies))

    for i, freq in enumerate(chord_freqs):
        # Each note gets progressively weaker (fundamental is strongest)
        amplitude = signal_amplitude * (0.8 ** i)
        gaussian = amplitude * np.exp(-(frequencies - freq)**2 / (2*sigma_hz**2))
        spectrum += gaussian

    # Add noise
    spectrum += noise_amplitude * np.abs(np.random.randn(len(frequencies)))

    # Ensure non-negative
    spectrum = np.maximum(spectrum, 0)

    return spectrum


def test_snr_sweep():
    """Test detection performance vs SNR."""
    print("=" * 70)
    print("BHT/MHT Chord Detection - SNR Sweep Test")
    print("=" * 70)

    # Setup
    A0 = 27.5
    frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)

    # C major chord frequencies
    C4 = 261.63  # C4
    E4 = 329.63  # E4
    G4 = 392.00  # G4
    chord_freqs = [C4, E4, G4]

    # Build templates
    print("\nBuilding chord templates...")
    templates = build_chord_templates(
        frequencies,
        chord_types=['major', 'minor', 'dim', 'aug'],
        template_type='gaussian',
        sigma_hz=10.0
    )
    print(f"Generated {len(templates)} templates")

    # Initialize detectors
    bht = BHTChordDetector(
        templates['C_major'],
        'C_major',
        threshold=6.0
    )

    mht = MHTChordDetector(
        templates,
        threshold=6.5
    )

    # Test with varying signal levels
    print("\nTesting with varying signal-to-noise ratios:")
    print("-" * 70)
    print(f"{'Signal':>8} {'Noise':>8} {'SNR_dB':>8} {'BHT_SNR':>10} "
          f"{'MHT_SNR':>10} {'Detected':>10} {'Best Chord':>15}")
    print("-" * 70)

    signal_levels = [10, 20, 30, 40, 50, 75, 100, 150, 200]
    noise_level = 1.0

    results = []

    for signal_amp in signal_levels:
        # Generate spectrum
        spectrum = generate_chord_spectrum(
            frequencies,
            chord_freqs,
            signal_amplitude=signal_amp,
            noise_amplitude=noise_level,
            sigma_hz=5.0
        )

        # Calculate theoretical SNR (dB)
        signal_power = signal_amp ** 2
        noise_power = noise_level ** 2
        snr_db = 10 * np.log10(signal_power / noise_power)

        # Test BHT
        bht_result = bht.detect(spectrum)

        # Test MHT
        mht_result = mht.detect(spectrum)

        detected = "YES" if mht_result['detected'] else "NO"
        best_chord = mht_result['chord'] if mht_result['detected'] else "None"

        print(f"{signal_amp:8.1f} {noise_level:8.1f} {snr_db:8.1f} "
              f"{bht_result['snr']:10.2f} {mht_result['snr']:10.2f} "
              f"{detected:>10} {best_chord:>15}")

        results.append({
            'signal_amp': signal_amp,
            'snr_db': snr_db,
            'bht_snr': bht_result['snr'],
            'mht_snr': mht_result['snr'],
            'detected': mht_result['detected'],
            'best_chord': best_chord
        })

    print("-" * 70)

    return results, frequencies, templates


def test_chord_discrimination():
    """Test ability to discriminate between different chords."""
    print("\n" + "=" * 70)
    print("Chord Discrimination Test")
    print("=" * 70)

    # Setup
    A0 = 27.5
    frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)

    # Define chords to test
    test_chords = {
        'C_major': [261.63, 329.63, 392.00],    # C4, E4, G4
        'C_minor': [261.63, 311.13, 392.00],    # C4, D#4, G4
        'C_dim':   [261.63, 311.13, 369.99],    # C4, D#4, F#4
        'G_major': [392.00, 493.88, 587.33],    # G4, B4, D5
    }

    # Build templates
    templates = build_chord_templates(
        frequencies,
        chord_types=['major', 'minor', 'dim', 'aug'],
        template_type='gaussian',
        sigma_hz=10.0
    )

    # Initialize MHT detector
    mht = MHTChordDetector(templates, threshold=6.5)

    print("\nTesting chord discrimination (signal_amp=100, noise=1.0):")
    print("-" * 70)
    print(f"{'True Chord':>15} {'Detected':>15} {'SNR':>8} {'Correct':>10}")
    print("-" * 70)

    for true_chord, chord_freqs in test_chords.items():
        # Generate spectrum
        spectrum = generate_chord_spectrum(
            frequencies,
            chord_freqs,
            signal_amplitude=100.0,
            noise_amplitude=1.0,
            sigma_hz=5.0
        )

        # Detect
        result = mht.detect(spectrum)

        detected = result['chord'] if result['detected'] else "None"
        correct = "YES" if detected == true_chord else "NO"

        print(f"{true_chord:>15} {detected:>15} {result['snr']:8.2f} {correct:>10}")

        # Show top 3 candidates
        if result['detected']:
            print(f"{'':>15} Top 3 candidates:")
            for i, (chord, snr) in enumerate(result['top_5_chords'][:3], 1):
                marker = "***" if chord == true_chord else "   "
                print(f"{'':>15} {marker} {i}. {chord:15s} SNR={snr:6.2f}")

    print("-" * 70)


def plot_results(results):
    """Plot SNR sweep results."""
    snr_dbs = [r['snr_db'] for r in results]
    bht_snrs = [r['bht_snr'] for r in results]
    mht_snrs = [r['mht_snr'] for r in results]
    detected = [r['detected'] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: SNR vs signal amplitude
    ax1.plot(snr_dbs, bht_snrs, 'b-o', label='BHT SNR', linewidth=2)
    ax1.plot(snr_dbs, mht_snrs, 'r-s', label='MHT SNR', linewidth=2)
    ax1.axhline(y=6.0, color='b', linestyle='--', label='BHT threshold (γ=6.0)')
    ax1.axhline(y=6.5, color='r', linestyle='--', label='MHT threshold (γ=6.5)')
    ax1.set_xlabel('Input SNR (dB)', fontsize=12)
    ax1.set_ylabel('Detector SNR', fontsize=12)
    ax1.set_title('Matched-Filter SNR vs Input SNR', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Detection success
    colors = ['red' if not d else 'green' for d in detected]
    ax2.scatter(snr_dbs, mht_snrs, c=colors, s=100, alpha=0.6)
    ax2.axhline(y=6.5, color='k', linestyle='--', label='Detection threshold')
    ax2.set_xlabel('Input SNR (dB)', fontsize=12)
    ax2.set_ylabel('MHT SNR', fontsize=12)
    ax2.set_title('Detection Success (Green=Detected, Red=Missed)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('bht_mht_validation.png', dpi=150)
    print(f"\nSaved plot to: bht_mht_validation.png")

    return fig


def visualize_template_matching():
    """Visualize how template matching works."""
    print("\n" + "=" * 70)
    print("Template Matching Visualization")
    print("=" * 70)

    # Setup
    A0 = 27.5
    frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)

    # C major chord
    C4, E4, G4 = 261.63, 329.63, 392.00

    # Generate spectrum
    spectrum = generate_chord_spectrum(
        frequencies,
        [C4, E4, G4],
        signal_amplitude=100.0,
        noise_amplitude=1.0,
        sigma_hz=5.0
    )

    # Build templates
    templates = build_chord_templates(
        frequencies,
        chord_types=['major'],
        template_type='gaussian',
        sigma_hz=10.0
    )

    # Get C major and G major templates
    h_Cmaj = templates['C_major']
    h_Gmaj = templates['G_major']

    # Plot
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))

    # Plot 1: Input spectrum
    ax = axes[0]
    ax.plot(frequencies, spectrum, 'k-', linewidth=1)
    ax.axvline(C4, color='r', linestyle='--', alpha=0.5, label='C4')
    ax.axvline(E4, color='g', linestyle='--', alpha=0.5, label='E4')
    ax.axvline(G4, color='b', linestyle='--', alpha=0.5, label='G4')
    ax.set_xlim([200, 500])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Input Spectrum (C Major Chord + Noise)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: C major template
    ax = axes[1]
    ax.plot(frequencies, h_Cmaj * 50, 'r-', linewidth=1)
    ax.set_xlim([200, 500])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Template Amplitude')
    ax.set_title('C Major Template (scaled for visualization)')
    ax.grid(True, alpha=0.3)

    # Plot 3: G major template (wrong chord)
    ax = axes[2]
    ax.plot(frequencies, h_Gmaj * 50, 'b-', linewidth=1)
    ax.set_xlim([200, 500])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Template Amplitude')
    ax.set_title('G Major Template (wrong chord - for comparison)')
    ax.grid(True, alpha=0.3)

    # Plot 4: Product (spectrum × template)
    ax = axes[3]
    product_C = spectrum * h_Cmaj
    product_G = spectrum * h_Gmaj
    ax.plot(frequencies, product_C, 'r-', linewidth=1, label='Spectrum × C_major', alpha=0.7)
    ax.plot(frequencies, product_G, 'b-', linewidth=1, label='Spectrum × G_major', alpha=0.7)
    ax.set_xlim([200, 500])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Product')
    ax.set_title(f'Matched Filter Product (SNR_C={np.sum(product_C):.1f}, SNR_G={np.sum(product_G):.1f})')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('template_matching_visualization.png', dpi=150)
    print(f"Saved visualization to: template_matching_visualization.png")

    return fig


if __name__ == "__main__":
    # Run tests
    results, frequencies, templates = test_snr_sweep()

    test_chord_discrimination()

    # Generate plots
    try:
        plot_results(results)
        visualize_template_matching()
        print("\n✓ All tests complete! Check PNG files for visualizations.")
    except Exception as e:
        print(f"\nWarning: Could not generate plots: {e}")
        print("(matplotlib may not be available or display not configured)")

    print("\n" + "=" * 70)
    print("Validation complete!")
    print("=" * 70)
