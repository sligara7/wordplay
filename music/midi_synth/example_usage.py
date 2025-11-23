"""
Example Usage of Modular MIDI Synthesizer

This demonstrates the various ways to use the synthesizer.
"""

from modules.synthesizer import MIDISynthesizer
from pathlib import Path


def example_1_simple():
    """Example 1: Simplest usage - synthesize and save."""
    print("=" * 60)
    print("Example 1: Simple synthesis")
    print("=" * 60)

    synth = MIDISynthesizer()

    # Synthesize MIDI file and save
    synth.synthesize_and_save(
        'test_files/simple.mid',
        'output_simple.wav'
    )


def example_2_custom_effects():
    """Example 2: Custom effects settings."""
    print("\n" + "=" * 60)
    print("Example 2: Custom effects")
    print("=" * 60)

    synth = MIDISynthesizer(
        reverb_enabled=True,
        chorus_enabled=True  # Enable chorus
    )

    audio = synth.synthesize_file(
        'test_files/chord_progression.mid',
        reverb_wet=0.4,    # More reverb
        chorus_wet=0.3,    # Add chorus
        target_peak=0.90   # Leave some headroom
    )

    synth.save_wav('output_with_effects.wav', audio)


def example_3_modular_approach():
    """Example 3: Use modules directly for fine control."""
    print("\n" + "=" * 60)
    print("Example 3: Modular approach with direct control")
    print("=" * 60)

    from modules import (
        MIDIParser, ControllerManager, InstrumentEngine,
        EffectsProcessor, AudioMixer, MasterProcessor
    )

    # Initialize modules
    parser = MIDIParser()
    controller_manager = ControllerManager()
    instrument_engine = InstrumentEngine(sample_rate=44100)
    effects = EffectsProcessor(sample_rate=44100)
    mixer = AudioMixer(sample_rate=44100)
    master = MasterProcessor(sample_rate=44100)

    # Parse MIDI
    midi_data = parser.parse_file('test_files/c_scale.mid')
    notes = midi_data['notes']
    duration = midi_data['duration']

    # Apply controllers
    controller_manager.apply_events(
        midi_data['program_changes'],
        midi_data['controllers'],
        midi_data['pitch_bends']
    )

    # Synthesize notes
    note_audio = {}
    for idx, note in enumerate(notes):
        channel = note['channel']
        state = controller_manager.get_state(channel)

        audio = instrument_engine.synthesize_note(
            midi_note=note['note'],
            velocity=note['velocity'],
            duration=note['duration'],
            program=state['program'],
            channel=channel
        )

        note_audio[idx] = audio

    # Mix with custom panning
    pan_per_channel = {}
    for ch in range(16):
        pan_per_channel[ch] = controller_manager.get_pan_stereo_gains(ch)

    mixed_audio = mixer.mix_notes(
        notes, note_audio, duration,
        pan_per_channel=pan_per_channel,
        stereo=True
    )

    # Apply custom reverb settings
    mixed_audio = effects.apply_reverb(
        mixed_audio,
        room_size=0.7,    # Larger room
        damping=0.3,      # Less damping (brighter)
        wet=0.5           # More reverb
    )

    # Master with custom settings
    final_audio = master.master(
        mixed_audio,
        target_peak=0.95,
        use_limiter=True,
        use_dither=True
    )

    # Analyze
    stats = master.analyze_audio(final_audio)
    print(f"Peak: {stats['peak_db']:.2f} dB")
    print(f"RMS: {stats['rms_db']:.2f} dB")
    print(f"Dynamic range: {stats['dynamic_range_db']:.2f} dB")

    # Save
    master_audio_int16 = master.to_int16(final_audio)
    import wave
    import numpy as np
    with wave.open('output_modular.wav', 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(master_audio_int16.tobytes())

    print("Saved: output_modular.wav")


def example_4_analyze_only():
    """Example 4: Analyze MIDI without synthesizing."""
    print("\n" + "=" * 60)
    print("Example 4: Analyze MIDI file")
    print("=" * 60)

    from modules import MIDIParser

    parser = MIDIParser()
    midi_data = parser.parse_file('test_files/simple.mid')

    print(f"Duration: {midi_data['duration']:.2f}s")
    print(f"Notes: {len(midi_data['notes'])}")
    print(f"Program changes: {len(midi_data['program_changes'])}")
    print(f"Controllers: {len(midi_data['controllers'])}")
    print(f"Pitch bends: {len(midi_data['pitch_bends'])}")
    print(f"Tempo changes: {len(midi_data['tempo_changes'])}")
    print(f"Initial tempo: {midi_data['initial_tempo_bpm']:.2f} BPM")

    # Show first few notes
    print("\nFirst 5 notes:")
    for note in midi_data['notes'][:5]:
        print(f"  Ch {note['channel']}: Note {note['note']} "
              f"vel {note['velocity']} @ {note['start']:.2f}s "
              f"dur {note['duration']:.2f}s")


def example_5_compare_with_without_effects():
    """Example 5: Compare dry vs wet."""
    print("\n" + "=" * 60)
    print("Example 5: Compare dry vs wet")
    print("=" * 60)

    # Dry (no effects)
    synth_dry = MIDISynthesizer(reverb_enabled=False, chorus_enabled=False)
    audio_dry = synth_dry.synthesize_file(
        'test_files/chord_progression.mid',
        reverb_wet=0.0,
        chorus_wet=0.0
    )
    synth_dry.save_wav('output_dry.wav', audio_dry)

    # Wet (with effects)
    synth_wet = MIDISynthesizer(reverb_enabled=True, chorus_enabled=True)
    audio_wet = synth_wet.synthesize_file(
        'test_files/chord_progression.mid',
        reverb_wet=0.5,
        chorus_wet=0.3
    )
    synth_wet.save_wav('output_wet.wav', audio_wet)

    print("Compare output_dry.wav vs output_wet.wav")


def main():
    """Run all examples."""
    print("MIDI Synthesizer - Example Usage")
    print("=" * 60)

    # Check if test files exist
    test_dir = Path('test_files')
    if not test_dir.exists():
        print(f"\nWarning: {test_dir} does not exist.")
        print("Creating test MIDI files...")

        # Create test directory
        test_dir.mkdir(exist_ok=True)

        # Create simple test MIDI
        from create_test_midi import create_simple_midi
        create_simple_midi('test_files/simple.mid')

        print("Test files created!")

    # Run examples
    try:
        # Example 4 doesn't require synthesis, always safe to run
        example_4_analyze_only()

        # Comment out examples you don't want to run
        # example_1_simple()
        # example_2_custom_effects()
        # example_3_modular_approach()
        # example_5_compare_with_without_effects()

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Make sure test MIDI files exist in test_files/ directory")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
