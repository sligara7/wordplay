#!/usr/bin/env python3
"""
Debug script to investigate onset detection issues
"""

from scipy.io import wavfile
from spectral_analyzer import SpectralAnalyzer
from audio_graph_builder import AudioGraphBuilder
from harmonic_analyzer import HarmonicAnalyzer
from onset_detector import OnsetDetector

# Load audio
wav_path = 'wav_file/andy_song_2.wav'
print(f"Loading {wav_path}...")
sample_rate, audio_data = wavfile.read(wav_path)

# Extract left channel
if len(audio_data.shape) > 1:
    audio_data = audio_data[:, 0]

print(f"Audio: {len(audio_data)} samples at {sample_rate} Hz")

# Spectral analysis
print("\n1. Spectral Analysis...")
analyzer = SpectralAnalyzer(
    samplefreq=sample_rate,
    cycles=4,
    standard_A4=440.0,
    note_begin=21,
    note_end=108,
    increments=1
)
spectral_data = analyzer.dotop(audio_data)
print(f"   Spectral data shape: {spectral_data.shape}")

# Build graph
print("\n2. Building Graph...")
graph_builder = AudioGraphBuilder(
    spectral_data=spectral_data,
    frequencies=analyzer.frequencies,
    sample_rate=sample_rate,
    window_length=analyzer.window_length,
    intensity_threshold=0.01
)
graph = graph_builder.build_graph()
print(f"   Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

# Harmonic analysis
print("\n3. Harmonic Analysis...")
harmonic_analyzer = HarmonicAnalyzer(graph)
fundamentals_by_time = harmonic_analyzer.analyze_all_time_samples()
filtered_fundamentals = harmonic_analyzer.filter_noise(
    min_confidence=0.1,
    min_duration_samples=2
)
print(f"   Detected {len(filtered_fundamentals)} fundamentals")

# Show first few fundamentals
if filtered_fundamentals:
    print("\n   First 5 fundamentals:")
    for i, fund in enumerate(filtered_fundamentals[:5]):
        print(f"   {i}: {fund}")
else:
    print("   WARNING: No fundamentals detected!")
    exit(1)

# Onset detection
print("\n4. Onset Detection...")
onset_detector = OnsetDetector(
    graph=graph,
    onset_threshold=0.001,
    min_onset_gap_seconds=0.05
)

# Debug: Check if fundamentals have required fields
print("\n   Checking fundamental structure:")
fund = filtered_fundamentals[0]
print(f"   Keys: {fund.keys()}")
print(f"   Has 'node_id': {'node_id' in fund}")
print(f"   Has 'frequency': {'frequency' in fund}")

# Try to get freq_idx from node
if 'node_id' in fund:
    node_id = fund['node_id']
    if node_id in graph.nodes:
        node_data = graph.nodes[node_id]
        print(f"   Node data keys: {node_data.keys()}")
        print(f"   freq_idx: {node_data.get('freq_idx')}")
        print(f"   time_idx: {node_data.get('time_idx')}")
        print(f"   intensity: {node_data.get('intensity')}")
    else:
        print(f"   ERROR: node_id '{node_id}' not in graph!")
else:
    print(f"   ERROR: fundamental missing 'node_id'!")

# Try onset detection
note_events = onset_detector.detect_onsets(filtered_fundamentals)
print(f"\n   Detected {len(note_events)} note events")

if note_events:
    print("\n   First 5 note events:")
    for i, event in enumerate(note_events[:5]):
        print(f"   {i}: {event}")
else:
    print("\n   WARNING: No note events detected!")

    # Debug further - check derivatives for first fundamental
    print("\n   Debugging first fundamental:")
    fund = filtered_fundamentals[0]
    node_id = fund['node_id']
    freq_idx = graph.nodes[node_id].get('freq_idx')

    if freq_idx is not None:
        derivatives = onset_detector.calculate_intensity_derivatives(freq_idx)
        print(f"   Freq_idx {freq_idx} has {len(derivatives)} derivatives")
        if derivatives:
            print(f"   First 5 derivatives: {derivatives[:5]}")
            max_deriv = max(derivatives, key=lambda x: x[1])
            print(f"   Max derivative: {max_deriv[1]:.6f} at time_idx {max_deriv[0]}")
            print(f"   Onset threshold: {onset_detector.onset_threshold}")
        else:
            print(f"   ERROR: No derivatives calculated!")
