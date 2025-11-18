#!/usr/bin/env python3
"""Debug autocorrelation fundamental detection."""

import numpy as np
from scipy.io import wavfile
from spectral_analyzer import SpectralAnalyzer
from autocorrelation_analyzer import AutocorrelationAnalyzer

def debug_autocorrelation(wav_path: str):
    """Debug autocorrelation detection on a WAV file."""

    # Load audio
    sample_rate, audio_data = wavfile.read(wav_path)

    # Extract left channel if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    print(f"Audio: {len(audio_data)} samples at {sample_rate} Hz")
    print(f"Duration: {len(audio_data) / sample_rate:.2f} seconds\n")

    # Spectral analysis
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=3,
        standard_A4=440.0,
        note_begin=21,  # A0
        note_end=108,   # C8
        increments=12
    )

    spectral_data = analyzer.dotop(audio_data)
    print(f"Spectral data: {spectral_data.shape}")
    print(f"Frequency range: {analyzer.frequencies[0]:.2f} - {analyzer.frequencies[-1]:.2f} Hz")
    print(f"Frequency resolution: {(analyzer.frequencies[-1] - analyzer.frequencies[0]) / len(analyzer.frequencies):.4f} Hz/bin\n")

    # Test different autocorrelation parameters
    test_configs = [
        {"min_autocorr_peak": 0.3, "min_freq": 80.0, "max_freq": 1000.0, "intensity": 0.02},
        {"min_autocorr_peak": 0.2, "min_freq": 80.0, "max_freq": 1000.0, "intensity": 0.02},
        {"min_autocorr_peak": 0.1, "min_freq": 80.0, "max_freq": 1000.0, "intensity": 0.01},
        {"min_autocorr_peak": 0.1, "min_freq": 50.0, "max_freq": 2000.0, "intensity": 0.01},
    ]

    for i, config in enumerate(test_configs):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: min_peak={config['min_autocorr_peak']}, "
              f"freq={config['min_freq']:.0f}-{config['max_freq']:.0f}Hz, "
              f"intensity={config['intensity']}")
        print(f"{'='*60}")

        autocorr_analyzer = AutocorrelationAnalyzer(
            spectral_data=spectral_data,
            frequencies=analyzer.frequencies,
            sample_rate=sample_rate,
            window_length=analyzer.window_length,
            min_autocorr_peak=config['min_autocorr_peak'],
            min_frequency=config['min_freq'],
            max_frequency=config['max_freq']
        )

        note_events = autocorr_analyzer.analyze_all_times(
            intensity_threshold=config['intensity'],
            min_duration_samples=2
        )

        if note_events:
            print(f"\nDetected {len(note_events)} notes:")
            # Show first 10 notes
            for j, note in enumerate(note_events[:10]):
                midi_note = note['midi_note']
                freq = note['frequency']
                duration = note['duration_seconds']
                conf = note['confidence']
                print(f"  {j+1}. MIDI {midi_note:3d} ({freq:7.2f} Hz) - "
                      f"duration={duration:.3f}s, confidence={conf:.3f}")

            if len(note_events) > 10:
                print(f"  ... and {len(note_events) - 10} more")

            # Show frequency distribution
            freqs = [n['frequency'] for n in note_events]
            print(f"\nFrequency range: {min(freqs):.2f} - {max(freqs):.2f} Hz")
            print(f"Median frequency: {np.median(freqs):.2f} Hz")
        else:
            print("  No notes detected!")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python debug_autocorrelation.py <wav_file>")
        sys.exit(1)

    debug_autocorrelation(sys.argv[1])
