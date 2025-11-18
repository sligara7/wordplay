"""
Chord Recognizer with Music Theory Graph Correlation

Uses the music theory knowledge graph to:
1. Detect chords in audio
2. Filter fundamentals based on music theory validity
3. Correlate detected patterns with theoretical expectations
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from music_theory_graph import music_theory_graph


class ChordRecognizer:
    """
    Recognize chords using graph-based music theory correlation.

    Concept: Overlay music theory graph with audio graph.
    High correlation = musically valid, keep it.
    Low correlation = likely error, filter it out.
    """

    def __init__(self, time_window_ms: float = 100):
        """
        Initialize chord recognizer.

        Args:
            time_window_ms: Time window for grouping simultaneous notes (default: 100ms)
        """
        self.time_window_ms = time_window_ms
        self.time_window_seconds = time_window_ms / 1000.0
        self.theory_graph = music_theory_graph

        # Chord templates (from your chords.py)
        self.chord_templates = {
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
        }

    def analyze_with_theory_correlation(self,
                                       fundamentals: List[Dict],
                                       audio_graph: nx.Graph) -> Dict:
        """
        Analyze fundamentals using music theory graph correlation.

        This is the main method that:
        1. Groups notes by time windows
        2. Correlates each window with music theory
        3. Filters based on correlation scores

        Args:
            fundamentals: List of fundamental notes from HarmonicAnalyzer
            audio_graph: The audio analysis graph

        Returns:
            Dictionary with:
            - 'filtered_fundamentals': Notes that pass theory correlation
            - 'detected_chords': Identified chords with scores
            - 'detected_key': Most likely key
            - 'correlation_timeline': Theory correlation over time
        """
        if not fundamentals:
            return {
                'filtered_fundamentals': [],
                'detected_chords': [],
                'detected_key': None,
                'correlation_timeline': []
            }

        # Step 1: Group fundamentals by time windows
        time_windows = self._group_by_time_windows(fundamentals)

        # Step 2: Detect global key (analyze all fundamentals)
        global_key = self._detect_key(fundamentals)

        # Step 3: Analyze each time window
        detected_chords = []
        correlation_timeline = []
        filtered_fundamentals = []

        for window_idx, (window_time, window_notes) in enumerate(time_windows):
            # Correlate with theory graph
            start_time = window_time
            end_time = window_time + self.time_window_seconds

            correlation = self.theory_graph.correlate_with_audio_graph(
                audio_graph,
                (start_time, end_time)
            )

            # Get best chord for this window
            best_chord, chord_score = correlation['best_chord']

            # Store timeline info
            correlation_timeline.append({
                'time': window_time,
                'key_correlation': correlation['keys'].get(global_key, 0) if global_key else 0,
                'chord': best_chord,
                'chord_score': chord_score,
                'num_notes': len(window_notes)
            })

            # Filter notes based on theory correlation
            if chord_score > 0.5:  # Good chord match
                # Keep notes that fit the chord
                chord_pitch_classes = self._get_chord_pitch_classes(best_chord)

                for note in window_notes:
                    pc = self._note_to_pitch_class(note['note'])

                    if pc in chord_pitch_classes:
                        # Note fits chord - keep with boosted confidence
                        note['theory_score'] = chord_score
                        note['chord'] = best_chord
                        note['confidence'] = note.get('confidence', 1.0) * 1.1
                        filtered_fundamentals.append(note)
                    elif note.get('confidence', 0) > 0.4:
                        # Moderate signal but doesn't fit chord
                        # Might be passing tone, chromatic note, or detection error
                        note['theory_score'] = chord_score * 0.6
                        note['chord'] = None
                        note['confidence'] = note.get('confidence', 1.0) * 0.8
                        filtered_fundamentals.append(note)

                # Record detected chord
                if best_chord:
                    detected_chords.append({
                        'time': window_time,
                        'chord': best_chord,
                        'score': chord_score,
                        'notes': [n['note'] for n in window_notes if
                                 self._note_to_pitch_class(n['note']) in chord_pitch_classes]
                    })

            else:  # Weak chord match - use key-based filtering
                if global_key:
                    key_pitch_classes = self._get_key_pitch_classes(global_key)

                    for note in window_notes:
                        pc = self._note_to_pitch_class(note['note'])

                        if pc in key_pitch_classes:
                            # Note fits key scale
                            note['theory_score'] = correlation['keys'].get(global_key, 0)
                            note['key'] = global_key
                            filtered_fundamentals.append(note)
                        elif note.get('confidence', 0) > 0.5:
                            # Strong chromatic note - might be real
                            note['theory_score'] = 0.4
                            note['confidence'] = note.get('confidence', 1.0) * 0.7
                            filtered_fundamentals.append(note)
                else:
                    # No key detected - keep moderate-confidence notes
                    for note in window_notes:
                        if note.get('confidence', 0) > 0.3:
                            note['theory_score'] = 0.5
                            filtered_fundamentals.append(note)

        return {
            'filtered_fundamentals': filtered_fundamentals,
            'detected_chords': detected_chords,
            'detected_key': global_key,
            'correlation_timeline': correlation_timeline,
            'total_windows': len(time_windows),
            'filtering_stats': {
                'original_count': len(fundamentals),
                'filtered_count': len(filtered_fundamentals),
                'reduction': 1.0 - (len(filtered_fundamentals) / max(1, len(fundamentals)))
            }
        }

    def _group_by_time_windows(self, fundamentals: List[Dict]) -> List[Tuple[float, List[Dict]]]:
        """Group fundamentals into time windows."""
        if not fundamentals:
            return []

        # Sort by time
        sorted_notes = sorted(fundamentals, key=lambda n: n.get('time_seconds', 0))

        windows = []
        current_window_start = sorted_notes[0].get('time_seconds', 0)
        current_window_notes = []

        for note in sorted_notes:
            note_time = note.get('time_seconds', 0)

            if note_time - current_window_start <= self.time_window_seconds:
                # Same window
                current_window_notes.append(note)
            else:
                # New window
                if current_window_notes:
                    windows.append((current_window_start, current_window_notes))

                current_window_start = note_time
                current_window_notes = [note]

        # Add last window
        if current_window_notes:
            windows.append((current_window_start, current_window_notes))

        return windows

    def _detect_key(self, fundamentals: List[Dict]) -> Optional[str]:
        """
        Detect musical key from pitch histogram.

        Uses Krumhansl-Schmuckler algorithm.
        """
        # Build pitch class histogram
        pitch_classes = [self._note_to_pitch_class(n['note']) for n in fundamentals]
        histogram = np.bincount(pitch_classes, minlength=12)

        if histogram.sum() == 0:
            return None

        # Normalize
        histogram = histogram / histogram.sum()

        # Score all keys
        best_key = None
        best_score = -1

        for key_node in self.theory_graph.theory_graph.nodes():
            if self.theory_graph.theory_graph.nodes[key_node].get('type') == 'key':
                score = self.theory_graph._score_key(key_node, histogram * len(fundamentals))

                if score > best_score:
                    best_score = score
                    best_key = key_node

        return best_key if best_score > 0.3 else None

    def _note_to_pitch_class(self, note_name: str) -> int:
        """Convert note name to pitch class (0-11)."""
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
            'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10
        }

        # Extract pitch class (remove octave)
        pitch_class_name = ''.join(c for c in note_name if not c.isdigit())
        return note_map.get(pitch_class_name, 0)

    def _get_chord_pitch_classes(self, chord_name: str) -> List[int]:
        """Get pitch classes for a chord (e.g., 'C_major' -> [0, 4, 7])."""
        if not chord_name or '_' not in chord_name:
            return []

        parts = chord_name.split('_')
        if len(parts) < 2:
            return []

        root = parts[0]
        chord_type = '_'.join(parts[1:])

        # Get root pitch class
        root_pc = self._note_to_pitch_class(root)

        # Get intervals for chord type
        intervals = self.chord_templates.get(chord_type, [])

        # Calculate pitch classes
        return [(root_pc + interval) % 12 for interval in intervals]

    def _get_key_pitch_classes(self, key_name: str) -> List[int]:
        """Get pitch classes for a key scale."""
        if not key_name:
            return list(range(12))  # Return all if unknown

        # Major scale intervals
        major_intervals = [0, 2, 4, 5, 7, 9, 11]
        # Minor scale intervals
        minor_intervals = [0, 2, 3, 5, 7, 8, 10]

        parts = key_name.split('_')
        if len(parts) < 2:
            return list(range(12))

        root = parts[0]
        mode = parts[1]

        root_pc = self._note_to_pitch_class(root)
        intervals = major_intervals if mode == 'major' else minor_intervals

        return [(root_pc + interval) % 12 for interval in intervals]

    def visualize_analysis(self, analysis_results: Dict, output_path: str = 'chord_analysis.png'):
        """
        Visualize chord recognition results over time.

        Shows:
        - Detected chords timeline
        - Theory correlation scores
        - Filtering effectiveness
        """
        import matplotlib.pyplot as plt

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))

        timeline = analysis_results['correlation_timeline']
        if not timeline:
            return

        times = [t['time'] for t in timeline]
        chord_scores = [t['chord_score'] for t in timeline]
        key_correlations = [t['key_correlation'] for t in timeline]
        num_notes = [t['num_notes'] for t in timeline]

        # Plot 1: Chord correlation over time
        ax1.plot(times, chord_scores, 'b-', linewidth=2)
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Chord Correlation Score')
        ax1.set_title('Chord Recognition Confidence Over Time')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0.5, color='r', linestyle='--', label='Threshold')
        ax1.legend()

        # Plot 2: Key correlation over time
        ax2.plot(times, key_correlations, 'g-', linewidth=2)
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Key Correlation Score')
        ax2.set_title(f"Key Correlation ({analysis_results.get('detected_key', 'Unknown')})")
        ax2.grid(True, alpha=0.3)

        # Plot 3: Number of notes per window
        ax3.bar(times, num_notes, width=self.time_window_seconds, alpha=0.7)
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Notes Detected')
        ax3.set_title('Note Density Over Time')
        ax3.grid(True, alpha=0.3)

        # Plot 4: Filtering statistics
        stats = analysis_results['filtering_stats']
        categories = ['Original', 'Filtered']
        counts = [stats['original_count'], stats['filtered_count']]
        colors = ['red', 'green']

        ax4.bar(categories, counts, color=colors, alpha=0.7)
        ax4.set_ylabel('Number of Notes')
        ax4.set_title(f"Filtering Results ({stats['reduction']*100:.1f}% reduced)")

        for i, count in enumerate(counts):
            ax4.text(i, count, str(count), ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(output_path)
        print(f"Saved chord analysis visualization to {output_path}")

        return fig

    def get_statistics(self, analysis_results: Dict) -> Dict:
        """Get detailed statistics about the analysis."""
        return {
            'detected_key': analysis_results.get('detected_key'),
            'num_chords': len(analysis_results.get('detected_chords', [])),
            'filtering_stats': analysis_results.get('filtering_stats', {}),
            'avg_chord_score': np.mean([t['chord_score']
                                       for t in analysis_results.get('correlation_timeline', [])])
                              if analysis_results.get('correlation_timeline') else 0,
            'time_coverage': len(analysis_results.get('correlation_timeline', [])) *
                            self.time_window_seconds
        }
