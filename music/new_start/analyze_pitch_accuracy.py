#!/usr/bin/env python3
"""
Analyze pitch accuracy in detail to understand discrepancies.
"""

import sys
import mido
from collections import Counter

def analyze_pitch_accuracy(original_midi: str, transcribed_midi: str):
    """Detailed pitch accuracy analysis."""

    print("=" * 70)
    print("PITCH ACCURACY ANALYSIS")
    print("=" * 70)

    # Load original MIDI
    original = mido.MidiFile(original_midi)
    original_notes = []
    for track in original.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                original_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    # Load transcribed MIDI
    transcribed = mido.MidiFile(transcribed_midi)
    transcribed_notes = []
    for track in transcribed.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                transcribed_notes.append({
                    'time': time,
                    'note': msg.note,
                    'velocity': msg.velocity
                })

    print(f"\n[Note Counts]")
    print(f"  Original: {len(original_notes)}")
    print(f"  Transcribed: {len(transcribed_notes)}")
    print(f"  Detection rate: {len(transcribed_notes)/max(1, len(original_notes))*100:.1f}%")

    # Pitch distribution
    original_pitches = [n['note'] for n in original_notes]
    transcribed_pitches = [n['note'] for n in transcribed_notes]

    orig_counts = Counter(original_pitches)
    trans_counts = Counter(transcribed_pitches)

    print(f"\n[Pitch Distribution]")
    print(f"  Original unique pitches: {len(orig_counts)}")
    print(f"  Transcribed unique pitches: {len(trans_counts)}")

    # Convert to note names for clarity
    def midi_to_name(midi_num):
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_num // 12) - 1
        note = notes[midi_num % 12]
        return f"{note}{octave}"

    print(f"\n[Original Top 10 Pitches]")
    for i, (pitch, count) in enumerate(orig_counts.most_common(10), 1):
        print(f"  {i}. MIDI {pitch:3d} ({midi_to_name(pitch):4s}): {count:3d} occurrences")

    print(f"\n[Transcribed Top 10 Pitches]")
    for i, (pitch, count) in enumerate(trans_counts.most_common(10), 1):
        orig_count = orig_counts.get(pitch, 0)
        print(f"  {i}. MIDI {pitch:3d} ({midi_to_name(pitch):4s}): {count:3d} occurrences (original: {orig_count})")

    # Pitch accuracy
    orig_set = set(original_pitches)
    trans_set = set(transcribed_pitches)

    matches = orig_set & trans_set
    only_original = orig_set - trans_set
    only_transcribed = trans_set - orig_set

    print(f"\n[Pitch Set Analysis]")
    print(f"  Pitches in both: {len(matches)}")
    print(f"  Only in original: {len(only_original)}")
    print(f"  Only in transcribed: {len(only_transcribed)}")
    print(f"  Pitch accuracy: {len(matches)/max(1, len(orig_set))*100:.1f}%")

    if only_original:
        print(f"\n[Missing Pitches] (in original but not transcribed)")
        for pitch in sorted(only_original):
            print(f"  MIDI {pitch:3d} ({midi_to_name(pitch):4s}): {orig_counts[pitch]} occurrences")

    if only_transcribed:
        print(f"\n[Extra Pitches] (in transcribed but not original)")
        for pitch in sorted(only_transcribed):
            print(f"  MIDI {pitch:3d} ({midi_to_name(pitch):4s}): {trans_counts[pitch]} occurrences")

    # Octave analysis
    print(f"\n[Octave Analysis]")
    orig_octaves = Counter([p // 12 - 1 for p in original_pitches])
    trans_octaves = Counter([p // 12 - 1 for p in transcribed_pitches])

    print(f"  Original octave distribution:")
    for octave in sorted(orig_octaves.keys()):
        print(f"    Octave {octave}: {orig_octaves[octave]} notes")

    print(f"  Transcribed octave distribution:")
    for octave in sorted(trans_octaves.keys()):
        orig_oct_count = orig_octaves.get(octave, 0)
        print(f"    Octave {octave}: {trans_octaves[octave]} notes (original: {orig_oct_count})")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python analyze_pitch_accuracy.py <original.mid> <transcribed.mid>")
        sys.exit(1)

    analyze_pitch_accuracy(sys.argv[1], sys.argv[2])
