#!/usr/bin/env python3
"""
MIDI Tokenizer - Converts MIDI files into token sequences for graph analysis.

This module extends the Wordplay framework to music by treating MIDI notes
as tokens that can be analyzed using the same graph-based techniques.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class MidiNote:
    """Represents a MIDI note event."""
    pitch: int  # MIDI pitch (0-127)
    velocity: int  # Note velocity (0-127)
    start_time: float  # Start time in ticks or seconds
    duration: float  # Duration in ticks or seconds
    channel: int  # MIDI channel (0-15)

    def to_token(self, mode='pitch') -> str:
        """
        Convert note to a token string.

        Args:
            mode: Tokenization mode
                - 'pitch': Just the pitch name (e.g., 'C4', 'D#5')
                - 'pitch_duration': Pitch + duration bucket (e.g., 'C4_quarter')
                - 'pitch_velocity': Pitch + velocity level (e.g., 'C4_mf')
                - 'full': All attributes (e.g., 'C4_quarter_mf')
        """
        pitch_name = self._midi_to_note_name(self.pitch)

        if mode == 'pitch':
            return pitch_name
        elif mode == 'pitch_duration':
            duration_bucket = self._duration_to_bucket(self.duration)
            return f"{pitch_name}_{duration_bucket}"
        elif mode == 'pitch_velocity':
            velocity_level = self._velocity_to_level(self.velocity)
            return f"{pitch_name}_{velocity_level}"
        elif mode == 'full':
            duration_bucket = self._duration_to_bucket(self.duration)
            velocity_level = self._velocity_to_level(self.velocity)
            return f"{pitch_name}_{duration_bucket}_{velocity_level}"
        else:
            return pitch_name

    @staticmethod
    def _midi_to_note_name(pitch: int) -> str:
        """Convert MIDI pitch number to note name (e.g., 60 -> 'C4')."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = note_names[pitch % 12]
        return f"{note}{octave}"

    @staticmethod
    def _duration_to_bucket(duration: float) -> str:
        """Convert duration to musical bucket (whole, half, quarter, etc.)."""
        # Assuming 480 ticks per quarter note (common MIDI standard)
        # Adjust these thresholds based on your MIDI file's time division
        if duration >= 1920:
            return 'whole'
        elif duration >= 960:
            return 'half'
        elif duration >= 480:
            return 'quarter'
        elif duration >= 240:
            return 'eighth'
        elif duration >= 120:
            return 'sixteenth'
        else:
            return 'short'

    @staticmethod
    def _velocity_to_level(velocity: int) -> str:
        """Convert velocity to musical dynamic level."""
        if velocity >= 112:
            return 'fff'  # fortississimo
        elif velocity >= 96:
            return 'ff'   # fortissimo
        elif velocity >= 80:
            return 'f'    # forte
        elif velocity >= 64:
            return 'mf'   # mezzo-forte
        elif velocity >= 48:
            return 'mp'   # mezzo-piano
        elif velocity >= 32:
            return 'p'    # piano
        else:
            return 'pp'   # pianissimo


class MidiTokenizer:
    """
    Tokenizes MIDI files into sequences that can be analyzed with word graph tools.
    """

    def __init__(self, tokenization_mode='pitch'):
        """
        Initialize the MIDI tokenizer.

        Args:
            tokenization_mode: How to tokenize notes
                - 'pitch': Just pitch names
                - 'pitch_duration': Pitch + rhythm
                - 'pitch_velocity': Pitch + dynamics
                - 'full': All attributes
        """
        self.tokenization_mode = tokenization_mode
        self.notes: List[MidiNote] = []
        self.tokens: List[str] = []

    def parse_midi_file(self, file_path: str) -> List[MidiNote]:
        """
        Parse a MIDI file and extract note events.

        Args:
            file_path: Path to MIDI file

        Returns:
            List of MidiNote objects sorted by start time
        """
        try:
            import mido
        except ImportError:
            raise ImportError(
                "mido library is required for MIDI parsing. "
                "Install it with: pip install mido"
            )

        notes = []
        midi_file = mido.MidiFile(file_path)

        # Track note_on events to match with note_off
        active_notes = defaultdict(lambda: defaultdict(dict))  # [channel][pitch] -> start_time

        current_time = 0
        for track in midi_file.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time

                if msg.type == 'note_on' and msg.velocity > 0:
                    # Note starts
                    active_notes[msg.channel][msg.note] = {
                        'start_time': current_time,
                        'velocity': msg.velocity
                    }

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Note ends
                    if msg.note in active_notes[msg.channel]:
                        note_info = active_notes[msg.channel][msg.note]
                        duration = current_time - note_info['start_time']

                        note = MidiNote(
                            pitch=msg.note,
                            velocity=note_info['velocity'],
                            start_time=note_info['start_time'],
                            duration=duration,
                            channel=msg.channel
                        )
                        notes.append(note)

                        # Remove from active notes
                        del active_notes[msg.channel][msg.note]

        # Sort notes by start time
        notes.sort(key=lambda n: n.start_time)

        self.notes = notes
        return notes

    def tokenize(self, notes: Optional[List[MidiNote]] = None) -> List[str]:
        """
        Convert notes to tokens.

        Args:
            notes: List of MidiNote objects (uses self.notes if None)

        Returns:
            List of token strings
        """
        if notes is None:
            notes = self.notes

        self.tokens = [note.to_token(self.tokenization_mode) for note in notes]
        return self.tokens

    def get_statistics(self) -> Dict:
        """Get statistics about the tokenized MIDI file."""
        if not self.tokens:
            return {}

        token_counts = Counter(self.tokens)

        return {
            'total_notes': len(self.notes),
            'total_tokens': len(self.tokens),
            'unique_tokens': len(token_counts),
            'most_common_tokens': token_counts.most_common(10),
            'tokenization_mode': self.tokenization_mode,
            'pitch_range': {
                'lowest': min(note.pitch for note in self.notes),
                'highest': max(note.pitch for note in self.notes),
                'lowest_note': MidiNote._midi_to_note_name(min(note.pitch for note in self.notes)),
                'highest_note': MidiNote._midi_to_note_name(max(note.pitch for note in self.notes))
            },
            'duration_stats': {
                'shortest': min(note.duration for note in self.notes),
                'longest': max(note.duration for note in self.notes),
                'average': sum(note.duration for note in self.notes) / len(self.notes)
            }
        }

    def export_tokens_as_text(self, output_path: str):
        """
        Export tokens as a text file that can be processed by word_graph_builder.py

        Args:
            output_path: Path to output text file
        """
        # Join tokens with spaces to create a "sentence"
        text = ' '.join(self.tokens)

        with open(output_path, 'w') as f:
            f.write(text)

        print(f"Exported {len(self.tokens)} tokens to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Tokenize MIDI files for graph analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic tokenization (pitch only)
  python3 src/midi_tokenizer.py music/song.mid -o music/song_tokens.txt

  # Include rhythm information
  python3 src/midi_tokenizer.py music/song.mid -o music/song_tokens.txt -m pitch_duration

  # Full tokenization (pitch + rhythm + dynamics)
  python3 src/midi_tokenizer.py music/song.mid -o music/song_tokens.txt -m full

  # View statistics only
  python3 src/midi_tokenizer.py music/song.mid --stats-only
        """
    )

    parser.add_argument('midi_file', help='Path to MIDI file')
    parser.add_argument('-o', '--output', help='Output text file for tokens')
    parser.add_argument(
        '-m', '--mode',
        choices=['pitch', 'pitch_duration', 'pitch_velocity', 'full'],
        default='pitch',
        help='Tokenization mode (default: pitch)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only print statistics, do not export tokens'
    )

    args = parser.parse_args()

    # Validate input file
    if not Path(args.midi_file).exists():
        print(f"Error: MIDI file not found: {args.midi_file}")
        return 1

    # Create tokenizer
    tokenizer = MidiTokenizer(tokenization_mode=args.mode)

    # Parse and tokenize
    print(f"Parsing MIDI file: {args.midi_file}")
    notes = tokenizer.parse_midi_file(args.midi_file)
    print(f"Found {len(notes)} notes")

    tokens = tokenizer.tokenize()
    print(f"Generated {len(tokens)} tokens")

    # Print statistics
    stats = tokenizer.get_statistics()
    print("\n=== MIDI Statistics ===")
    print(json.dumps(stats, indent=2))

    # Export if not stats-only
    if not args.stats_only:
        if not args.output:
            # Auto-generate output filename
            input_path = Path(args.midi_file)
            args.output = input_path.parent / f"{input_path.stem}_tokens.txt"

        tokenizer.export_tokens_as_text(args.output)
        print(f"\nNext steps:")
        print(f"  1. Build graph: python3 src/word_graph_builder.py {args.output} -o output/music_graph.json")
        print(f"  2. Analyze: python3 src/analyze_word_graph.py output/music_graph.json")

    return 0


if __name__ == '__main__':
    exit(main())
