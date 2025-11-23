"""
MIDI Parser Module

Responsibility: Read MIDI files and extract all event data

Input: MIDI file path
Output: Structured dict with notes, controllers, tempo changes, etc.
"""

import mido
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class MIDIParser:
    """
    Parse MIDI files into structured event data.

    Extracts:
    - Notes (on/off, velocity, duration)
    - Program changes
    - Controllers (CC messages)
    - Pitch bends
    - Tempo changes
    """

    def __init__(self):
        """Initialize MIDI parser."""
        pass

    def parse_file(self, midi_path: str) -> Dict:
        """
        Parse MIDI file and extract all events.

        Args:
            midi_path: Path to MIDI file

        Returns:
            Dict with:
                - notes: List of note events
                - program_changes: List of program change events
                - controllers: List of controller events
                - pitch_bends: List of pitch bend events
                - tempo_changes: List of tempo change events
                - duration: Total duration in seconds
                - initial_tempo_bpm: Starting tempo
                - ticks_per_beat: MIDI ticks per beat
        """
        midi_path = Path(midi_path)
        mid = mido.MidiFile(midi_path)

        # Extract tempo changes
        tempo_changes = self._extract_tempo_changes(mid)
        initial_tempo = tempo_changes[0][1] if tempo_changes else 500000
        initial_tempo_bpm = mido.tempo2bpm(initial_tempo)
        ticks_per_beat = mid.ticks_per_beat

        # Parse all events from all tracks
        notes = []
        program_changes = []
        controllers = []
        pitch_bends = []

        active_notes = {}  # Track note_on waiting for note_off

        for track_idx, track in enumerate(mid.tracks):
            current_tick = 0

            for msg in track:
                current_tick += msg.time

                # Convert to seconds
                time_seconds = self._tick_to_second(
                    current_tick, tempo_changes, ticks_per_beat
                )

                # Note events
                if msg.type == 'note_on' and msg.velocity > 0:
                    key = (msg.channel, msg.note)
                    active_notes[key] = {
                        'channel': msg.channel,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'start': time_seconds,
                        'track': track_idx
                    }

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        note_info = active_notes.pop(key)
                        note_info['duration'] = time_seconds - note_info['start']
                        notes.append(note_info)

                # Control change
                elif msg.type == 'control_change':
                    controllers.append({
                        'time': time_seconds,
                        'channel': msg.channel,
                        'controller': msg.control,
                        'value': msg.value
                    })

                # Pitch bend
                elif msg.type == 'pitchwheel':
                    pitch_bends.append({
                        'time': time_seconds,
                        'channel': msg.channel,
                        'pitch': msg.pitch
                    })

                # Program change
                elif msg.type == 'program_change':
                    program_changes.append({
                        'time': time_seconds,
                        'channel': msg.channel,
                        'program': msg.program
                    })

        # Calculate total duration
        duration = max(
            (n['start'] + n['duration'] for n in notes),
            default=0.0
        )

        return {
            'notes': notes,
            'program_changes': program_changes,
            'controllers': controllers,
            'pitch_bends': pitch_bends,
            'tempo_changes': tempo_changes,
            'duration': duration,
            'initial_tempo_bpm': initial_tempo_bpm,
            'ticks_per_beat': ticks_per_beat,
        }

    def _extract_tempo_changes(self, mid: mido.MidiFile) -> List[Tuple[int, int]]:
        """
        Extract all tempo changes from MIDI file.

        Returns:
            List of (tick, tempo_microseconds) tuples
        """
        tempo_changes = []

        for track in mid.tracks:
            current_tick = 0
            for msg in track:
                current_tick += msg.time
                if msg.type == 'set_tempo':
                    tempo_changes.append((current_tick, msg.tempo))

        # Sort by tick
        tempo_changes.sort(key=lambda x: x[0])

        # Ensure we have at least one tempo
        if not tempo_changes:
            tempo_changes = [(0, 500000)]  # Default 120 BPM

        return tempo_changes

    def _tick_to_second(self, tick: int,
                       tempo_changes: List[Tuple[int, int]],
                       tpb: int) -> float:
        """
        Convert MIDI ticks to seconds accounting for tempo changes.

        Args:
            tick: Current tick position
            tempo_changes: List of (tick, tempo_microseconds)
            tpb: Ticks per beat

        Returns:
            Time in seconds
        """
        if not tempo_changes:
            return mido.tick2second(tick, tpb, 500000)

        time_seconds = 0.0
        current_tick = 0
        current_tempo = tempo_changes[0][1]

        for i, (tempo_tick, tempo) in enumerate(tempo_changes):
            if tick <= tempo_tick:
                # Target is before this tempo change
                delta_ticks = tick - current_tick
                time_seconds += mido.tick2second(delta_ticks, tpb, current_tempo)
                return time_seconds
            else:
                # Add time up to this tempo change
                delta_ticks = tempo_tick - current_tick
                time_seconds += mido.tick2second(delta_ticks, tpb, current_tempo)
                current_tick = tempo_tick
                current_tempo = tempo

        # Add remaining time after last tempo change
        delta_ticks = tick - current_tick
        time_seconds += mido.tick2second(delta_ticks, tpb, current_tempo)

        return time_seconds
