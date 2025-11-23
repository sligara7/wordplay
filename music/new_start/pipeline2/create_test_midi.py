#!/usr/bin/env python3
"""
Create simple test MIDI files for pipeline2 validation.
"""

import mido
from pathlib import Path


def create_simple_chord_progression(output_path='test_chord_progression.mid'):
    """
    Create a MIDI file with simple I-IV-V-I chord progression in C major.

    Chords:
    - C major (C-E-G) at 0.0s
    - F major (F-A-C) at 1.0s
    - G major (G-B-D) at 2.0s
    - C major (C-E-G) at 3.0s
    """
    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM)
    tempo = mido.bpm2tempo(120)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))

    # Ticks per beat
    tpb = mid.ticks_per_beat

    # Define chords (MIDI note numbers)
    chords = [
        # (name, notes, start_beat, duration_beats)
        ('C_major', [60, 64, 67], 0.0, 4.0),  # C4, E4, G4
        ('F_major', [65, 69, 72], 4.0, 4.0),  # F4, A4, C5
        ('G_major', [67, 71, 74], 8.0, 4.0),  # G4, B4, D5
        ('C_major', [60, 64, 67], 12.0, 4.0), # C4, E4, G4
    ]

    # Create note events
    events = []  # (absolute_tick, note, velocity, on/off)

    for chord_name, notes, start_beat, duration_beats in chords:
        start_tick = int(start_beat * tpb)
        end_tick = int((start_beat + duration_beats) * tpb)

        for note in notes:
            events.append((start_tick, note, 80, 'on'))
            events.append((end_tick, note, 0, 'off'))

    # Sort events by time
    events.sort()

    # Convert to MIDI messages with delta times
    current_tick = 0
    for tick, note, velocity, event_type in events:
        delta = tick - current_tick

        if event_type == 'on':
            track.append(mido.Message('note_on', note=note, velocity=velocity, time=delta))
        else:
            track.append(mido.Message('note_off', note=note, velocity=0, time=delta))

        current_tick = tick

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)
    print(f"Created: {output_path}")
    print(f"  Duration: {16 * 60 / 120:.1f}s (16 beats at 120 BPM)")
    print(f"  Chords: C major → F major → G major → C major")

    return output_path


def create_single_chord(output_path='test_c_major.mid', chord_name='C_major'):
    """
    Create a MIDI file with a single sustained C major chord.
    """
    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM)
    tempo = mido.bpm2tempo(120)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))

    tpb = mid.ticks_per_beat

    # C major chord: C4, E4, G4
    notes = [60, 64, 67]

    # Note on at beat 0
    for note in notes:
        track.append(mido.Message('note_on', note=note, velocity=80, time=0))

    # Note off at beat 4
    for i, note in enumerate(notes):
        time = tpb * 4 if i == 0 else 0
        track.append(mido.Message('note_off', note=note, velocity=0, time=time))

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)
    print(f"Created: {output_path}")
    print(f"  Duration: 2.0s")
    print(f"  Chord: {chord_name} (C4-E4-G4)")

    return output_path


def create_scale(output_path='test_c_scale.mid'):
    """
    Create a MIDI file with C major scale.
    """
    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM)
    tempo = mido.bpm2tempo(120)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))

    tpb = mid.ticks_per_beat

    # C major scale
    scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C

    current_tick = 0

    for note in scale_notes:
        # Note on
        track.append(mido.Message('note_on', note=note, velocity=80, time=0))

        # Note off after 1 beat
        track.append(mido.Message('note_off', note=note, velocity=0, time=tpb))

        current_tick += tpb

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)
    print(f"Created: {output_path}")
    print(f"  Duration: 4.0s (8 notes)")
    print(f"  Notes: C major scale")

    return output_path


if __name__ == "__main__":
    # Create examples directory
    examples_dir = Path(__file__).parent / 'examples'
    examples_dir.mkdir(exist_ok=True)

    print("Creating test MIDI files...")
    print()

    # Create test files
    create_single_chord(examples_dir / 'simple_c_major.mid')
    print()

    create_simple_chord_progression(examples_dir / 'chord_progression.mid')
    print()

    create_scale(examples_dir / 'c_scale.mid')
    print()

    print("✓ Test MIDI files created in examples/")
