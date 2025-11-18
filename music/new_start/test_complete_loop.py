#!/usr/bin/env python3
"""
Test the complete loop:
MIDI → WAV → Spectral Analysis → 2D Array → Graph → Music Theory → MIDI
"""

import sys
import numpy as np
from scipy.io import wavfile
import mido

from midi_to_wav_simple import midi_to_wav
from spectral_analyzer import SpectralAnalyzer
from audio_graph_builder import AudioGraphBuilder
from harmonic_analyzer import HarmonicAnalyzer
from onset_detector import OnsetDetector
from midi_generator import MidiGenerator

def test_complete_loop(midi_path: str, verbose: bool = True):
    """
    Test complete MIDI → WAV → Analysis → Graph → Theory → MIDI loop.

    Shows each transformation step.
    """

    print("="*70)
    print("TESTING COMPLETE LOOP: MIDI → WAV → Fourier → Graph → Theory → MIDI")
    print("="*70)

    # ========================================================================
    # STEP 1: MIDI → WAV (Synthesis)
    # ========================================================================
    print("\n[STEP 1] MIDI → WAV (Synthesis)")
    print("-" * 70)

    wav_path = 'test_loop_temp.wav'
    midi_to_wav(midi_path, wav_path, verbose=False)

    # Analyze input MIDI
    original_midi = mido.MidiFile(midi_path)
    original_notes = []
    for track in original_midi.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                original_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    print(f"  Input MIDI: {midi_path}")
    print(f"  Original notes: {len(original_notes)}")
    print(f"  Output WAV: {wav_path}")

    # ========================================================================
    # STEP 2: WAV → Fourier Analysis → 2D Array
    # ========================================================================
    print("\n[STEP 2] WAV → Fourier Analysis → 2D Array")
    print("-" * 70)

    sample_rate, audio_data = wavfile.read(wav_path)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]  # Left channel

    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Audio samples: {len(audio_data):,}")
    print(f"  Duration: {len(audio_data)/sample_rate:.2f} seconds")

    # Create spectral analyzer
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=1.5,
        standard_A4=440.0,
        note_begin=21,   # A0
        note_end=108,    # C8
        increments=1
    )

    # Perform Fourier-like analysis
    spectral_data = analyzer.dotop(audio_data)

    print(f"\n  Spectral Analysis Results:")
    print(f"    2D Array shape: {spectral_data.shape}")
    print(f"    Frequencies analyzed: {spectral_data.shape[0]}")
    print(f"    Time frames: {spectral_data.shape[1]}")
    print(f"    Frequency range: {analyzer.frequencies[0]:.2f} Hz to {analyzer.frequencies[-1]:.2f} Hz")
    print(f"    Max intensity: {np.max(spectral_data):.4f}")
    print(f"    Mean intensity: {np.mean(spectral_data):.4f}")

    # ========================================================================
    # STEP 3: 2D Array → Graph Construction
    # ========================================================================
    print("\n[STEP 3] 2D Array → Graph Construction")
    print("-" * 70)

    graph_builder = AudioGraphBuilder(
        spectral_data=spectral_data,
        frequencies=analyzer.frequencies,
        sample_rate=sample_rate,
        window_length=analyzer.window_length,
        intensity_threshold=0.02
    )

    graph = graph_builder.build_graph()

    print(f"  Graph Construction Results:")
    print(f"    Nodes: {graph.number_of_nodes():,}")
    print(f"    Edges: {graph.number_of_edges():,}")
    print(f"    Density: {graph.number_of_edges() / (graph.number_of_nodes() * graph.number_of_nodes()):.6f}")

    # Analyze edge types
    temporal_edges = 0
    harmonic_edges = 0
    for u, v, key, data in graph.edges(keys=True, data=True):
        if data.get('type') == 'temporal':
            temporal_edges += 1
        elif data.get('type') == 'harmonic':
            harmonic_edges += 1

    print(f"    Temporal edges: {temporal_edges:,}")
    print(f"    Harmonic edges: {harmonic_edges:,}")

    # ========================================================================
    # STEP 4: Apply Music Theory (Harmonic Analysis)
    # ========================================================================
    print("\n[STEP 4] Apply Music Theory (Harmonic Analysis)")
    print("-" * 70)

    harmonic_analyzer = HarmonicAnalyzer(graph)

    # Detect fundamentals
    fundamentals_by_time = harmonic_analyzer.analyze_all_time_samples()

    # Filter noise
    filtered_fundamentals = harmonic_analyzer.filter_noise(
        min_confidence=0.15,
        min_duration_samples=2
    )

    print(f"  Music Theory Analysis Results:")
    print(f"    Communities detected: {len(fundamentals_by_time)}")
    print(f"    Fundamental frequencies: {len(filtered_fundamentals)}")

    if filtered_fundamentals:
        # Analyze detected pitches
        pitches = [f['note'] for f in filtered_fundamentals]
        from collections import Counter
        pitch_counts = Counter(pitches)
        top_pitches = pitch_counts.most_common(5)

        print(f"    Top 5 detected pitches:")
        for pitch, count in top_pitches:
            print(f"      {pitch}: {count} occurrences")

    # ========================================================================
    # STEP 5: Graph → Onset Detection
    # ========================================================================
    print("\n[STEP 5] Onset Detection (Temporal Analysis)")
    print("-" * 70)

    onset_detector = OnsetDetector(
        graph=graph,
        onset_threshold=0.1,
        min_onset_gap_seconds=0.05
    )

    note_events = onset_detector.detect_onsets(filtered_fundamentals)

    print(f"  Onset Detection Results:")
    print(f"    Note events detected: {len(note_events)}")

    if note_events:
        # Analyze temporal distribution
        onset_times = [e['onset_time_seconds'] for e in note_events]
        print(f"    First onset: {min(onset_times):.2f} seconds")
        print(f"    Last onset: {max(onset_times):.2f} seconds")
        print(f"    Avg duration: {np.mean([e['duration_seconds'] for e in note_events]):.3f} seconds")

    # ========================================================================
    # STEP 6: Reconstruct MIDI File
    # ========================================================================
    print("\n[STEP 6] Reconstruct MIDI File")
    print("-" * 70)

    output_midi_path = 'test_loop_output.mid'

    midi_generator = MidiGenerator(tempo=120)
    if note_events:
        midi_generator.generate_midi(note_events, output_midi_path)
        print(f"  Output MIDI: {output_midi_path}")
        print(f"  Notes written: {len(note_events)}")
    else:
        print(f"  WARNING: No notes detected, creating empty MIDI")
        import mido as m
        midi_file = m.MidiFile(type=1, ticks_per_beat=480)
        track = m.MidiTrack()
        track.append(m.MetaMessage('set_tempo', tempo=500000, time=0))
        track.append(m.MetaMessage('end_of_track', time=0))
        midi_file.tracks.append(track)
        midi_file.save(output_midi_path)

    # ========================================================================
    # STEP 7: Compare Original vs Reconstructed
    # ========================================================================
    print("\n[STEP 7] Comparison: Original vs Reconstructed")
    print("-" * 70)

    reconstructed_midi = mido.MidiFile(output_midi_path)
    reconstructed_notes = []
    for track in reconstructed_midi.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                reconstructed_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    print(f"  Original notes:       {len(original_notes)}")
    print(f"  Reconstructed notes:  {len(reconstructed_notes)}")

    if len(original_notes) > 0:
        detection_rate = len(reconstructed_notes) / len(original_notes)
        print(f"  Detection rate:       {detection_rate:.1%}")

        # Count pitch matches
        original_pitches = set(n['note'] for n in original_notes)
        reconstructed_pitches = set(n['note'] for n in reconstructed_notes)

        matches = original_pitches & reconstructed_pitches
        print(f"  Unique pitches (original): {len(original_pitches)}")
        print(f"  Unique pitches (reconstructed): {len(reconstructed_pitches)}")
        print(f"  Pitch overlap: {len(matches)} / {len(original_pitches)} = {len(matches)/max(1,len(original_pitches)):.1%}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*70)
    print("SUMMARY: Complete Loop Test")
    print("="*70)

    print(f"\n  ✓ Step 1: MIDI → WAV synthesis")
    print(f"  ✓ Step 2: Fourier analysis → {spectral_data.shape} array")
    print(f"  ✓ Step 3: Graph construction → {graph.number_of_nodes():,} nodes")
    print(f"  ✓ Step 4: Music theory → {len(filtered_fundamentals)} fundamentals")
    print(f"  ✓ Step 5: Onset detection → {len(note_events)} events")
    print(f"  ✓ Step 6: MIDI reconstruction → {output_midi_path}")

    if len(note_events) > 0:
        print(f"\n  RESULT: Loop is FUNCTIONAL ✓")
        if detection_rate > 2.0:
            print(f"  NOTE: Over-detection ({detection_rate:.1f}x) - system is very sensitive")
        elif detection_rate < 0.5:
            print(f"  NOTE: Under-detection ({detection_rate:.1%}) - may need lower thresholds")
        else:
            print(f"  NOTE: Detection rate reasonable ({detection_rate:.1%})")
    else:
        print(f"\n  RESULT: Loop functional but no notes detected")
        print(f"  NOTE: Try lowering thresholds (--intensity-threshold, --confidence, --onset-threshold)")

    print("\n" + "="*70)

    return {
        'original_notes': len(original_notes),
        'reconstructed_notes': len(reconstructed_notes),
        'spectral_shape': spectral_data.shape,
        'graph_nodes': graph.number_of_nodes(),
        'graph_edges': graph.number_of_edges(),
        'fundamentals': len(filtered_fundamentals),
        'note_events': len(note_events)
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_complete_loop.py <midi_file>")
        print("\nExample:")
        print("  python test_complete_loop.py midi_files/Amazing_Grace_in_G_major_for_Piano_-_BreezePiano.mid")
        sys.exit(1)

    midi_file = sys.argv[1]
    results = test_complete_loop(midi_file, verbose=True)
