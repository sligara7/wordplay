"""
Music Theory Knowledge Graph

Represents music theory concepts (keys, scales, chords, progressions) as graphs
that can be overlaid/correlated with the audio analysis graph.

Concept: Music theory provides structural constraints. High correlation between
the audio graph and theory graph = musically correct. Low correlation = errors to filter.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class MusicTheoryGraph:
    """
    Graph representation of music theory concepts.

    Nodes represent musical concepts (notes, chords, keys).
    Edges represent relationships (harmonic, scalar, progressional).
    """

    def __init__(self):
        """Initialize music theory knowledge graph."""
        self.theory_graph = nx.MultiDiGraph()

        # Build the theory graph
        self._build_pitch_class_graph()
        self._build_key_graphs()
        self._build_chord_graphs()
        self._build_progression_graphs()

    def _build_pitch_class_graph(self):
        """
        Build graph of 12 pitch classes and their relationships.

        Edges represent intervals:
        - 'semitone' (chromatic neighbor)
        - 'fifth' (circle of fifths)
        - 'third' (tertian harmony)
        """
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F',
                        'F#', 'G', 'G#', 'A', 'A#', 'B']

        for i, pc in enumerate(pitch_classes):
            self.theory_graph.add_node(
                pc,
                type='pitch_class',
                chromatic_index=i
            )

        # Add chromatic (semitone) edges
        for i in range(12):
            pc1 = pitch_classes[i]
            pc2 = pitch_classes[(i + 1) % 12]
            self.theory_graph.add_edge(pc1, pc2, relationship='semitone', weight=1.0)
            self.theory_graph.add_edge(pc2, pc1, relationship='semitone', weight=1.0)

        # Add perfect fifth edges (circle of fifths)
        for i in range(12):
            pc1 = pitch_classes[i]
            pc2 = pitch_classes[(i + 7) % 12]  # +7 semitones = perfect fifth
            self.theory_graph.add_edge(pc1, pc2, relationship='fifth', weight=2.0)
            self.theory_graph.add_edge(pc2, pc1, relationship='fourth', weight=1.5)

        # Add major third edges (tertian harmony)
        for i in range(12):
            pc1 = pitch_classes[i]
            pc2 = pitch_classes[(i + 4) % 12]  # +4 semitones = major third
            self.theory_graph.add_edge(pc1, pc2, relationship='major_third', weight=1.8)

    def _build_key_graphs(self):
        """
        Build graphs for all 24 major and minor keys.

        Each key is a subgraph containing its scale notes with strong edges.
        """
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F',
                        'F#', 'G', 'G#', 'A', 'A#', 'B']

        # Major scale pattern (W-W-H-W-W-W-H)
        major_intervals = [0, 2, 4, 5, 7, 9, 11]

        # Natural minor scale pattern (W-H-W-W-H-W-W)
        minor_intervals = [0, 2, 3, 5, 7, 8, 10]

        for i, root in enumerate(pitch_classes):
            # Major key
            key_name_major = f"{root}_major"
            self.theory_graph.add_node(
                key_name_major,
                type='key',
                mode='major',
                root=root
            )

            # Add scale degree nodes and edges
            for degree, interval in enumerate(major_intervals, 1):
                pc = pitch_classes[(i + interval) % 12]
                edge_data = {
                    'relationship': 'scale_member',
                    'key': key_name_major,
                    'degree': degree,
                    'weight': 3.0  # High weight for scale membership
                }
                self.theory_graph.add_edge(key_name_major, pc, **edge_data)

            # Minor key
            key_name_minor = f"{root}_minor"
            self.theory_graph.add_node(
                key_name_minor,
                type='key',
                mode='minor',
                root=root
            )

            for degree, interval in enumerate(minor_intervals, 1):
                pc = pitch_classes[(i + interval) % 12]
                edge_data = {
                    'relationship': 'scale_member',
                    'key': key_name_minor,
                    'degree': degree,
                    'weight': 3.0
                }
                self.theory_graph.add_edge(key_name_minor, pc, **edge_data)

    def _build_chord_graphs(self):
        """
        Build graph representations of chord types.

        Each chord type is a template showing interval relationships.
        """
        # Chord templates (intervals from root)
        chord_templates = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'diminished': [0, 3, 6],
            'augmented': [0, 4, 8],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            'maj7': [0, 4, 7, 11],
            'min7': [0, 3, 7, 10],
            'dom7': [0, 4, 7, 10],
            'dim7': [0, 3, 6, 9],
            'halfdim7': [0, 3, 6, 10],
            'dom9': [0, 4, 7, 10, 14],
            'maj11': [0, 4, 7, 11, 14, 17],
        }

        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F',
                        'F#', 'G', 'G#', 'A', 'A#', 'B']

        for chord_type, intervals in chord_templates.items():
            # Create chord template node
            template_name = f"chord_template_{chord_type}"
            self.theory_graph.add_node(
                template_name,
                type='chord_template',
                chord_type=chord_type,
                intervals=intervals
            )

            # For each root note, create a chord instance
            for i, root in enumerate(pitch_classes):
                chord_name = f"{root}_{chord_type}"
                self.theory_graph.add_node(
                    chord_name,
                    type='chord',
                    root=root,
                    chord_type=chord_type
                )

                # Link to template
                self.theory_graph.add_edge(
                    chord_name, template_name,
                    relationship='instance_of',
                    weight=1.0
                )

                # Add edges to chord member notes
                for degree, interval in enumerate(intervals, 1):
                    pc = pitch_classes[(i + interval) % 12]
                    self.theory_graph.add_edge(
                        chord_name, pc,
                        relationship='chord_member',
                        degree=degree,
                        weight=2.5  # High weight for chord membership
                    )

    def _build_progression_graphs(self):
        """
        Build graphs of common chord progressions.

        Edges represent typical progression relationships.
        """
        # Common progressions in major keys (by degree)
        common_progressions = {
            'authentic_cadence': [(5, 1)],  # V → I
            'plagal_cadence': [(4, 1)],     # IV → I
            'deceptive_cadence': [(5, 6)],  # V → vi
            'pop_progression': [(1, 5), (5, 6), (6, 4), (4, 1)],  # I-V-vi-IV
            'jazz_turnaround': [(2, 5), (5, 1)],  # ii-V-I
            '50s_progression': [(1, 6), (6, 4), (4, 5), (5, 1)],  # I-vi-IV-V
        }

        for prog_name, transitions in common_progressions.items():
            prog_node = f"progression_{prog_name}"
            self.theory_graph.add_node(
                prog_node,
                type='progression',
                name=prog_name
            )

            for from_degree, to_degree in transitions:
                edge_data = {
                    'relationship': 'progression',
                    'from_degree': from_degree,
                    'to_degree': to_degree,
                    'weight': 2.0,
                    'progression': prog_name
                }
                # Add abstract progression edge
                self.theory_graph.add_edge(
                    f"degree_{from_degree}",
                    f"degree_{to_degree}",
                    **edge_data
                )

    def get_key_subgraph(self, key: str) -> nx.Graph:
        """
        Extract subgraph for a specific key.

        Returns graph containing only the scale notes for that key.
        """
        key_node = f"{key}_major" if '_' not in key else key

        # Get all scale members for this key
        scale_notes = []
        for successor in self.theory_graph.successors(key_node):
            if self.theory_graph.nodes[successor].get('type') == 'pitch_class':
                scale_notes.append(successor)

        return self.theory_graph.subgraph([key_node] + scale_notes)

    def get_chord_subgraph(self, root: str, chord_type: str) -> nx.Graph:
        """
        Extract subgraph for a specific chord.

        Returns graph containing the chord and its member notes.
        """
        chord_node = f"{root}_{chord_type}"

        # Get all chord members
        chord_notes = []
        if chord_node in self.theory_graph:
            for successor in self.theory_graph.successors(chord_node):
                if self.theory_graph.nodes[successor].get('type') == 'pitch_class':
                    chord_notes.append(successor)

        return self.theory_graph.subgraph([chord_node] + chord_notes)

    def correlate_with_audio_graph(self, audio_graph: nx.Graph,
                                   time_window: Tuple[float, float]) -> Dict:
        """
        Correlate music theory graph with audio analysis graph.

        High correlation = musically correct
        Low correlation = likely errors

        Args:
            audio_graph: Graph from AudioGraphBuilder
            time_window: (start_time, end_time) in seconds

        Returns:
            Dictionary with correlation scores for keys and chords
        """
        # Extract notes from audio graph in time window
        detected_notes = self._extract_notes_from_audio_graph(
            audio_graph, time_window
        )

        if not detected_notes:
            return {'keys': {}, 'chords': {}, 'best_key': None, 'best_chord': None}

        # Build pitch class histogram
        pitch_classes = [n['pitch_class'] for n in detected_notes]
        pitch_histogram = np.bincount(pitch_classes, minlength=12)

        # Score all keys
        key_scores = {}
        for key_node in self.theory_graph.nodes():
            if self.theory_graph.nodes[key_node].get('type') == 'key':
                score = self._score_key(key_node, pitch_histogram)
                key_scores[key_node] = score

        # Score all possible chords
        chord_scores = {}
        for chord_node in self.theory_graph.nodes():
            if self.theory_graph.nodes[chord_node].get('type') == 'chord':
                score = self._score_chord(chord_node, pitch_classes)
                chord_scores[chord_node] = score

        # Find best matches
        best_key = max(key_scores.items(), key=lambda x: x[1]) if key_scores else (None, 0)
        best_chord = max(chord_scores.items(), key=lambda x: x[1]) if chord_scores else (None, 0)

        return {
            'keys': key_scores,
            'chords': chord_scores,
            'best_key': best_key,
            'best_chord': best_chord,
            'detected_notes': detected_notes
        }

    def _extract_notes_from_audio_graph(self, audio_graph: nx.Graph,
                                       time_window: Tuple[float, float]) -> List[Dict]:
        """Extract detected notes from audio graph in time window."""
        notes = []
        start_time, end_time = time_window

        for node_id in audio_graph.nodes():
            node_data = audio_graph.nodes[node_id]
            time_seconds = node_data.get('time_seconds', 0)

            if start_time <= time_seconds <= end_time:
                if 'note' in node_data and 'intensity' in node_data:
                    # Extract pitch class (C, C#, D, etc.)
                    note_name = node_data['note']
                    pitch_class_num = self._note_name_to_pitch_class(note_name)

                    notes.append({
                        'node_id': node_id,
                        'note_name': note_name,
                        'pitch_class': pitch_class_num,
                        'intensity': node_data['intensity'],
                        'time': time_seconds
                    })

        return notes

    def _note_name_to_pitch_class(self, note_name: str) -> int:
        """Convert note name (e.g., 'C4', 'F#3') to pitch class (0-11)."""
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }

        # Extract pitch class (remove octave number)
        pitch_class_name = ''.join(c for c in note_name if not c.isdigit())
        return note_map.get(pitch_class_name, 0)

    def _score_key(self, key_node: str, pitch_histogram: np.ndarray) -> float:
        """
        Score how well detected pitches fit a key.

        Uses weighted correlation:
        - Scale tones get high weight
        - Non-scale tones penalized
        """
        # Get scale notes for this key
        scale_pitch_classes = []
        for successor in self.theory_graph.successors(key_node):
            if self.theory_graph.nodes[successor].get('type') == 'pitch_class':
                pc_index = self.theory_graph.nodes[successor]['chromatic_index']
                scale_pitch_classes.append(pc_index)

        # Create key profile (1 for in-scale, 0 for out-of-scale)
        key_profile = np.zeros(12)
        for pc in scale_pitch_classes:
            key_profile[pc] = 1.0

        # Normalize histograms
        if pitch_histogram.sum() > 0:
            pitch_dist = pitch_histogram / pitch_histogram.sum()
        else:
            return 0.0

        # Correlation score
        score = np.dot(pitch_dist, key_profile)

        # Penalty for out-of-key notes
        out_of_key = pitch_dist * (1 - key_profile)
        penalty = out_of_key.sum()

        return score - 0.5 * penalty

    def _score_chord(self, chord_node: str, pitch_classes: List[int]) -> float:
        """
        Score how well detected pitches fit a chord.

        Perfect match = 1.0
        Partial match = proportional
        """
        # Get chord member pitch classes
        chord_pitch_classes = []
        for successor in self.theory_graph.successors(chord_node):
            if self.theory_graph.nodes[successor].get('type') == 'pitch_class':
                pc_index = self.theory_graph.nodes[successor]['chromatic_index']
                chord_pitch_classes.append(pc_index)

        if not chord_pitch_classes:
            return 0.0

        # Count matches
        unique_pitches = set(pitch_classes)
        matches = len(unique_pitches & set(chord_pitch_classes))

        # Score = matches / expected
        score = matches / len(chord_pitch_classes)

        # Bonus if all chord tones present
        if matches == len(chord_pitch_classes):
            score += 0.5

        # Penalty for extra non-chord tones
        extra_notes = len(unique_pitches - set(chord_pitch_classes))
        penalty = extra_notes * 0.1

        return max(0, score - penalty)

    def visualize_correlation(self, correlation_results: Dict,
                            output_path: str = 'theory_correlation.png'):
        """
        Visualize correlation results.

        Shows how well detected notes match music theory expectations.
        """
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot key correlations (top 10)
        key_scores = correlation_results.get('keys', {})
        if key_scores:
            sorted_keys = sorted(key_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            keys, scores = zip(*sorted_keys)

            ax1.barh(range(len(keys)), scores)
            ax1.set_yticks(range(len(keys)))
            ax1.set_yticklabels(keys)
            ax1.set_xlabel('Correlation Score')
            ax1.set_title('Top 10 Key Correlations')
            ax1.invert_yaxis()

        # Plot chord correlations (top 15)
        chord_scores = correlation_results.get('chords', {})
        if chord_scores:
            sorted_chords = sorted(chord_scores.items(), key=lambda x: x[1], reverse=True)[:15]
            chords, scores = zip(*sorted_chords)

            ax2.barh(range(len(chords)), scores)
            ax2.set_yticks(range(len(chords)))
            ax2.set_yticklabels(chords)
            ax2.set_xlabel('Correlation Score')
            ax2.set_title('Top 15 Chord Correlations')
            ax2.invert_yaxis()

        plt.tight_layout()
        plt.savefig(output_path)
        print(f"Saved correlation visualization to {output_path}")

        return fig


# Create singleton instance
music_theory_graph = MusicTheoryGraph()
