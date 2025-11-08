#!/usr/bin/env python3
"""
Temporal-Aware Music Tokenizer - Captures rhythm, duration, and timing.

This addresses the limitation that basic tokenization loses temporal structure.
Sheet music and MIDI files have critical timing information that must be
preserved in the graph representation.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import mido


class TemporalMidiTokenizer:
    """
    Tokenize MIDI with full temporal awareness: pitch + duration + timing.

    Unlike basic tokenization that only captures "which notes," this captures
    "which notes, for how long, in what rhythm pattern."
    """

    def __init__(self, mode='pitch_duration', quantize=True, ppq=480):
        """
        Initialize temporal tokenizer.

        Args:
            mode: Tokenization mode
                - 'pitch_duration': Note + duration (e.g., 'C4_quarter')
                - 'pitch_ioi': Note + inter-onset interval (e.g., 'C4_ioi480')
                - 'rhythm_pattern': Rhythmic groupings (e.g., 'quarter_quarter_half')
            quantize: Quantize to standard note values
            ppq: Pulses per quarter note (default 480)
        """
        self.mode = mode
        self.quantize = quantize
        self.ppq = ppq
        self.notes = []
        self.tempo = 500000  # Default: 120 BPM

    def parse_midi_with_timing(self, file_path: str) -> List[Dict]:
        """
        Parse MIDI with full timing information.

        Returns list of notes with:
        - pitch
        - start_time (in ticks)
        - duration (in ticks)
        - velocity
        - inter_onset_interval (time since previous note)
        """
        midi_file = mido.MidiFile(file_path)
        notes = []
        active_notes = {}

        current_time = 0
        for track in midi_file.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time

                # Track tempo changes
                if msg.type == 'set_tempo':
                    self.tempo = msg.tempo

                if msg.type == 'note_on' and msg.velocity > 0:
                    active_notes[msg.note] = {
                        'start': current_time,
                        'velocity': msg.velocity,
                        'channel': msg.channel
                    }

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in active_notes:
                        note_info = active_notes[msg.note]
                        duration = current_time - note_info['start']

                        notes.append({
                            'pitch': msg.note,
                            'start_time': note_info['start'],
                            'duration': duration,
                            'velocity': note_info['velocity'],
                            'channel': note_info['channel']
                        })

                        del active_notes[msg.note]

        # Sort by start time
        notes.sort(key=lambda n: n['start_time'])

        # Calculate inter-onset intervals (IOI)
        for i in range(len(notes)):
            if i > 0:
                notes[i]['ioi'] = notes[i]['start_time'] - notes[i-1]['start_time']
            else:
                notes[i]['ioi'] = 0

        self.notes = notes
        return notes

    def duration_to_name(self, ticks: int) -> str:
        """Convert tick duration to musical note value."""
        # At 480 PPQ:
        whole = self.ppq * 4        # 1920
        half = self.ppq * 2         # 960
        quarter = self.ppq          # 480
        eighth = self.ppq // 2      # 240
        sixteenth = self.ppq // 4   # 120

        if self.quantize:
            # Quantize to nearest standard value
            values = [
                (whole, 'whole'),
                (half + quarter, 'dotted_half'),  # 1440
                (half, 'half'),
                (quarter + eighth, 'dotted_quarter'),  # 720
                (quarter, 'quarter'),
                (eighth + sixteenth, 'dotted_eighth'),  # 360
                (eighth, 'eighth'),
                (sixteenth, 'sixteenth')
            ]

            for threshold, name in values:
                if ticks >= threshold * 0.75:  # Within 25% tolerance
                    return name
            return 'short'
        else:
            # Exact tick count
            return f'{ticks}ticks'

    def midi_to_note_name(self, pitch: int) -> str:
        """Convert MIDI pitch to note name."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = note_names[pitch % 12]
        return f"{note}{octave}"

    def tokenize(self) -> List[str]:
        """
        Tokenize with temporal awareness.

        Returns list of tokens that include timing information.
        """
        tokens = []

        for note in self.notes:
            pitch_name = self.midi_to_note_name(note['pitch'])

            if self.mode == 'pitch_duration':
                # Note + its duration
                duration = self.duration_to_name(note['duration'])
                token = f"{pitch_name}_{duration}"

            elif self.mode == 'pitch_ioi':
                # Note + time since previous note (rhythm)
                ioi = self.duration_to_name(note['ioi'])
                token = f"{pitch_name}_ioi{ioi}"

            elif self.mode == 'full_temporal':
                # Note + duration + IOI
                duration = self.duration_to_name(note['duration'])
                ioi = self.duration_to_name(note['ioi'])
                token = f"{pitch_name}_dur{duration}_ioi{ioi}"

            else:
                token = pitch_name

            tokens.append(token)

        return tokens

    def extract_rhythm_pattern(self) -> List[str]:
        """
        Extract pure rhythm pattern (durations without pitches).

        Useful for analyzing rhythmic structure independently.
        """
        return [self.duration_to_name(note['duration']) for note in self.notes]

    def get_statistics(self) -> Dict:
        """Get temporal statistics."""
        if not self.notes:
            return {}

        durations = [note['duration'] for note in self.notes]
        iois = [note['ioi'] for note in self.notes if note['ioi'] > 0]

        # Get BPM from tempo
        bpm = 60_000_000 / self.tempo if self.tempo > 0 else 120

        # Rhythm pattern frequency
        rhythm_pattern = self.extract_rhythm_pattern()
        rhythm_counts = Counter(rhythm_pattern)

        return {
            'total_notes': len(self.notes),
            'tempo_bpm': round(bpm, 2),
            'timing_statistics': {
                'shortest_duration': min(durations),
                'longest_duration': max(durations),
                'average_duration': sum(durations) / len(durations),
                'shortest_ioi': min(iois) if iois else 0,
                'longest_ioi': max(iois) if iois else 0,
                'average_ioi': sum(iois) / len(iois) if iois else 0
            },
            'rhythm_pattern_frequency': rhythm_counts.most_common(10),
            'duration_distribution': Counter([self.duration_to_name(d) for d in durations])
        }


def main():
    parser = argparse.ArgumentParser(
        description='Temporal-aware MIDI tokenization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tokenize with pitch + duration
  python3 src/temporal_midi_tokenizer.py music/song.mid -o music/song_temporal.txt

  # Extract rhythm pattern only
  python3 src/temporal_midi_tokenizer.py music/song.mid --rhythm-only

  # Full temporal analysis
  python3 src/temporal_midi_tokenizer.py music/song.mid -m full_temporal
        """
    )

    parser.add_argument('midi_file', help='Path to MIDI file')
    parser.add_argument('-o', '--output', help='Output token file')
    parser.add_argument(
        '-m', '--mode',
        choices=['pitch_duration', 'pitch_ioi', 'full_temporal'],
        default='pitch_duration',
        help='Tokenization mode'
    )
    parser.add_argument('--rhythm-only', action='store_true', help='Extract rhythm pattern only')
    parser.add_argument('--no-quantize', action='store_true', help='Use exact tick values')
    parser.add_argument('--stats-only', action='store_true', help='Show statistics only')

    args = parser.parse_args()

    if not Path(args.midi_file).exists():
        print(f"Error: MIDI file not found: {args.midi_file}")
        return 1

    # Create tokenizer
    tokenizer = TemporalMidiTokenizer(
        mode=args.mode,
        quantize=not args.no_quantize
    )

    # Parse MIDI
    print(f"Parsing MIDI with temporal information: {args.midi_file}")
    notes = tokenizer.parse_midi_with_timing(args.midi_file)
    print(f"Found {len(notes)} notes with timing data")

    # Get statistics
    stats = tokenizer.get_statistics()
    print("\n=== Temporal Analysis ===")
    print(json.dumps(stats, indent=2))

    if not args.stats_only:
        if args.rhythm_only:
            # Extract rhythm pattern
            pattern = tokenizer.extract_rhythm_pattern()
            output = args.output or Path(args.midi_file).with_suffix('.rhythm.txt')

            with open(output, 'w') as f:
                f.write(' '.join(pattern))

            print(f"\nRhythm pattern exported to {output}")
        else:
            # Full tokenization
            tokens = tokenizer.tokenize()
            output = args.output or Path(args.midi_file).with_suffix('.temporal.txt')

            with open(output, 'w') as f:
                f.write(' '.join(tokens))

            print(f"\nTemporal tokens exported to {output}")
            print(f"Example tokens: {' '.join(tokens[:5])}")

            print(f"\nNext steps:")
            print(f"  1. Build graph: python3 src/midi_graph_builder.py {output} -o output/temporal_graph.json")
            print(f"  2. Analyze: python3 src/analyze_word_graph.py output/temporal_graph.json")

    return 0


if __name__ == '__main__':
    exit(main())
