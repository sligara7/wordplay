"""
MIDI Generator - Converts detected note events to standard MIDI files

This module takes note events from onset detection and creates standard MIDI
files that can be imported into DAWs (Logic, Ableton, MuseScore, etc.).
"""

import mido
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class MidiGenerator:
    """
    Generates standard MIDI files from detected note events.

    Handles MIDI file structure, timing conversion, tempo/time signature,
    and metadata. Creates MIDI files compatible with all standard DAWs.
    """

    def __init__(self, tempo: int = 120, time_signature: Tuple[int, int] = (4, 4),
                 ticks_per_beat: int = 480):
        """
        Initialize MIDI generator with tempo and time signature.

        Args:
            tempo: Tempo in BPM (beats per minute), default: 120
            time_signature: Time signature as (numerator, denominator), default: (4, 4)
            ticks_per_beat: MIDI resolution in ticks per quarter note, default: 480
        """
        self.tempo = tempo
        self.time_signature = time_signature
        self.ticks_per_beat = ticks_per_beat

    def note_name_to_midi_number(self, note_name: str) -> int:
        """
        Convert note name (e.g., 'C4', 'A#3', 'Bb5') to MIDI note number.

        Args:
            note_name: Note name like 'C4', 'A#3', 'Bb5'

        Returns:
            MIDI note number (0-127)
        """
        # Map note names to semitones
        note_map = {
            'C': 0, 'C#': 1, 'Db': 1,
            'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4,
            'F': 5, 'F#': 6, 'Gb': 6,
            'G': 7, 'G#': 8, 'Ab': 8,
            'A': 9, 'A#': 10, 'Bb': 10,
            'B': 11
        }

        # Parse note name and octave
        note_name = note_name.strip()

        # Extract octave (last character should be digit)
        if not note_name or not note_name[-1].isdigit():
            raise ValueError(f"Invalid note name: {note_name}")

        octave = int(note_name[-1])
        note = note_name[:-1]

        # Look up semitone
        if note not in note_map:
            raise ValueError(f"Invalid note: {note}")

        semitone = note_map[note]

        # Calculate MIDI number: (octave + 1) * 12 + semitone
        # MIDI standard: C-1 = 0, C0 = 12, C1 = 24, ..., C4 (middle C) = 60
        midi_number = (octave + 1) * 12 + semitone

        # Clamp to valid MIDI range
        return max(0, min(127, midi_number))

    def seconds_to_ticks(self, seconds: float) -> int:
        """
        Convert time in seconds to MIDI ticks.

        Args:
            seconds: Time in seconds

        Returns:
            Time in MIDI ticks
        """
        # Calculate ticks per second
        # tempo is in BPM (beats per minute)
        # ticks_per_beat is MIDI resolution
        beats_per_second = self.tempo / 60.0
        ticks_per_second = beats_per_second * self.ticks_per_beat

        ticks = seconds * ticks_per_second

        return int(round(ticks))

    def create_midi_track(self, note_events: List[Dict]) -> mido.MidiTrack:
        """
        Create a MIDI track from note events.

        Converts note events to MIDI note_on and note_off messages with
        proper timing (delta times).

        Args:
            note_events: Note events from OnsetDetector with keys:
                        onset_time_seconds, duration_seconds, velocity,
                        note_name, midi_note

        Returns:
            mido.MidiTrack with note on/off events
        """
        track = mido.MidiTrack()

        # Create a list of MIDI events (note on/off) with absolute times
        midi_events = []

        for note_event in note_events:
            # Get MIDI note number
            if 'midi_note' in note_event:
                midi_note = note_event['midi_note']
            elif 'note_name' in note_event:
                midi_note = self.note_name_to_midi_number(note_event['note_name'])
            else:
                raise ValueError("Note event must have 'midi_note' or 'note_name'")

            # Get timing
            onset_time = note_event.get('onset_time_seconds',
                                        note_event.get('onset_time', 0))
            duration = note_event.get('duration_seconds',
                                      note_event.get('duration', 0.25))
            velocity = note_event.get('velocity', 64)

            # Convert to ticks
            onset_ticks = self.seconds_to_ticks(onset_time)
            offset_ticks = self.seconds_to_ticks(onset_time + duration)

            # Add note_on event
            midi_events.append({
                'time': onset_ticks,
                'type': 'note_on',
                'note': midi_note,
                'velocity': velocity
            })

            # Add note_off event
            midi_events.append({
                'time': offset_ticks,
                'type': 'note_off',
                'note': midi_note,
                'velocity': 0
            })

        # Sort events by time
        midi_events.sort(key=lambda x: x['time'])

        # Convert absolute times to delta times and add to track
        current_time = 0
        for event in midi_events:
            delta_time = event['time'] - current_time
            current_time = event['time']

            if event['type'] == 'note_on':
                track.append(mido.Message('note_on',
                                          note=event['note'],
                                          velocity=event['velocity'],
                                          time=delta_time))
            elif event['type'] == 'note_off':
                track.append(mido.Message('note_off',
                                          note=event['note'],
                                          velocity=event['velocity'],
                                          time=delta_time))

        return track

    def add_metadata(self, track: mido.MidiTrack,
                     key_signature: Optional[str] = None):
        """
        Add metadata to MIDI track (tempo, time signature, key).

        Inserts meta messages at the beginning of the track.

        Args:
            track: MIDI track to add metadata to
            key_signature: Optional key signature (e.g., 'C major', 'A minor')
        """
        # Metadata should be inserted at the beginning
        # We'll insert in reverse order so they end up in correct order

        # Add track name
        track.insert(0, mido.MetaMessage('track_name',
                                         name='Transcribed Audio',
                                         time=0))

        # Add time signature
        track.insert(0, mido.MetaMessage('time_signature',
                                         numerator=self.time_signature[0],
                                         denominator=self.time_signature[1],
                                         time=0))

        # Add tempo (convert BPM to microseconds per beat)
        microseconds_per_beat = int(60_000_000 / self.tempo)
        track.insert(0, mido.MetaMessage('set_tempo',
                                         tempo=microseconds_per_beat,
                                         time=0))

        # Add key signature if provided
        if key_signature:
            # Parse key signature (simplified - just sets to C major by default)
            # Full implementation would parse 'C major', 'A minor', etc.
            track.insert(0, mido.MetaMessage('key_signature',
                                             key='C',
                                             time=0))

    def validate_note_events(self, note_events: List[Dict]) -> bool:
        """
        Validate that note events have required fields.

        Args:
            note_events: Note events to validate

        Returns:
            True if valid

        Raises:
            ValueError: If note events are invalid
        """
        if not note_events:
            raise ValueError("No note events provided")

        required_fields_sets = [
            {'onset_time_seconds', 'duration_seconds', 'velocity'},
            {'onset_time', 'duration', 'velocity'}
        ]

        for i, event in enumerate(note_events):
            # Check if event has required time/duration fields
            has_valid_fields = any(
                all(field in event for field in fields)
                for fields in required_fields_sets
            )

            if not has_valid_fields:
                raise ValueError(
                    f"Note event {i} missing required fields. "
                    f"Need (onset_time_seconds, duration_seconds, velocity) "
                    f"or (onset_time, duration, velocity). Got: {list(event.keys())}"
                )

            # Check if event has note information
            if 'midi_note' not in event and 'note_name' not in event:
                raise ValueError(
                    f"Note event {i} missing note information. "
                    f"Need 'midi_note' or 'note_name'"
                )

            # Validate velocity range
            velocity = event.get('velocity', 64)
            if not (0 <= velocity <= 127):
                raise ValueError(
                    f"Note event {i} has invalid velocity {velocity}. "
                    f"Must be 0-127"
                )

        return True

    def generate_midi(self, note_events: List[Dict], output_path: str,
                      key_signature: Optional[str] = None) -> str:
        """
        Main method to generate MIDI file from note events.

        Creates a complete MIDI file with proper structure, timing,
        tempo, time signature, and metadata.

        Args:
            note_events: Note events from onset detector
            output_path: Path to save MIDI file (e.g., 'output.mid')
            key_signature: Optional key signature (e.g., 'C major')

        Returns:
            Path to created MIDI file

        Raises:
            ValueError: If note events are invalid
        """
        # Validate note events
        self.validate_note_events(note_events)

        # Create MIDI file (type 1 = one or more tracks, synchronous)
        midi_file = mido.MidiFile(type=1, ticks_per_beat=self.ticks_per_beat)

        # Create track from note events
        track = self.create_midi_track(note_events)

        # Add metadata to track
        self.add_metadata(track, key_signature)

        # Add end of track message
        track.append(mido.MetaMessage('end_of_track', time=0))

        # Add track to MIDI file
        midi_file.tracks.append(track)

        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save MIDI file
        midi_file.save(output_path)

        return str(output_path_obj)
