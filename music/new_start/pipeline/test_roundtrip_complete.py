#!/usr/bin/env python3
"""
Complete Roundtrip Test with A.wav vs B.wav Comparison

Full pipeline:
1. MIDI → A.wav (enhanced synthesis)
2. A.wav → Spectral analysis → Chord detection
3. Detected chords → MIDI (reconstructed)
4. MIDI → B.wav (re-synthesis)
5. Compare A.wav vs B.wav

This allows audible comparison of original synthesis vs detected chords.
"""

import sys
import time
import numpy as np
import mido
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


def chord_name_to_midi_notes(chord_name, root_octave=4):
    """
    Convert chord name to MIDI note numbers.

    Args:
        chord_name: e.g., "C#_major_oct3"
        root_octave: Override octave if needed

    Returns:
        List of MIDI note numbers for this chord
    """
    # Parse chord name
    parts = chord_name.split('_')
    root = parts[0]
    octave_str = [p for p in parts if p.startswith('oct')]
    octave = int(octave_str[0].replace('oct', '')) if octave_str else root_octave
    chord_type = '_'.join([p for p in parts[1:] if not p.startswith('oct')])

    # Note to MIDI number mapping (C4 = 60)
    note_map = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
        'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }

    root_note = note_map.get(root, 0) + (octave * 12)

    # Chord intervals (semitones from root)
    chord_intervals = {
        'major': [0, 4, 7],
        'minor': [0, 3, 7],
        'dim': [0, 3, 6],
        'aug': [0, 4, 8],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
        'maj7': [0, 4, 7, 11],
        'min7': [0, 3, 7, 10],
        'dom7': [0, 4, 7, 10],
        'maj9': [0, 4, 7, 11, 14],
        'dom9': [0, 4, 7, 10, 14],
        'maj11': [0, 4, 7, 11, 14, 17],
    }

    intervals = chord_intervals.get(chord_type, [0, 4, 7])  # Default to major
    midi_notes = [root_note + interval for interval in intervals]

    return midi_notes


def chords_to_midi(chord_segments, output_path, tempo=120, velocity=80):
    """
    Convert chord segments to MIDI file.

    Args:
        chord_segments: List of dicts with 'start_time', 'duration', 'chord'
        output_path: Output MIDI file path
        tempo: Tempo in BPM
        velocity: Note velocity (0-127)

    Returns:
        Path to created MIDI file
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo_us = mido.bpm2tempo(tempo)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo_us, time=0))

    # Convert chord segments to MIDI events
    # We need to track when notes turn on/off
    events = []

    for seg in chord_segments:
        start_time = seg['start_time']
        duration = seg['duration']
        chord_name = seg['chord']

        # Get MIDI notes for this chord
        midi_notes = chord_name_to_midi_notes(chord_name)

        # Create note on/off events
        for note in midi_notes:
            events.append({
                'time': start_time,
                'type': 'note_on',
                'note': note,
                'velocity': velocity
            })
            events.append({
                'time': start_time + duration,
                'type': 'note_off',
                'note': note,
                'velocity': 0
            })

    # Sort events by time
    events.sort(key=lambda x: (x['time'], 0 if x['type'] == 'note_on' else 1))

    # Convert to MIDI messages with delta times
    current_time = 0.0
    ticks_per_beat = mid.ticks_per_beat

    for event in events:
        # Calculate delta time in ticks
        delta_seconds = event['time'] - current_time
        delta_ticks = int(mido.second2tick(delta_seconds, ticks_per_beat, tempo_us))

        if event['type'] == 'note_on':
            track.append(mido.Message('note_on',
                                     note=event['note'],
                                     velocity=event['velocity'],
                                     time=delta_ticks))
        else:
            track.append(mido.Message('note_off',
                                     note=event['note'],
                                     velocity=0,
                                     time=delta_ticks))

        current_time = event['time']

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)

    return output_path


def complete_roundtrip_test(midi_path, filter_mode="HARD", output_dir=None, verbose=True):
    """
    Complete roundtrip test with A.wav vs B.wav comparison.

    Args:
        midi_path: Path to input MIDI file
        filter_mode: Theory filtering mode (HARD, MEDIUM, SOFT, BASELINE)
        output_dir: Directory for output files (default: same as input)
        verbose: Print detailed output

    Returns:
        Dict with test results and file paths
    """
    midi_path = Path(midi_path)

    # Set output directory
    if output_dir is None:
        output_dir = midi_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("="*80)
        print(f"COMPLETE ROUNDTRIP TEST: {midi_path.name}")
        print("="*80)
        print(f"Filter mode: {filter_mode}")
        print()

    # ============================================================================
    # STEP 1: MIDI → A.wav (Original synthesis)
    # ============================================================================
    if verbose:
        print("[1/5] MIDI → A.wav (Original Synthesis)")
        print("-" * 80)

    a_wav_path = output_dir / (midi_path.stem + "_A.wav")

    synth_start = time.perf_counter()
    enhanced_midi_to_wav(str(midi_path), str(a_wav_path), verbose=verbose)
    synth_time = time.perf_counter() - synth_start

    if verbose:
        print(f"✓ A.wav created: {a_wav_path.name}")
        print(f"  Synthesis time: {synth_time:.2f}s")
        print()

    # ============================================================================
    # STEP 2: A.wav → Spectral Analysis
    # ============================================================================
    if verbose:
        print("[2/5] A.wav → Spectral Analysis")
        print("-" * 80)

    # Load audio
    sample_rate, audio_data = wavfile.read(a_wav_path)

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

    # ============================================================================
    # STEP 3: Chord Detection
    # ============================================================================
    if verbose:
        print(f"[3/5] Chord Detection ({filter_mode} mode)")
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

    # Apply theory filtering
    time_per_slice = duration / spectral_data.shape[1]

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

    chord_segments = filter_results['detections']

    if verbose:
        print(f"✓ Detected {len(chord_segments)} chord segments")
        print()

    # ============================================================================
    # STEP 4: Detected Chords → MIDI
    # ============================================================================
    if verbose:
        print("[4/5] Detected Chords → MIDI")
        print("-" * 80)

    detected_midi_path = output_dir / (midi_path.stem + "_detected.mid")

    midi_start = time.perf_counter()
    chords_to_midi(chord_segments, detected_midi_path, tempo=120, velocity=80)
    midi_time = time.perf_counter() - midi_start

    if verbose:
        print(f"✓ MIDI created: {detected_midi_path.name}")
        print(f"  Chords: {len(chord_segments)} segments")
        print(f"  Creation time: {midi_time:.3f}s")
        print()

    # ============================================================================
    # STEP 5: MIDI → B.wav (Re-synthesis)
    # ============================================================================
    if verbose:
        print("[5/5] MIDI → B.wav (Re-synthesis from Detected Chords)")
        print("-" * 80)

    b_wav_path = output_dir / (midi_path.stem + "_B.wav")

    resynth_start = time.perf_counter()
    enhanced_midi_to_wav(str(detected_midi_path), str(b_wav_path), verbose=verbose)
    resynth_time = time.perf_counter() - resynth_start

    if verbose:
        print(f"✓ B.wav created: {b_wav_path.name}")
        print(f"  Re-synthesis time: {resynth_time:.2f}s")
        print()

    # ============================================================================
    # RESULTS
    # ============================================================================
    chord_counter = Counter([seg['chord'] for seg in chord_segments])

    if verbose:
        print("="*80)
        print("COMPLETE ROUNDTRIP RESULTS")
        print("="*80)
        print(f"Input MIDI:      {midi_path.name}")
        print(f"A.wav (original): {a_wav_path.name}")
        print(f"Detected MIDI:   {detected_midi_path.name}")
        print(f"B.wav (detected): {b_wav_path.name}")
        print()
        print(f"Chord segments:  {len(chord_segments)}")
        print(f"Unique chords:   {len(chord_counter)}")
        print(f"Detected key:    {filter_results['key']}")
        print()
        print("Top 10 detected chords:")
        for i, (chord, count) in enumerate(chord_counter.most_common(10), 1):
            print(f"  {i:2d}. {chord:30s} ({count} segments)")
        print()
        print(f"Total time: {synth_time + spec_time + detect_time + midi_time + resynth_time:.2f}s")
        print()
        print("COMPARISON:")
        print(f"  A.wav = Original synthesis from {midi_path.name}")
        print(f"  B.wav = Re-synthesis from detected chords")
        print(f"  Listen to both to hear detection quality!")
        print("="*80)

    return {
        'input_midi': str(midi_path),
        'a_wav': str(a_wav_path),
        'detected_midi': str(detected_midi_path),
        'b_wav': str(b_wav_path),
        'chord_segments': len(chord_segments),
        'unique_chords': len(chord_counter),
        'detected_key': filter_results['key'],
        'total_time': synth_time + spec_time + detect_time + midi_time + resynth_time
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_roundtrip_complete.py INPUT.mid [FILTER_MODE] [OUTPUT_DIR]")
        print()
        print("Filter modes: HARD (default), MEDIUM, SOFT, BASELINE")
        print()
        print("Examples:")
        print("  python test_roundtrip_complete.py CdL.mid HARD")
        print("  python test_roundtrip_complete.py CdL.mid HARD ../working_files")
        print()
        print("Output files:")
        print("  INPUT_A.wav          - Original synthesis")
        print("  INPUT_detected.mid   - Detected chords as MIDI")
        print("  INPUT_B.wav          - Re-synthesis from detected chords")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    filter_mode = sys.argv[2] if len(sys.argv) > 2 else "HARD"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    if not input_path.is_file():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    complete_roundtrip_test(input_path, filter_mode=filter_mode, output_dir=output_dir, verbose=True)
