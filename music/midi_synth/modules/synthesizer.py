"""
MIDI Synthesizer - Main Orchestrator

Responsibility: Coordinate all modules to synthesize MIDI files

This is the high-level interface that users interact with.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict
import wave

from .midi_parser import MIDIParser
from .controller_manager import ControllerManager
from .instrument_engine import InstrumentEngine
from .effects_processor import EffectsProcessor
from .audio_mixer import AudioMixer
from .master_processor import MasterProcessor


class MIDISynthesizer:
    """
    Complete MIDI to WAV synthesizer with modular architecture.

    Usage:
        synth = MIDISynthesizer(sample_rate=44100)
        audio = synth.synthesize_file('input.mid')
        synth.save_wav('output.wav', audio)
    """

    def __init__(self, sample_rate: int = 44100,
                 reverb_enabled: bool = True,
                 chorus_enabled: bool = False):
        """
        Initialize MIDI synthesizer.

        Args:
            sample_rate: Audio sample rate in Hz
            reverb_enabled: Enable reverb effect
            chorus_enabled: Enable chorus effect
        """
        self.sample_rate = sample_rate
        self.reverb_enabled = reverb_enabled
        self.chorus_enabled = chorus_enabled

        # Initialize modules
        self.parser = MIDIParser()
        self.controller_manager = ControllerManager()
        self.instrument_engine = InstrumentEngine(sample_rate)
        self.effects = EffectsProcessor(sample_rate)
        self.mixer = AudioMixer(sample_rate)
        self.master = MasterProcessor(sample_rate)

    def synthesize_file(self, midi_path: str,
                       reverb_wet: float = 0.3,
                       chorus_wet: float = 0.2,
                       target_peak: float = 0.95,
                       stereo: bool = True) -> np.ndarray:
        """
        Synthesize MIDI file to audio.

        Args:
            midi_path: Path to MIDI file
            reverb_wet: Reverb wet/dry mix (0.0 to 1.0)
            chorus_wet: Chorus wet/dry mix (0.0 to 1.0)
            target_peak: Target peak level for final audio
            stereo: Output stereo (True) or mono (False)

        Returns:
            Audio array (float32, -1.0 to 1.0)
        """
        # Step 1: Parse MIDI file
        print(f"Parsing MIDI file: {midi_path}")
        midi_data = self.parser.parse_file(midi_path)

        notes = midi_data['notes']
        program_changes = midi_data['program_changes']
        controllers = midi_data['controllers']
        pitch_bends = midi_data['pitch_bends']
        duration = midi_data['duration']

        print(f"Found {len(notes)} notes, duration: {duration:.2f}s")

        # Step 2: Apply controller events to manager
        self.controller_manager.apply_events(program_changes, controllers, pitch_bends)

        # Step 3: Synthesize each note
        print("Synthesizing notes...")
        note_audio = {}

        for idx, note in enumerate(notes):
            channel = note['channel']
            midi_note = note['note']
            velocity = note['velocity']
            note_duration = note['duration']

            # Get controller state for this channel
            state = self.controller_manager.get_state(channel)
            program = state['program']

            # Calculate effective velocity (considering volume and expression)
            effective_velocity = self.controller_manager.calculate_effective_velocity(
                channel, velocity
            )

            # Calculate pitch bend
            pitch_bend_semitones = self.controller_manager.calculate_pitch_bend_semitones(channel)
            midi_note_bent = midi_note + pitch_bend_semitones

            # Extend duration if sustain pedal is on
            if self.controller_manager.should_extend_duration(channel):
                note_duration = note_duration * 1.5

            # Synthesize note
            audio = self.instrument_engine.synthesize_note(
                midi_note_bent, effective_velocity, note_duration,
                program, channel
            )

            note_audio[idx] = audio

            # Progress indicator
            if (idx + 1) % 100 == 0:
                print(f"  Synthesized {idx + 1}/{len(notes)} notes")

        print(f"Synthesized {len(notes)} notes")

        # Step 4: Get pan settings for each channel
        pan_per_channel = {}
        for ch in range(16):
            pan_per_channel[ch] = self.controller_manager.get_pan_stereo_gains(ch)

        # Step 5: Mix notes
        print("Mixing audio...")
        mixed_audio = self.mixer.mix_notes(
            notes, note_audio, duration,
            pan_per_channel=pan_per_channel,
            stereo=stereo
        )

        # Check for clipping before effects
        clipping_stats = self.mixer.check_clipping(mixed_audio)
        if clipping_stats['num_clipped'] > 0:
            print(f"Warning: {clipping_stats['num_clipped']} samples clipping before effects")

        # Step 6: Apply effects
        if self.reverb_enabled and reverb_wet > 0:
            print(f"Applying reverb (wet: {reverb_wet:.2f})...")
            mixed_audio = self.effects.apply_reverb(mixed_audio, wet=reverb_wet)

        if self.chorus_enabled and chorus_wet > 0:
            print(f"Applying chorus (wet: {chorus_wet:.2f})...")
            mixed_audio = self.effects.apply_chorus(mixed_audio, wet=chorus_wet)

        # Step 7: Master processing
        print("Mastering...")
        final_audio = self.master.master(
            mixed_audio,
            target_peak=target_peak,
            use_limiter=True,
            use_dither=False
        )

        # Step 8: Analyze final audio
        stats = self.master.analyze_audio(final_audio)
        print(f"Final audio stats:")
        print(f"  Peak: {stats['peak']:.4f} ({stats['peak_db']:.2f} dB)")
        print(f"  RMS: {stats['rms']:.4f} ({stats['rms_db']:.2f} dB)")
        print(f"  Dynamic range: {stats['dynamic_range_db']:.2f} dB")
        print(f"  Duration: {stats['duration_seconds']:.2f}s")

        if stats['clipped_samples'] > 0:
            print(f"  Warning: {stats['clipped_samples']} samples clipping ({stats['clipping_percentage']:.2f}%)")

        return final_audio

    def save_wav(self, output_path: str, audio: np.ndarray,
                bit_depth: int = 16):
        """
        Save audio to WAV file.

        Args:
            output_path: Output file path
            audio: Audio array (float32, -1.0 to 1.0)
            bit_depth: Bit depth (16 or 24)
        """
        output_path = Path(output_path)

        # Convert to int16
        if bit_depth == 16:
            audio_int = self.master.to_int16(audio, apply_dither=True)
        elif bit_depth == 24:
            # 24-bit conversion
            audio = np.clip(audio, -1.0, 1.0)
            max_value = 2 ** 23 - 1
            audio_int = (audio * max_value).astype(np.int32)
        else:
            raise ValueError(f"Unsupported bit depth: {bit_depth}")

        # Determine number of channels
        if audio.ndim == 1:
            num_channels = 1
        else:
            num_channels = audio.shape[1]

        # Write WAV file
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(self.sample_rate)

            if bit_depth == 16:
                wav_file.writeframes(audio_int.tobytes())
            elif bit_depth == 24:
                # 24-bit requires special handling
                # Python wave module doesn't directly support 24-bit
                # We need to use scipy or numpy
                import scipy.io.wavfile as wavfile
                wavfile.write(str(output_path), self.sample_rate, audio_int)

        print(f"Saved WAV file: {output_path}")

    def synthesize_and_save(self, midi_path: str, output_path: str,
                           reverb_wet: float = 0.3,
                           chorus_wet: float = 0.2,
                           target_peak: float = 0.95,
                           bit_depth: int = 16):
        """
        Convenience method: synthesize and save in one call.

        Args:
            midi_path: Input MIDI file path
            output_path: Output WAV file path
            reverb_wet: Reverb wet/dry mix
            chorus_wet: Chorus wet/dry mix
            target_peak: Target peak level
            bit_depth: Output bit depth (16 or 24)
        """
        audio = self.synthesize_file(
            midi_path,
            reverb_wet=reverb_wet,
            chorus_wet=chorus_wet,
            target_peak=target_peak
        )

        self.save_wav(output_path, audio, bit_depth=bit_depth)


def main():
    """
    Command-line interface for MIDI synthesizer.

    Usage:
        python -m modules.synthesizer input.mid output.wav
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m modules.synthesizer <input.mid> <output.wav>")
        print("\nOptional arguments:")
        print("  --reverb-wet <0.0-1.0>    Reverb wet/dry mix (default: 0.3)")
        print("  --chorus-wet <0.0-1.0>    Chorus wet/dry mix (default: 0.0)")
        print("  --no-reverb               Disable reverb")
        print("  --chorus                  Enable chorus")
        print("  --peak <0.0-1.0>          Target peak level (default: 0.95)")
        print("  --bit-depth <16|24>       Output bit depth (default: 16)")
        sys.exit(1)

    midi_path = sys.argv[1]
    output_path = sys.argv[2]

    # Parse optional arguments
    reverb_wet = 0.3
    chorus_wet = 0.0
    reverb_enabled = True
    chorus_enabled = False
    target_peak = 0.95
    bit_depth = 16

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--reverb-wet' and i + 1 < len(sys.argv):
            reverb_wet = float(sys.argv[i + 1])
            i += 2
        elif arg == '--chorus-wet' and i + 1 < len(sys.argv):
            chorus_wet = float(sys.argv[i + 1])
            chorus_enabled = True
            i += 2
        elif arg == '--no-reverb':
            reverb_enabled = False
            i += 1
        elif arg == '--chorus':
            chorus_enabled = True
            chorus_wet = 0.2
            i += 1
        elif arg == '--peak' and i + 1 < len(sys.argv):
            target_peak = float(sys.argv[i + 1])
            i += 2
        elif arg == '--bit-depth' and i + 1 < len(sys.argv):
            bit_depth = int(sys.argv[i + 1])
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            i += 1

    # Create synthesizer
    synth = MIDISynthesizer(
        sample_rate=44100,
        reverb_enabled=reverb_enabled,
        chorus_enabled=chorus_enabled
    )

    # Synthesize and save
    synth.synthesize_and_save(
        midi_path,
        output_path,
        reverb_wet=reverb_wet,
        chorus_wet=chorus_wet,
        target_peak=target_peak,
        bit_depth=bit_depth
    )


if __name__ == '__main__':
    main()
