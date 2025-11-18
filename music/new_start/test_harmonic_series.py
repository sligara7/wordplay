#!/usr/bin/env python3
"""
Test harmonic series analyzer vs original harmonic analyzer.
"""

import sys
from scipy.io import wavfile
from spectral_analyzer import SpectralAnalyzer
from audio_graph_builder import AudioGraphBuilder
from harmonic_analyzer import HarmonicAnalyzer
from harmonic_series_analyzer import HarmonicSeriesAnalyzer
from collections import Counter

def test_harmonic_series(wav_path: str):
    """Compare old vs new harmonic analysis."""

    print("=" * 80)
    print("HARMONIC SERIES ANALYZER TEST")
    print("=" * 80)
    print(f"\nAnalyzing: {wav_path}\n")

    # Load and analyze audio
    sample_rate, audio_data = wavfile.read(wav_path)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    print(f"Audio: {len(audio_data):,} samples at {sample_rate} Hz ({len(audio_data)/sample_rate:.2f}s)")

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
    print(f"Spectral data: {spectral_data.shape} (frequencies × time)")

    # Build graph
    graph_builder = AudioGraphBuilder(
        spectral_data=spectral_data,
        frequencies=analyzer.frequencies,
        sample_rate=sample_rate,
        window_length=analyzer.window_length,
        intensity_threshold=0.02
    )
    graph = graph_builder.build_graph()
    print(f"Graph: {graph.number_of_nodes():,} nodes, {graph.number_of_edges():,} edges")

    print("\n" + "-" * 80)
    print("ORIGINAL HARMONIC ANALYZER (Louvain Community Detection)")
    print("-" * 80)

    # Original analyzer
    original_analyzer = HarmonicAnalyzer(graph)
    original_fundamentals_by_time = original_analyzer.analyze_all_time_samples()
    original_filtered = original_analyzer.filter_noise(
        min_confidence=0.15,
        min_duration_samples=2
    )

    print(f"Time samples analyzed: {len(original_fundamentals_by_time)}")
    print(f"Fundamentals detected: {len(original_filtered)}")

    original_pitches = [f['note'] for f in original_filtered]
    original_counts = Counter(original_pitches)
    print(f"Unique pitches: {len(original_counts)}")
    print(f"Top 5 pitches: {original_counts.most_common(5)}")

    print("\n" + "-" * 80)
    print("NEW HARMONIC SERIES ANALYZER (Exponential Decay Detection)")
    print("-" * 80)

    # New analyzer
    new_analyzer = HarmonicSeriesAnalyzer(
        audio_graph=graph,
        frequency_tolerance=0.02,  # 2% tolerance
        min_harmonics=2,
        decay_threshold=0.5
    )
    new_fundamentals_by_time = new_analyzer.analyze_all_time_samples()
    new_filtered = new_analyzer.filter_noise(
        fundamentals_by_time=new_fundamentals_by_time,
        min_confidence=0.5,  # Higher confidence threshold
        min_duration_samples=2  # With cycles=1.5 (0.145s), 2 samples = 0.29s (reasonable for notes)
    )

    print(f"Time samples analyzed: {len(new_fundamentals_by_time)}")
    print(f"Fundamentals detected: {len(new_filtered)}")

    new_pitches = [f['note'] for f in new_filtered]
    new_counts = Counter(new_pitches)
    print(f"Unique pitches: {len(new_counts)}")
    print(f"Top 5 pitches: {new_counts.most_common(5)}")

    # Show statistics on harmonic detection
    if new_fundamentals_by_time:
        all_new_funds = []
        for funds in new_fundamentals_by_time.values():
            all_new_funds.extend(funds)

        # Count fundamentals by number of harmonics
        harmonic_counts = Counter([f['num_harmonics'] for f in all_new_funds])
        print(f"\nHarmonic series distribution:")
        for num_harmonics in sorted(harmonic_counts.keys()):
            count = harmonic_counts[num_harmonics]
            print(f"  {num_harmonics} harmonics: {count} fundamentals")

        # Show average decay scores
        with_harmonics = [f for f in all_new_funds if f['num_harmonics'] > 0]
        if with_harmonics:
            avg_decay_score = sum(f['decay_score'] for f in with_harmonics) / len(with_harmonics)
            avg_confidence = sum(f['confidence'] for f in with_harmonics) / len(with_harmonics)
            print(f"\nAverage decay score (R²): {avg_decay_score:.3f}")
            print(f"Average confidence: {avg_confidence:.3f}")

    print("\n" + "-" * 80)
    print("COMPARISON")
    print("-" * 80)

    reduction = (len(original_filtered) - len(new_filtered)) / max(1, len(original_filtered)) * 100
    print(f"Original fundamentals: {len(original_filtered)}")
    print(f"New fundamentals:      {len(new_filtered)}")
    print(f"Reduction:             {reduction:.1f}%")

    # Pitch overlap
    original_set = set(original_pitches)
    new_set = set(new_pitches)
    overlap = original_set & new_set
    only_original = original_set - new_set
    only_new = new_set - original_set

    print(f"\nPitch overlap: {len(overlap)} / {len(original_set)} = {len(overlap)/max(1,len(original_set))*100:.1f}%")

    if only_original:
        print(f"\nPitches removed by new analyzer ({len(only_original)}):")
        for pitch in sorted(only_original):
            print(f"  {pitch}: {original_counts[pitch]} occurrences")

    if only_new:
        print(f"\nPitches added by new analyzer ({len(only_new)}):")
        for pitch in sorted(only_new):
            print(f"  {pitch}: {new_counts[pitch]} occurrences")

    print("\n" + "=" * 80)

    return {
        'original_count': len(original_filtered),
        'new_count': len(new_filtered),
        'reduction': reduction
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_harmonic_series.py <wav_file>")
        print("\nExample:")
        print("  python test_harmonic_series.py test_amazing_grace.wav")
        sys.exit(1)

    wav_file = sys.argv[1]
    test_harmonic_series(wav_file)
