# Audio-to-MIDI Transcription Using Graph Theory

## Overview

This document describes a novel graph-based approach to transcribing audio recordings (WAV files) into MIDI/sheet music. Unlike traditional signal processing methods, this approach treats frequency-time-intensity data as a **network of relationships** that can be analyzed using graph theory to separate root notes from harmonics, detect note onsets, and apply music theory constraints.

---

## The Problem

### Challenge: Multi-Dimensional Complexity

When analyzing musical audio with a Fourier-like transform, we obtain a 2D array:
- **Y-axis (Frequency)**: Notes and sub-notes (e.g., 75.0, 75.25, 75.5, 75.75, 76.0)
  - Typically 82 notes across ~8 octaves
  - Sub-note divisions (e.g., quarter-note increments) for precision
  - Frequencies increase exponentially
- **X-axis (Time)**: Discrete samples
  - Sample rate typically based on multiples of 1/27.5 Hz (A0 = 27.5 Hz)
  - Example: 5 cycles of 27.5 Hz ≈ 182ms per sample
- **Cell Value (Intensity)**: Energy at each frequency-time point

### What Makes Transcription Difficult

1. **Harmonics**: Each instrument produces overtones (2f, 3f, 4f, 5f...) with unique signatures
   - Example: A piano playing A440 also produces energy at 880Hz, 1320Hz, 1760Hz...
   - Different instruments have different harmonic profiles

2. **Multiple Simultaneous Instruments**:
   - Melody, harmony, bass, percussion all playing at once
   - Percussion lacks clear harmonic structure
   - Spectral overlap makes separation challenging

3. **Chords**: Multiple notes played simultaneously
   - Each note has its own harmonic series
   - Harmonic series can interfere or reinforce

4. **Sustain vs. Onset**:
   - Notes may maintain intensity across samples (sustain)
   - Notes may decay exponentially
   - Different instruments have different ADSR (Attack, Decay, Sustain, Release) envelopes
   - Need to detect when a note actually **starts** vs. when it's being held

5. **Music Theory Constraints**:
   - Not all note combinations are equally likely
   - Songs follow key signatures, scales, chord progressions
   - Temporal patterns (rhythm, meter) provide structure

---

## The Graph-Based Solution

### Core Concept

**Treat each frequency-time-intensity point as a node in a multi-layered network**, then use graph analysis to:
1. Identify communities of harmonically-related frequencies → **fundamental frequency detection**
2. Analyze temporal flow patterns → **onset vs. sustain detection**
3. Apply music theory as edge weights → **constrain to musical patterns**
4. Use centrality measures → **identify important notes**
5. Detect structural patterns → **separate instruments**

### Graph Structure

#### Nodes
Each node represents:
```python
Node = {
    'id': f'f{frequency_index}_t{time_index}',
    'frequency': 440.0,  # Hz
    'note': 'A4',        # Note name
    'time_sample': 42,    # Sample index
    'time_seconds': 1.234,  # Absolute time
    'intensity': 0.75,   # Normalized intensity [0, 1]
    'octave': 4,
    'sub_note': 0.0      # 0.0, 0.25, 0.5, 0.75
}
```

#### Edge Types

**1. Temporal Edges** (Same frequency, adjacent time samples)
```python
TemporalEdge = {
    'source': 'f440_t42',
    'target': 'f440_t43',
    'type': 'temporal',
    'weight': intensity_correlation,  # How similar are intensities?
    'delta_intensity': 0.05,          # Change in intensity
    'flow': 0.75                      # Intensity "flowing" through time
}
```

**2. Harmonic Edges** (Harmonically-related frequencies, same time)
```python
HarmonicEdge = {
    'source': 'f220_t42',    # A3
    'target': 'f440_t42',    # A4 (2x harmonic)
    'type': 'harmonic',
    'harmonic_ratio': 2.0,   # f_target / f_source
    'weight': intensity_product,  # Both present?
    'is_octave': True
}
```

**3. Music Theory Edges** (Notes in same scale/chord, same time)
```python
MusicTheoryEdge = {
    'source': 'f261_t42',    # C4
    'target': 'f329_t42',    # E4
    'type': 'music_theory',
    'relation': 'major_third',
    'weight': scale_membership,  # Both in C major scale?
    'chord_function': 'I'         # Tonic chord
}
```

**4. Cross-Layer Edges** (Different layers for different instruments)
```python
CrossLayerEdge = {
    'source': 'melody_f440_t42',
    'target': 'harmony_f261_t42',
    'type': 'cross_layer',
    'weight': spectral_separation,  # How separable are the instruments?
}
```

---

## Graph Analysis Methods

### 1. Harmonic Filtering via Community Detection

**Goal**: Separate fundamental frequencies from their harmonics

**Method**:
1. Create a harmonic subgraph for each time sample
   - Nodes: All frequencies with intensity > threshold
   - Edges: Connect frequencies related by harmonic ratios (1:2, 2:3, 3:4, 3:5, etc.)
   - Edge weights: Product of intensities (both harmonics must be strong)

2. Apply community detection algorithms:
   ```python
   # Louvain method for modularity optimization
   communities = nx.community.louvain_communities(harmonic_graph, weight='weight')

   # Label propagation for fast clustering
   communities = nx.community.label_propagation_communities(harmonic_graph)
   ```

3. Identify fundamentals within each community:
   - The **lowest frequency** in each community is likely the fundamental
   - Use **degree centrality** to confirm (fundamentals have many harmonic connections)
   - Use **PageRank** to find most "important" frequency (harmonics point to it)

**Expected Outcome**:
- Piano playing A440 → Community: {220Hz, 440Hz, 660Hz, 880Hz, 1100Hz, 1320Hz...}
- Fundamental identified: 220Hz (A3) if strong, or 440Hz (A4) if A3 is weak/missing

**Refinements**:
- **Harmonic templates**: Different instruments have characteristic harmonic profiles
  - Piano: Strong odd and even harmonics (2f, 3f, 4f, 5f...)
  - Clarinet: Strong odd harmonics (3f, 5f, 7f...)
  - Strings: All harmonics with 1/n² decay
- Use **template matching** to weight edges based on instrument probability

---

### 2. Onset Detection via Temporal Flow Analysis

**Goal**: Distinguish note onsets (attacks) from sustained/decaying notes

**Method**:

#### A. Intensity Derivative
```python
# For each frequency across time
for freq in frequencies:
    temporal_sequence = [intensity(freq, t) for t in time_samples]
    derivatives = np.diff(temporal_sequence)

    # Sudden increase = onset
    onsets = [t for t, d in enumerate(derivatives) if d > onset_threshold]
```

#### B. Graph-Based Flow Detection
1. Model intensity as **flow** through temporal edges
2. Calculate **flow derivatives** at each node:
   ```python
   flow_in = sum(edge['flow'] for edge in in_edges)
   flow_out = sum(edge['flow'] for edge in out_edges)
   flow_delta = flow_out - flow_in

   # Negative delta = onset (flow increasing)
   # Near-zero delta = sustain
   # Positive delta = release (flow decreasing)
   ```

3. Use **betweenness centrality** on temporal paths:
   - High betweenness = transition point (onset or release)
   - Low betweenness = sustained note

#### C. Spectral Flux
```python
# Compare spectral content between consecutive time samples
spectral_flux[t] = sum(|intensity(f, t) - intensity(f, t-1)| for f in frequencies)

# High flux = something changed (onset/offset)
# Low flux = stable (sustain)
```

#### D. Multi-Frequency Consensus
- A true onset should show simultaneous intensity increases across all harmonics
- Create **harmonic community** first (from step 1)
- Check if all members show onset at same time
- This filters out noise (random intensity fluctuations in single frequencies)

**Expected Outcome**:
- Piano note: Sharp attack (high flow delta) → exponential decay (gradually positive flow delta)
- Violin note: Gradual attack (moderate flow delta) → sustain (near-zero delta)
- Drum hit: Extremely sharp attack → very fast decay (no clear pitch)

---

### 3. Music Theory Constraints

**Goal**: Use musical structure to filter implausible note combinations

**Method**:

#### A. Key Signature Detection
```python
# Analyze all fundamentals across time
note_histogram = Counter(detected_notes)

# Find key that maximizes scale membership
for key in all_keys:  # C major, G major, A minor, etc.
    scale_notes = get_scale_notes(key)
    score = sum(note_histogram[note] for note in scale_notes)

# Most likely key = highest score
```

#### B. Scale/Chord Edge Weighting
```python
# Add edges between notes in the same scale (at same time sample)
for t in time_samples:
    active_notes = get_active_notes(t)
    for n1, n2 in combinations(active_notes, 2):
        if in_same_scale(n1, n2, detected_key):
            graph.add_edge(n1, n2, weight=scale_bonus, type='scale')
        if forms_chord(n1, n2, ...):  # Check all active notes
            graph.add_edge(n1, n2, weight=chord_bonus, type='chord')
```

#### C. Chord Progression Constraints
```python
# Common progressions: I-IV-V-I, I-V-vi-IV, ii-V-I, etc.
progression_graph = nx.DiGraph()
progression_graph.add_edges_from([
    ('I', 'IV'), ('I', 'V'), ('I', 'vi'),
    ('IV', 'I'), ('IV', 'V'), ('IV', 'ii'),
    ('V', 'I'), ('V', 'vi'),
    # ... etc
])

# Use shortest path in progression graph to validate chord sequences
detected_chords = [identify_chord(notes, t) for t in time_samples]
if nx.has_path(progression_graph, chord[t], chord[t+1]):
    # Valid progression, boost confidence
    boost_edge_weights(time=t)
```

#### D. Voice Leading Analysis
```python
# Smooth voice leading = small note-to-note intervals
for voice in separated_voices:  # After instrument separation
    intervals = [abs(note[t+1] - note[t]) for t in range(len(voice)-1)]

    # Penalize large leaps (unlikely in melody)
    if max(intervals) > 12:  # Octave jump
        reduce_confidence(voice)

    # Prefer stepwise motion (2 semitones or less)
    smoothness_score = sum(1 for i in intervals if i <= 2) / len(intervals)
```

**Expected Outcome**:
- Ambiguous frequencies → Resolved by scale membership
- Random noise → Filtered out (doesn't fit chord progressions)
- Enhanced transcription accuracy through musical plausibility

---

### 4. Instrument Separation via Structural Analysis

**Goal**: Separate multiple simultaneous instruments into distinct voices

**Method**:

#### A. Spectral Range Clustering
```python
# Different instruments occupy different frequency ranges
frequency_ranges = {
    'bass': (40, 250),      # E1 to B3
    'harmony': (200, 1000), # G3 to C6
    'melody': (500, 2000),  # C5 to C7
    'percussion': None      # Wide spectrum, no clear pitch
}

# Assign nodes to layers based on frequency
for node in graph.nodes():
    for instrument, (f_min, f_max) in frequency_ranges.items():
        if f_min <= node['frequency'] <= f_max:
            node['layer'] = instrument
```

#### B. Structural Holes (Betweenness Centrality)
```python
# Nodes with high betweenness connect distinct communities
betweenness = nx.betweenness_centrality(graph, weight='weight')

# High betweenness nodes bridge instruments
# Example: Middle C (C4) might bridge bass and melody
boundary_nodes = [n for n, b in betweenness.items() if b > threshold]
```

#### C. Timbre-Based Edge Weights
```python
# Different instruments have different harmonic signatures
def timbre_similarity(node1, node2):
    """Compare harmonic profiles"""
    harmonics1 = get_harmonic_community(node1)
    harmonics2 = get_harmonic_community(node2)

    # Instruments with similar harmonic ratios have similar timbre
    return compare_harmonic_profiles(harmonics1, harmonics2)

# Cluster nodes with similar timbre
timbre_communities = nx.community.louvain_communities(
    graph,
    weight=timbre_similarity
)
```

#### D. Temporal Correlation
```python
# Notes from same instrument tend to move together
for freq1, freq2 in combinations(frequencies, 2):
    temporal_profile1 = [intensity(freq1, t) for t in time_samples]
    temporal_profile2 = [intensity(freq2, t) for t in time_samples]

    correlation = np.corrcoef(temporal_profile1, temporal_profile2)[0, 1]

    # High correlation = likely same instrument
    if correlation > threshold:
        graph.add_edge(freq1, freq2, weight=correlation, type='correlation')
```

**Expected Outcome**:
- Bass line separated from melody
- Chords (harmony) identified as distinct from melody
- Percussion filtered out or analyzed separately

---

### 5. Noise Filtering via Graph Properties

**Goal**: Distinguish musical signal from noise

**Method**:

#### A. Orphaned Nodes
```python
# From system_of_systems_graph_v2.py: Detect orphaned interfaces
orphaned = [n for n in graph.nodes() if graph.degree(n) == 0]

# Nodes with no harmonic, temporal, or music theory connections = noise
# Remove these nodes
graph.remove_nodes_from(orphaned)
```

#### B. Weakly Connected Components
```python
# True notes should be connected through harmonics OR time OR music theory
components = list(nx.weakly_connected_components(graph))

# Small components (size < threshold) are likely noise
noise_components = [c for c in components if len(c) < min_component_size]
for component in noise_components:
    graph.remove_nodes_from(component)
```

#### C. Intensity Thresholding
```python
# Remove nodes below intensity threshold
min_intensity = np.percentile([node['intensity'] for node in graph.nodes()], 5)
weak_nodes = [n for n in graph.nodes() if n['intensity'] < min_intensity]
graph.remove_nodes_from(weak_nodes)
```

#### D. Temporal Consistency
```python
# Musical notes should persist for minimum duration
for freq in frequencies:
    temporal_sequence = get_temporal_nodes(freq)

    # If note appears for only 1 sample, likely noise
    if len(temporal_sequence) < min_duration_samples:
        graph.remove_nodes_from(temporal_sequence)
```

---

## System Integration with Reflow Tools

The `system_of_systems_graph_v2.py` tool provides several applicable methods:

### 1. Gap Detection → Orphaned Harmonics
- **Orphaned Interfaces**: Harmonics that are "consumed" (expected) but not "provided" (detected)
  - Example: Fundamental at 220Hz detected, but missing 2nd harmonic at 440Hz
  - May indicate weak harmonic or need for interpolation

### 2. Community Detection → Instrument/Harmonic Separation
- **Louvain Algorithm**: Already implemented in system_of_systems_graph
- Apply to harmonic subgraph, temporal subgraph, music theory subgraph

### 3. Centrality Measures → Fundamental Identification
- **PageRank**: Harmonics "vote" for their fundamental
- **Betweenness**: Identify bridging notes (modulations, key changes)
- **Degree Centrality**: Fundamentals have high degree (many harmonics)

### 4. Path Analysis → Voice Leading
- **Shortest Paths**: Find smoothest melodic paths through note graph
- **Diameter**: Measure melodic range

### 5. Cycle Detection → Repeated Patterns
- **Simple Cycles**: Detect melodic motifs that repeat
- **Feedback Loops**: Chord progressions that return to tonic

### 6. Flow Analysis → Onset Detection
- **Maximum Flow**: Model intensity as flow through time
- **Minimum Cuts**: Identify temporal boundaries (phrase boundaries)

### 7. DAG Analysis → Temporal Ordering
- **Topological Sorting**: Order notes chronologically
- **Longest Paths**: Identify sustained notes

---

## Output: MIDI File Generation

Once root notes and timings are identified, generate MIDI:

```python
import mido

# Create MIDI file
mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)

# Add tempo
track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120)))

# For each detected note onset
for note_event in detected_notes:
    # Note on
    track.append(mido.Message('note_on',
        note=note_event['midi_note'],  # 0-127
        velocity=int(note_event['intensity'] * 127),
        time=time_to_ticks(note_event['onset_time'])
    ))

    # Note off
    track.append(mido.Message('note_off',
        note=note_event['midi_note'],
        velocity=0,
        time=time_to_ticks(note_event['duration'])
    ))

# Save
mid.save('transcription.mid')
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT: Audio File (.wav)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Specialized Fourier Transform                               │
│    • Divide octaves into sub-notes (0.25 increments)           │
│    • Sample every ~182ms (5 cycles of 27.5 Hz)                 │
│    • Output: 2D array [frequency, time] = intensity            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BUILD GRAPH                                                  │
│    • Nodes: (frequency, time, intensity)                       │
│    • Temporal edges: Same freq, adjacent time                  │
│    • Harmonic edges: Related freqs (2f, 3f, etc.)              │
│    • Music theory edges: Scale/chord relationships             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. HARMONIC FILTERING (Community Detection)                    │
│    • Cluster harmonically-related frequencies                  │
│    • Identify fundamental (lowest freq in community)           │
│    • Use PageRank/degree centrality to confirm                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. ONSET DETECTION (Temporal Flow Analysis)                    │
│    • Calculate intensity derivatives                           │
│    • Model as flow through temporal edges                      │
│    • High betweenness = onset/release points                   │
│    • Verify across harmonic community (consensus)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. MUSIC THEORY FILTERING                                      │
│    • Detect key signature (scale membership)                   │
│    • Validate chord progressions                               │
│    • Analyze voice leading (smooth melodic lines)              │
│    • Boost plausible notes, filter implausible                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. INSTRUMENT SEPARATION (Structural Analysis)                 │
│    • Cluster by spectral range (bass/harmony/melody)           │
│    • Use structural holes to identify boundaries               │
│    • Timbre similarity for same-instrument grouping            │
│    • Temporal correlation for voice tracking                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. NOISE FILTERING                                             │
│    • Remove orphaned nodes (no connections)                    │
│    • Filter weak components                                    │
│    • Intensity thresholding                                    │
│    • Temporal consistency checks                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. OUTPUT: MIDI File / Sheet Music                             │
│    • Root notes identified                                     │
│    • Onset times detected                                      │
│    • Velocities (intensities) mapped                           │
│    • Multiple tracks (if instruments separated)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Advantages of Graph-Based Approach

### Over Traditional Signal Processing:

1. **Holistic Analysis**: Considers harmonic, temporal, and musical relationships simultaneously
   - Traditional: Processes each frequency independently
   - Graph: Leverages connections between frequencies

2. **Music Theory Integration**: Natural representation of scales, chords, progressions
   - Traditional: Hard to encode musical rules in Fourier/wavelet domains
   - Graph: Music theory becomes edge weights and path constraints

3. **Robust to Noise**: Graph structure provides redundancy
   - Traditional: Single-point noise can corrupt estimates
   - Graph: Community consensus filters noise

4. **Interpretable**: Graph structure is human-readable
   - Traditional: Spectrograms require expert interpretation
   - Graph: Can visualize note relationships directly

5. **Extensible**: Easy to add new constraints or analysis methods
   - Traditional: Requires redesigning signal processing pipeline
   - Graph: Add new edge types or analysis algorithms

### Compared to Machine Learning:

1. **Explainable**: Graph analysis provides reasoning for decisions
   - ML: "Black box" neural networks
   - Graph: "Note A is fundamental because it has harmonics at 2A, 3A, 4A"

2. **No Training Data Required**: Music theory provides constraints
   - ML: Requires large labeled datasets
   - Graph: Uses universal music theory rules

3. **Generalizable**: Works across different musical styles
   - ML: May overfit to training genre
   - Graph: Music theory is style-agnostic

4. **Computationally Efficient**: Graph algorithms are well-optimized
   - ML: Deep networks require GPUs
   - Graph: NetworkX runs on CPU

---

## Future Enhancements

### 1. Multi-Layer Graphs
- Separate layers for each instrument
- Cross-layer edges for synchronization
- Enables independent analysis of each voice

### 2. Temporal Hierarchies
- Micro-level: Note onsets (milliseconds)
- Meso-level: Phrases and motifs (seconds)
- Macro-level: Sections and form (minutes)
- Multi-scale graph analysis

### 3. Probabilistic Graphs
- Edge weights as probabilities
- Bayesian inference for fundamental detection
- Uncertainty quantification in transcription

### 4. Real-Time Processing
- Streaming graph construction
- Incremental analysis as audio plays
- Low-latency transcription

### 5. Genre-Specific Models
- Different harmonic templates for jazz vs. classical vs. rock
- Style-specific chord progressions
- Adapt graph structure to musical context

### 6. Integration with Existing wordplay Features
- Combine audio transcription with MIDI analysis
- Compare transcribed MIDI to original score
- Analyze how performances differ from written music
- Cross-domain analysis: Audio → MIDI → Text (lyrics)

---

## Implementation Notes

### Data Structures

```python
# Input: 2D array from specialized Fourier transform
frequency_time_matrix = np.array([
    # frequency_index, time_index → intensity
    [0.1, 0.3, 0.8, 0.7, 0.5, ...],  # frequency 0
    [0.0, 0.0, 0.2, 0.3, 0.1, ...],  # frequency 1
    # ... (82 frequencies × N time samples)
])

# Graph representation
import networkx as nx

G = nx.MultiDiGraph()  # Directed, allows multiple edge types

# Add nodes
for f_idx in range(num_frequencies):
    for t_idx in range(num_time_samples):
        G.add_node(
            f'f{f_idx}_t{t_idx}',
            frequency=index_to_frequency(f_idx),
            time=index_to_time(t_idx),
            intensity=frequency_time_matrix[f_idx, t_idx],
            # ... other attributes
        )

# Add edges (temporal, harmonic, music theory)
# ... (see detailed methods above)
```

### Performance Considerations

- **Graph Size**: 82 frequencies × 1000 time samples = 82,000 nodes
  - May need sparse representations for long audio files
  - Consider sliding window approach (analyze 10-second chunks)

- **Edge Density**:
  - Temporal edges: O(num_frequencies × num_time_samples)
  - Harmonic edges: O(num_frequencies² × num_time_samples) - **expensive**
  - Optimization: Only connect harmonics with intensity > threshold

- **Analysis Complexity**:
  - Community detection: O(E log N) for Louvain
  - Betweenness centrality: O(NE) - **expensive for large graphs**
  - Optimization: Compute on subgraphs (per time sample or frequency range)

### Integration with Wordplay

This module will follow the established wordplay pattern:

```
audio_file.wav
    → AudioGraphAnalyzer.from_wav()
    → builds graph with harmonics/temporal/music_theory edges
    → analyze_graph() applies NetworkX algorithms
    → filter_fundamentals() identifies root notes
    → detect_onsets() finds note start times
    → generate_midi() creates output
    → transcription.mid
```

Compatible with existing tools:
- `midi_graph_builder.py` can analyze the generated MIDI
- `batch_graph_merger.py` can compare multiple transcriptions
- `polyphonic_midi_analyzer.py` can validate multi-instrument separation

---

## References

### Music Information Retrieval
- Klapuri, A. "Multiple Fundamental Frequency Estimation by Summing Harmonic Amplitudes"
- Benetos, E. "Automatic Music Transcription: Challenges and Future Directions"
- Salamon, J. "Melody Extraction from Polyphonic Music Signals"

### Graph Theory Applications
- Newman, M.E.J. "Networks: An Introduction" (Community detection)
- Brandes, U. "A Faster Algorithm for Betweenness Centrality" (Flow analysis)
- Blondel, V. "Fast Unfolding of Communities" (Louvain method)

### Music Theory
- Aldwell, E. "Harmony & Voice Leading" (Chord progressions, voice leading)
- Kostka, S. "Tonal Harmony" (Functional harmony, scales)
- Caplin, W. "Classical Form" (Musical structure)

### Existing Wordplay Documentation
- `MIDI_SUPPORT.md`: MIDI file handling
- `POLYPHONIC_MUSIC.md`: Multi-instrument analysis
- `TEMPORAL_ANALYSIS.md`: Rhythm and timing

---

## Contact & Contributions

This approach is experimental and welcomes collaboration. Key areas for development:

1. **Fourier Transform Integration**: Connect specialized transform output to graph builder
2. **Validation**: Compare against ground-truth MIDI transcriptions
3. **Optimization**: Performance tuning for real-time processing
4. **Expansion**: Genre-specific models, additional instruments

---

**Status**: Design phase - awaiting specialized Fourier transform implementation
**Next Steps**: Create skeleton `audio_graph_analyzer.py` with placeholder for transform input
