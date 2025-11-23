"""
Test Modular MIDI Synthesizer

Quick smoke tests to verify all modules work correctly.
"""

import numpy as np
from pathlib import Path
import sys


def test_midi_parser():
    """Test MIDI parser module."""
    print("\n" + "=" * 60)
    print("Test 1: MIDI Parser")
    print("=" * 60)

    from modules.midi_parser import MIDIParser

    # Create test MIDI file if needed
    test_file = Path('test_files/simple.mid')
    if not test_file.exists():
        print("Creating test MIDI file...")
        from create_test_midi import create_simple_midi
        create_simple_midi()

    parser = MIDIParser()
    midi_data = parser.parse_file(str(test_file))

    print(f"✓ Parsed MIDI file")
    print(f"  Notes: {len(midi_data['notes'])}")
    print(f"  Duration: {midi_data['duration']:.2f}s")
    print(f"  Tempo: {midi_data['initial_tempo_bpm']:.2f} BPM")

    assert len(midi_data['notes']) > 0, "No notes found"
    assert midi_data['duration'] > 0, "Invalid duration"

    print("✓ MIDI Parser test PASSED")
    return True


def test_controller_manager():
    """Test controller manager module."""
    print("\n" + "=" * 60)
    print("Test 2: Controller Manager")
    print("=" * 60)

    from modules.controller_manager import ControllerManager

    manager = ControllerManager()

    # Test initial state
    state = manager.get_state(0)
    assert state['volume'] == 100, "Default volume should be 100"
    assert state['pan'] == 64, "Default pan should be 64 (center)"
    print("✓ Initial state correct")

    # Test controller changes
    controllers = [
        {'time': 0.0, 'channel': 0, 'controller': 7, 'value': 80}  # Volume
    ]
    manager.apply_events([], controllers, [])

    state = manager.get_state(0)
    assert state['volume'] == 80, "Volume should be updated to 80"
    print("✓ Controller changes applied")

    # Test effective velocity
    effective = manager.calculate_effective_velocity(0, 100)
    assert effective < 100, "Effective velocity should be scaled by volume"
    print(f"✓ Effective velocity: {effective}")

    # Test pan
    left, right = manager.get_pan_stereo_gains(0)
    assert 0 <= left <= 1, "Left gain out of range"
    assert 0 <= right <= 1, "Right gain out of range"
    print(f"✓ Pan gains: L={left:.2f}, R={right:.2f}")

    print("✓ Controller Manager test PASSED")
    return True


def test_instrument_engine():
    """Test instrument engine module."""
    print("\n" + "=" * 60)
    print("Test 3: Instrument Engine")
    print("=" * 60)

    from modules.instrument_engine import InstrumentEngine

    engine = InstrumentEngine(sample_rate=44100)

    # Test piano synthesis
    audio = engine.synthesize_note(60, 80, 0.5, program=0, channel=0)
    assert len(audio) == int(0.5 * 44100), "Audio length incorrect"
    assert audio.dtype == np.float32, "Audio should be float32"
    assert np.max(np.abs(audio)) <= 1.0, "Audio exceeds ±1.0"
    print(f"✓ Piano note synthesized: {len(audio)} samples")

    # Test different instruments
    programs = [0, 16, 40, 56]  # Piano, Organ, Violin, Trumpet
    for program in programs:
        audio = engine.synthesize_note(60, 80, 0.1, program=program, channel=0)
        assert len(audio) > 0, f"Program {program} failed"
    print(f"✓ Multiple instruments tested")

    # Test percussion (channel 9)
    audio = engine.synthesize_note(35, 100, 0.2, program=0, channel=9)
    assert len(audio) > 0, "Percussion failed"
    print("✓ Percussion synthesized")

    print("✓ Instrument Engine test PASSED")
    return True


def test_audio_mixer():
    """Test audio mixer module."""
    print("\n" + "=" * 60)
    print("Test 4: Audio Mixer")
    print("=" * 60)

    from modules.audio_mixer import AudioMixer
    from modules.instrument_engine import InstrumentEngine

    mixer = AudioMixer(sample_rate=44100)
    engine = InstrumentEngine(sample_rate=44100)

    # Create test notes
    notes = [
        {'start': 0.0, 'duration': 0.5, 'channel': 0, 'note': 60, 'velocity': 80},
        {'start': 0.5, 'duration': 0.5, 'channel': 0, 'note': 64, 'velocity': 80},
    ]

    # Synthesize notes
    note_audio = {}
    for idx, note in enumerate(notes):
        audio = engine.synthesize_note(note['note'], note['velocity'], note['duration'])
        note_audio[idx] = audio

    # Mix
    mixed = mixer.mix_notes(notes, note_audio, total_duration=1.0, stereo=True)

    assert mixed.shape == (44100, 2), f"Mixed shape incorrect: {mixed.shape}"
    assert mixed.dtype == np.float32, "Mixed should be float32"
    print(f"✓ Mixed audio: {mixed.shape}")

    # Test clipping detection
    stats = mixer.check_clipping(mixed)
    print(f"✓ Clipping check: {stats['num_clipped']} samples, peak: {stats['peak']:.4f}")

    print("✓ Audio Mixer test PASSED")
    return True


def test_effects_processor():
    """Test effects processor module."""
    print("\n" + "=" * 60)
    print("Test 5: Effects Processor")
    print("=" * 60)

    from modules.effects_processor import EffectsProcessor

    effects = EffectsProcessor(sample_rate=44100)

    # Create test audio (1 second of noise)
    audio = np.random.uniform(-0.1, 0.1, (44100, 2)).astype(np.float32)

    # Test reverb
    reverbed = effects.apply_reverb(audio, wet=0.3)
    assert reverbed.shape == audio.shape, "Reverb changed shape"
    print("✓ Reverb applied")

    # Test chorus
    chorused = effects.apply_chorus(audio, wet=0.2)
    assert chorused.shape == audio.shape, "Chorus changed shape"
    print("✓ Chorus applied")

    # Test compression
    compressed = effects.apply_compression(audio, threshold=-20, ratio=4.0)
    assert compressed.shape == audio.shape, "Compression changed shape"
    print("✓ Compression applied")

    print("✓ Effects Processor test PASSED")
    return True


def test_master_processor():
    """Test master processor module."""
    print("\n" + "=" * 60)
    print("Test 6: Master Processor")
    print("=" * 60)

    from modules.master_processor import MasterProcessor

    master = MasterProcessor(sample_rate=44100)

    # Create test audio
    audio = np.random.uniform(-0.5, 0.5, (44100, 2)).astype(np.float32)

    # Test soft limiting
    limited = master.soft_limit(audio, threshold=0.8, ceiling=1.0)
    assert np.max(np.abs(limited)) <= 1.0, "Limiter failed"
    print(f"✓ Soft limiter applied, peak: {np.max(np.abs(limited)):.4f}")

    # Test normalization
    normalized = master.normalize(audio, target_peak=0.95)
    peak = np.max(np.abs(normalized))
    assert 0.94 <= peak <= 0.96, f"Normalization failed: peak={peak}"
    print(f"✓ Normalized to peak: {peak:.4f}")

    # Test analysis
    stats = master.analyze_audio(audio)
    assert 'peak' in stats, "Analysis missing peak"
    assert 'rms' in stats, "Analysis missing RMS"
    print(f"✓ Analysis: peak={stats['peak_db']:.2f}dB, rms={stats['rms_db']:.2f}dB")

    # Test int16 conversion
    audio_int16 = master.to_int16(audio)
    assert audio_int16.dtype == np.int16, "Conversion failed"
    print("✓ Int16 conversion successful")

    print("✓ Master Processor test PASSED")
    return True


def test_full_synthesis():
    """Test full synthesis pipeline."""
    print("\n" + "=" * 60)
    print("Test 7: Full Synthesis Pipeline")
    print("=" * 60)

    from modules.synthesizer import MIDISynthesizer

    # Create test MIDI if needed
    test_file = Path('test_files/simple.mid')
    if not test_file.exists():
        from create_test_midi import create_simple_midi
        create_simple_midi()

    synth = MIDISynthesizer(sample_rate=44100, reverb_enabled=True)

    # Synthesize
    audio = synth.synthesize_file(str(test_file), reverb_wet=0.3, target_peak=0.95)

    assert audio.ndim == 2, "Output should be stereo"
    assert audio.shape[1] == 2, "Output should have 2 channels"
    assert audio.dtype == np.float32, "Output should be float32"
    assert np.max(np.abs(audio)) <= 1.0, "Output exceeds ±1.0"

    print(f"✓ Synthesized audio: {audio.shape}")
    print(f"  Peak: {np.max(np.abs(audio)):.4f}")

    # Test save
    output_path = Path('test_output.wav')
    synth.save_wav(str(output_path), audio)

    assert output_path.exists(), "WAV file not created"
    print(f"✓ Saved to: {output_path}")

    # Clean up
    output_path.unlink()
    print("✓ Cleanup complete")

    print("✓ Full Synthesis test PASSED")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("MODULAR MIDI SYNTHESIZER - TEST SUITE")
    print("=" * 60)

    tests = [
        test_midi_parser,
        test_controller_manager,
        test_instrument_engine,
        test_audio_mixer,
        test_effects_processor,
        test_master_processor,
        test_full_synthesis,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n✗ {test.__name__} FAILED")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
