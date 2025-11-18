"""
Build a NetworkX graph from spectral analysis data for audio-to-MIDI transcription.

This module converts the 2D frequency-time-intensity array from spectral_analyzer.py
into a directed graph where nodes represent frequency-time points and edges represent
temporal, harmonic, and music theory relationships.
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional


class AudioGraphBuilder:
    """
    Build a graph representation of audio spectral data.

    Nodes represent (frequency, time, intensity) points.
    Edges represent:
    - Temporal relationships (same frequency across time)
    - Harmonic relationships (harmonically-related frequencies at same time)
    - Music theory relationships (notes in same scale/chord)
    """

    def __init__(self,
                 spectral_data: np.ndarray,
                 frequencies: np.ndarray,
                 sample_rate: int,
                 window_length: int,
                 intensity_threshold: float = 0.01,
                 harmonic_ratios: Optional[List[float]] = None):
        """
        Initialize the audio graph builder.

        Args:
            spectral_data: 2D array [frequency_index, time_index] = intensity
            frequencies: Array of frequencies in Hz corresponding to each frequency index
            sample_rate: Audio sample rate in Hz
            window_length: Length of analysis window in samples
            intensity_threshold: Minimum intensity to include a node (default: 0.01)
            harmonic_ratios: List of harmonic ratios to connect (default: [2, 3, 4, 5])
        """
        self.spectral_data = spectral_data
        self.frequencies = frequencies
        self.sample_rate = sample_rate
        self.window_length = window_length
        self.intensity_threshold = intensity_threshold
        self.harmonic_ratios = harmonic_ratios or [2.0, 3.0, 4.0, 5.0, 1.5, 2.5]

        # Normalize spectral data
        max_intensity = np.max(spectral_data)
        if max_intensity > 0:
            self.spectral_data = spectral_data / max_intensity

        self.num_frequencies = spectral_data.shape[0]
        self.num_time_samples = spectral_data.shape[1]

        # Create graph
        self.graph = nx.MultiDiGraph()

        # Build note name lookup
        self._build_note_names()

    def _build_note_names(self):
        """Build a mapping from frequency index to note names."""
        note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
        self.note_lookup = []

        A0_freq = 27.5  # A0 frequency
        for freq in self.frequencies:
            # Calculate semitones above A0
            semitones = 12 * np.log2(freq / A0_freq)
            octave = int(semitones // 12)
            # Round and wrap to ensure note_idx is in [0, 11]
            note_idx = int(round(semitones % 12)) % 12
            note_name = f"{note_names[note_idx]}{octave}"
            self.note_lookup.append(note_name)

    def _get_time_in_seconds(self, time_index: int) -> float:
        """Convert time index to seconds."""
        return (time_index * self.window_length) / self.sample_rate

    def _node_id(self, freq_idx: int, time_idx: int) -> str:
        """Generate a unique node ID."""
        return f"f{freq_idx}_t{time_idx}"

    def add_nodes(self):
        """
        Add nodes to the graph for all frequency-time points above threshold.

        Each node contains:
        - frequency: Frequency in Hz
        - note: Note name (e.g., 'A4')
        - time_sample: Time sample index
        - time_seconds: Absolute time in seconds
        - intensity: Normalized intensity [0, 1]
        - freq_index: Frequency index in spectral array
        """
        node_count = 0

        for freq_idx in range(self.num_frequencies):
            for time_idx in range(self.num_time_samples):
                intensity = self.spectral_data[freq_idx, time_idx]

                # Only add nodes with intensity above threshold
                if intensity >= self.intensity_threshold:
                    node_id = self._node_id(freq_idx, time_idx)

                    self.graph.add_node(
                        node_id,
                        frequency=self.frequencies[freq_idx],
                        note=self.note_lookup[freq_idx],
                        time_sample=time_idx,
                        time_idx=time_idx,  # For onset detector
                        time_seconds=self._get_time_in_seconds(time_idx),
                        intensity=float(intensity),
                        freq_index=freq_idx,
                        freq_idx=freq_idx  # For onset detector
                    )
                    node_count += 1

        print(f"Added {node_count} nodes to graph")
        return node_count

    def add_temporal_edges(self):
        """
        Add temporal edges connecting the same frequency across adjacent time samples.

        Edge attributes:
        - type: 'temporal'
        - weight: Correlation between intensities
        - delta_intensity: Change in intensity
        - flow: Intensity flowing through time
        """
        edge_count = 0

        for freq_idx in range(self.num_frequencies):
            for time_idx in range(self.num_time_samples - 1):
                source_id = self._node_id(freq_idx, time_idx)
                target_id = self._node_id(freq_idx, time_idx + 1)

                # Only add edge if both nodes exist
                if source_id in self.graph.nodes and target_id in self.graph.nodes:
                    source_intensity = self.graph.nodes[source_id]['intensity']
                    target_intensity = self.graph.nodes[target_id]['intensity']

                    # Calculate edge properties
                    delta_intensity = target_intensity - source_intensity
                    avg_intensity = (source_intensity + target_intensity) / 2

                    # Weight based on average intensity (strong flows are more important)
                    weight = avg_intensity

                    self.graph.add_edge(
                        source_id,
                        target_id,
                        edge_type='temporal',
                        weight=weight,
                        delta_intensity=float(delta_intensity),
                        flow=float(avg_intensity)
                    )
                    edge_count += 1

        print(f"Added {edge_count} temporal edges")
        return edge_count

    def add_harmonic_edges(self):
        """
        Add harmonic edges connecting harmonically-related frequencies at the same time.

        Edge attributes:
        - type: 'harmonic'
        - harmonic_ratio: Ratio between frequencies
        - weight: Product of intensities (both must be strong)
        - is_octave: True if ratio is a power of 2
        """
        edge_count = 0

        for time_idx in range(self.num_time_samples):
            # Get all active nodes at this time sample
            active_nodes = []
            for freq_idx in range(self.num_frequencies):
                node_id = self._node_id(freq_idx, time_idx)
                if node_id in self.graph.nodes:
                    active_nodes.append((freq_idx, node_id))

            # Connect harmonically-related frequencies
            for i, (freq_idx1, node_id1) in enumerate(active_nodes):
                freq1 = self.frequencies[freq_idx1]
                intensity1 = self.graph.nodes[node_id1]['intensity']

                for freq_idx2, node_id2 in active_nodes[i+1:]:
                    freq2 = self.frequencies[freq_idx2]
                    intensity2 = self.graph.nodes[node_id2]['intensity']

                    # Calculate frequency ratio
                    ratio = freq2 / freq1

                    # Check if ratio matches any harmonic ratio (within tolerance)
                    for harmonic_ratio in self.harmonic_ratios:
                        if abs(ratio - harmonic_ratio) < 0.05:  # 5% tolerance
                            # Add edge from lower to higher frequency
                            weight = intensity1 * intensity2  # Both must be strong
                            is_octave = abs(ratio - 2.0) < 0.05 or abs(ratio - 4.0) < 0.05

                            self.graph.add_edge(
                                node_id1,
                                node_id2,
                                edge_type='harmonic',
                                harmonic_ratio=float(ratio),
                                weight=weight,
                                is_octave=is_octave
                            )
                            edge_count += 1
                            break

        print(f"Added {edge_count} harmonic edges")
        return edge_count

    def build_graph(self) -> nx.MultiDiGraph:
        """
        Build the complete graph with nodes and all edge types.

        Returns:
            NetworkX MultiDiGraph with spectral data represented as nodes and edges
        """
        print("Building audio graph...")
        print(f"Spectral data shape: {self.spectral_data.shape}")
        print(f"Frequency range: {self.frequencies[0]:.2f} Hz to {self.frequencies[-1]:.2f} Hz")
        print(f"Duration: {self._get_time_in_seconds(self.num_time_samples-1):.2f} seconds")
        print(f"Intensity threshold: {self.intensity_threshold}")
        print()

        # Add nodes
        self.add_nodes()

        # Add edges
        self.add_temporal_edges()
        self.add_harmonic_edges()

        print()
        print(f"Graph statistics:")
        print(f"  Nodes: {self.graph.number_of_nodes()}")
        print(f"  Edges: {self.graph.number_of_edges()}")
        print(f"  Density: {nx.density(self.graph):.6f}")

        return self.graph

    def get_node_data_at_time(self, time_idx: int) -> List[Dict]:
        """
        Get all node data at a specific time index.

        Args:
            time_idx: Time sample index

        Returns:
            List of node attribute dictionaries
        """
        nodes_at_time = []
        for freq_idx in range(self.num_frequencies):
            node_id = self._node_id(freq_idx, time_idx)
            if node_id in self.graph.nodes:
                node_data = dict(self.graph.nodes[node_id])
                node_data['node_id'] = node_id
                nodes_at_time.append(node_data)

        return nodes_at_time

    def get_temporal_sequence(self, freq_idx: int) -> List[Tuple[int, float]]:
        """
        Get the temporal sequence of intensities for a specific frequency.

        Args:
            freq_idx: Frequency index

        Returns:
            List of (time_index, intensity) tuples
        """
        sequence = []
        for time_idx in range(self.num_time_samples):
            node_id = self._node_id(freq_idx, time_idx)
            if node_id in self.graph.nodes:
                intensity = self.graph.nodes[node_id]['intensity']
                sequence.append((time_idx, intensity))

        return sequence


def build_audio_graph_from_file(spectral_analyzer, spectral_data,
                                  intensity_threshold=0.01) -> AudioGraphBuilder:
    """
    Convenience function to build an audio graph from spectral analyzer output.

    Args:
        spectral_analyzer: SpectralAnalyzer instance with frequency and timing info
        spectral_data: 2D numpy array from spectral_analyzer.dotop()
        intensity_threshold: Minimum intensity to include nodes

    Returns:
        AudioGraphBuilder instance with built graph
    """
    builder = AudioGraphBuilder(
        spectral_data=spectral_data,
        frequencies=spectral_analyzer.frequencies,
        sample_rate=spectral_analyzer.sample_freq,
        window_length=spectral_analyzer.window_length,
        intensity_threshold=intensity_threshold
    )

    builder.build_graph()

    return builder


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('/home/ajs7/project/wordplay/music/new_start')
    from spectral_analyzer import SpectralAnalyzer
    from scipy.io.wavfile import read

    # Read audio file
    file_path = '/home/ajs7/Music/CdL.wav'
    sample_rate, audio_data = read(file_path)

    # Analyze audio
    analyzer = SpectralAnalyzer(samplefreq=sample_rate)
    left_channel = audio_data[:, 0] if len(audio_data.shape) > 1 else audio_data
    spectral_data = analyzer.dotop(left_channel)

    # Build graph
    builder = build_audio_graph_from_file(analyzer, spectral_data, intensity_threshold=0.05)

    print("\nExample node:")
    for node_id in list(builder.graph.nodes())[:1]:
        print(f"  {node_id}: {builder.graph.nodes[node_id]}")

    print("\nExample temporal edge:")
    temporal_edges = [e for e in builder.graph.edges(data=True) if e[2]['edge_type'] == 'temporal']
    if temporal_edges:
        print(f"  {temporal_edges[0]}")

    print("\nExample harmonic edge:")
    harmonic_edges = [e for e in builder.graph.edges(data=True) if e[2]['edge_type'] == 'harmonic']
    if harmonic_edges:
        print(f"  {harmonic_edges[0]}")
