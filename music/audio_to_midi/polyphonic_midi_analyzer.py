#!/usr/bin/env python3
"""
Polyphonic MIDI Analyzer - Handle multi-track, multi-voice music structures.

This module treats music as a multi-layered graph system:
- Vertical dimension: Simultaneous notes (chords/structures)
- Horizontal dimension: Chord progressions and transitions
- Multi-track: Different instruments as separate layers
- Rhythmic patterns: Percussion and drum structures

Conceptual model:
- Chords are "mini-graphs" or structural units
- Chord progressions form higher-level graphs
- Each instrument/track is a separate layer
- Layers interact through shared timing and harmonic relationships
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import mido


@dataclass
class Chord:
    """Represents a chord (multiple simultaneous notes)."""
    pitches: Set[int]  # Set of MIDI pitches
    start_time: float
    duration: float
    channel: int

    def to_token(self, mode='pitch_set') -> str:
        """
        Convert chord to a token string.

        Args:
            mode: How to represent the chord
                - 'pitch_set': Sorted pitch names (e.g., 'C4_E4_G4')
                - 'chord_name': Music theory name (e.g., 'Cmaj')
                - 'intervals': Interval structure (e.g., 'M3_m3')
        """
        if mode == 'pitch_set':
            sorted_pitches = sorted(self.pitches)
            notes = [self._midi_to_note_name(p) for p in sorted_pitches]
            return '_'.join(notes)

        elif mode == 'chord_name':
            return self._identify_chord()

        elif mode == 'intervals':
            return self._get_interval_structure()

        return self.to_token('pitch_set')

    @staticmethod
    def _midi_to_note_name(pitch: int) -> str:
        """Convert MIDI pitch to note name."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = note_names[pitch % 12]
        return f"{note}{octave}"

    def _identify_chord(self) -> str:
        """
        Identify chord name using music theory.

        Returns chord symbol (e.g., 'Cmaj', 'Gmin7', 'Ddim')
        """
        if not self.pitches:
            return 'silence'

        if len(self.pitches) == 1:
            return self._midi_to_note_name(list(self.pitches)[0])

        # Get root (lowest note)
        sorted_pitches = sorted(self.pitches)
        root = sorted_pitches[0]
        root_name = self._midi_to_note_name(root).replace(str(root // 12 - 1), '')

        # Calculate intervals from root
        intervals = [(p - root) % 12 for p in sorted_pitches[1:]]
        intervals.sort()

        # Identify common chord types
        chord_patterns = {
            (4, 7): 'maj',          # Major triad
            (3, 7): 'min',          # Minor triad
            (3, 6): 'dim',          # Diminished
            (4, 8): 'aug',          # Augmented
            (4, 7, 10): 'maj7',     # Major 7th
            (4, 7, 11): '7',        # Dominant 7th
            (3, 7, 10): 'min7',     # Minor 7th
            (3, 6, 10): 'dim7',     # Diminished 7th
            (2, 7): 'sus2',         # Suspended 2nd
            (5, 7): 'sus4',         # Suspended 4th
        }

        intervals_tuple = tuple(intervals)
        chord_type = chord_patterns.get(intervals_tuple, 'chord')

        return f"{root_name}{chord_type}"

    def _get_interval_structure(self) -> str:
        """Get interval structure (e.g., 'M3_m3' for major triad)."""
        if len(self.pitches) <= 1:
            return 'single'

        sorted_pitches = sorted(self.pitches)
        intervals = []

        for i in range(len(sorted_pitches) - 1):
            interval = sorted_pitches[i + 1] - sorted_pitches[i]
            intervals.append(str(interval))

        return '_'.join(intervals)


@dataclass
class TrackStructure:
    """Represents the structure of a single MIDI track/instrument."""
    track_name: str
    channel: int
    instrument: int  # MIDI program number
    chords: List[Chord] = field(default_factory=list)
    is_percussion: bool = False


class PolyphonicMidiAnalyzer:
    """
    Analyze polyphonic MIDI files with multiple tracks and simultaneous notes.
    """

    def __init__(self,
                 chord_mode='chord_name',
                 time_quantization=120,  # Ticks (e.g., 120 = 16th note at 480 ppq)
                 merge_threshold=10):    # Ticks - notes within this are "simultaneous"
        """
        Initialize the polyphonic analyzer.

        Args:
            chord_mode: How to tokenize chords ('pitch_set', 'chord_name', 'intervals')
            time_quantization: Quantize timing to this resolution (in ticks)
            merge_threshold: Notes within this many ticks are considered simultaneous
        """
        self.chord_mode = chord_mode
        self.time_quantization = time_quantization
        self.merge_threshold = merge_threshold
        self.tracks: List[TrackStructure] = []
        self.tempo = 500000  # Default tempo (microseconds per quarter note)

    def parse_midi_file(self, file_path: str) -> List[TrackStructure]:
        """
        Parse a polyphonic MIDI file into multiple track structures.

        Args:
            file_path: Path to MIDI file

        Returns:
            List of TrackStructure objects (one per instrument/channel)
        """
        midi_file = mido.MidiFile(file_path)

        # Organize notes by track and channel
        track_events = defaultdict(lambda: defaultdict(list))  # [track_idx][channel] -> events
        track_names = {}
        instruments = {}

        for track_idx, track in enumerate(midi_file.tracks):
            current_time = 0
            track_name = f"Track_{track_idx}"

            for msg in track:
                current_time += msg.time

                # Get track name
                if msg.type == 'track_name':
                    track_name = msg.name
                    track_names[track_idx] = track_name

                # Get instrument
                if msg.type == 'program_change':
                    instruments[(track_idx, msg.channel)] = msg.program

                # Collect note events
                if msg.type in ['note_on', 'note_off']:
                    track_events[track_idx][msg.channel].append({
                        'type': msg.type,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'time': current_time,
                        'channel': msg.channel
                    })

        # Convert events to chord structures for each track/channel
        tracks = []

        for track_idx in track_events:
            for channel in track_events[track_idx]:
                events = track_events[track_idx][channel]

                # Determine if percussion (channel 9/10)
                is_percussion = (channel == 9)

                # Extract chords from events
                chords = self._extract_chords(events)

                track_structure = TrackStructure(
                    track_name=track_names.get(track_idx, f"Track_{track_idx}"),
                    channel=channel,
                    instrument=instruments.get((track_idx, channel), 0),
                    chords=chords,
                    is_percussion=is_percussion
                )

                tracks.append(track_structure)

        self.tracks = tracks
        return tracks

    def _extract_chords(self, events: List[Dict]) -> List[Chord]:
        """
        Extract chords from note events.

        Groups notes that occur within merge_threshold ticks as a single chord.
        """
        chords = []

        # Track active notes
        active_notes = {}  # note -> {'start_time': ..., 'velocity': ...}

        # Sort events by time
        events.sort(key=lambda e: e['time'])

        # Group events by quantized time
        time_slices = defaultdict(list)
        for event in events:
            quantized_time = (event['time'] // self.time_quantization) * self.time_quantization
            time_slices[quantized_time].append(event)

        # Process each time slice
        for time in sorted(time_slices.keys()):
            slice_events = time_slices[time]

            # Process note offs first
            for event in slice_events:
                if event['type'] == 'note_off' or (event['type'] == 'note_on' and event['velocity'] == 0):
                    if event['note'] in active_notes:
                        note_info = active_notes[event['note']]

                        # Create chord from this note
                        # (In full implementation, we'd group simultaneous notes)
                        chord = Chord(
                            pitches={event['note']},
                            start_time=note_info['start_time'],
                            duration=event['time'] - note_info['start_time'],
                            channel=event['channel']
                        )

                        del active_notes[event['note']]

            # Process note ons
            for event in slice_events:
                if event['type'] == 'note_on' and event['velocity'] > 0:
                    active_notes[event['note']] = {
                        'start_time': event['time'],
                        'velocity': event['velocity']
                    }

        # Group simultaneous notes into chords
        chords = self._group_into_chords(events)

        return chords

    def _group_into_chords(self, events: List[Dict]) -> List[Chord]:
        """Group simultaneous notes into chord objects."""
        # Track note on/off events
        note_events = defaultdict(dict)  # note -> {'on': time, 'off': time}

        for event in events:
            note = event['note']
            time = event['time']

            if event['type'] == 'note_on' and event['velocity'] > 0:
                if note not in note_events:
                    note_events[note] = {}
                note_events[note]['on'] = time
                note_events[note]['channel'] = event['channel']

            elif event['type'] == 'note_off' or (event['type'] == 'note_on' and event['velocity'] == 0):
                if note in note_events and 'on' in note_events[note]:
                    note_events[note]['off'] = time

        # Group notes that start at similar times
        time_groups = defaultdict(list)  # start_time -> [notes]

        for note, info in note_events.items():
            if 'on' in info and 'off' in info:
                quantized_start = (info['on'] // self.merge_threshold) * self.merge_threshold
                time_groups[quantized_start].append({
                    'note': note,
                    'start': info['on'],
                    'end': info['off'],
                    'channel': info['channel']
                })

        # Create chord objects
        chords = []
        for start_time in sorted(time_groups.keys()):
            notes_at_time = time_groups[start_time]

            if not notes_at_time:
                continue

            pitches = {n['note'] for n in notes_at_time}
            avg_start = sum(n['start'] for n in notes_at_time) / len(notes_at_time)
            avg_end = sum(n['end'] for n in notes_at_time) / len(notes_at_time)
            channel = notes_at_time[0]['channel']

            chord = Chord(
                pitches=pitches,
                start_time=avg_start,
                duration=avg_end - avg_start,
                channel=channel
            )
            chords.append(chord)

        return chords

    def get_track_tokens(self, track_idx: int) -> List[str]:
        """Get tokens for a specific track."""
        if track_idx >= len(self.tracks):
            return []

        track = self.tracks[track_idx]
        return [chord.to_token(self.chord_mode) for chord in track.chords]

    def get_all_track_tokens(self) -> Dict[str, List[str]]:
        """Get tokens for all tracks."""
        result = {}
        for i, track in enumerate(self.tracks):
            track_id = f"{track.track_name}_ch{track.channel}"
            result[track_id] = [chord.to_token(self.chord_mode) for chord in track.chords]

        return result

    def get_statistics(self) -> Dict:
        """Get statistics about the polyphonic structure."""
        stats = {
            'num_tracks': len(self.tracks),
            'tracks': []
        }

        for track in self.tracks:
            chord_tokens = [chord.to_token(self.chord_mode) for chord in track.chords]
            token_counts = Counter(chord_tokens)

            track_stats = {
                'name': track.track_name,
                'channel': track.channel,
                'instrument': track.instrument,
                'is_percussion': track.is_percussion,
                'num_chords': len(track.chords),
                'unique_chords': len(token_counts),
                'most_common_chords': token_counts.most_common(10)
            }
            stats['tracks'].append(track_stats)

        return stats

    def export_track_tokens(self, output_dir: str):
        """
        Export tokens for each track to separate files.

        Creates one file per track, allowing separate graph analysis.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, track in enumerate(self.tracks):
            tokens = [chord.to_token(self.chord_mode) for chord in track.chords]

            # Create filename
            track_name = track.track_name.replace(' ', '_').replace('/', '_')
            filename = f"{track_name}_ch{track.channel}.txt"
            filepath = output_path / filename

            # Write tokens
            with open(filepath, 'w') as f:
                f.write(' '.join(tokens))

            print(f"Exported {len(tokens)} tokens to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze polyphonic MIDI files with multiple tracks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze with chord names
  python3 src/polyphonic_midi_analyzer.py music/song.mid -o music/tracks/ -m chord_name

  # Analyze with pitch sets
  python3 src/polyphonic_midi_analyzer.py music/song.mid -o music/tracks/ -m pitch_set

  # View statistics only
  python3 src/polyphonic_midi_analyzer.py music/song.mid --stats-only
        """
    )

    parser.add_argument('midi_file', help='Path to MIDI file')
    parser.add_argument('-o', '--output', help='Output directory for track tokens')
    parser.add_argument(
        '-m', '--mode',
        choices=['pitch_set', 'chord_name', 'intervals'],
        default='chord_name',
        help='Chord tokenization mode (default: chord_name)'
    )
    parser.add_argument(
        '--quantize',
        type=int,
        default=120,
        help='Time quantization in ticks (default: 120)'
    )
    parser.add_argument(
        '--merge-threshold',
        type=int,
        default=10,
        help='Threshold for merging simultaneous notes (default: 10 ticks)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only print statistics, do not export'
    )

    args = parser.parse_args()

    # Validate input
    if not Path(args.midi_file).exists():
        print(f"Error: MIDI file not found: {args.midi_file}")
        return 1

    # Create analyzer
    analyzer = PolyphonicMidiAnalyzer(
        chord_mode=args.mode,
        time_quantization=args.quantize,
        merge_threshold=args.merge_threshold
    )

    # Parse MIDI
    print(f"Parsing polyphonic MIDI: {args.midi_file}")
    tracks = analyzer.parse_midi_file(args.midi_file)
    print(f"Found {len(tracks)} tracks/channels")

    # Print statistics
    stats = analyzer.get_statistics()
    print("\n=== Polyphonic MIDI Statistics ===")
    print(json.dumps(stats, indent=2))

    # Export if not stats-only
    if not args.stats_only:
        if not args.output:
            input_path = Path(args.midi_file)
            args.output = input_path.parent / f"{input_path.stem}_tracks"

        analyzer.export_track_tokens(args.output)

        print(f"\nNext steps:")
        print(f"  1. Build graphs for each track")
        print(f"  2. Analyze each track separately")
        print(f"  3. Compare tracks to see interactions")

    return 0


if __name__ == '__main__':
    exit(main())
