"""
Unit tests for OnsetDetector

Tests onset detection, duration estimation, and velocity conversion.
"""

import unittest
import networkx as nx
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from onset_detector import OnsetDetector, frequency_to_midi_note


class TestFrequencyToMidiNote(unittest.TestCase):
    """Test frequency to MIDI note conversion."""

    def test_a4_equals_69(self):
        """A4 (440 Hz) should be MIDI note 69."""
        self.assertEqual(frequency_to_midi_note(440.0), 69)

    def test_middle_c(self):
        """Middle C (261.63 Hz) should be MIDI note 60."""
        # C4 = 261.63 Hz
        self.assertEqual(frequency_to_midi_note(261.63), 60)

    def test_c5(self):
        """C5 (523.25 Hz) should be MIDI note 72."""
        self.assertEqual(frequency_to_midi_note(523.25), 72)

    def test_clamp_low(self):
        """Very low frequencies should clamp to 0."""
        self.assertEqual(frequency_to_midi_note(1.0), 0)

    def test_clamp_high(self):
        """Very high frequencies should clamp to 127."""
        self.assertEqual(frequency_to_midi_note(20000.0), 127)


class TestOnsetDetector(unittest.TestCase):
    """Test OnsetDetector class."""

    def setUp(self):
        """Create a simple test graph."""
        self.graph = nx.MultiDiGraph()

        # Graph metadata
        self.graph.graph['sample_rate'] = 44100
        self.graph.graph['window_length'] = 2048

        # Create a simple temporal sequence for frequency index 10
        # Simulates a note onset: intensity jumps from 0.1 to 0.8
        freq_idx = 10
        frequency = 440.0  # A4

        # Time samples: 0, 1, 2, 3, 4, 5
        # Intensity:    0.1, 0.2, 0.8, 0.7, 0.6, 0.3 (onset at t=2)
        intensities = [0.1, 0.2, 0.8, 0.7, 0.6, 0.3]

        for time_idx, intensity in enumerate(intensities):
            node_id = f"node_{freq_idx}_{time_idx}"
            self.graph.add_node(
                node_id,
                freq_idx=freq_idx,
                time_idx=time_idx,
                frequency=frequency,
                intensity=intensity,
                note='A4'
            )

    def test_initialization(self):
        """Test OnsetDetector initialization."""
        detector = OnsetDetector(self.graph)

        self.assertEqual(detector.onset_threshold, 0.3)
        self.assertEqual(detector.min_onset_gap_seconds, 0.05)
        self.assertEqual(detector.sample_rate, 44100)
        self.assertEqual(detector.window_length, 2048)

    def test_calculate_intensity_derivatives(self):
        """Test intensity derivative calculation."""
        detector = OnsetDetector(self.graph)

        derivatives = detector.calculate_intensity_derivatives(freq_idx=10)

        # Should have 5 derivatives (6 nodes - 1)
        self.assertEqual(len(derivatives), 5)

        # Check that derivatives are calculated correctly
        # From 0.1 to 0.2: derivative = 0.1
        # From 0.2 to 0.8: derivative = 0.6 (should trigger onset)
        time_indices, derivative_values = zip(*derivatives)

        self.assertAlmostEqual(derivative_values[0], 0.1, places=6)
        self.assertAlmostEqual(derivative_values[1], 0.6, places=6)

    def test_detect_onsets_for_frequency(self):
        """Test onset detection for a single frequency."""
        detector = OnsetDetector(self.graph, onset_threshold=0.3)

        onsets = detector.detect_onsets_for_frequency(freq_idx=10, frequency=440.0)

        # Should detect one onset at time index 2 (derivative 0.6 > 0.3)
        self.assertEqual(len(onsets), 1)
        self.assertEqual(onsets[0]['time_sample'], 2)
        self.assertAlmostEqual(onsets[0]['intensity'], 0.8, places=6)

    def test_estimate_note_duration(self):
        """Test note duration estimation."""
        detector = OnsetDetector(self.graph)

        # Onset at time_idx=2, should decay to below 30% of 0.8 (=0.24) at time_idx=5 (0.3)
        duration = detector.estimate_note_duration(freq_idx=10, onset_time_idx=2)

        # Duration should be at least 50ms (minimum)
        self.assertGreater(duration, 0.0)

        # Should be approximately 3 samples worth of time
        expected_duration_approx = 3 * (2048 / 44100)
        self.assertGreater(duration, 0.05)  # At least 50ms

    def test_intensity_to_velocity(self):
        """Test intensity to velocity conversion."""
        detector = OnsetDetector(self.graph)

        # Test extremes
        self.assertEqual(detector.intensity_to_velocity(0.0), 1)  # Minimum
        self.assertEqual(detector.intensity_to_velocity(1.0), 127)  # Maximum

        # Test middle range
        vel_mid = detector.intensity_to_velocity(0.5)
        self.assertGreater(vel_mid, 60)
        self.assertLess(vel_mid, 100)

    def test_detect_onsets(self):
        """Test main onset detection method."""
        detector = OnsetDetector(self.graph, onset_threshold=0.3)

        # Create fundamentals list
        fundamentals = [
            {
                'node_id': 'node_10_2',
                'frequency': 440.0,
                'note': 'A4',
                'intensity': 0.8,
                'time_seconds': 0.1,
                'confidence': 0.9
            }
        ]

        note_events = detector.detect_onsets(fundamentals)

        # Should detect at least one note event
        self.assertGreater(len(note_events), 0)

        # Check note event structure
        event = note_events[0]
        self.assertIn('onset_time_seconds', event)
        self.assertIn('duration_seconds', event)
        self.assertIn('velocity', event)
        self.assertIn('note_name', event)
        self.assertIn('midi_note', event)

        # Check MIDI note is correct (A4 = 69)
        self.assertEqual(event['midi_note'], 69)


if __name__ == '__main__':
    unittest.main()
