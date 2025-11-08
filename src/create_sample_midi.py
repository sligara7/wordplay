#!/usr/bin/env python3
"""
Create sample MIDI files for testing the MIDI tokenizer.

This script generates simple MIDI melodies that can be used to test
the graph analysis capabilities.
"""

import argparse
from pathlib import Path


def create_simple_melody(output_path: str):
    """
    Create a simple C major scale melody.

    Args:
        output_path: Where to save the MIDI file
    """
    try:
        import mido
        from mido import Message, MidiFile, MidiTrack
    except ImportError:
        raise ImportError(
            "mido library is required. Install it with: pip install mido"
        )

    # Create MIDI file with one track
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Add track name
    track.append(Message('program_change', program=0, time=0))

    # C major scale: C, D, E, F, G, A, B, C
    # MIDI notes: 60, 62, 64, 65, 67, 69, 71, 72
    scale = [60, 62, 64, 65, 67, 69, 71, 72]

    # Quarter note = 480 ticks (standard)
    quarter_note = 480

    # Play scale up and down
    melody = scale + list(reversed(scale[:-1]))

    for note in melody:
        # Note on
        track.append(Message('note_on', note=note, velocity=64, time=0))
        # Note off after quarter note
        track.append(Message('note_off', note=note, velocity=64, time=quarter_note))

    # Save file
    mid.save(output_path)
    print(f"Created simple melody: {output_path}")
    print(f"  Notes: {len(melody)}")
    print(f"  Pattern: C major scale up and down")


def create_twinkle_twinkle(output_path: str):
    """
    Create 'Twinkle Twinkle Little Star' melody.

    Args:
        output_path: Where to save the MIDI file
    """
    try:
        import mido
        from mido import Message, MidiFile, MidiTrack
    except ImportError:
        raise ImportError(
            "mido library is required. Install it with: pip install mido"
        )

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=0, time=0))

    # Twinkle Twinkle Little Star in C major
    # C C G G A A G (Twinkle twinkle little star)
    # F F E E D D C (How I wonder what you are)
    notes = [
        60, 60, 67, 67, 69, 69, 67,  # Twinkle twinkle little star
        65, 65, 64, 64, 62, 62, 60,  # How I wonder what you are
        67, 67, 65, 65, 64, 64, 62,  # Up above the world so high
        67, 67, 65, 65, 64, 64, 62,  # Like a diamond in the sky
        60, 60, 67, 67, 69, 69, 67,  # Twinkle twinkle little star
        65, 65, 64, 64, 62, 62, 60   # How I wonder what you are
    ]

    durations = [480] * len(notes)  # All quarter notes
    durations[6] = 960   # Half note on "star"
    durations[13] = 960  # Half note on "are"
    durations[20] = 960  # Half note on "high"
    durations[27] = 960  # Half note on "sky"
    durations[34] = 960  # Half note on "star"
    durations[41] = 960  # Half note on "are"

    for note, duration in zip(notes, durations):
        track.append(Message('note_on', note=note, velocity=64, time=0))
        track.append(Message('note_off', note=note, velocity=64, time=duration))

    mid.save(output_path)
    print(f"Created Twinkle Twinkle: {output_path}")
    print(f"  Notes: {len(notes)}")
    print(f"  Pattern: Famous children's song")


def create_chord_progression(output_path: str):
    """
    Create a simple chord progression (C - G - Am - F).

    Args:
        output_path: Where to save the MIDI file
    """
    try:
        import mido
        from mido import Message, MidiFile, MidiTrack
    except ImportError:
        raise ImportError(
            "mido library is required. Install it with: pip install mido"
        )

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=0, time=0))

    # Define chords (as MIDI note numbers)
    chords = [
        [60, 64, 67],  # C major (C, E, G)
        [67, 71, 74],  # G major (G, B, D)
        [69, 60, 64],  # A minor (A, C, E)
        [65, 69, 60],  # F major (F, A, C)
    ]

    whole_note = 1920

    # Play each chord
    for chord in chords * 2:  # Repeat twice
        # All notes on at the same time (time=0 for subsequent notes)
        for i, note in enumerate(chord):
            track.append(Message('note_on', note=note, velocity=64, time=0))

        # All notes off at the same time (after whole note duration)
        for i, note in enumerate(chord):
            time = whole_note if i == 0 else 0
            track.append(Message('note_off', note=note, velocity=64, time=time))

    mid.save(output_path)
    print(f"Created chord progression: {output_path}")
    print(f"  Chords: C - G - Am - F (repeated)")
    print(f"  Pattern: Common pop progression")


def main():
    parser = argparse.ArgumentParser(
        description='Create sample MIDI files for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'type',
        choices=['scale', 'twinkle', 'chords', 'all'],
        help='Type of MIDI file to create'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='music',
        help='Output directory (default: music/)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Create requested file(s)
    if args.type in ['scale', 'all']:
        create_simple_melody(str(output_dir / 'scale.mid'))

    if args.type in ['twinkle', 'all']:
        create_twinkle_twinkle(str(output_dir / 'twinkle.mid'))

    if args.type in ['chords', 'all']:
        create_chord_progression(str(output_dir / 'chords.mid'))

    print("\nSample MIDI files created successfully!")
    print("\nNext steps:")
    print(f"  1. Tokenize: python3 src/midi_tokenizer.py {output_dir}/*.mid")
    print(f"  2. Build graph: python3 src/word_graph_builder.py <tokens.txt> -o output/graph.json")
    print(f"  3. Analyze: python3 src/analyze_word_graph.py output/graph.json")


if __name__ == '__main__':
    exit(main())
