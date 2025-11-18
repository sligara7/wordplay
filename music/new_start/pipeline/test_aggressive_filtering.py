#!/usr/bin/env python3
"""
Test Aggressive Theory Filtering

Compares 4 detection modes:
1. BASELINE: Pure argmax(SNR), no theory
2. SOFT: Multiplicative bonuses (in-key: 1.5×, good-prog: 1.3×)
3. MEDIUM: Strong penalties (out-of-key: 0.5×, bad-prog: 0.7×)
4. HARD: Only in-key chords (strict filtering)
"""

import numpy as np
import sys
import time

# Import components
from spectral_analyzer import SpectralAnalyzer
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs
from aggressive_theory_filter import AggressiveTheoryFilter

try:
    from scipy.io import wavfile
except ImportError:
    print("scipy not installed. Install: pip install scipy")
    sys.exit(1)


def load_audio(wav_path):
    """Load WAV audio file."""
    sample_rate, audio_data = wavfile.read(wav_path)

    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0

    duration = len(audio_data) / sample_rate

    return audio_data, sample_rate, duration


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


def analyze_chord_complexity(chord_durations):
    """Analyze chord complexity distribution."""
    simple_chords = ['major', 'minor']
    complex_chords = ['maj11', 'dom9', 'aug', 'dim']
    sus_chords = ['sus2', 'sus4']

    simple_count = sum(1 for c in chord_durations.keys() if any(s in c for s in simple_chords))
    complex_count = sum(1 for c in chord_durations.keys() if any(s in c for s in complex_chords))
    sus_count = sum(1 for c in chord_durations.keys() if any(s in c for s in sus_chords))
    seventh_count = sum(1 for c in chord_durations.keys() if 'min7' in c or 'maj7' in c or 'dom7' in c)

    return {
        'simple': simple_count,
        'complex': complex_count,
        'sus': sus_count,
        'seventh': seventh_count,
        'total': len(chord_durations)
    }


def compare_all_modes(wav_path):
    """
    Compare baseline vs all three aggressive filtering modes.
    """
    print("="*80)
    print("COMPREHENSIVE FILTERING COMPARISON")
    print("="*80)
    print()

    # Load audio
    print(f"Loading audio: {wav_path}")
    audio_data, sample_rate, duration = load_audio(wav_path)
    print(f"  Duration: {duration:.2f}s")
    print(f"  Sample rate: {sample_rate} Hz")
    print()

    # Spectral analysis
    print("[1/3] Spectral analysis...")
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
    print("[2/3] Loading PSF templates...")
    templates, frequencies, metadata = load_multi_octave_psfs("multi_octave_psf_templates.pkl")
    print(f"  ✓ Loaded {len(templates)} templates")
    print()

    # Initialize ultra-fast detector
    print("[3/3] Running ultra-fast PSF detector...")
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
    all_template_names = detector.template_names

    print(f"Time per slice: {time_per_slice:.4f}s ({num_times} slices)")
    print()

    # =================================================================
    # MODE 0: BASELINE (no theory)
    # =================================================================
    print("="*80)
    print("MODE 0: BASELINE (argmax SNR, no music theory)")
    print("="*80)

    baseline_chords = []
    for i in range(num_times):
        if results['detected_flags'][i]:
            baseline_chords.append({
                'time': i * time_per_slice,
                'chord': results['chord_names'][i],
                'snr': results['best_snrs'][i]
            })

    baseline_merged = merge_consecutive_chords(baseline_chords, time_per_slice)

    # Analyze
    baseline_durations = {}
    for seg in baseline_merged:
        chord = seg['chord']
        if chord not in baseline_durations:
            baseline_durations[chord] = 0
        baseline_durations[chord] += seg['duration']

    baseline_complexity = analyze_chord_complexity(baseline_durations)

    print(f"Detected: {len(baseline_chords)} time slices")
    print(f"Merged: {len(baseline_merged)} segments")
    print(f"Unique chords: {baseline_complexity['total']}")
    print(f"  Simple (major/minor): {baseline_complexity['simple']}")
    print(f"  7th chords: {baseline_complexity['seventh']}")
    print(f"  Sus chords: {baseline_complexity['sus']}")
    print(f"  Complex (maj11/dom9/aug/dim): {baseline_complexity['complex']}")
    print()

    top_baseline = sorted(baseline_durations.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 chords (by duration):")
    for i, (chord, dur) in enumerate(top_baseline, 1):
        print(f"  {i}. {chord:25s} ({dur:.2f}s)")
    print()

    # =================================================================
    # MODE 1: SOFT filtering
    # =================================================================
    print("="*80)
    print("MODE 1: SOFT FILTERING")
    print("="*80)

    soft_filter = AggressiveTheoryFilter(
        snr_threshold=6.5,
        top_k_candidates=10,
        filter_mode='SOFT'
    )

    soft_results = soft_filter.detect_with_aggressive_filtering(
        results['snr_matrix'],
        all_template_names,
        time_per_slice
    )

    soft_chords = soft_results['detections']
    soft_durations = {}
    for seg in soft_chords:
        chord = seg['chord']
        if chord not in soft_durations:
            soft_durations[chord] = 0
        soft_durations[chord] += seg['duration']

    soft_complexity = analyze_chord_complexity(soft_durations)

    print(f"Unique chords: {soft_complexity['total']}")
    print(f"  Simple: {soft_complexity['simple']}, 7th: {soft_complexity['seventh']}, Sus: {soft_complexity['sus']}, Complex: {soft_complexity['complex']}")
    print()

    top_soft = sorted(soft_durations.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 chords:")
    for i, (chord, dur) in enumerate(top_soft, 1):
        print(f"  {i}. {chord:25s} ({dur:.2f}s)")
    print()

    # =================================================================
    # MODE 2: MEDIUM filtering
    # =================================================================
    print("="*80)
    print("MODE 2: MEDIUM FILTERING")
    print("="*80)

    medium_filter = AggressiveTheoryFilter(
        snr_threshold=6.5,
        top_k_candidates=10,
        filter_mode='MEDIUM'
    )

    medium_results = medium_filter.detect_with_aggressive_filtering(
        results['snr_matrix'],
        all_template_names,
        time_per_slice
    )

    medium_chords = medium_results['detections']
    medium_durations = {}
    for seg in medium_chords:
        chord = seg['chord']
        if chord not in medium_durations:
            medium_durations[chord] = 0
        medium_durations[chord] += seg['duration']

    medium_complexity = analyze_chord_complexity(medium_durations)

    print(f"Unique chords: {medium_complexity['total']}")
    print(f"  Simple: {medium_complexity['simple']}, 7th: {medium_complexity['seventh']}, Sus: {medium_complexity['sus']}, Complex: {medium_complexity['complex']}")
    print()

    top_medium = sorted(medium_durations.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 chords:")
    for i, (chord, dur) in enumerate(top_medium, 1):
        print(f"  {i}. {chord:25s} ({dur:.2f}s)")
    print()

    # =================================================================
    # MODE 3: HARD filtering
    # =================================================================
    print("="*80)
    print("MODE 3: HARD FILTERING (only in-key chords)")
    print("="*80)

    hard_filter = AggressiveTheoryFilter(
        snr_threshold=6.5,
        top_k_candidates=10,
        filter_mode='HARD'
    )

    hard_results = hard_filter.detect_with_aggressive_filtering(
        results['snr_matrix'],
        all_template_names,
        time_per_slice
    )

    hard_chords = hard_results['detections']
    hard_durations = {}
    for seg in hard_chords:
        chord = seg['chord']
        if chord not in hard_durations:
            hard_durations[chord] = 0
        hard_durations[chord] += seg['duration']

    hard_complexity = analyze_chord_complexity(hard_durations)

    print(f"Unique chords: {hard_complexity['total']}")
    print(f"  Simple: {hard_complexity['simple']}, 7th: {hard_complexity['seventh']}, Sus: {hard_complexity['sus']}, Complex: {hard_complexity['complex']}")
    print()

    top_hard = sorted(hard_durations.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 chords:")
    for i, (chord, dur) in enumerate(top_hard, 1):
        print(f"  {i}. {chord:25s} ({dur:.2f}s)")
    print()

    # =================================================================
    # FINAL COMPARISON
    # =================================================================
    print("="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    print()

    print(f"{'Mode':<15} {'Segments':<12} {'Unique':<10} {'Simple':<10} {'7th':<8} {'Sus':<8} {'Complex':<10} {'In-Key %':<10}")
    print("-" * 90)

    baseline_in_key = "N/A"
    print(f"{'BASELINE':<15} {len(baseline_merged):<12} {baseline_complexity['total']:<10} {baseline_complexity['simple']:<10} {baseline_complexity['seventh']:<8} {baseline_complexity['sus']:<8} {baseline_complexity['complex']:<10} {baseline_in_key:<10}")

    soft_in_key_pct = f"{100*soft_results['stats']['num_in_key']/soft_results['stats']['total_detections']:.1f}%"
    print(f"{'SOFT':<15} {len(soft_chords):<12} {soft_complexity['total']:<10} {soft_complexity['simple']:<10} {soft_complexity['seventh']:<8} {soft_complexity['sus']:<8} {soft_complexity['complex']:<10} {soft_in_key_pct:<10}")

    medium_in_key_pct = f"{100*medium_results['stats']['num_in_key']/medium_results['stats']['total_detections']:.1f}%"
    print(f"{'MEDIUM':<15} {len(medium_chords):<12} {medium_complexity['total']:<10} {medium_complexity['simple']:<10} {medium_complexity['seventh']:<8} {medium_complexity['sus']:<8} {medium_complexity['complex']:<10} {medium_in_key_pct:<10}")

    hard_in_key_pct = f"{100*hard_results['stats']['num_in_key']/hard_results['stats']['total_detections']:.1f}%" if hard_results['stats']['total_detections'] > 0 else "100.0%"
    print(f"{'HARD':<15} {len(hard_chords):<12} {hard_complexity['total']:<10} {hard_complexity['simple']:<10} {hard_complexity['seventh']:<8} {hard_complexity['sus']:<8} {hard_complexity['complex']:<10} {hard_in_key_pct:<10}")

    print()
    print("="*80)
    print("✓ Comparison complete!")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_aggressive_filtering.py INPUT.wav")
        print()
        print("Compares 4 detection modes:")
        print("  BASELINE - Pure SNR (no theory)")
        print("  SOFT     - Multiplicative bonuses")
        print("  MEDIUM   - Strong penalties for out-of-key")
        print("  HARD     - Only in-key chords")
        sys.exit(1)

    wav_path = sys.argv[1]
    compare_all_modes(wav_path)
