#!/usr/bin/env python3
"""
Debug script to understand chord recognition filtering behavior.
"""

import sys
from scipy.io import wavfile
from spectral_analyzer import SpectralAnalyzer
from audio_graph_builder import AudioGraphBuilder
from harmonic_analyzer import HarmonicAnalyzer
from chord_recognizer import ChordRecognizer
from collections import Counter

def debug_chord_recognition(wav_path: str):
    """Debug chord recognition on a WAV file."""

    print(f"Analyzing: {wav_path}")
    print("=" * 70)

    # Load audio
    sample_rate, audio_data = wavfile.read(wav_path)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    # Spectral analysis
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=1.5,
        standard_A4=440.0,
        note_begin=21,
        note_end=108,
        increments=1
    )
    spectral_data = analyzer.dotop(audio_data)

    # Build graph
    graph_builder = AudioGraphBuilder(
        spectral_data=spectral_data,
        frequencies=analyzer.frequencies,
        sample_rate=sample_rate,
        window_length=analyzer.window_length,
        intensity_threshold=0.02
    )
    graph = graph_builder.build_graph()

    # Harmonic analysis
    harmonic_analyzer = HarmonicAnalyzer(graph)
    fundamentals_by_time = harmonic_analyzer.analyze_all_time_samples()
    filtered_fundamentals = harmonic_analyzer.filter_noise(
        min_confidence=0.15,
        min_duration_samples=2
    )

    print(f"\n[Before Chord Recognition]")
    print(f"  Fundamentals: {len(filtered_fundamentals)}")

    # Show pitch distribution
    pitches_before = [f['note'] for f in filtered_fundamentals]
    pitch_counts_before = Counter(pitches_before)
    print(f"  Unique pitches: {len(pitch_counts_before)}")
    print(f"  Top 5 pitches: {pitch_counts_before.most_common(5)}")

    # Apply chord recognition
    chord_recognizer = ChordRecognizer(time_window_ms=100)
    theory_results = chord_recognizer.analyze_with_theory_correlation(
        filtered_fundamentals, graph
    )

    print(f"\n[Chord Recognition Results]")
    print(f"  Detected key: {theory_results['detected_key']}")
    print(f"  Detected chords: {len(theory_results['detected_chords'])}")
    print(f"  Time windows analyzed: {theory_results['total_windows']}")

    # Show filtering stats
    stats = theory_results['filtering_stats']
    print(f"\n[Filtering Statistics]")
    print(f"  Original count: {stats['original_count']}")
    print(f"  Filtered count: {stats['filtered_count']}")
    print(f"  Reduction: {stats['reduction']*100:.1f}%")

    # Show pitch distribution after filtering
    filtered_notes = theory_results['filtered_fundamentals']
    pitches_after = [f['note'] for f in filtered_notes]
    pitch_counts_after = Counter(pitches_after)
    print(f"\n[After Chord Recognition]")
    print(f"  Fundamentals: {len(filtered_notes)}")
    print(f"  Unique pitches: {len(pitch_counts_after)}")
    print(f"  Top 5 pitches: {pitch_counts_after.most_common(5)}")

    # Show which pitches were removed most
    removed_pitches = {}
    for pitch in pitch_counts_before:
        before = pitch_counts_before[pitch]
        after = pitch_counts_after.get(pitch, 0)
        if before > after:
            removed_pitches[pitch] = before - after

    print(f"\n[Pitches Removed]")
    top_removed = sorted(removed_pitches.items(), key=lambda x: x[1], reverse=True)[:10]
    for pitch, count in top_removed:
        print(f"  {pitch}: {count} removed (had {pitch_counts_before[pitch]}, now {pitch_counts_after.get(pitch, 0)})")

    # Show detected chords
    print(f"\n[Detected Chords] (first 10)")
    for i, chord in enumerate(theory_results['detected_chords'][:10]):
        print(f"  {i+1}. Time {chord['time']:.2f}s: {chord['chord']} (score: {chord['score']:.2f})")
        print(f"      Notes: {chord['notes']}")

    # Show correlation timeline summary
    timeline = theory_results['correlation_timeline']
    if timeline:
        avg_chord_score = sum(t['chord_score'] for t in timeline) / len(timeline)
        avg_key_corr = sum(t['key_correlation'] for t in timeline) / len(timeline)
        print(f"\n[Correlation Timeline Summary]")
        print(f"  Average chord score: {avg_chord_score:.3f}")
        print(f"  Average key correlation: {avg_key_corr:.3f}")
        print(f"  Avg notes per window: {sum(t['num_notes'] for t in timeline) / len(timeline):.1f}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_chord_recognition.py <wav_file>")
        print("\nExample:")
        print("  python debug_chord_recognition.py test_amazing_grace.wav")
        sys.exit(1)

    wav_file = sys.argv[1]
    debug_chord_recognition(wav_file)
