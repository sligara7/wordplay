"""
Create Test MIDI Files

Generates simple MIDI files for testing the synthesizer.
"""

import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
from pathlib import Path


def create_simple_midi(output_path='test_files/simple.mid'):
    """
    Create a simple MIDI file with a C major scale.
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM)
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))

    # Set program (Acoustic Grand Piano)
    track.append(Message('program_change', program=0, time=0))

    # C major scale: C D E F G A B C
    scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]

    ticks_per_beat = mid.ticks_per_beat
    quarter_note = ticks_per_beat

    for i, note in enumerate(scale_notes):
        # Note on
        track.append(Message('note_on', note=note, velocity=80, time=0 if i == 0 else quarter_note))

        # Note off (after quarter note)
        track.append(Message('note_off', note=note, velocity=0, time=quarter_note))

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_path)
    print(f"Created: {output_path}")


def create_chord_progression(output_path='test_files/chord_progression.mid'):
    """
    Create a MIDI file with a I-V-vi-IV chord progression (C-G-Am-F).
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))

    # Set program (Acoustic Grand Piano)
    track.append(Message('program_change', program=0, time=0))

    # Chord progression: C, G, Am, F
    chords = [
        [60, 64, 67],  # C major (C-E-G)
        [67, 71, 74],  # G major (G-B-D)
        [69, 72, 76],  # A minor (A-C-E)
        [65, 69, 72],  # F major (F-A-C)
    ]

    ticks_per_beat = mid.ticks_per_beat
    whole_note = ticks_per_beat * 4

    for i, chord in enumerate(chords):
        # Note ons (all at once)
        for j, note in enumerate(chord):
            track.append(Message('note_on', note=note, velocity=70,
                               time=0 if j > 0 else (0 if i == 0 else whole_note)))

        # Note offs (all at once, after whole note)
        for j, note in enumerate(chord):
            track.append(Message('note_off', note=note, velocity=0,
                               time=whole_note if j == 0 else 0))

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_path)
    print(f"Created: {output_path}")


def create_instrument_demo(output_path='test_files/instrument_demo.mid'):
    """
    Create a MIDI file demonstrating different instruments.
    """
    mid = MidiFile()

    # Set tempo
    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    tempo_track.append(MetaMessage('end_of_track', time=0))

    # Instruments to demo
    instruments = [
        (0, 'Acoustic Grand Piano'),
        (16, 'Drawbar Organ'),
        (24, 'Acoustic Guitar (nylon)'),
        (40, 'Violin'),
        (56, 'Trumpet'),
        (73, 'Flute'),
    ]

    ticks_per_beat = mid.ticks_per_beat
    whole_note = ticks_per_beat * 4

    for channel, (program, name) in enumerate(instruments):
        track = MidiTrack()
        mid.tracks.append(track)

        track.append(MetaMessage('track_name', name=name, time=0))
        track.append(Message('program_change', program=program, channel=channel, time=0))

        # Play middle C
        track.append(Message('note_on', note=60, velocity=80, channel=channel, time=0))
        track.append(Message('note_off', note=60, velocity=0, channel=channel, time=whole_note))

        # End of track
        track.append(MetaMessage('end_of_track', time=0))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_path)
    print(f"Created: {output_path}")


def create_controller_demo(output_path='test_files/controller_demo.mid'):
    """
    Create a MIDI file demonstrating controllers (volume, pan).
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))

    # Set program
    track.append(Message('program_change', program=0, time=0))

    ticks_per_beat = mid.ticks_per_beat
    quarter_note = ticks_per_beat

    # Play notes with changing volume
    volumes = [40, 60, 80, 100, 120, 100, 80, 60]

    for i, volume in enumerate(volumes):
        # Set volume (CC 7)
        track.append(Message('control_change', control=7, value=volume,
                           time=0 if i == 0 else quarter_note))

        # Note on
        track.append(Message('note_on', note=60, velocity=80, time=0))

        # Note off
        track.append(Message('note_off', note=60, velocity=0, time=quarter_note))

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_path)
    print(f"Created: {output_path}")


def create_percussion_demo(output_path='test_files/percussion_demo.mid'):
    """
    Create a MIDI file with percussion (channel 9).
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))

    # Channel 9 = percussion (General MIDI)
    channel = 9

    # GM percussion notes
    percussion = [
        (35, 'Bass Drum'),
        (38, 'Snare'),
        (42, 'Hi-hat Closed'),
        (46, 'Hi-hat Open'),
        (49, 'Crash Cymbal'),
    ]

    ticks_per_beat = mid.ticks_per_beat
    quarter_note = ticks_per_beat

    for i, (note, name) in enumerate(percussion):
        # Note on
        track.append(Message('note_on', note=note, velocity=100, channel=channel,
                           time=0 if i == 0 else quarter_note))

        # Note off
        track.append(Message('note_off', note=note, velocity=0, channel=channel,
                           time=quarter_note))

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_path)
    print(f"Created: {output_path}")


def main():
    """Create all test MIDI files."""
    print("Creating test MIDI files...")
    print("=" * 60)

    create_simple_midi()
    create_chord_progression()
    create_instrument_demo()
    create_controller_demo()
    create_percussion_demo()

    print("=" * 60)
    print("All test MIDI files created in test_files/")


if __name__ == '__main__':
    main()
