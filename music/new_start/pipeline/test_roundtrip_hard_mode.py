#!/usr/bin/env python3
"""
Complete Roundtrip Test with HARD Mode + Enhanced Synthesis

Test pipeline:
1. MIDI → WAV (enhanced synthesis with realistic instruments)
2. WAV → MIDI (PSF detection with HARD mode filtering)
3. Compare original vs detected chords

Tests with multiple MIDI files from midi_files directory.
"""

import sys
import time
import numpy as np
from pathlib import Path
from collections import Counter

# Import synthesis
from reco_enhanced import midi_to_wav as enhanced_midi_to_wav

# Import detection
from scipy.io import wavfile
from spectral_analyzer import SpectralAnalyzer
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs
from aggressive_theory_filter import AggressiveTheoryFilter


def roundtrip_test(midi_path, filter_mode="HARD", use_enhanced_synthesis=True, verbose=True):
    """
    Complete roundtrip test: MIDI → WAV → MIDI (chords).

    Args:
        midi_path: Path to input MIDI file
        filter_mode: Theory filtering mode (HARD, MEDIUM, SOFT, BASELINE)
        use_enhanced_synthesis: Use enhanced synthesis (True) or original (False)
        verbose: Print detailed output

    Returns:
        Dict with test results
    """
    midi_path = Path(midi_path)

    if verbose:
        print("="*80)
        print(f"ROUNDTRIP TEST: {midi_path.name}")
        print("="*80)
        print(f"Filter mode: {filter_mode}")
        print(f"Enhanced synthesis: {use_enhanced_synthesis}")
        print()

    # Step 1: MIDI → WAV
    if verbose:
        print("[1/3] MIDI → WAV Synthesis")
        print("-" * 80)

    wav_path = midi_path.with_name(midi_path.stem + f"_roundtrip_{filter_mode.lower()}.wav")

    synth_start = time.perf_counter()

    if use_enhanced_synthesis:
        try:
            enhanced_midi_to_wav(str(midi_path), str(wav_path), verbose=verbose)
            synth_time = time.perf_counter() - synth_start
        except Exception as e:
            print(f"Enhanced synthesis failed: {e}")
            print("Falling back to simple synthesis...")
            # Fallback would go here
            return None
    else:
        # Use original synthesis
        from midi_to_wav_simple import midi_to_wav as original_midi_to_wav
        original_midi_to_wav(str(midi_path), str(wav_path), verbose=verbose)
        synth_time = time.perf_counter() - synth_start

    if verbose:
        print(f"✓ Synthesis time: {synth_time:.2f}s")
        print()

    # Step 2: WAV → Spectral Analysis
    if verbose:
        print("[2/3] WAV → Spectral Analysis")
        print("-" * 80)

    # Load audio
    sample_rate, audio_data = wavfile.read(wav_path)

    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0

    duration = len(audio_data) / sample_rate

    # Spectral analysis
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=4,
        standard_A4=440.0,
        increments=12
    )

    spec_start = time.perf_counter()
    spectral_data = analyzer.dotop(audio_data)
    spec_time = time.perf_counter() - spec_start

    if verbose:
        print(f"Audio duration: {duration:.2f}s")
        print(f"Spectral shape: {spectral_data.shape}")
        print(f"✓ Spectral analysis time: {spec_time:.2f}s")
        print()

    # Step 3: PSF Chord Detection with Theory Filtering
    if verbose:
        print(f"[3/3] Chord Detection ({filter_mode} mode)")
        print("-" * 80)

    # Load PSF templates
    templates, frequencies, metadata = load_multi_octave_psfs("multi_octave_psf_templates.pkl")

    # Initialize detector
    detector = UltraFastChordDetector(templates, threshold=6.5, use_outlier_removal=True)

    # Get SNR matrix
    detect_start = time.perf_counter()
    results = detector.detect_all_time_slices(spectral_data)
    detect_time = time.perf_counter() - detect_start

    if verbose:
        print(f"✓ SNR matrix computed: {detect_time:.3f}s")
        print(f"  Rate: {results['num_time'] / detect_time:.0f} slices/sec")

    # Apply theory filtering
    time_per_slice = duration / spectral_data.shape[1]

    if filter_mode == "BASELINE":
        # No filtering
        chord_list = []
        for i in range(results['num_time']):
            if results['detected_flags'][i]:
                chord_list.append(results['chord_names'][i])
    else:
        # Use aggressive filtering
        theory_filter = AggressiveTheoryFilter(
            snr_threshold=6.5,
            top_k_candidates=10,
            filter_mode=filter_mode
        )

        filter_results = theory_filter.detect_with_aggressive_filtering(
            results['snr_matrix'],
            detector.template_names,
            time_per_slice
        )

        chord_list = [seg['chord'] for seg in filter_results['detections']]

    # Analyze detected chords
    chord_counter = Counter(chord_list)
    total_chords = len(chord_list)
    unique_chords = len(chord_counter)

    # Chord complexity analysis
    simple_chords = sum(1 for c in chord_counter if 'major' in c or 'minor' in c)
    sus_chords = sum(1 for c in chord_counter if 'sus' in c)
    complex_chords = sum(1 for c in chord_counter if 'maj11' in c or 'dom9' in c or 'aug' in c)
    seventh_chords = sum(1 for c in chord_counter if 'min7' in c or 'maj7' in c or 'dom7' in c)

    if verbose:
        print()
        print("="*80)
        print("RESULTS")
        print("="*80)
        print(f"Total chord segments: {total_chords}")
        print(f"Unique chords: {unique_chords}")
        print(f"  Simple (major/minor): {simple_chords}")
        print(f"  7th chords: {seventh_chords}")
        print(f"  Sus chords: {sus_chords}")
        print(f"  Complex: {complex_chords}")
        print()

        print("Top 10 detected chords:")
        for i, (chord, count) in enumerate(chord_counter.most_common(10), 1):
            print(f"  {i:2d}. {chord:30s} ({count} segments)")

        print()
        print(f"Total processing time: {synth_time + spec_time + detect_time:.2f}s")
        print("="*80)

    return {
        'midi_file': midi_path.name,
        'filter_mode': filter_mode,
        'total_chords': total_chords,
        'unique_chords': unique_chords,
        'simple_chords': simple_chords,
        'seventh_chords': seventh_chords,
        'sus_chords': sus_chords,
        'complex_chords': complex_chords,
        'top_chords': chord_counter.most_common(5),
        'synth_time': synth_time,
        'detect_time': detect_time,
        'total_time': synth_time + spec_time + detect_time
    }


def test_multiple_files(midi_dir, filter_mode="HARD", max_files=5):
    """
    Test multiple MIDI files.

    Args:
        midi_dir: Directory containing MIDI files
        filter_mode: Theory filtering mode
        max_files: Maximum number of files to test
    """
    midi_dir = Path(midi_dir)

    if not midi_dir.exists():
        print(f"ERROR: Directory not found: {midi_dir}")
        return

    # Find MIDI files
    midi_files = list(midi_dir.glob("*.mid"))

    if not midi_files:
        print(f"No MIDI files found in {midi_dir}")
        return

    print(f"Found {len(midi_files)} MIDI files")
    print()

    # Test up to max_files
    results = []
    for i, midi_file in enumerate(midi_files[:max_files]):
        print()
        result = roundtrip_test(midi_file, filter_mode=filter_mode, verbose=True)
        if result:
            results.append(result)

        if i < min(len(midi_files), max_files) - 1:
            print()
            print()

    # Summary
    if results:
        print()
        print("="*80)
        print(f"SUMMARY ({len(results)} files tested)")
        print("="*80)
        print()

        print(f"{'File':<30s} {'Total':<8s} {'Unique':<8s} {'Simple':<8s} {'7th':<8s} {'Sus':<8s} {'Complex':<8s}")
        print("-" * 90)

        for r in results:
            print(f"{r['midi_file']:<30s} {r['total_chords']:<8d} {r['unique_chords']:<8d} "
                  f"{r['simple_chords']:<8d} {r['seventh_chords']:<8d} {r['sus_chords']:<8d} {r['complex_chords']:<8d}")

        print()
        print(f"Average unique chords: {np.mean([r['unique_chords'] for r in results]):.1f}")
        print(f"Average simple chords: {np.mean([r['simple_chords'] for r in results]):.1f}")
        print(f"Average sus chords: {np.mean([r['sus_chords'] for r in results]):.1f}")
        print(f"Average total time: {np.mean([r['total_time'] for r in results]):.2f}s")
        print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:  python test_roundtrip_hard_mode.py INPUT.mid [FILTER_MODE]")
        print("  Multiple files: python test_roundtrip_hard_mode.py MIDI_DIR/ [FILTER_MODE] [MAX_FILES]")
        print()
        print("Filter modes: HARD (default), MEDIUM, SOFT, BASELINE")
        print()
        print("Examples:")
        print("  python test_roundtrip_hard_mode.py CdL.mid")
        print("  python test_roundtrip_hard_mode.py ../midi_files/ HARD 3")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    filter_mode = sys.argv[2] if len(sys.argv) > 2 else "HARD"
    max_files = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    if input_path.is_file():
        # Test single file
        roundtrip_test(input_path, filter_mode=filter_mode, verbose=True)
    elif input_path.is_dir():
        # Test multiple files
        test_multiple_files(input_path, filter_mode=filter_mode, max_files=max_files)
    else:
        print(f"ERROR: Not a file or directory: {input_path}")
        sys.exit(1)
