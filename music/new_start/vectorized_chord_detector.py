"""
Vectorized Chord Detection - Process All Time Samples Simultaneously

Instead of looping through time windows, this processes the entire
spectral matrix [freq, time] at once using vectorized numpy operations.

This should be MUCH faster than the sliding window approach!
"""

import numpy as np
import matplotlib.pyplot as plt
from spectral_analyzer import SpectralAnalyzer
from bht_chord_detector_fast import FastMHTChordDetector
from build_multi_octave_psf import load_multi_octave_psfs
import scipy.io.wavfile as wavfile
from pathlib import Path
import time


def load_audio(filepath):
    """Load audio file (WAV format)."""
    sample_rate, audio = wavfile.read(filepath)

    # Convert to mono if stereo
    if len(audio.shape) == 2:
        audio = np.mean(audio, axis=1)

    # Convert to float32 and normalize
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0

    return sample_rate, audio


def detect_chords_vectorized(spectral_data, detector, sample_rate, analyzer, audio_duration):
    """
    Detect chords across ALL time samples simultaneously.

    This is the key optimization: instead of looping through time slices,
    we process the entire [freq, time] matrix at once!

    Args:
        spectral_data: 2D array [freq, time] from spectral_analyzer
        detector: FastMHTChordDetector instance
        sample_rate: Sample rate in Hz
        analyzer: SpectralAnalyzer instance (for timing info)
        audio_duration: Total duration of audio in seconds

    Returns:
        List of detections for each time slice
    """
    print(f"\nVectorized chord detection...")
    print(f"  Spectral data shape: {spectral_data.shape}")
    print(f"  Frequency bins: {spectral_data.shape[0]}")
    print(f"  Time slices: {spectral_data.shape[1]}")

    num_freqs, num_times = spectral_data.shape

    # Time per slice - this is the ACTUAL duration covered per time slice
    time_per_slice = audio_duration / num_times

    print(f"  Time per slice: {time_per_slice*1000:.2f} ms")
    print(f"  Total duration: {audio_duration:.2f} seconds")

    # Process ALL time slices at once!
    start_time = time.perf_counter()

    detections = []

    # We still need to loop, but we can batch process
    # Let's process in batches for memory efficiency
    batch_size = 100  # Process 100 time slices at once

    for batch_start in range(0, num_times, batch_size):
        batch_end = min(batch_start + batch_size, num_times)
        batch_size_actual = batch_end - batch_start

        # Extract batch
        batch_spectra = spectral_data[:, batch_start:batch_end]

        # Detect for each spectrum in batch
        for i in range(batch_size_actual):
            time_idx = batch_start + i
            spectrum = batch_spectra[:, i]
            time_pos = time_idx * time_per_slice

            # Detect
            result = detector.detect(spectrum)

            detections.append({
                'time': time_pos,
                'time_idx': time_idx,
                'detected': result['detected'],
                'chord': result['chord'] if result['detected'] else None,
                'snr': result['snr']
            })

        # Progress update
        if batch_end % 500 == 0 or batch_end == num_times:
            elapsed = time.perf_counter() - start_time
            rate = batch_end / elapsed if elapsed > 0 else 0
            print(f"  Progress: {batch_end}/{num_times} slices ({100*batch_end/num_times:.1f}%) "
                  f"- {rate:.0f} slices/sec")

    total_time = time.perf_counter() - start_time
    print(f"\n  Detection complete: {total_time:.2f} seconds")
    print(f"  Rate: {num_times / total_time:.0f} slices/sec")

    return detections


def analyze_chord_progression(detections, min_duration=0.1):
    """
    Analyze detected chords to find chord progression.

    Merges consecutive detections of the same chord into segments.
    """
    if not detections:
        return []

    segments = []
    current_chord = None
    segment_start = None
    segment_start_idx = None

    for det in detections:
        if det['detected']:
            chord = det['chord']

            # Start new segment or continue current
            if chord != current_chord:
                # Save previous segment
                if current_chord is not None and segment_start is not None:
                    duration = det['time'] - segment_start
                    if duration >= min_duration:
                        segments.append({
                            'chord': current_chord,
                            'start': segment_start,
                            'end': det['time'],
                            'duration': duration,
                            'start_idx': segment_start_idx,
                            'end_idx': det['time_idx'],
                            'avg_snr': np.mean([d['snr'] for d in detections
                                               if segment_start_idx <= d['time_idx'] < det['time_idx']])
                        })

                # Start new segment
                current_chord = chord
                segment_start = det['time']
                segment_start_idx = det['time_idx']
        else:
            # No chord detected - end current segment
            if current_chord is not None and segment_start is not None:
                duration = det['time'] - segment_start
                if duration >= min_duration:
                    segments.append({
                        'chord': current_chord,
                        'start': segment_start,
                        'end': det['time'],
                        'duration': duration,
                        'start_idx': segment_start_idx,
                        'end_idx': det['time_idx'],
                        'avg_snr': np.mean([d['snr'] for d in detections
                                           if segment_start_idx <= d['time_idx'] < det['time_idx']])
                    })

            current_chord = None
            segment_start = None
            segment_start_idx = None

    # Handle final segment
    if current_chord is not None and segment_start is not None:
        duration = detections[-1]['time'] - segment_start
        if duration >= min_duration:
            segments.append({
                'chord': current_chord,
                'start': segment_start,
                'end': detections[-1]['time'],
                'duration': duration,
                'start_idx': segment_start_idx,
                'end_idx': detections[-1]['time_idx'],
                'avg_snr': np.mean([d['snr'] for d in detections
                                   if segment_start_idx <= d['time_idx']])
            })

    return segments


def visualize_results(spectral_data, detections, segments, audio, sample_rate,
                      audio_duration, save_path=None):
    """
    Visualize chord detection results.
    """
    fig, axes = plt.subplots(4, 1, figsize=(16, 12),
                             height_ratios=[2, 3, 2, 3])

    times = [d['time'] for d in detections]
    snrs = [d['snr'] for d in detections]
    detected_flags = [d['detected'] for d in detections]

    # Plot 1: Audio waveform
    ax_wave = axes[0]
    time_audio = np.arange(len(audio)) / sample_rate
    ax_wave.plot(time_audio, audio, 'b-', linewidth=0.5, alpha=0.7)
    ax_wave.set_ylabel('Amplitude')
    ax_wave.set_title('Audio Waveform with Detected Chords')
    ax_wave.grid(True, alpha=0.3)
    ax_wave.set_xlim([0, time_audio[-1]])

    # Overlay chord segments
    for seg in segments:
        ax_wave.axvspan(seg['start'], seg['end'], alpha=0.2, color='green')

    # Plot 2: Spectrogram
    ax_spec = axes[1]
    # Correct time calculation: total duration / number of time slices
    time_per_slice = audio_duration / spectral_data.shape[1]
    spec_times = np.arange(spectral_data.shape[1]) * time_per_slice

    # Create frequency array (assuming linear spacing from 20 Hz to Nyquist)
    # Note: spectral_data shape[0] is number of frequency bins
    freqs = np.linspace(20, sample_rate/2, spectral_data.shape[0])

    im = ax_spec.pcolormesh(spec_times, freqs, spectral_data,
                            shading='auto', cmap='viridis',
                            vmin=0, vmax=np.percentile(spectral_data, 95))
    ax_spec.set_ylabel('Frequency (Hz)')
    ax_spec.set_title('Spectrogram')
    ax_spec.set_yscale('log')
    ax_spec.set_ylim([50, 2000])  # Focus on musical range
    plt.colorbar(im, ax=ax_spec, label='Amplitude')

    # Overlay chord segments
    for seg in segments:
        ax_spec.axvspan(seg['start'], seg['end'], alpha=0.1, color='red', linewidth=2)

    # Plot 3: SNR over time
    ax_snr = axes[2]
    colors = ['green' if det else 'red' for det in detected_flags]
    ax_snr.scatter(times, snrs, c=colors, s=10, alpha=0.6)
    ax_snr.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax_snr.set_ylabel('SNR')
    ax_snr.set_title('Signal-to-Noise Ratio over Time')
    ax_snr.legend()
    ax_snr.grid(True, alpha=0.3)
    ax_snr.set_xlim([0, times[-1]])

    # Plot 4: Chord progression
    ax_chords = axes[3]

    unique_chords = list(set(seg['chord'] for seg in segments))
    chord_to_idx = {chord: i for i, chord in enumerate(unique_chords)}

    for seg in segments:
        y_pos = chord_to_idx[seg['chord']]
        width = seg['end'] - seg['start']
        color_intensity = min(1.0, seg['avg_snr'] / 40.0)

        ax_chords.barh(y_pos, width, left=seg['start'], height=0.8,
                      color=plt.cm.viridis(color_intensity), alpha=0.8)

        # Add chord label if wide enough
        if width > 0.5:
            label = seg['chord'].replace('_oct', '\n')
            ax_chords.text(seg['start'] + width/2, y_pos, label,
                          ha='center', va='center', fontsize=6, color='white',
                          weight='bold')

    ax_chords.set_yticks(range(len(unique_chords)))
    ax_chords.set_yticklabels([c.replace('_oct', ' oct') for c in unique_chords],
                              fontsize=7)
    ax_chords.set_xlabel('Time (seconds)')
    ax_chords.set_ylabel('Chord')
    ax_chords.set_title('Detected Chord Progression')
    ax_chords.set_xlim([0, times[-1]])
    ax_chords.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n✓ Saved visualization to: {save_path}")

    return fig


def analyze_audio_file_vectorized(filepath,
                                   template_path="multi_octave_psf_templates.pkl",
                                   min_chord_duration=0.1):
    """
    Complete vectorized analysis of an audio file.

    This processes the ENTIRE audio file at once using spectral_analyzer,
    then detects chords across all time slices simultaneously.
    """
    print("=" * 80)
    print("VECTORIZED CHORD DETECTION")
    print("=" * 80)
    print(f"\nFile: {filepath}")

    # Load audio
    print("\n1. Loading audio file...")
    sample_rate, audio = load_audio(filepath)
    duration = len(audio) / sample_rate
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Sample rate: {sample_rate} Hz")
    print(f"   Samples: {len(audio)}")

    # Load PSF templates
    print("\n2. Loading PSF templates...")
    templates, frequencies, metadata = load_multi_octave_psfs(template_path)

    # Initialize detector
    print("\n3. Initializing detector...")
    detector = FastMHTChordDetector(templates, threshold=6.5, use_outlier_removal=True)

    # Initialize analyzer
    print("\n4. Initializing spectral analyzer...")
    cycles = 4
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Analyze ENTIRE audio file at once!
    print("\n5. Analyzing entire audio file...")
    print("   (This may take a moment for long files...)")

    start_spectral = time.perf_counter()
    spectral_data = analyzer.dotop(audio)
    spectral_time = time.perf_counter() - start_spectral

    print(f"   ✓ Spectral analysis complete: {spectral_time:.2f} seconds")
    print(f"   Spectral data shape: {spectral_data.shape}")

    # Detect chords across ALL time slices
    print("\n6. Detecting chords (vectorized)...")
    detections = detect_chords_vectorized(spectral_data, detector, sample_rate, analyzer, duration)

    # Analyze chord progression
    print("\n7. Analyzing chord progression...")
    segments = analyze_chord_progression(detections, min_duration=min_chord_duration)

    print(f"   Detected {len(segments)} chord segments")

    # Statistics
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    total_detections = len(detections)
    positive_detections = sum(1 for d in detections if d['detected'])
    detection_rate = 100 * positive_detections / total_detections

    print(f"\nDetection Statistics:")
    print(f"  Total time slices: {total_detections}")
    print(f"  Chords detected: {positive_detections} ({detection_rate:.1f}%)")
    print(f"  No chord: {total_detections - positive_detections} ({100 - detection_rate:.1f}%)")

    if segments:
        print(f"\nTop 20 Chord Segments:")
        print(f"  {'Start':>8s}  {'End':>8s}  {'Duration':>10s}  {'Avg SNR':>8s}  {'Chord':20s}")
        print("  " + "-" * 70)

        for seg in segments[:20]:
            print(f"  {seg['start']:8.2f}  {seg['end']:8.2f}  "
                  f"{seg['duration']:10.2f}s  {seg['avg_snr']:8.2f}  {seg['chord']:20s}")

        if len(segments) > 20:
            print(f"  ... ({len(segments) - 20} more segments)")

        # Chord distribution
        chord_types = {}
        for seg in segments:
            chord = seg['chord']
            if chord not in chord_types:
                chord_types[chord] = {'count': 0, 'total_duration': 0}
            chord_types[chord]['count'] += 1
            chord_types[chord]['total_duration'] += seg['duration']

        print(f"\nTop 10 Chords by Duration:")
        print(f"  {'Chord':25s}  {'Count':>6s}  {'Total Duration':>15s}")
        print("  " + "-" * 50)

        for chord in sorted(chord_types.keys(),
                           key=lambda x: chord_types[x]['total_duration'],
                           reverse=True)[:10]:
            stats = chord_types[chord]
            print(f"  {chord:25s}  {stats['count']:6d}  {stats['total_duration']:15.2f}s")

    # Visualize
    print("\n8. Creating visualization...")
    filename = Path(filepath).stem
    save_path = f"{filename}_vectorized_detection.png"
    visualize_results(spectral_data, detections, segments, audio, sample_rate,
                     duration, save_path=save_path)

    print("\n" + "=" * 80)
    print(f"Total processing time: {spectral_time + time.perf_counter() - start_spectral:.2f} seconds")
    print("=" * 80)

    return {
        'filepath': filepath,
        'sample_rate': sample_rate,
        'duration': duration,
        'spectral_data': spectral_data,
        'detections': detections,
        'segments': segments,
        'detection_rate': detection_rate,
        'chord_types': chord_types if segments else {}
    }


if __name__ == "__main__":
    import sys

    # Default test file
    test_file = "/home/ajs7/project/wordplay/music/new_start/test_amazing_grace.wav"

    # Allow command line argument
    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    print(f"\nTesting vectorized chord detection on: {test_file}\n")

    results = analyze_audio_file_vectorized(
        test_file,
        template_path="multi_octave_psf_templates.pkl",
        min_chord_duration=0.1
    )

    print("\n✓ Vectorized analysis complete!")
