#!/usr/bin/env python3
"""
Audio-to-MIDI Transcription Using Graph Theory

This module implements a novel graph-based approach to transcribing audio files (.wav)
into MIDI/sheet music by treating frequency-time-intensity data as a network.

Key Concepts:
- Nodes: (frequency, time, intensity) points from specialized Fourier transform
- Edges: Harmonic relationships, temporal flow, music theory constraints
- Analysis: Community detection, centrality measures, flow analysis

Architecture:
    Input: 2D array [frequency_index, time_index] = intensity
        ↓
    Build Graph: Add nodes and edges (harmonic, temporal, music theory)
        ↓
    Analyze: Apply NetworkX algorithms
        ↓
    Filter: Separate fundamentals from harmonics, detect onsets
        ↓
    Output: MIDI file with transcribed notes

See AUDIO_TRANSCRIPTION.md for detailed methodology.
"""

import json
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import mido
import networkx as nx
import numpy as np

# Music theory constants
A0_FREQUENCY = 27.5  # Lowest A note (MIDI note 21)
SEMITONES_PER_OCTAVE = 12
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Harmonic ratios for common overtones
HARMONIC_RATIOS = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]

# Common chord intervals (semitones)
CHORD_INTERVALS = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'diminished': [0, 3, 6],
    'augmented': [0, 4, 8],
    'major7': [0, 4, 7, 11],
    'minor7': [0, 3, 7, 10],
    'dominant7': [0, 4, 7, 10],
}

# Scale degrees (semitones from root)
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor_natural': [0, 2, 3, 5, 7, 8, 10],
    'minor_harmonic': [0, 2, 3, 5, 7, 8, 11],
    'minor_melodic': [0, 2, 3, 5, 7, 9, 11],
    'chromatic': list(range(12)),
}

# Common chord progressions (Nashville notation: I, ii, iii, IV, V, vi, vii°)
COMMON_PROGRESSIONS = [
    ['I', 'IV', 'V', 'I'],      # Basic progression
    ['I', 'V', 'vi', 'IV'],     # Pop progression
    ['ii', 'V', 'I'],           # Jazz turnaround
    ['I', 'vi', 'IV', 'V'],     # 50s progression
    ['I', 'IV', 'I', 'V'],      # Blues progression
]


@dataclass
class AudioNode:
    """Represents a frequency-time-intensity point in the graph."""
    frequency_index: int      # Index in the frequency array
    time_index: int          # Index in the time array
    frequency_hz: float      # Actual frequency in Hz
    time_seconds: float      # Actual time in seconds
    intensity: float         # Normalized intensity [0, 1]
    note_name: str          # E.g., "A4"
    midi_note: int          # MIDI note number (0-127)
    octave: int             # Octave number
    sub_note: float         # Sub-note increment (0.0, 0.25, 0.5, 0.75)

    def __hash__(self):
        return hash((self.frequency_index, self.time_index))

    @property
    def node_id(self) -> str:
        """Unique identifier for this node."""
        return f"f{self.frequency_index}_t{self.time_index}"


@dataclass
class TranscriptionResult:
    """Results from audio transcription."""
    notes: List[Dict]           # Detected notes with timing and velocity
    graph: nx.MultiDiGraph      # Full analysis graph
    fundamentals: Set[str]      # Node IDs identified as fundamental frequencies
    harmonics: Set[str]         # Node IDs identified as harmonics
    onsets: Dict[str, float]    # Node ID → onset time (seconds)
    key_signature: str          # Detected key (e.g., "C_major")
    tempo_bpm: float           # Detected tempo
    metadata: Dict             # Additional analysis metadata


class AudioGraphAnalyzer:
    """
    Graph-based audio-to-MIDI transcription engine.

    This class builds a multi-layer graph from frequency-time-intensity data
    and applies graph theory algorithms to extract musical structure.

    Usage:
        analyzer = AudioGraphAnalyzer(
            frequency_time_matrix=fft_output,
            sample_rate_hz=22050,
            frequencies=frequency_array
        )
        result = analyzer.analyze()
        analyzer.export_midi("output.mid", result)
    """

    def __init__(
        self,
        frequency_time_matrix: np.ndarray,
        sample_rate_hz: float,
        frequencies: np.ndarray,
        time_samples: Optional[np.ndarray] = None,
        intensity_threshold: float = 0.1,
        onset_threshold: float = 0.2,
        harmonic_tolerance: float = 0.02,
    ):
        """
        Initialize the audio graph analyzer.

        Args:
            frequency_time_matrix: 2D array [frequency_idx, time_idx] = intensity
                Shape: (num_frequencies, num_time_samples)
            sample_rate_hz: Sample rate of the audio file (e.g., 44100)
            frequencies: Array of frequency values (Hz) for each frequency index
                Shape: (num_frequencies,)
            time_samples: Array of time values (seconds) for each time index
                If None, computed from sample_rate_hz
            intensity_threshold: Minimum intensity to consider (filter noise)
            onset_threshold: Minimum intensity change to detect onset
            harmonic_tolerance: Tolerance for harmonic ratio matching (e.g., 0.02 = 2%)
        """
        self.frequency_time_matrix = frequency_time_matrix
        self.sample_rate_hz = sample_rate_hz
        self.frequencies = frequencies
        self.intensity_threshold = intensity_threshold
        self.onset_threshold = onset_threshold
        self.harmonic_tolerance = harmonic_tolerance

        # Compute time samples if not provided
        if time_samples is None:
            num_samples = frequency_time_matrix.shape[1]
            self.time_samples = np.arange(num_samples) / sample_rate_hz
        else:
            self.time_samples = time_samples

        # Initialize graph
        self.graph = nx.MultiDiGraph()

        # Analysis results
        self.nodes_by_time: Dict[int, List[AudioNode]] = defaultdict(list)
        self.nodes_by_freq: Dict[int, List[AudioNode]] = defaultdict(list)
        self.harmonic_communities: List[Set[str]] = []
        self.fundamentals: Set[str] = set()
        self.harmonics: Set[str] = set()
        self.onsets: Dict[str, float] = {}
        self.detected_key: Optional[str] = None

    # ========================================================================
    # PHASE 1: GRAPH CONSTRUCTION
    # ========================================================================

    def build_graph(self):
        """
        Build the complete graph from frequency-time-intensity data.

        Steps:
            1. Add nodes for all (frequency, time, intensity) points
            2. Add temporal edges (same frequency, adjacent time)
            3. Add harmonic edges (harmonic ratios, same time)
            4. Add music theory edges (scale/chord relationships, same time)
        """
        print("Building graph from frequency-time-intensity data...")

        self._add_nodes()
        self._add_temporal_edges()
        self._add_harmonic_edges()
        # Music theory edges added after key detection

        print(f"Graph built: {self.graph.number_of_nodes()} nodes, "
              f"{self.graph.number_of_edges()} edges")

    def _add_nodes(self):
        """Add a node for each (frequency, time, intensity) point above threshold."""
        num_frequencies, num_time_samples = self.frequency_time_matrix.shape

        for f_idx in range(num_frequencies):
            for t_idx in range(num_time_samples):
                intensity = self.frequency_time_matrix[f_idx, t_idx]

                # Skip low-intensity points (noise filtering)
                if intensity < self.intensity_threshold:
                    continue

                # Create node
                freq_hz = self.frequencies[f_idx]
                time_sec = self.time_samples[t_idx]
                midi_note = self._frequency_to_midi(freq_hz)
                note_name, octave, sub_note = self._midi_to_note(midi_note)

                node = AudioNode(
                    frequency_index=f_idx,
                    time_index=t_idx,
                    frequency_hz=freq_hz,
                    time_seconds=time_sec,
                    intensity=intensity,
                    note_name=note_name,
                    midi_note=midi_note,
                    octave=octave,
                    sub_note=sub_note,
                )

                # Add to graph
                self.graph.add_node(
                    node.node_id,
                    **{
                        'frequency_index': f_idx,
                        'time_index': t_idx,
                        'frequency_hz': freq_hz,
                        'time_seconds': time_sec,
                        'intensity': intensity,
                        'note_name': note_name,
                        'midi_note': midi_note,
                        'octave': octave,
                        'sub_note': sub_note,
                    }
                )

                # Index for fast lookup
                self.nodes_by_time[t_idx].append(node)
                self.nodes_by_freq[f_idx].append(node)

    def _add_temporal_edges(self):
        """
        Add edges between same frequency at consecutive time samples.

        These edges represent temporal flow (sustain, onset, release).
        Edge weight = intensity correlation.
        """
        for f_idx in range(len(self.frequencies)):
            temporal_sequence = sorted(
                self.nodes_by_freq[f_idx],
                key=lambda n: n.time_index
            )

            for i in range(len(temporal_sequence) - 1):
                node1 = temporal_sequence[i]
                node2 = temporal_sequence[i + 1]

                # Only connect adjacent time samples
                if node2.time_index == node1.time_index + 1:
                    # Intensity correlation (how similar are they?)
                    correlation = min(node1.intensity, node2.intensity) / \
                                  max(node1.intensity, node2.intensity)

                    # Intensity change (positive = increasing, negative = decreasing)
                    delta_intensity = node2.intensity - node1.intensity

                    # Flow (intensity moving through time)
                    flow = (node1.intensity + node2.intensity) / 2.0

                    self.graph.add_edge(
                        node1.node_id,
                        node2.node_id,
                        type='temporal',
                        weight=correlation,
                        delta_intensity=delta_intensity,
                        flow=flow,
                    )

    def _add_harmonic_edges(self):
        """
        Add edges between harmonically-related frequencies at same time.

        Harmonic relationships: f, 2f, 3f, 4f, 5f, ...
        Edge weight = product of intensities (both must be strong).
        """
        for t_idx in range(len(self.time_samples)):
            nodes_at_time = self.nodes_by_time[t_idx]

            # Check all pairs for harmonic relationships
            for node1, node2 in combinations(nodes_at_time, 2):
                # Calculate frequency ratio
                if node1.frequency_hz == 0 or node2.frequency_hz == 0:
                    continue

                ratio = node2.frequency_hz / node1.frequency_hz

                # Check if ratio matches harmonic series (within tolerance)
                for harmonic_ratio in HARMONIC_RATIOS:
                    if abs(ratio - harmonic_ratio) / harmonic_ratio < self.harmonic_tolerance:
                        # Harmonically related!
                        weight = node1.intensity * node2.intensity  # Both must be strong

                        self.graph.add_edge(
                            node1.node_id,
                            node2.node_id,
                            type='harmonic',
                            harmonic_ratio=harmonic_ratio,
                            weight=weight,
                            is_octave=(harmonic_ratio == 2.0),
                        )
                        break

    def _add_music_theory_edges(self):
        """
        Add edges between notes in same scale/chord at same time.

        Requires key detection to run first.
        Edge weight = scale membership bonus.
        """
        if self.detected_key is None:
            warnings.warn("Key not detected yet, skipping music theory edges")
            return

        # Parse key (e.g., "C_major" → root=0, scale=[0,2,4,5,7,9,11])
        key_root, scale_type = self.detected_key.split('_')
        root_semitone = NOTES.index(key_root)
        scale_intervals = SCALES.get(scale_type, SCALES['major'])

        for t_idx in range(len(self.time_samples)):
            nodes_at_time = self.nodes_by_time[t_idx]

            # Check all pairs for scale/chord relationships
            for node1, node2 in combinations(nodes_at_time, 2):
                # Compute interval (semitones)
                interval = abs(node1.midi_note - node2.midi_note) % 12

                # Check if both notes in scale
                note1_in_scale = (node1.midi_note % 12 - root_semitone) % 12 in scale_intervals
                note2_in_scale = (node2.midi_note % 12 - root_semitone) % 12 in scale_intervals

                if note1_in_scale and note2_in_scale:
                    # Both in scale, add edge
                    self.graph.add_edge(
                        node1.node_id,
                        node2.node_id,
                        type='scale',
                        interval=interval,
                        weight=0.5,  # Moderate boost
                    )

                # Check for chord intervals
                for chord_name, chord_intervals in CHORD_INTERVALS.items():
                    if interval in chord_intervals:
                        self.graph.add_edge(
                            node1.node_id,
                            node2.node_id,
                            type='chord',
                            chord_type=chord_name,
                            interval=interval,
                            weight=0.8,  # Strong boost for chord tones
                        )

    # ========================================================================
    # PHASE 2: HARMONIC FILTERING (Fundamental Detection)
    # ========================================================================

    def detect_fundamentals(self):
        """
        Identify fundamental frequencies vs. harmonics using community detection.

        Algorithm:
            1. For each time sample, extract harmonic subgraph
            2. Apply community detection (Louvain method)
            3. Within each community, lowest frequency = fundamental
            4. Confirm with PageRank and degree centrality
        """
        print("Detecting fundamentals via community detection...")

        for t_idx in range(len(self.time_samples)):
            # Extract harmonic subgraph for this time sample
            harmonic_subgraph = self._get_harmonic_subgraph(t_idx)

            if harmonic_subgraph.number_of_nodes() == 0:
                continue

            # Apply community detection
            try:
                communities = nx.community.louvain_communities(
                    harmonic_subgraph,
                    weight='weight',
                    seed=42
                )
            except Exception:
                # Fallback to label propagation
                communities = nx.community.label_propagation_communities(
                    harmonic_subgraph
                )

            # Process each community
            for community in communities:
                community_nodes = [
                    self.graph.nodes[node_id]
                    for node_id in community
                ]

                # Lowest frequency = fundamental
                fundamental_node = min(
                    community_nodes,
                    key=lambda n: n['frequency_hz']
                )
                fundamental_id = f"f{fundamental_node['frequency_index']}_t{t_idx}"

                # Mark as fundamental
                self.fundamentals.add(fundamental_id)
                self.graph.nodes[fundamental_id]['is_fundamental'] = True

                # Mark others as harmonics
                for node_id in community:
                    if node_id != fundamental_id:
                        self.harmonics.add(node_id)
                        self.graph.nodes[node_id]['is_harmonic'] = True
                        self.graph.nodes[node_id]['fundamental'] = fundamental_id

        print(f"Detected {len(self.fundamentals)} fundamental frequencies, "
              f"{len(self.harmonics)} harmonics")

    def _get_harmonic_subgraph(self, time_index: int) -> nx.Graph:
        """Extract subgraph of harmonic edges at a specific time sample."""
        nodes_at_time = [node.node_id for node in self.nodes_by_time[time_index]]

        # Get all harmonic edges between these nodes
        harmonic_edges = [
            (u, v, data)
            for u, v, data in self.graph.edges(data=True)
            if data.get('type') == 'harmonic' and u in nodes_at_time and v in nodes_at_time
        ]

        # Create subgraph
        subgraph = nx.Graph()
        subgraph.add_nodes_from(nodes_at_time)
        for u, v, data in harmonic_edges:
            subgraph.add_edge(u, v, weight=data.get('weight', 1.0))

        return subgraph

    # ========================================================================
    # PHASE 3: ONSET DETECTION (Temporal Analysis)
    # ========================================================================

    def detect_onsets(self):
        """
        Detect note onsets (attacks) vs. sustains using temporal flow analysis.

        Algorithm:
            1. Calculate intensity derivatives along temporal edges
            2. Model intensity as flow through time
            3. Sudden positive flow delta = onset
            4. Near-zero delta = sustain
            5. Negative delta = release
            6. Verify across harmonic community (all harmonics should onset together)
        """
        print("Detecting note onsets via temporal flow analysis...")

        # For each fundamental frequency
        for fundamental_id in self.fundamentals:
            f_idx = self.graph.nodes[fundamental_id]['frequency_index']

            # Get temporal sequence for this frequency
            temporal_sequence = sorted(
                self.nodes_by_freq[f_idx],
                key=lambda n: n.time_index
            )

            # Calculate derivatives
            for i in range(1, len(temporal_sequence)):
                prev_node = temporal_sequence[i - 1]
                curr_node = temporal_sequence[i]

                # Intensity change
                delta_intensity = curr_node.intensity - prev_node.intensity

                # Onset = significant increase
                if delta_intensity > self.onset_threshold:
                    # Mark as onset
                    onset_time = curr_node.time_seconds
                    self.onsets[curr_node.node_id] = onset_time
                    self.graph.nodes[curr_node.node_id]['is_onset'] = True
                    self.graph.nodes[curr_node.node_id]['onset_time'] = onset_time

        print(f"Detected {len(self.onsets)} note onsets")

    # ========================================================================
    # PHASE 4: MUSIC THEORY ANALYSIS
    # ========================================================================

    def detect_key_signature(self):
        """
        Detect the key signature using note histogram and scale matching.

        Algorithm:
            1. Count occurrences of each note (weighted by intensity)
            2. For each possible key, compute scale membership score
            3. Key with highest score = detected key
        """
        print("Detecting key signature...")

        # Build note histogram (weighted by intensity)
        note_histogram = Counter()
        for node_id in self.fundamentals:
            node = self.graph.nodes[node_id]
            midi_note = node['midi_note']
            intensity = node['intensity']
            note_class = midi_note % 12  # 0=C, 1=C#, ..., 11=B
            note_histogram[note_class] += intensity

        # Try all keys
        best_key = None
        best_score = -1

        for root in range(12):  # All possible roots
            for scale_name, scale_intervals in SCALES.items():
                if scale_name == 'chromatic':
                    continue  # Skip chromatic (trivial)

                # Calculate score (sum of intensities for notes in scale)
                score = sum(
                    note_histogram[(root + interval) % 12]
                    for interval in scale_intervals
                )

                if score > best_score:
                    best_score = score
                    best_key = f"{NOTES[root]}_{scale_name}"

        self.detected_key = best_key
        print(f"Detected key: {self.detected_key}")

        # Now add music theory edges
        self._add_music_theory_edges()

    # ========================================================================
    # PHASE 5: NOISE FILTERING
    # ========================================================================

    def filter_noise(self):
        """
        Remove noise nodes using graph properties.

        Criteria for noise:
            1. Orphaned nodes (no connections)
            2. Weakly connected components (too small)
            3. Low intensity
            4. Temporal inconsistency (appears for only 1 sample)
        """
        print("Filtering noise...")

        # 1. Remove orphaned nodes
        orphaned = [n for n in self.graph.nodes() if self.graph.degree(n) == 0]
        self.graph.remove_nodes_from(orphaned)
        print(f"Removed {len(orphaned)} orphaned nodes")

        # 2. Remove weak components
        weak_components = list(nx.weakly_connected_components(self.graph))
        min_component_size = 3  # At least 3 nodes
        small_components = [c for c in weak_components if len(c) < min_component_size]
        nodes_to_remove = set().union(*small_components)
        self.graph.remove_nodes_from(nodes_to_remove)
        print(f"Removed {len(nodes_to_remove)} nodes in small components")

        # 3. Temporal consistency (appears for at least 2 consecutive samples)
        # This is handled during onset detection

    # ========================================================================
    # PHASE 6: MIDI GENERATION
    # ========================================================================

    def generate_midi_notes(self) -> List[Dict]:
        """
        Generate MIDI note events from detected fundamentals and onsets.

        Returns:
            List of note events, each with:
                - midi_note: MIDI note number (0-127)
                - onset_time: Start time (seconds)
                - duration: Note duration (seconds)
                - velocity: MIDI velocity (0-127)
        """
        print("Generating MIDI notes...")

        note_events = []

        # Group fundamentals by frequency
        fundamentals_by_freq = defaultdict(list)
        for node_id in self.fundamentals:
            node = self.graph.nodes[node_id]
            f_idx = node['frequency_index']
            fundamentals_by_freq[f_idx].append(node)

        # For each frequency track, identify note boundaries
        for f_idx, nodes in fundamentals_by_freq.items():
            # Sort by time
            nodes = sorted(nodes, key=lambda n: n['time_index'])

            current_note = None
            for i, node in enumerate(nodes):
                node_id = f"f{node['frequency_index']}_t{node['time_index']}"

                # Check if this is an onset
                if node_id in self.onsets:
                    # Finish previous note
                    if current_note is not None:
                        current_note['duration'] = node['time_seconds'] - current_note['onset_time']
                        note_events.append(current_note)

                    # Start new note
                    current_note = {
                        'midi_note': node['midi_note'],
                        'onset_time': node['time_seconds'],
                        'duration': 0.0,  # Will be updated
                        'velocity': int(node['intensity'] * 127),
                        'note_name': node['note_name'],
                    }
                elif current_note is not None:
                    # Sustaining current note, update intensity (take max)
                    current_note['velocity'] = max(
                        current_note['velocity'],
                        int(node['intensity'] * 127)
                    )

            # Finish last note
            if current_note is not None:
                last_time = nodes[-1]['time_seconds']
                current_note['duration'] = last_time - current_note['onset_time']
                if current_note['duration'] > 0:
                    note_events.append(current_note)

        # Sort by onset time
        note_events = sorted(note_events, key=lambda n: n['onset_time'])

        print(f"Generated {len(note_events)} MIDI notes")
        return note_events

    def export_midi(self, output_path: str, notes: List[Dict], tempo_bpm: float = 120):
        """
        Export notes to a MIDI file.

        Args:
            output_path: Path to output .mid file
            notes: List of note events from generate_midi_notes()
            tempo_bpm: Tempo in beats per minute
        """
        print(f"Exporting MIDI to {output_path}...")

        # Create MIDI file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_bpm)))

        # Convert notes to MIDI messages
        current_time_ticks = 0
        ticks_per_second = mid.ticks_per_beat * (tempo_bpm / 60.0)

        for note in notes:
            # Note on
            onset_ticks = int(note['onset_time'] * ticks_per_second)
            delta_ticks = onset_ticks - current_time_ticks

            track.append(mido.Message(
                'note_on',
                note=note['midi_note'],
                velocity=note['velocity'],
                time=delta_ticks
            ))
            current_time_ticks = onset_ticks

            # Note off
            duration_ticks = int(note['duration'] * ticks_per_second)
            track.append(mido.Message(
                'note_off',
                note=note['midi_note'],
                velocity=0,
                time=duration_ticks
            ))
            current_time_ticks += duration_ticks

        # Save
        mid.save(output_path)
        print(f"MIDI file saved: {output_path}")

    # ========================================================================
    # ANALYSIS PIPELINE
    # ========================================================================

    def analyze(self) -> TranscriptionResult:
        """
        Run complete analysis pipeline.

        Steps:
            1. Build graph (nodes + edges)
            2. Detect fundamentals (harmonic filtering)
            3. Detect onsets (temporal flow)
            4. Detect key signature (music theory)
            5. Filter noise
            6. Generate MIDI notes

        Returns:
            TranscriptionResult with notes, graph, and metadata
        """
        print("\n" + "="*70)
        print("AUDIO-TO-MIDI TRANSCRIPTION - GRAPH-BASED ANALYSIS")
        print("="*70 + "\n")

        # Phase 1: Build graph
        self.build_graph()

        # Phase 2: Harmonic filtering
        self.detect_fundamentals()

        # Phase 3: Onset detection
        self.detect_onsets()

        # Phase 4: Music theory
        self.detect_key_signature()

        # Phase 5: Noise filtering
        self.filter_noise()

        # Phase 6: Generate MIDI
        notes = self.generate_midi_notes()

        # Compile results
        result = TranscriptionResult(
            notes=notes,
            graph=self.graph,
            fundamentals=self.fundamentals,
            harmonics=self.harmonics,
            onsets=self.onsets,
            key_signature=self.detected_key or "unknown",
            tempo_bpm=120.0,  # TODO: Detect tempo
            metadata={
                'num_nodes': self.graph.number_of_nodes(),
                'num_edges': self.graph.number_of_edges(),
                'num_fundamentals': len(self.fundamentals),
                'num_harmonics': len(self.harmonics),
                'num_onsets': len(self.onsets),
                'num_notes': len(notes),
            }
        )

        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"Detected {len(notes)} notes in key of {result.key_signature}")
        print(f"Graph: {result.metadata['num_nodes']} nodes, "
              f"{result.metadata['num_edges']} edges")
        print()

        return result

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    @staticmethod
    def _frequency_to_midi(frequency_hz: float) -> int:
        """Convert frequency (Hz) to MIDI note number."""
        if frequency_hz <= 0:
            return 0
        # MIDI note = 69 + 12 * log2(f / 440)
        midi_note = 69 + 12 * np.log2(frequency_hz / 440.0)
        return int(round(midi_note))

    @staticmethod
    def _midi_to_note(midi_note: int) -> Tuple[str, int, float]:
        """
        Convert MIDI note number to (note_name, octave, sub_note).

        Examples:
            60 → ("C", 4, 0.0)     # Middle C
            60.5 → ("C", 4, 0.5)   # Between C and C#
        """
        octave = (midi_note // 12) - 1
        note_index = int(midi_note) % 12
        sub_note = midi_note - int(midi_note)
        note_name = NOTES[note_index]

        if sub_note > 0:
            return f"{note_name}~", octave, sub_note
        else:
            return f"{note_name}{octave}", octave, 0.0

    def export_graph_json(self, output_path: str):
        """
        Export graph in system_of_systems_graph.json format.

        Compatible with wordplay's existing graph analysis tools.
        """
        print(f"Exporting graph to {output_path}...")

        # Convert to JSON-serializable format
        graph_data = {
            'framework_id': 'audio_transcription',
            'metadata': {
                'sample_rate_hz': self.sample_rate_hz,
                'num_frequencies': len(self.frequencies),
                'num_time_samples': len(self.time_samples),
                'intensity_threshold': self.intensity_threshold,
                'onset_threshold': self.onset_threshold,
                'detected_key': self.detected_key,
            },
            'nodes': [
                {
                    'id': node_id,
                    **data
                }
                for node_id, data in self.graph.nodes(data=True)
            ],
            'links': [
                {
                    'source': u,
                    'target': v,
                    **data
                }
                for u, v, data in self.graph.edges(data=True)
            ],
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
        }

        # Save
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)

        print(f"Graph exported: {output_path}")


# ============================================================================
# PLACEHOLDER FOR SPECIALIZED FOURIER TRANSFORM
# ============================================================================

def specialized_fourier_transform(
    audio_file_path: str,
    num_sub_notes: int = 4,
    sample_duration_cycles: int = 5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    PLACEHOLDER: Specialized Fourier transform for musical analysis.

    This function will be implemented by the user with their custom transform
    that extracts frequency-time-intensity data from audio files.

    Args:
        audio_file_path: Path to .wav audio file
        num_sub_notes: Number of sub-divisions per note (e.g., 4 = quarter-note)
        sample_duration_cycles: Number of cycles of lowest frequency (27.5 Hz)
            for each time sample (e.g., 5 cycles = ~182ms)

    Returns:
        Tuple of (frequency_time_matrix, frequencies, time_samples):
            - frequency_time_matrix: 2D array [freq_idx, time_idx] = intensity
                Shape: (num_frequencies, num_time_samples)
            - frequencies: Array of frequency values (Hz) for each index
                Shape: (num_frequencies,)
            - time_samples: Array of time values (seconds) for each index
                Shape: (num_time_samples,)

    Expected Implementation:
        1. Load audio file (.wav)
        2. Divide frequency spectrum into notes + sub-notes
           - 82 notes across 8 octaves
           - Each note divided into `num_sub_notes` increments
           - Total frequencies = 82 * num_sub_notes
        3. Divide time into samples
           - Sample duration = sample_duration_cycles / 27.5 Hz
           - Example: 5 cycles / 27.5 Hz = 182ms per sample
        4. For each (frequency, time) point:
           - Apply specialized Fourier transform
           - Extract intensity at that frequency during that time window
        5. Return 2D array + frequency/time axes
    """
    raise NotImplementedError(
        "Specialized Fourier transform not implemented. "
        "Please provide your custom transform that extracts "
        "frequency-time-intensity data from audio files."
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """
    Example usage of the audio graph analyzer.

    This demonstrates the complete workflow from audio file to MIDI output.
    """
    # STEP 1: Apply specialized Fourier transform (user-provided)
    # Uncomment when transform is implemented:
    #
    # audio_file = "song.wav"
    # frequency_time_matrix, frequencies, time_samples = specialized_fourier_transform(
    #     audio_file,
    #     num_sub_notes=4,
    #     sample_duration_cycles=5
    # )

    # For now, use dummy data
    print("WARNING: Using dummy data. Provide specialized_fourier_transform() implementation.")
    num_frequencies = 82 * 4  # 82 notes × 4 sub-notes
    num_time_samples = 100
    frequency_time_matrix = np.random.rand(num_frequencies, num_time_samples) * 0.3
    frequencies = A0_FREQUENCY * (2 ** (np.arange(num_frequencies) / (12 * 4)))
    time_samples = None  # Will be computed from sample rate

    # STEP 2: Create analyzer
    analyzer = AudioGraphAnalyzer(
        frequency_time_matrix=frequency_time_matrix,
        sample_rate_hz=22050,
        frequencies=frequencies,
        time_samples=time_samples,
        intensity_threshold=0.1,
        onset_threshold=0.15,
    )

    # STEP 3: Run analysis
    result = analyzer.analyze()

    # STEP 4: Export MIDI
    analyzer.export_midi("output/transcription.mid", result.notes, tempo_bpm=120)

    # STEP 5: Export graph (for further analysis with wordplay tools)
    analyzer.export_graph_json("output/audio_graph.json")

    # STEP 6: Print summary
    print("\nTranscription Summary:")
    print(f"  Key: {result.key_signature}")
    print(f"  Tempo: {result.tempo_bpm} BPM")
    print(f"  Notes detected: {len(result.notes)}")
    print(f"  First 5 notes:")
    for note in result.notes[:5]:
        print(f"    {note['note_name']}: "
              f"onset={note['onset_time']:.2f}s, "
              f"duration={note['duration']:.2f}s, "
              f"velocity={note['velocity']}")


if __name__ == "__main__":
    main()
