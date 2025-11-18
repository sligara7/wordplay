"""
Real Audio Chord Detection

Tests the multi-octave PSF detector on real audio recordings.

Features:
- Time-based chord detection (analyzes entire audio file)
- Sliding window approach for temporal resolution
- Chord transition detection
- Visualization of chord progression over time
- SNR tracking for confidence scoring
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
    """
    Load audio file (WAV format).

    Returns:
        sample_rate, audio_data (mono, float32)
    """
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


def detect_chords_over_time(audio, sample_rate, detector, analyzer,
                             hop_size=0.1, min_snr=6.5):
    """
    Detect chords over time using sliding window.

    Args:
        audio: Audio signal (mono, float32)
        sample_rate: Sample rate in Hz
        detector: FastMHTChordDetector instance
        analyzer: SpectralAnalyzer instance
        hop_size: Time between analyses in seconds (default: 0.1 = 100ms)
        min_snr: Minimum SNR for chord detection

    Returns:
        List of dicts with time-based chord detections
    """
    print(f"\nAnalyzing audio...")
    print(f"  Duration: {len(audio) / sample_rate:.2f} seconds")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Hop size: {hop_size} sec ({hop_size*1000:.0f} ms)")

    # Calculate window parameters
    # spectral_analyzer uses analysis_length as window size
    window_duration = analyzer.analysis_length
    window_samples = analyzer.window_length
    hop_samples = int(hop_size * sample_rate)

    print(f"  Window size: {window_duration:.3f} sec ({window_samples} samples)")
    print(f"  Hop samples: {hop_samples}")

    # Sliding window analysis
    detections = []
    num_windows = (len(audio) - window_samples) // hop_samples

    print(f"  Number of windows: {num_windows}")
    print()

    start_time = time.perf_counter()

    for i in range(num_windows):
        # Extract window
        start_idx = i * hop_samples
        end_idx = start_idx + window_samples
        window = audio[start_idx:end_idx]

        # Time position (center of window)
        time_pos = (start_idx + window_samples // 2) / sample_rate

        # Analyze spectral content
        spectral_data = analyzer.dotop(window)

        # Use middle time slice (most stable)
        mid_time = spectral_data.shape[1] // 2
        spectrum = spectral_data[:, mid_time]

        # Detect chord
        result = detector.detect(spectrum)

        # Store detection
        detection = {
            'time': time_pos,
            'window_idx': i,
            'detected': result['detected'],
            'chord': result['chord'] if result['detected'] else None,
            'snr': result['snr'],
            'all_snrs': result.get('all_snrs', {}),
            'spectrum': spectrum
        }

        detections.append(detection)

        # Progress update
        if (i + 1) % 50 == 0 or i == num_windows - 1:
            elapsed = time.perf_counter() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  Progress: {i+1}/{num_windows} windows ({100*(i+1)/num_windows:.1f}%) "
                  f"- {rate:.1f} windows/sec")

    total_time = time.perf_counter() - start_time
    print(f"\n  Analysis complete: {total_time:.2f} seconds")
    print(f"  Rate: {num_windows / total_time:.1f} windows/sec")

    return detections


def analyze_chord_progression(detections, min_duration=0.2):
    """
    Analyze detected chords to find chord progression.

    Merges consecutive detections of the same chord into chord segments.

    Args:
        detections: List of detection dicts from detect_chords_over_time
        min_duration: Minimum duration for a chord (seconds)

    Returns:
        List of chord segments with start, end, duration
    """
    if not detections:
        return []

    segments = []
    current_chord = None
    segment_start = None

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
                            'avg_snr': np.mean([d['snr'] for d in detections
                                               if segment_start <= d['time'] < det['time']])
                        })

                # Start new segment
                current_chord = chord
                segment_start = det['time']
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
                        'avg_snr': np.mean([d['snr'] for d in detections
                                           if segment_start <= d['time'] < det['time']])
                    })

            current_chord = None
            segment_start = None

    # Handle final segment
    if current_chord is not None and segment_start is not None:
        duration = detections[-1]['time'] - segment_start
        if duration >= min_duration:
            segments.append({
                'chord': current_chord,
                'start': segment_start,
                'end': detections[-1]['time'],
                'duration': duration,
                'avg_snr': np.mean([d['snr'] for d in detections
                                   if segment_start <= d['time']])
            })

    return segments


def visualize_chord_detection(detections, segments, audio, sample_rate,
                               save_path=None, show_spectrum=True):
    """
    Visualize chord detection results.

    Args:
        detections: Detection results from detect_chords_over_time
        segments: Chord segments from analyze_chord_progression
        audio: Original audio signal
        sample_rate: Sample rate
        save_path: Optional path to save figure
        show_spectrum: Include spectrogram plot
    """
    fig_height = 12 if show_spectrum else 9
    fig, axes = plt.subplots(3 if show_spectrum else 2, 1,
                             figsize=(16, fig_height),
                             height_ratios=[2, 2, 3] if show_spectrum else [2, 3])

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
        # Add chord label
        mid_time = (seg['start'] + seg['end']) / 2
        chord_label = seg['chord'].replace('_oct', '\noct')
        ax_wave.text(mid_time, ax_wave.get_ylim()[1] * 0.8, chord_label,
                    ha='center', va='top', fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    # Plot 2: SNR over time
    ax_snr = axes[1]

    # Color by detection
    colors = ['green' if det else 'red' for det in detected_flags]
    ax_snr.scatter(times, snrs, c=colors, s=20, alpha=0.6)
    ax_snr.axhline(y=6.5, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax_snr.set_ylabel('SNR')
    ax_snr.set_title('Signal-to-Noise Ratio over Time')
    ax_snr.legend()
    ax_snr.grid(True, alpha=0.3)
    ax_snr.set_xlim([0, times[-1]])

    # Add chord segment backgrounds
    for seg in segments:
        ax_snr.axvspan(seg['start'], seg['end'], alpha=0.1, color='green')

    # Plot 3: Chord progression (spectrogram-style or bar chart)
    ax_chords = axes[2 if show_spectrum else 1]

    if show_spectrum:
        # Create spectrogram from detections
        # (This is a simplified version - could be enhanced)
        ax_chords.set_ylabel('Chord Type')
        ax_chords.set_xlabel('Time (seconds)')
        ax_chords.set_title('Detected Chord Progression')

        # Plot chord segments as colored bars
        unique_chords = list(set(seg['chord'] for seg in segments))
        chord_to_idx = {chord: i for i, chord in enumerate(unique_chords)}

        for seg in segments:
            y_pos = chord_to_idx[seg['chord']]
            width = seg['end'] - seg['start']
            color_intensity = min(1.0, seg['avg_snr'] / 40.0)  # Normalize SNR to [0,1]

            ax_chords.barh(y_pos, width, left=seg['start'], height=0.8,
                          color=plt.cm.viridis(color_intensity), alpha=0.8)

            # Add chord label
            if width > 0.5:  # Only label if segment is wide enough
                ax_chords.text(seg['start'] + width/2, y_pos,
                              seg['chord'].replace('_oct', '\n'),
                              ha='center', va='center', fontsize=7, color='white',
                              weight='bold')

        ax_chords.set_yticks(range(len(unique_chords)))
        ax_chords.set_yticklabels(unique_chords)
        ax_chords.set_xlim([0, times[-1]])
        ax_chords.grid(True, alpha=0.3, axis='x')
    else:
        # Simple timeline view
        ax_chords.set_xlabel('Time (seconds)')
        ax_chords.set_ylabel('Chord')
        ax_chords.set_title('Chord Timeline')

        for i, seg in enumerate(segments):
            ax_chords.barh(i, seg['duration'], left=seg['start'],
                          height=0.8, alpha=0.7)
            ax_chords.text(seg['start'] + seg['duration']/2, i,
                          f"{seg['chord']}\n{seg['duration']:.2f}s",
                          ha='center', va='center', fontsize=8)

        ax_chords.set_yticks(range(len(segments)))
        ax_chords.set_yticklabels([f"Seg {i}" for i in range(len(segments))])
        ax_chords.set_xlim([0, times[-1]])
        ax_chords.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n✓ Saved visualization to: {save_path}")

    return fig


def analyze_audio_file(filepath, template_path="multi_octave_psf_templates.pkl",
                       hop_size=0.1, min_chord_duration=0.2):
    """
    Complete analysis of an audio file.

    Args:
        filepath: Path to WAV file
        template_path: Path to PSF templates
        hop_size: Time between analyses (seconds)
        min_chord_duration: Minimum chord duration (seconds)

    Returns:
        Dict with complete analysis results
    """
    print("=" * 80)
    print("REAL AUDIO CHORD DETECTION")
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
    # Use same cycles as template generation (4 cycles)
    cycles = 4
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Detect chords over time
    print("\n5. Detecting chords over time...")
    detections = detect_chords_over_time(audio, sample_rate, detector, analyzer,
                                         hop_size=hop_size)

    # Analyze chord progression
    print("\n6. Analyzing chord progression...")
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
    print(f"  Total windows: {total_detections}")
    print(f"  Chords detected: {positive_detections} ({detection_rate:.1f}%)")
    print(f"  No chord: {total_detections - positive_detections} ({100 - detection_rate:.1f}%)")

    if segments:
        print(f"\nChord Progression ({len(segments)} segments):")
        print(f"  {'Start':>8s}  {'End':>8s}  {'Duration':>10s}  {'Avg SNR':>8s}  {'Chord':20s}")
        print("  " + "-" * 70)

        for seg in segments[:20]:  # Show first 20
            print(f"  {seg['start']:8.2f}  {seg['end']:8.2f}  "
                  f"{seg['duration']:10.2f}s  {seg['avg_snr']:8.2f}  {seg['chord']:20s}")

        if len(segments) > 20:
            print(f"  ... ({len(segments) - 20} more segments)")

        # Chord type distribution
        chord_types = {}
        for seg in segments:
            chord = seg['chord']
            if chord not in chord_types:
                chord_types[chord] = {'count': 0, 'total_duration': 0}
            chord_types[chord]['count'] += 1
            chord_types[chord]['total_duration'] += seg['duration']

        print(f"\nChord Distribution:")
        print(f"  {'Chord':25s}  {'Count':>6s}  {'Total Duration':>15s}  {'Avg Duration':>15s}")
        print("  " + "-" * 70)

        for chord in sorted(chord_types.keys(),
                           key=lambda x: chord_types[x]['total_duration'],
                           reverse=True)[:10]:
            stats = chord_types[chord]
            avg_dur = stats['total_duration'] / stats['count']
            print(f"  {chord:25s}  {stats['count']:6d}  "
                  f"{stats['total_duration']:15.2f}s  {avg_dur:15.2f}s")

    # Visualize
    print("\n7. Creating visualization...")
    filename = Path(filepath).stem
    save_path = f"{filename}_chord_detection.png"
    visualize_chord_detection(detections, segments, audio, sample_rate,
                             save_path=save_path)

    print("\n" + "=" * 80)

    return {
        'filepath': filepath,
        'sample_rate': sample_rate,
        'duration': duration,
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

    print(f"\nTesting real audio chord detection on: {test_file}\n")

    results = analyze_audio_file(
        test_file,
        template_path="multi_octave_psf_templates.pkl",
        hop_size=0.1,  # 100ms resolution
        min_chord_duration=0.2  # 200ms minimum chord duration
    )

    print("\n✓ Analysis complete!")
