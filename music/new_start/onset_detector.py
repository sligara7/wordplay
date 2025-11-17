"""
Onset Detector - Detects note onsets using temporal flow analysis

This module analyzes the audio graph to identify when notes begin (onsets),
how long they're sustained (duration), and how loud they are (velocity).
Uses temporal intensity derivatives to detect attack phase of notes.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


def frequency_to_midi_note(frequency: float) -> int:
    """
    Convert frequency in Hz to MIDI note number.

    Uses the standard MIDI tuning formula with A4 = 440 Hz = MIDI note 69.

    Args:
        frequency: Frequency in Hz

    Returns:
        MIDI note number (0-127)
    """
    if frequency <= 0:
        return 0

    # Formula: note = 69 + 12 * log2(frequency / 440)
    note = 69 + 12 * np.log2(frequency / 440.0)
    note_int = int(round(note))

    # Clamp to valid MIDI range
    return max(0, min(127, note_int))


class OnsetDetector:
    """
    Detects note onsets using temporal flow analysis on the audio graph.

    Analyzes intensity changes over time to identify when notes begin (attack phase),
    estimates how long they're sustained, and calculates MIDI velocity from intensity.
    """

    def __init__(self, graph: nx.MultiDiGraph, onset_threshold: float = 0.3,
                 min_onset_gap_seconds: float = 0.05):
        """
        Initialize onset detector with audio graph.

        Args:
            graph: Audio graph from AudioGraphBuilder with temporal edges
            onset_threshold: Minimum intensity increase to qualify as onset (default: 0.3)
            min_onset_gap_seconds: Minimum time between onsets in seconds (default: 0.05 = 50ms)
        """
        self.graph = graph
        self.onset_threshold = onset_threshold
        self.min_onset_gap_seconds = min_onset_gap_seconds

        # Extract sample rate and window length from graph metadata if available
        self.sample_rate = graph.graph.get('sample_rate', 44100)
        self.window_length = graph.graph.get('window_length', 2048)

        # Calculate time per sample
        self.seconds_per_sample = self.window_length / self.sample_rate

    def calculate_intensity_derivatives(self, freq_idx: int) -> List[Tuple[int, float]]:
        """
        Calculate temporal intensity derivatives for a frequency.

        Analyzes how intensity changes over time by computing derivatives
        along temporal edges in the graph.

        Args:
            freq_idx: Frequency index to analyze

        Returns:
            List of (time_index, derivative) tuples
        """
        derivatives = []

        # Find all nodes for this frequency across time
        freq_nodes = [n for n in self.graph.nodes()
                      if self.graph.nodes[n].get('freq_idx') == freq_idx]

        if not freq_nodes:
            return derivatives

        # Sort by time index
        freq_nodes_sorted = sorted(freq_nodes,
                                    key=lambda n: self.graph.nodes[n].get('time_idx', 0))

        # Calculate derivatives between consecutive time samples
        for i in range(len(freq_nodes_sorted) - 1):
            node_current = freq_nodes_sorted[i]
            node_next = freq_nodes_sorted[i + 1]

            intensity_current = self.graph.nodes[node_current].get('intensity', 0)
            intensity_next = self.graph.nodes[node_next].get('intensity', 0)
            time_idx = self.graph.nodes[node_next].get('time_idx', 0)

            # Calculate derivative (change in intensity per time sample)
            derivative = intensity_next - intensity_current

            derivatives.append((time_idx, derivative))

        return derivatives

    def detect_onsets_for_frequency(self, freq_idx: int, frequency: float) -> List[Dict]:
        """
        Detect all onsets for a specific frequency.

        Finds peaks in the intensity derivative that exceed the onset threshold,
        indicating the attack phase of a note.

        Args:
            freq_idx: Frequency index
            frequency: Actual frequency in Hz

        Returns:
            List of onset dictionaries with time_sample, time_seconds, intensity, frequency
        """
        derivatives = self.calculate_intensity_derivatives(freq_idx)

        if not derivatives:
            return []

        onsets = []
        min_gap_samples = int(self.min_onset_gap_seconds / self.seconds_per_sample)

        # Find peaks in derivatives (positive changes exceeding threshold)
        for time_idx, derivative in derivatives:
            if derivative > self.onset_threshold:
                # Check if this onset is far enough from previous onset
                if onsets and (time_idx - onsets[-1]['time_sample']) < min_gap_samples:
                    # Too close to previous onset, skip
                    continue

                # Find the node at this time index to get intensity
                node = None
                for n in self.graph.nodes():
                    if (self.graph.nodes[n].get('freq_idx') == freq_idx and
                        self.graph.nodes[n].get('time_idx') == time_idx):
                        node = n
                        break

                if node:
                    intensity = self.graph.nodes[node].get('intensity', 0)
                    time_seconds = time_idx * self.seconds_per_sample

                    onsets.append({
                        'time_sample': time_idx,
                        'time_seconds': time_seconds,
                        'intensity': intensity,
                        'frequency': frequency,
                        'freq_idx': freq_idx
                    })

        return onsets

    def estimate_note_duration(self, freq_idx: int, onset_time_idx: int) -> float:
        """
        Estimate how long a note is held after onset.

        Follows temporal edges forward from the onset to find when intensity
        drops below a threshold, indicating the end of the note.

        Args:
            freq_idx: Frequency index
            onset_time_idx: Time index of onset

        Returns:
            Duration in seconds
        """
        # Find all nodes for this frequency
        freq_nodes = [n for n in self.graph.nodes()
                      if self.graph.nodes[n].get('freq_idx') == freq_idx]

        # Sort by time
        freq_nodes_sorted = sorted(freq_nodes,
                                    key=lambda n: self.graph.nodes[n].get('time_idx', 0))

        # Find onset node
        onset_idx_in_list = None
        for i, node in enumerate(freq_nodes_sorted):
            if self.graph.nodes[node].get('time_idx') == onset_time_idx:
                onset_idx_in_list = i
                break

        if onset_idx_in_list is None:
            # Default duration if onset not found
            return 0.25  # 250ms default

        # Get onset intensity
        onset_node = freq_nodes_sorted[onset_idx_in_list]
        onset_intensity = self.graph.nodes[onset_node].get('intensity', 0)

        # Define offset threshold (when note ends)
        offset_threshold = onset_intensity * 0.3  # 30% of onset intensity

        # Follow forward in time to find offset
        offset_time_idx = onset_time_idx
        for i in range(onset_idx_in_list + 1, len(freq_nodes_sorted)):
            node = freq_nodes_sorted[i]
            intensity = self.graph.nodes[node].get('intensity', 0)

            if intensity < offset_threshold:
                # Found offset
                offset_time_idx = self.graph.nodes[node].get('time_idx', onset_time_idx)
                break
        else:
            # Note sustained until end, use last time index
            if freq_nodes_sorted:
                offset_time_idx = self.graph.nodes[freq_nodes_sorted[-1]].get('time_idx',
                                                                                onset_time_idx)

        # Calculate duration
        duration_samples = offset_time_idx - onset_time_idx
        duration_seconds = duration_samples * self.seconds_per_sample

        # Ensure minimum duration (50ms for very short notes)
        return max(0.05, duration_seconds)

    def intensity_to_velocity(self, intensity: float) -> int:
        """
        Convert normalized intensity to MIDI velocity.

        Applies a non-linear curve to map intensity to musically meaningful
        dynamics (velocity values).

        Args:
            intensity: Normalized intensity [0, 1]

        Returns:
            MIDI velocity (0-127)
        """
        # Apply non-linear curve for more musical dynamics
        # Use square root to compress high intensities
        if intensity <= 0:
            return 1  # ppp (very soft)

        # Square root curve gives better dynamic range
        velocity_float = 127.0 * np.sqrt(min(1.0, intensity))

        # Ensure minimum velocity for audible notes
        velocity = int(round(velocity_float))
        velocity = max(1, min(127, velocity))

        return velocity

    def detect_onsets(self, fundamentals: List[Dict]) -> List[Dict]:
        """
        Main method to detect onsets from fundamental notes.

        Groups fundamentals by frequency, detects onsets for each frequency,
        estimates duration, calculates velocity, and creates note events.

        Args:
            fundamentals: Fundamental notes from HarmonicAnalyzer with keys:
                         node_id, frequency, note, intensity, time_seconds, confidence

        Returns:
            List of note events with keys:
                onset_time_seconds, duration_seconds, velocity, note_name, midi_note
        """
        if not fundamentals:
            return []

        # Group fundamentals by frequency (freq_idx)
        freq_groups = defaultdict(list)
        for fund in fundamentals:
            freq_idx = self.graph.nodes[fund['node_id']].get('freq_idx')
            if freq_idx is not None:
                freq_groups[freq_idx].append(fund)

        note_events = []

        # Process each frequency
        for freq_idx, fund_list in freq_groups.items():
            # Get representative frequency from first fundamental
            if not fund_list:
                continue

            frequency = fund_list[0]['frequency']
            note_name = fund_list[0]['note']

            # Detect onsets for this frequency
            onsets = self.detect_onsets_for_frequency(freq_idx, frequency)

            # Create note events from onsets
            for onset in onsets:
                # Estimate duration
                duration = self.estimate_note_duration(freq_idx, onset['time_sample'])

                # Calculate velocity from intensity
                velocity = self.intensity_to_velocity(onset['intensity'])

                # Convert frequency to MIDI note number
                midi_note = frequency_to_midi_note(frequency)

                # Create note event
                note_event = {
                    'onset_time_seconds': onset['time_seconds'],
                    'duration_seconds': duration,
                    'velocity': velocity,
                    'note_name': note_name,
                    'midi_note': midi_note,
                    'frequency': frequency
                }

                note_events.append(note_event)

        # Sort by onset time
        note_events.sort(key=lambda x: x['onset_time_seconds'])

        return note_events

    def get_statistics(self) -> Dict:
        """
        Get statistics about detected onsets.

        Returns:
            Dictionary with onset statistics
        """
        # This is a placeholder for future statistics tracking
        return {
            'onset_threshold': self.onset_threshold,
            'min_onset_gap_seconds': self.min_onset_gap_seconds,
            'sample_rate': self.sample_rate,
            'seconds_per_sample': self.seconds_per_sample
        }
