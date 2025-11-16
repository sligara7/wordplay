"""
Harmonic analysis using graph community detection to identify fundamental frequencies.

This module implements methods to separate fundamental frequencies from their harmonics
using community detection algorithms on the harmonic subgraph.
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class HarmonicAnalyzer:
    """
    Analyze harmonic structure of audio graph to identify fundamental frequencies.

    Uses community detection to group harmonically-related frequencies and
    identify the fundamental (root) frequency of each harmonic series.
    """

    def __init__(self, audio_graph: nx.MultiDiGraph):
        """
        Initialize harmonic analyzer.

        Args:
            audio_graph: Graph from AudioGraphBuilder with harmonic edges
        """
        self.graph = audio_graph
        self.fundamentals = {}  # time_idx -> list of fundamental nodes
        self.harmonic_communities = {}  # time_idx -> list of communities

    def extract_harmonic_subgraph(self, time_idx: int) -> nx.Graph:
        """
        Extract the harmonic subgraph for a specific time sample.

        Creates an undirected graph containing only nodes at the specified time
        and only harmonic edges between them.

        Args:
            time_idx: Time sample index

        Returns:
            Undirected graph with harmonic relationships
        """
        subgraph = nx.Graph()

        # Find all nodes at this time
        nodes_at_time = []
        for node_id in self.graph.nodes():
            if self.graph.nodes[node_id]['time_sample'] == time_idx:
                nodes_at_time.append(node_id)
                # Copy node attributes
                subgraph.add_node(node_id, **self.graph.nodes[node_id])

        # Add harmonic edges
        for node_id in nodes_at_time:
            # Get all edges from this node
            for neighbor in self.graph.neighbors(node_id):
                if neighbor in nodes_at_time:
                    # Check if there's a harmonic edge
                    edges = self.graph.get_edge_data(node_id, neighbor)
                    if edges:
                        for edge_data in edges.values():
                            if edge_data.get('edge_type') == 'harmonic':
                                # Add to undirected subgraph
                                if not subgraph.has_edge(node_id, neighbor):
                                    subgraph.add_edge(
                                        node_id,
                                        neighbor,
                                        weight=edge_data['weight'],
                                        harmonic_ratio=edge_data.get('harmonic_ratio', 1.0)
                                    )

        return subgraph

    def detect_harmonic_communities(self, time_idx: int) -> List[Set[str]]:
        """
        Detect communities of harmonically-related frequencies.

        Args:
            time_idx: Time sample index

        Returns:
            List of communities (sets of node IDs)
        """
        subgraph = self.extract_harmonic_subgraph(time_idx)

        if subgraph.number_of_nodes() == 0:
            return []

        # Use Louvain method for community detection
        try:
            communities = nx.community.louvain_communities(subgraph, weight='weight')
            return [set(c) for c in communities]
        except:
            # Fallback to connected components if Louvain fails
            return [set(c) for c in nx.connected_components(subgraph)]

    def identify_fundamental_in_community(self,
                                           community: Set[str],
                                           subgraph: nx.Graph) -> Tuple[str, float]:
        """
        Identify the fundamental frequency within a harmonic community.

        The fundamental is identified as:
        1. The lowest frequency in the community (most likely)
        2. Confirmed by high degree centrality (many harmonic connections)
        3. Confirmed by PageRank (harmonics point to it)

        Args:
            community: Set of node IDs in the community
            subgraph: Harmonic subgraph

        Returns:
            Tuple of (fundamental_node_id, confidence_score)
        """
        if not community:
            return None, 0.0

        # Get frequencies of all nodes in community
        freq_to_node = {}
        for node_id in community:
            freq = self.graph.nodes[node_id]['frequency']
            freq_to_node[freq] = node_id

        # Candidate 1: Lowest frequency
        lowest_freq = min(freq_to_node.keys())
        fundamental_candidate = freq_to_node[lowest_freq]

        # Calculate confidence based on graph metrics
        confidence_scores = []

        # Metric 1: Degree centrality (fundamentals have many harmonic connections)
        if len(community) > 1:
            community_subgraph = subgraph.subgraph(community)
            degree_centrality = nx.degree_centrality(community_subgraph)
            if fundamental_candidate in degree_centrality:
                confidence_scores.append(degree_centrality[fundamental_candidate])

        # Metric 2: Intensity (louder notes are more likely to be fundamental)
        intensity = self.graph.nodes[fundamental_candidate]['intensity']
        confidence_scores.append(intensity)

        # Metric 3: Number of harmonics (more harmonics = more confident)
        expected_harmonics = [2, 3, 4, 5]  # Common harmonic ratios
        harmonic_count = 0
        for ratio in expected_harmonics:
            expected_freq = lowest_freq * ratio
            # Check if any frequency in community is close to expected harmonic
            for freq in freq_to_node.keys():
                if abs(freq - expected_freq) / expected_freq < 0.05:  # 5% tolerance
                    harmonic_count += 1
                    break

        harmonic_score = min(harmonic_count / len(expected_harmonics), 1.0)
        confidence_scores.append(harmonic_score)

        # Average confidence
        confidence = np.mean(confidence_scores) if confidence_scores else 0.5

        return fundamental_candidate, confidence

    def analyze_all_time_samples(self) -> Dict[int, List[Dict]]:
        """
        Analyze all time samples to identify fundamentals.

        Returns:
            Dictionary mapping time_idx to list of fundamental note dictionaries
        """
        all_fundamentals = {}

        # Get all unique time samples
        time_samples = set()
        for node_id in self.graph.nodes():
            time_samples.add(self.graph.nodes[node_id]['time_sample'])

        for time_idx in sorted(time_samples):
            # Detect communities
            communities = self.detect_harmonic_communities(time_idx)
            self.harmonic_communities[time_idx] = communities

            # Extract subgraph for this time
            subgraph = self.extract_harmonic_subgraph(time_idx)

            # Identify fundamental in each community
            fundamentals_at_time = []
            for community in communities:
                fundamental_id, confidence = self.identify_fundamental_in_community(
                    community, subgraph
                )

                if fundamental_id:
                    node_data = dict(self.graph.nodes[fundamental_id])
                    fundamentals_at_time.append({
                        'node_id': fundamental_id,
                        'frequency': node_data['frequency'],
                        'note': node_data['note'],
                        'intensity': node_data['intensity'],
                        'time_sample': time_idx,
                        'time_seconds': node_data['time_seconds'],
                        'confidence': confidence,
                        'community_size': len(community)
                    })

            all_fundamentals[time_idx] = fundamentals_at_time

        self.fundamentals = all_fundamentals
        return all_fundamentals

    def get_fundamental_timeline(self, min_confidence: float = 0.3) -> List[Dict]:
        """
        Get a timeline of all detected fundamental notes.

        Args:
            min_confidence: Minimum confidence threshold to include a note

        Returns:
            List of fundamental note dictionaries sorted by time
        """
        timeline = []

        for time_idx in sorted(self.fundamentals.keys()):
            for fundamental in self.fundamentals[time_idx]:
                if fundamental['confidence'] >= min_confidence:
                    timeline.append(fundamental)

        return sorted(timeline, key=lambda x: x['time_seconds'])

    def filter_noise(self,
                     min_intensity: float = 0.1,
                     min_confidence: float = 0.3,
                     min_duration_samples: int = 2) -> List[Dict]:
        """
        Filter out noise and keep only sustained musical notes.

        Args:
            min_intensity: Minimum intensity threshold
            min_confidence: Minimum confidence threshold
            min_duration_samples: Minimum number of consecutive samples

        Returns:
            Filtered list of fundamental notes
        """
        timeline = self.get_fundamental_timeline(min_confidence=min_confidence)

        # Group by note name to find sustained notes
        note_sequences = defaultdict(list)
        for fundamental in timeline:
            if fundamental['intensity'] >= min_intensity:
                note_name = fundamental['note']
                note_sequences[note_name].append(fundamental)

        # Filter short-duration notes
        filtered_notes = []
        for note_name, sequence in note_sequences.items():
            # Sort by time
            sequence.sort(key=lambda x: x['time_sample'])

            # Find consecutive sequences
            current_sequence = [sequence[0]]
            for i in range(1, len(sequence)):
                # Check if consecutive in time
                if sequence[i]['time_sample'] - current_sequence[-1]['time_sample'] <= 2:
                    current_sequence.append(sequence[i])
                else:
                    # End of sequence
                    if len(current_sequence) >= min_duration_samples:
                        filtered_notes.extend(current_sequence)
                    current_sequence = [sequence[i]]

            # Handle last sequence
            if len(current_sequence) >= min_duration_samples:
                filtered_notes.extend(current_sequence)

        return sorted(filtered_notes, key=lambda x: x['time_seconds'])

    def get_statistics(self) -> Dict:
        """Get statistics about the harmonic analysis."""
        total_fundamentals = sum(len(f) for f in self.fundamentals.values())
        total_communities = sum(len(c) for c in self.harmonic_communities.values())

        timeline = self.get_fundamental_timeline()
        if timeline:
            avg_confidence = np.mean([f['confidence'] for f in timeline])
            avg_intensity = np.mean([f['intensity'] for f in timeline])
        else:
            avg_confidence = 0.0
            avg_intensity = 0.0

        return {
            'total_time_samples': len(self.fundamentals),
            'total_fundamentals_detected': total_fundamentals,
            'total_communities': total_communities,
            'avg_confidence': avg_confidence,
            'avg_intensity': avg_intensity
        }


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('/home/ajs7/project/wordplay/music/new_start')
    from spectral_analyzer import SpectralAnalyzer
    from audio_graph_builder import build_audio_graph_from_file
    from scipy.io.wavfile import read

    # Read audio file
    file_path = '/home/ajs7/Music/CdL.wav'
    sample_rate, audio_data = read(file_path)

    # Analyze audio
    print("Analyzing audio...")
    analyzer = SpectralAnalyzer(samplefreq=sample_rate)
    left_channel = audio_data[:, 0] if len(audio_data.shape) > 1 else audio_data
    spectral_data = analyzer.dotop(left_channel)

    # Build graph
    print("\nBuilding graph...")
    builder = build_audio_graph_from_file(analyzer, spectral_data, intensity_threshold=0.1)

    # Analyze harmonics
    print("\nAnalyzing harmonics...")
    harmonic_analyzer = HarmonicAnalyzer(builder.graph)
    fundamentals = harmonic_analyzer.analyze_all_time_samples()

    # Print statistics
    stats = harmonic_analyzer.get_statistics()
    print("\nHarmonic Analysis Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Get filtered timeline
    filtered_timeline = harmonic_analyzer.filter_noise(
        min_intensity=0.15,
        min_confidence=0.4,
        min_duration_samples=3
    )

    print(f"\nFiltered notes: {len(filtered_timeline)}")
    print("\nFirst 10 fundamental notes:")
    for note in filtered_timeline[:10]:
        print(f"  {note['time_seconds']:.2f}s: {note['note']} "
              f"(intensity={note['intensity']:.2f}, confidence={note['confidence']:.2f})")
