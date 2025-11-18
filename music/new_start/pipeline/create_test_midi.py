#!/usr/bin/env python3
"""
Create a simple test MIDI file for testing synthesis.

Creates a short musical phrase with different instruments.
"""

import mido
from mido import Message, MidiFile, MidiTrack


def create_test_midi(output_path="test_synthesis.mid"):
    """
    Create a test MIDI file with various instruments.

    Args:
        output_path: Path for output MIDI file
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM)
    tempo = mido.bpm2tempo(120)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    # Ticks per beat
    ticks_per_beat = mid.ticks_per_beat  # Default 480

    # Helper function to calculate ticks
    def beats_to_ticks(beats):
        return int(beats * ticks_per_beat)

    # Track 1: Guitar (program 25 = Acoustic Guitar)
    track.append(Message('program_change', program=24, time=0, channel=0))  # Program 24 = Nylon Guitar (0-indexed)

    # Simple C major arpeggio (guitar)
    notes = [60, 64, 67, 72]  # C, E, G, C
    for i, note in enumerate(notes):
        track.append(Message('note_on', note=note, velocity=80, time=0 if i > 0 else 0, channel=0))
        track.append(Message('note_off', note=note, velocity=0, time=beats_to_ticks(0.5), channel=0))

    # Track 2: Brass (program 57 = Trumpet)
    track.append(Message('program_change', program=56, time=beats_to_ticks(0.5), channel=1))

    # Brass melody
    brass_notes = [67, 69, 71, 72]  # G, A, B, C
    for i, note in enumerate(brass_notes):
        track.append(Message('note_on', note=note, velocity=100, time=0 if i > 0 else 0, channel=1))
        track.append(Message('note_off', note=note, velocity=0, time=beats_to_ticks(0.5), channel=1))

    # Track 3: Strings (program 41 = Violin)
    track.append(Message('program_change', program=40, time=beats_to_ticks(0.5), channel=2))

    # Long sustained string note
    track.append(Message('note_on', note=64, velocity=60, time=0, channel=2))  # E
    track.append(Message('note_off', note=64, velocity=0, time=beats_to_ticks(4), channel=2))

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=beats_to_ticks(1)))

    # Save
    mid.save(output_path)

    print(f"✓ Created test MIDI: {output_path}")
    print(f"  Duration: ~6 seconds")
    print(f"  Instruments: Guitar (ch0), Trumpet (ch1), Violin (ch2)")
    print(f"  Total messages: {len(track)}")

    return output_path


if __name__ == "__main__":
    import sys

    output_file = sys.argv[1] if len(sys.argv) > 1 else "test_synthesis.mid"

    create_test_midi(output_file)
