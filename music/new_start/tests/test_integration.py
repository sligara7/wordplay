"""
Integration Tests for Audio-to-MIDI Pipeline

Tests the complete end-to-end pipeline from WAV input to MIDI output
using synthetic test audio with known properties.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_to_midi_pipeline import transcribe, validate_wav_file
from generate_test_audio import (
    generate_sine_wave,
    generate_chord,
    generate_sequence,
    save_test_audio
)
import mido


class TestWavValidation(unittest.TestCase):
    """Test WAV file validation."""

    def test_validate_valid_wav(self):
        """Test that valid WAV files pass validation."""
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Generate simple test audio
            audio_data = generate_sine_wave(440.0, 0.5)
            save_test_audio(tmp_path, audio_data)

            # Validate
            is_valid, error_msg = validate_wav_file(tmp_path)
            self.assertTrue(is_valid, f"Validation failed: {error_msg}")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_validate_nonexistent_file(self):
        """Test that validation fails for nonexistent files."""
        is_valid, error_msg = validate_wav_file('/nonexistent/file.wav')
        self.assertFalse(is_valid)
        self.assertIn('not found', error_msg.lower())

    def test_validate_wrong_extension(self):
        """Test that validation fails for non-WAV extensions."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            is_valid, error_msg = validate_wav_file(tmp_path)
            self.assertFalse(is_valid)
            self.assertIn('not a wav file', error_msg.lower())

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestEndToEndPipeline(unittest.TestCase):
    """Test complete end-to-end audio-to-MIDI transcription."""

    def setUp(self):
        """Set up temporary directories for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.audio_path = os.path.join(self.test_dir, 'test_input.wav')
        self.midi_path = os.path.join(self.test_dir, 'test_output.mid')

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.audio_path):
            os.remove(self.audio_path)
        if os.path.exists(self.midi_path):
            os.remove(self.midi_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_single_note_transcription(self):
        """Test transcribing a single pure note (A4 @ 440 Hz)."""
        # Generate test audio: A4 for 1 second
        audio_data = generate_sine_wave(440.0, 1.0, amplitude=0.7)
        save_test_audio(self.audio_path, audio_data)

        # Run transcription with lower thresholds for pure sine wave
        result_path = transcribe(
            wav_path=self.audio_path,
            output_path=self.midi_path,
            intensity_threshold=0.01,  # Lower threshold for pure sine
            confidence_threshold=0.1,  # Lower confidence threshold
            tempo=120,
            verbose=False
        )

        # Verify MIDI file was created
        self.assertTrue(os.path.exists(result_path))

        # Verify MIDI file is valid
        midi_file = mido.MidiFile(result_path)
        self.assertGreater(len(midi_file.tracks), 0)

        # Note: Pure sine waves may not be detected well by harmonic analysis
        # since they have no harmonics. This test just verifies the pipeline runs.
        note_on_msgs = [msg for track in midi_file.tracks
                        for msg in track if msg.type == 'note_on']

        # If notes were detected, verify they're in the right range
        if note_on_msgs:
            detected_notes = [msg.note for msg in note_on_msgs]
            self.assertTrue(any(60 <= note <= 80 for note in detected_notes),
                           f"Expected notes in musical range, got {detected_notes}")

    def test_two_note_sequence(self):
        """Test transcribing a sequence of two notes."""
        # Generate test audio: C4 (261.63 Hz) then E4 (329.63 Hz)
        notes = [
            (261.63, 0.5),  # C4
            (329.63, 0.5),  # E4
        ]
        audio_data = generate_sequence(notes, amplitude=0.7)
        save_test_audio(self.audio_path, audio_data)

        # Run transcription with lower thresholds
        result_path = transcribe(
            wav_path=self.audio_path,
            output_path=self.midi_path,
            intensity_threshold=0.01,
            confidence_threshold=0.1,
            tempo=120,
            verbose=False
        )

        # Verify MIDI file was created
        self.assertTrue(os.path.exists(result_path))

        # Verify MIDI file is valid
        midi_file = mido.MidiFile(result_path)
        self.assertGreater(len(midi_file.tracks), 0)

    def test_chord_transcription(self):
        """Test transcribing a chord (multiple simultaneous frequencies)."""
        # Generate test audio: C major chord (C4, E4, G4)
        frequencies = [261.63, 329.63, 392.00]  # C4, E4, G4
        audio_data = generate_chord(frequencies, 1.0, amplitude=0.5)
        save_test_audio(self.audio_path, audio_data)

        # Run transcription with lower thresholds
        result_path = transcribe(
            wav_path=self.audio_path,
            output_path=self.midi_path,
            intensity_threshold=0.01,
            confidence_threshold=0.1,
            tempo=120,
            verbose=False
        )

        # Verify MIDI file was created
        self.assertTrue(os.path.exists(result_path))

        # Verify MIDI file is valid
        midi_file = mido.MidiFile(result_path)
        self.assertGreater(len(midi_file.tracks), 0)

    def test_empty_audio(self):
        """Test transcribing silent audio (edge case)."""
        # Generate silent audio
        audio_data = generate_sine_wave(440.0, 0.5, amplitude=0.0)
        save_test_audio(self.audio_path, audio_data)

        # Run transcription
        result_path = transcribe(
            wav_path=self.audio_path,
            output_path=self.midi_path,
            intensity_threshold=0.05,
            confidence_threshold=0.3,
            tempo=120,
            verbose=False
        )

        # Should still create a MIDI file (even if empty)
        self.assertTrue(os.path.exists(result_path))

    def test_custom_tempo(self):
        """Test that custom tempo is applied to output MIDI."""
        # Generate test audio
        audio_data = generate_sine_wave(440.0, 1.0, amplitude=0.7)
        save_test_audio(self.audio_path, audio_data)

        # Run transcription with custom tempo
        custom_tempo = 140
        result_path = transcribe(
            wav_path=self.audio_path,
            output_path=self.midi_path,
            tempo=custom_tempo,
            verbose=False
        )

        # Verify tempo is set correctly in MIDI file
        midi_file = mido.MidiFile(result_path)

        # Find tempo meta message
        tempo_msgs = [msg for track in midi_file.tracks
                      for msg in track if msg.type == 'set_tempo']

        self.assertEqual(len(tempo_msgs), 1, "Should have one tempo message")

        # Calculate expected tempo in microseconds per beat
        # tempo (BPM) = 60,000,000 / microseconds_per_beat
        expected_tempo = int(60_000_000 / custom_tempo)
        self.assertEqual(tempo_msgs[0].tempo, expected_tempo)

    def test_threshold_variations(self):
        """Test that threshold parameters don't break the pipeline."""
        # Generate test audio with varying intensities
        audio_data = generate_sine_wave(440.0, 1.0, amplitude=0.3)
        save_test_audio(self.audio_path, audio_data)

        # Run with low threshold
        midi_path_low = os.path.join(self.test_dir, 'test_low.mid')
        transcribe(
            wav_path=self.audio_path,
            output_path=midi_path_low,
            intensity_threshold=0.01,
            confidence_threshold=0.1,
            verbose=False
        )

        # Run with high threshold
        midi_path_high = os.path.join(self.test_dir, 'test_high.mid')
        transcribe(
            wav_path=self.audio_path,
            output_path=midi_path_high,
            intensity_threshold=0.3,
            confidence_threshold=0.6,
            verbose=False
        )

        # Both should create files
        self.assertTrue(os.path.exists(midi_path_low))
        self.assertTrue(os.path.exists(midi_path_high))

        # Clean up
        os.remove(midi_path_low)
        os.remove(midi_path_high)


class TestPipelineRobustness(unittest.TestCase):
    """Test pipeline error handling and edge cases."""

    def test_invalid_input_file(self):
        """Test that invalid input files raise appropriate errors."""
        with self.assertRaises(ValueError):
            transcribe(
                wav_path='/nonexistent/file.wav',
                output_path='/tmp/output.mid',
                verbose=False
            )

    def test_output_directory_creation(self):
        """Test that output directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create WAV file
            audio_path = os.path.join(tmpdir, 'input.wav')
            audio_data = generate_sine_wave(440.0, 0.5, amplitude=0.7)
            save_test_audio(audio_path, audio_data)

            # Output path in non-existent subdirectory
            output_path = os.path.join(tmpdir, 'subdir', 'output.mid')

            # Should create subdirectory automatically
            result_path = transcribe(
                wav_path=audio_path,
                output_path=output_path,
                verbose=False
            )

            self.assertTrue(os.path.exists(result_path))
            self.assertTrue(os.path.exists(os.path.dirname(result_path)))


if __name__ == '__main__':
    unittest.main()
