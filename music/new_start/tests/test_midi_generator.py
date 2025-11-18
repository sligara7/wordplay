"""
Unit tests for MidiGenerator

Tests MIDI file creation, note conversion, and timing.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from midi_generator import MidiGenerator
import mido


class TestMidiGenerator(unittest.TestCase):
    """Test MidiGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = MidiGenerator(tempo=120, time_signature=(4, 4))

    def test_initialization(self):
        """Test MidiGenerator initialization."""
        self.assertEqual(self.generator.tempo, 120)
        self.assertEqual(self.generator.time_signature, (4, 4))
        self.assertEqual(self.generator.ticks_per_beat, 480)

    def test_note_name_to_midi_number(self):
        """Test note name to MIDI number conversion."""
        # Middle C (C4)
        self.assertEqual(self.generator.note_name_to_midi_number('C4'), 60)

        # A4 (standard tuning reference)
        self.assertEqual(self.generator.note_name_to_midi_number('A4'), 69)

        # C5
        self.assertEqual(self.generator.note_name_to_midi_number('C5'), 72)

        # Sharps
        self.assertEqual(self.generator.note_name_to_midi_number('C#4'), 61)
        self.assertEqual(self.generator.note_name_to_midi_number('A#4'), 70)

        # Flats
        self.assertEqual(self.generator.note_name_to_midi_number('Db4'), 61)
        self.assertEqual(self.generator.note_name_to_midi_number('Bb4'), 70)

    def test_note_name_to_midi_number_invalid(self):
        """Test that invalid note names raise ValueError."""
        with self.assertRaises(ValueError):
            self.generator.note_name_to_midi_number('H4')  # Invalid note

        with self.assertRaises(ValueError):
            self.generator.note_name_to_midi_number('C')  # Missing octave

        with self.assertRaises(ValueError):
            self.generator.note_name_to_midi_number('')  # Empty string

    def test_seconds_to_ticks(self):
        """Test time conversion from seconds to MIDI ticks."""
        # At 120 BPM with 480 ticks_per_beat:
        # beats_per_second = 120 / 60 = 2
        # ticks_per_second = 2 * 480 = 960

        # 1 second should be 960 ticks
        self.assertEqual(self.generator.seconds_to_ticks(1.0), 960)

        # 0.5 seconds should be 480 ticks
        self.assertEqual(self.generator.seconds_to_ticks(0.5), 480)

        # 0 seconds should be 0 ticks
        self.assertEqual(self.generator.seconds_to_ticks(0.0), 0)

    def test_create_midi_track(self):
        """Test MIDI track creation from note events."""
        note_events = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 0.5,
                'velocity': 80,
                'note_name': 'C4',
                'midi_note': 60
            },
            {
                'onset_time_seconds': 0.5,
                'duration_seconds': 0.5,
                'velocity': 70,
                'note_name': 'E4',
                'midi_note': 64
            }
        ]

        track = self.generator.create_midi_track(note_events)

        # Track should have messages
        self.assertGreater(len(track), 0)

        # Count note_on and note_off messages
        note_on_count = sum(1 for msg in track if msg.type == 'note_on')
        note_off_count = sum(1 for msg in track if msg.type == 'note_off')

        # Should have 2 note_on and 2 note_off messages
        self.assertEqual(note_on_count, 2)
        self.assertEqual(note_off_count, 2)

    def test_validate_note_events_valid(self):
        """Test that valid note events pass validation."""
        valid_events = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 0.5,
                'velocity': 80,
                'midi_note': 60
            }
        ]

        # Should not raise
        result = self.generator.validate_note_events(valid_events)
        self.assertTrue(result)

    def test_validate_note_events_invalid(self):
        """Test that invalid note events raise ValueError."""
        # Missing duration
        invalid_events = [
            {
                'onset_time_seconds': 0.0,
                'velocity': 80,
                'midi_note': 60
            }
        ]

        with self.assertRaises(ValueError):
            self.generator.validate_note_events(invalid_events)

        # Missing note information
        invalid_events2 = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 0.5,
                'velocity': 80
            }
        ]

        with self.assertRaises(ValueError):
            self.generator.validate_note_events(invalid_events2)

        # Invalid velocity
        invalid_events3 = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 0.5,
                'velocity': 200,  # > 127
                'midi_note': 60
            }
        ]

        with self.assertRaises(ValueError):
            self.generator.validate_note_events(invalid_events3)

    def test_generate_midi_file(self):
        """Test complete MIDI file generation."""
        note_events = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 0.5,
                'velocity': 80,
                'note_name': 'C4',
                'midi_note': 60
            },
            {
                'onset_time_seconds': 0.5,
                'duration_seconds': 0.5,
                'velocity': 70,
                'note_name': 'E4',
                'midi_note': 64
            },
            {
                'onset_time_seconds': 1.0,
                'duration_seconds': 1.0,
                'velocity': 90,
                'note_name': 'G4',
                'midi_note': 67
            }
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Generate MIDI file
            output_path = self.generator.generate_midi(note_events, tmp_path)

            # File should exist
            self.assertTrue(os.path.exists(output_path))

            # File should be readable by mido
            midi_file = mido.MidiFile(output_path)

            # Should have at least one track
            self.assertGreater(len(midi_file.tracks), 0)

            # Check tempo is set correctly
            # tempo meta message uses microseconds per beat
            tempo_msgs = [msg for msg in midi_file.tracks[0]
                          if msg.type == 'set_tempo']
            self.assertEqual(len(tempo_msgs), 1)

            # 120 BPM = 500000 microseconds per beat
            self.assertEqual(tempo_msgs[0].tempo, 500000)

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_generate_midi_with_key_signature(self):
        """Test MIDI file generation with key signature."""
        note_events = [
            {
                'onset_time_seconds': 0.0,
                'duration_seconds': 1.0,
                'velocity': 80,
                'midi_note': 60
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Generate with key signature
            self.generator.generate_midi(note_events, tmp_path,
                                         key_signature='C major')

            # File should be valid
            midi_file = mido.MidiFile(tmp_path)

            # Should have key signature meta message
            key_msgs = [msg for msg in midi_file.tracks[0]
                        if msg.type == 'key_signature']
            self.assertEqual(len(key_msgs), 1)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
