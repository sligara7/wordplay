"""
Ultra-Fast Vectorized Chord Detection

Uses single matrix multiplication to compute ALL template correlations
across ALL time slices simultaneously!

Key insight from user:
    PSF_matrix (660 × 1044) @ spectral_data (1044 × 1500) = correlations (660 × 1500)

This computes 660 × 1500 = 990,000 correlations in ONE matrix operation!
"""

import numpy as np
import time
from numba import njit, prange
from typing import Dict, List
import matplotlib.pyplot as plt
from pathlib import Path


class UltraFastChordDetector:
    """
    Ultra-fast chord detector using full matrix multiplication.

    Instead of looping through time slices, computes ALL correlations
    in a single matrix operation.
    """

    def __init__(self, psf_templates: Dict[str, np.ndarray],
                 threshold: float = 6.5,
                 use_outlier_removal: bool = True):
        """
        Initialize detector.

        Args:
            psf_templates: Dict mapping chord names to PSF arrays
            threshold: SNR threshold for detection
            use_outlier_removal: Use MHTOR (outlier removal)
        """
        self.threshold = threshold
        self.use_outlier_removal = use_outlier_removal

        # Extract template names and arrays
        self.template_names = list(psf_templates.keys())
        template_arrays = [psf_templates[name] for name in self.template_names]

        # Stack into matrix: (N_templates, N_frequencies)
        self.psf_matrix = np.array(template_arrays, dtype=np.float32)

        # Precompute template norms
        self.template_norms = np.linalg.norm(self.psf_matrix, axis=1)

        self.num_templates = len(self.template_names)
        self.num_frequencies = self.psf_matrix.shape[1]

        print(f"UltraFastChordDetector initialized:")
        print(f"  Templates: {self.num_templates}")
        print(f"  Frequencies: {self.num_frequencies}")
        print(f"  PSF matrix shape: {self.psf_matrix.shape}")
        print(f"  Threshold: {threshold}")
        print(f"  Outlier removal: {use_outlier_removal}")

    def detect_all_time_slices(self, spectral_data: np.ndarray) -> Dict:
        """
        Detect chords across ALL time slices using single matrix multiplication.

        This is the KEY optimization!

        Args:
            spectral_data: Spectral matrix (frequencies, time)
                          Shape: (N_frequencies, N_time_slices)

        Returns:
            Dict with:
                - 'snr_matrix': SNR for each template × time (N_templates, N_time)
                - 'best_template_indices': Best template for each time (N_time,)
                - 'best_snrs': SNR of best template for each time (N_time,)
                - 'detected_flags': Boolean array (N_time,) - above threshold?
                - 'chord_names': List of detected chord names (N_time,)
        """
        num_freq, num_time = spectral_data.shape

        assert num_freq == self.num_frequencies, \
            f"Frequency mismatch: {num_freq} vs {self.num_frequencies}"

        print(f"\nProcessing {num_time} time slices with {self.num_templates} templates...")
        start_time = time.perf_counter()

        # Step 1: Calculate background and sigma for each time slice (vectorized!)
        # Background = median of each column
        backgrounds = np.median(spectral_data, axis=0)  # Shape: (N_time,)

        # Subtract background from each column (broadcasting)
        signal_matrix = spectral_data - backgrounds[np.newaxis, :]  # Shape: (N_freq, N_time)

        # Calculate sigma for each time slice
        if self.use_outlier_removal:
            # MHTOR: Remove outliers before calculating sigma
            sigmas = np.zeros(num_time, dtype=np.float32)
            for t in range(num_time):
                signal = signal_matrix[:, t]
                # Remove top/bottom 10% as outliers
                sorted_signal = np.sort(np.abs(signal))
                n_keep = int(0.8 * len(sorted_signal))
                trimmed = sorted_signal[:n_keep]
                sigmas[t] = np.std(trimmed) if len(trimmed) > 0 else 1.0
        else:
            # Standard deviation of each column
            sigmas = np.std(signal_matrix, axis=0)  # Shape: (N_time,)

        # Avoid division by zero
        sigmas = np.maximum(sigmas, 1e-10)

        # Step 2: THE MAGIC - Single matrix multiplication!
        # PSF_matrix: (N_templates, N_freq)
        # signal_matrix: (N_freq, N_time)
        # Result: (N_templates, N_time)

        print(f"  Computing correlation matrix: ({self.num_templates}, {num_freq}) @ ({num_freq}, {num_time})")

        correlation_matrix = self.psf_matrix @ signal_matrix  # Shape: (N_templates, N_time)

        print(f"  ✓ Correlation matrix computed: {correlation_matrix.shape}")

        # Step 3: Normalize to get SNR matrix (vectorized!)
        # Divide each column by its sigma
        # Divide each row by its template norm

        # Broadcasting magic:
        # correlation_matrix: (N_templates, N_time)
        # sigmas: (N_time,) → broadcast to (1, N_time)
        # template_norms: (N_templates,) → broadcast to (N_templates, 1)

        snr_matrix = correlation_matrix / (sigmas[np.newaxis, :] * self.template_norms[:, np.newaxis] + 1e-10)

        print(f"  ✓ SNR matrix computed: {snr_matrix.shape}")

        # Step 4: Find best template for each time slice (vectorized!)
        best_template_indices = np.argmax(snr_matrix, axis=0)  # Shape: (N_time,)
        best_snrs = np.max(snr_matrix, axis=0)  # Shape: (N_time,)

        # Step 5: Threshold detection
        detected_flags = best_snrs > self.threshold

        # Step 6: Get chord names
        chord_names = [self.template_names[idx] if detected else None
                      for idx, detected in zip(best_template_indices, detected_flags)]

        elapsed = time.perf_counter() - start_time

        print(f"  ✓ All {num_time} time slices processed in {elapsed:.3f} seconds")
        print(f"  Rate: {num_time / elapsed:.0f} slices/sec")
        print(f"  Detected: {np.sum(detected_flags)}/{num_time} ({100*np.sum(detected_flags)/num_time:.1f}%)")

        return {
            'snr_matrix': snr_matrix,
            'best_template_indices': best_template_indices,
            'best_snrs': best_snrs,
            'detected_flags': detected_flags,
            'chord_names': chord_names,
            'num_time': num_time,
            'processing_time': elapsed
        }


def test_ultra_fast_detector():
    """
    Test the ultra-fast detector on real audio.
    """
    from build_multi_octave_psf import load_multi_octave_psfs
    from spectral_analyzer import SpectralAnalyzer
    import scipy.io.wavfile as wavfile

    print("=" * 80)
    print("ULTRA-FAST CHORD DETECTION TEST")
    print("=" * 80)

    # Load audio
    filepath = "/home/ajs7/project/wordplay/music/new_start/test_amazing_grace.wav"
    print(f"\n1. Loading audio: {filepath}")

    sample_rate, audio = wavfile.read(filepath)
    if len(audio.shape) == 2:
        audio = np.mean(audio, axis=1)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0

    duration = len(audio) / sample_rate
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Sample rate: {sample_rate} Hz")

    # Load templates
    print("\n2. Loading PSF templates...")
    templates, frequencies, metadata = load_multi_octave_psfs("multi_octave_psf_templates.pkl")

    # Initialize detector
    print("\n3. Initializing ultra-fast detector...")
    detector = UltraFastChordDetector(templates, threshold=6.5, use_outlier_removal=True)

    # Analyze audio
    print("\n4. Analyzing audio with spectral analyzer...")
    analyzer = SpectralAnalyzer(samplefreq=sample_rate, cycles=4, standard_A4=440.0)

    start_spectral = time.perf_counter()
    spectral_data = analyzer.dotop(audio)
    spectral_time = time.perf_counter() - start_spectral

    print(f"   ✓ Spectral analysis complete: {spectral_time:.2f} seconds")
    print(f"   Spectral data shape: {spectral_data.shape}")

    # Detect chords (THE FAST WAY!)
    print("\n5. Detecting chords using ultra-fast matrix multiplication...")
    results = detector.detect_all_time_slices(spectral_data)

    # Analyze results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    num_time = results['num_time']
    detected_count = np.sum(results['detected_flags'])

    print(f"\nTime slices: {num_time}")
    print(f"Detected: {detected_count} ({100*detected_count/num_time:.1f}%)")
    print(f"Processing time: {results['processing_time']:.3f} seconds")
    print(f"Rate: {num_time / results['processing_time']:.0f} slices/sec")

    # Show detected chords
    print(f"\nFirst 20 detections:")
    for i in range(min(20, num_time)):
        if results['detected_flags'][i]:
            time_pos = i * (duration / num_time)
            chord = results['chord_names'][i]
            snr = results['best_snrs'][i]
            print(f"  {time_pos:6.2f}s: {chord:25s} (SNR={snr:.2f})")

    # Visualize SNR matrix
    print("\n6. Visualizing results...")
    visualize_snr_matrix(results, spectral_data, audio, sample_rate, duration)

    print("\n" + "=" * 80)
    print(f"TOTAL TIME: {spectral_time + results['processing_time']:.2f} seconds")
    print(f"SPEEDUP: {duration / (spectral_time + results['processing_time']):.1f}× real-time")
    print("=" * 80)

    return results


def visualize_snr_matrix(results, spectral_data, audio, sample_rate, duration):
    """
    Visualize the SNR matrix - shows ALL templates × ALL times.
    """
    fig, axes = plt.subplots(4, 1, figsize=(16, 14), height_ratios=[2, 4, 2, 2])

    num_time = results['num_time']
    times = np.linspace(0, duration, num_time)

    # Plot 1: Audio waveform
    ax = axes[0]
    time_audio = np.arange(len(audio)) / sample_rate
    ax.plot(time_audio, audio, 'b-', linewidth=0.5, alpha=0.7)
    ax.set_ylabel('Amplitude')
    ax.set_title('Audio Waveform')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, duration])

    # Plot 2: SNR Matrix Heatmap (THE MAIN EVENT!)
    ax = axes[1]

    # Show SNR matrix as heatmap
    # Clip to reasonable range for visualization
    snr_display = np.clip(results['snr_matrix'], -5, 50)

    im = ax.imshow(snr_display, aspect='auto', cmap='viridis',
                   extent=[0, duration, len(results['snr_matrix']), 0],
                   interpolation='nearest')

    ax.set_ylabel('Template Index')
    ax.set_xlabel('Time (seconds)')
    ax.set_title('SNR Matrix: All Templates × All Time Slices\n(Bright = High SNR)')

    # Add threshold line
    ax.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.5)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, label='SNR')
    cbar.ax.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Threshold')

    # Plot 3: Best SNR over time
    ax = axes[2]
    colors = ['green' if d else 'red' for d in results['detected_flags']]
    ax.scatter(times, results['best_snrs'], c=colors, s=10, alpha=0.6)
    ax.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax.set_ylabel('Best SNR')
    ax.set_xlabel('Time (seconds)')
    ax.set_title('Best SNR over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, duration])

    # Plot 4: Detected chords timeline
    ax = axes[3]

    # Group consecutive same chords
    segments = []
    current_chord = None
    start_idx = None

    for i, chord in enumerate(results['chord_names']):
        if chord != current_chord:
            if current_chord is not None:
                segments.append({
                    'chord': current_chord,
                    'start': times[start_idx],
                    'end': times[i],
                    'y': len(segments) % 10  # Stack vertically
                })
            current_chord = chord
            start_idx = i

    # Final segment
    if current_chord is not None:
        segments.append({
            'chord': current_chord,
            'start': times[start_idx],
            'end': times[-1],
            'y': len(segments) % 10
        })

    # Plot segments
    for seg in segments:
        if seg['chord'] is not None:
            width = seg['end'] - seg['start']
            ax.barh(seg['y'], width, left=seg['start'], height=0.8, alpha=0.7)

            # Add label if wide enough
            if width > 2:
                label = seg['chord'].replace('_oct', '\n')
                ax.text(seg['start'] + width/2, seg['y'], label,
                       ha='center', va='center', fontsize=6)

    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Chord')
    ax.set_title('Detected Chord Timeline')
    ax.set_xlim([0, duration])
    ax.set_ylim([-1, 10])
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig('ultra_fast_detection_results.png', dpi=150, bbox_inches='tight')
    print("   ✓ Saved visualization: ultra_fast_detection_results.png")


if __name__ == "__main__":
    print("\nTesting ultra-fast chord detection with matrix multiplication...\n")
    results = test_ultra_fast_detector()
    print("\n✓ Test complete!")
