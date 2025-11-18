#!/usr/bin/env python3
"""
Generate Synthetic Test Data for Phase 1: Timing & Dynamics

Creates MIDI files with known:
- Onset times (for onset detection testing)
- Velocities (for velocity estimation testing)
- Note durations (for duration detection testing)
"""

import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import numpy as np
from pathlib import Path
import json


def create_simple_scale(output_path, tempo=120, note_duration=0.5):
    """
    Create a simple C major scale with quarter notes.

    Perfect for testing onset detection timing accuracy.

    Args:
        output_path: Path for output MIDI file
        tempo: BPM (beats per minute)
        note_duration: Duration of each note in seconds

    Returns:
        Ground truth dict with onset times and MIDI notes
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo_us = mido.bpm2tempo(tempo)
    track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))

    # C major scale: C4 to C5
    scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C

    ticks_per_beat = mid.ticks_per_beat
    ticks_per_note = int(mido.second2tick(note_duration, ticks_per_beat, tempo_us))

    ground_truth = {
        'onset_times': [],
        'midi_notes': [],
        'velocities': [],
        'durations': [],
        'tempo': tempo,
        'file': str(output_path)
    }

    current_time = 0.0

    for i, note in enumerate(scale_notes):
        # Note on
        track.append(Message('note_on', note=note, velocity=80, time=0 if i > 0 else 0))

        # Ground truth
        ground_truth['onset_times'].append(current_time)
        ground_truth['midi_notes'].append(note)
        ground_truth['velocities'].append(80)
        ground_truth['durations'].append(note_duration)

        # Note off
        track.append(Message('note_off', note=note, velocity=0, time=ticks_per_note))

        current_time += note_duration

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save MIDI
    mid.save(output_path)

    # Save ground truth
    gt_path = Path(output_path).with_suffix('.json')
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"✓ Created: {output_path}")
    print(f"  Notes: {len(scale_notes)}")
    print(f"  Duration: {current_time:.2f}s")
    print(f"  Ground truth: {gt_path}")

    return ground_truth


def create_dynamic_test(output_path, tempo=120):
    """
    Create a test with varying dynamics (velocities).

    Perfect for testing velocity estimation.

    Args:
        output_path: Path for output MIDI file
        tempo: BPM

    Returns:
        Ground truth dict
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo_us = mido.bpm2tempo(tempo)
    track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))

    # Create crescendo: pp (20) to ff (120)
    num_notes = 12
    velocities = np.linspace(20, 120, num_notes).astype(int)

    # All middle C
    note = 60
    note_duration = 0.5

    ticks_per_beat = mid.ticks_per_beat
    ticks_per_note = int(mido.second2tick(note_duration, ticks_per_beat, tempo_us))

    ground_truth = {
        'onset_times': [],
        'midi_notes': [],
        'velocities': [],
        'durations': [],
        'tempo': tempo,
        'file': str(output_path)
    }

    current_time = 0.0

    for i, velocity in enumerate(velocities):
        # Note on
        track.append(Message('note_on', note=note, velocity=int(velocity), time=0 if i > 0 else 0))

        # Ground truth
        ground_truth['onset_times'].append(current_time)
        ground_truth['midi_notes'].append(note)
        ground_truth['velocities'].append(int(velocity))
        ground_truth['durations'].append(note_duration)

        # Note off
        track.append(Message('note_off', note=note, velocity=0, time=ticks_per_note))

        current_time += note_duration

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)

    gt_path = Path(output_path).with_suffix('.json')
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"✓ Created: {output_path}")
    print(f"  Notes: {num_notes}")
    print(f"  Velocity range: {int(velocities[0])}-{int(velocities[-1])}")
    print(f"  Ground truth: {gt_path}")

    return ground_truth


def create_rhythm_test(output_path, tempo=120):
    """
    Create a test with various note durations.

    Perfect for testing onset detection with different rhythmic patterns.

    Args:
        output_path: Path for output MIDI file
        tempo: BPM

    Returns:
        Ground truth dict
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo_us = mido.bpm2tempo(tempo)
    track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))

    ticks_per_beat = mid.ticks_per_beat

    # Different note durations (in beats)
    durations_beats = [1.0, 0.5, 0.25, 0.25, 0.5, 1.0, 0.25, 0.25, 0.25, 0.25]

    # Notes (simple pattern)
    notes = [60, 62, 64, 65, 64, 62, 60, 62, 64, 60]

    ground_truth = {
        'onset_times': [],
        'midi_notes': [],
        'velocities': [],
        'durations': [],
        'tempo': tempo,
        'file': str(output_path)
    }

    current_time = 0.0

    for i, (duration_beats, note) in enumerate(zip(durations_beats, notes)):
        duration_seconds = duration_beats * (60.0 / tempo)
        ticks = int(mido.second2tick(duration_seconds, ticks_per_beat, tempo_us))

        # Note on
        track.append(Message('note_on', note=note, velocity=80, time=0 if i > 0 else 0))

        # Ground truth
        ground_truth['onset_times'].append(current_time)
        ground_truth['midi_notes'].append(note)
        ground_truth['velocities'].append(80)
        ground_truth['durations'].append(duration_seconds)

        # Note off
        track.append(Message('note_off', note=note, velocity=0, time=ticks))

        current_time += duration_seconds

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    # Save
    mid.save(output_path)

    gt_path = Path(output_path).with_suffix('.json')
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"✓ Created: {output_path}")
    print(f"  Notes: {len(notes)}")
    print(f"  Durations: {min(durations_beats):.2f} - {max(durations_beats):.2f} beats")
    print(f"  Ground truth: {gt_path}")

    return ground_truth


def create_all_test_data(output_dir="test_data"):
    """
    Create all test MIDI files for Phase 1.

    Args:
        output_dir: Directory to save test files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING PHASE 1 TEST DATA")
    print("="*80)
    print()

    # Test 1: Simple scale (onset timing)
    print("[1/3] Simple Scale Test")
    print("-" * 80)
    create_simple_scale(output_dir / "test_simple_scale.mid", tempo=120, note_duration=0.5)
    print()

    # Test 2: Dynamic test (velocity estimation)
    print("[2/3] Dynamic Test")
    print("-" * 80)
    create_dynamic_test(output_dir / "test_dynamics.mid", tempo=120)
    print()

    # Test 3: Rhythm test (complex onsets)
    print("[3/3] Rhythm Test")
    print("-" * 80)
    create_rhythm_test(output_dir / "test_rhythm.mid", tempo=120)
    print()

    print("="*80)
    print("✓ All test data generated!")
    print(f"  Location: {output_dir.absolute()}")
    print("="*80)


if __name__ == "__main__":
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "test_data"
    create_all_test_data(output_dir)
