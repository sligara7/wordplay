#!/usr/bin/env python3
"""
Test Theory-Filtered Chord Detection

Compares:
1. Baseline: argmax(SNR) at each time (no theory)
2. Theory-filtered: Using key detection + chord progressions
"""

import numpy as np
import sys
import time

# Import components
from spectral_analyzer import SpectralAnalyzer
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs
from theory_filtered_detector import TheoryFilteredChordDetector

# Import audio reading
try:
    from scipy.io import wavfile
except ImportError:
    print("scipy not installed. Install: pip install scipy")
    sys.exit(1)


def load_audio(wav_path):
    """Load WAV audio file."""
    sample_rate, audio_data = wavfile.read(wav_path)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Convert to float32
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0

    duration = len(audio_data) / sample_rate

    return audio_data, sample_rate, duration


def compare_detection_methods(wav_path):
    """
    Compare baseline vs theory-filtered detection.
    """
    print("="*80)
    print("CHORD DETECTION COMPARISON: Baseline vs Theory-Filtered")
    print("="*80)
    print()

    # Load audio
    print(f"Loading audio: {wav_path}")
    audio_data, sample_rate, duration = load_audio(wav_path)
    print(f"  Duration: {duration:.2f}s")
    print(f"  Sample rate: {sample_rate} Hz")
    print()

    # Spectral analysis
    print("[1/4] Spectral analysis...")
    start_time = time.perf_counter()

    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=4,
        standard_A4=440.0,
        increments=12
    )

    spectral_data = analyzer.dotop(audio_data)
    spectral_time = time.perf_counter() - start_time

    print(f"  ✓ Spectral shape: {spectral_data.shape}")
    print(f"  ✓ Time: {spectral_time:.2f}s")
    print()

    # Load PSF templates
    print("[2/4] Loading PSF templates...")
    templates, frequencies, metadata = load_multi_octave_psfs("multi_octave_psf_templates.pkl")
    print(f"  ✓ Loaded {len(templates)} templates")
    print()

    # Initialize ultra-fast detector
    print("[3/4] Running ultra-fast PSF detector...")
    detector = UltraFastChordDetector(templates, threshold=6.5, use_outlier_removal=True)

    start_time = time.perf_counter()
    results = detector.detect_all_time_slices(spectral_data)
    detection_time = time.perf_counter() - start_time

    print(f"  ✓ Detection time: {detection_time:.3f}s")
    print(f"  ✓ Rate: {results['snr_matrix'].shape[1] / detection_time:.0f} slices/sec")
    print()

    # Get time per slice
    num_times = spectral_data.shape[1]
    time_per_slice = duration / num_times

    print(f"Time per slice: {time_per_slice:.4f}s ({num_times} slices)")
    print()

    # METHOD 1: Baseline (argmax SNR, no theory)
    print("="*80)
    print("METHOD 1: BASELINE (argmax SNR, no music theory)")
    print("="*80)

    baseline_chords = []
    for i in range(num_times):
        if results['detected_flags'][i]:
            baseline_chords.append({
                'time': i * time_per_slice,
                'chord': results['chord_names'][i],
                'snr': results['best_snrs'][i]
            })

    # Merge consecutive
    baseline_merged = merge_consecutive_chords(baseline_chords, time_per_slice)

    print(f"Detected: {len(baseline_chords)} time slices")
    print(f"Merged: {len(baseline_merged)} segments")
    print()

    # Show top chords
    chord_durations = {}
    for seg in baseline_merged:
        chord = seg['chord']
        if chord not in chord_durations:
            chord_durations[chord] = 0
        chord_durations[chord] += seg['duration']

    top_chords = sorted(chord_durations.items(), key=lambda x: x[1], reverse=True)[:10]

    print("Top 10 chords (by duration):")
    for i, (chord, dur) in enumerate(top_chords, 1):
        print(f"  {i:2d}. {chord:25s} ({dur:.2f}s)")
    print()

    # METHOD 2: Theory-filtered
    print("="*80)
    print("METHOD 2: THEORY-FILTERED (key + progressions)")
    print("="*80)

    theory_detector = TheoryFilteredChordDetector(
        snr_threshold=6.5,
        top_k_candidates=5,
        progression_weight=0.3,
        key_weight=0.2
    )

    # Get list of all template names from detector
    all_template_names = detector.template_names

    theory_chords = theory_detector.detect_with_theory(
        results['snr_matrix'],
        all_template_names,
        time_per_slice
    )

    # Show top chords
    theory_chord_durations = {}
    for seg in theory_chords:
        chord = seg['chord']
        if chord not in theory_chord_durations:
            theory_chord_durations[chord] = 0
        theory_chord_durations[chord] += seg['duration']

    theory_top_chords = sorted(theory_chord_durations.items(), key=lambda x: x[1], reverse=True)[:10]

    print("Top 10 chords (by duration):")
    for i, (chord, dur) in enumerate(theory_top_chords, 1):
        print(f"  {i:2d}. {chord:25s} ({dur:.2f}s)")
    print()

    # COMPARISON
    print("="*80)
    print("COMPARISON")
    print("="*80)

    print(f"Baseline segments:       {len(baseline_merged)}")
    print(f"Theory-filtered segments: {len(theory_chords)}")
    print()

    print(f"Baseline unique chords:   {len(chord_durations)}")
    print(f"Theory unique chords:     {len(theory_chord_durations)}")
    print()

    # Compare chord complexity
    baseline_complex = sum(1 for c in chord_durations.keys() if 'maj11' in c or 'dom9' in c or 'aug' in c)
    theory_complex = sum(1 for c in theory_chord_durations.keys() if 'maj11' in c or 'dom9' in c or 'aug' in c)

    print(f"Baseline complex chords:  {baseline_complex}")
    print(f"Theory complex chords:    {theory_complex}")
    print()

    print("="*80)
    print("✓ Comparison complete!")
    print("="*80)


def merge_consecutive_chords(detections, time_per_slice):
    """Merge consecutive same-chord detections."""
    if not detections:
        return []

    segments = []
    current = None

    for det in detections:
        if current is None:
            current = {
                'start_time': det['time'],
                'chord': det['chord'],
                'snr_values': [det['snr']],
                'num_slices': 1
            }
        elif det['chord'] == current['chord']:
            current['snr_values'].append(det['snr'])
            current['num_slices'] += 1
        else:
            current['duration'] = current['num_slices'] * time_per_slice
            current['avg_snr'] = np.mean(current['snr_values'])
            segments.append(current)

            current = {
                'start_time': det['time'],
                'chord': det['chord'],
                'snr_values': [det['snr']],
                'num_slices': 1
            }

    if current:
        current['duration'] = current['num_slices'] * time_per_slice
        current['avg_snr'] = np.mean(current['snr_values'])
        segments.append(current)

    return segments


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_theory_filtering.py INPUT.wav")
        print()
        print("Compares baseline chord detection vs theory-filtered detection")
        sys.exit(1)

    wav_path = sys.argv[1]
    compare_detection_methods(wav_path)
