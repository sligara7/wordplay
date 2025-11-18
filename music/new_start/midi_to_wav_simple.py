#!/usr/bin/env python3
"""
Simple MIDI to WAV Converter using reco.py

Provides a clean interface to convert MIDI files to WAV audio.
"""

import sys
import os
import numpy as np
from scipy.io.wavfile import write

# Add midi_to_wav directory to path
midi_to_wav_path = os.path.join(os.path.dirname(__file__), 'midi_to_wav')
sys.path.insert(0, midi_to_wav_path)

# Disable Google Colab warnings by mocking the module
class MockColab:
    class GoogleColab:
        @staticmethod
        def mount(path):
            pass

sys.modules['google'] = MockColab()
sys.modules['google.colab'] = MockColab.GoogleColab

# Now import reco
from reco import midi_io


def midi_to_wav(midi_path: str, wav_path: str, verbose: bool = False, sample_rate: int = 44100) -> str:
    """
    Convert MIDI file to WAV audio using reco.py synthesis engine.

    Args:
        midi_path: Path to input MIDI file
        wav_path: Path for output WAV file
        verbose: Print progress messages
        sample_rate: Sample rate in Hz (default: 44100)

    Returns:
        Path to created WAV file
    """
    if verbose:
        print(f"Converting MIDI to WAV...")
        print(f"  Input:  {midi_path}")
        print(f"  Output: {wav_path}")

    try:
        # Create MIDI I/O processor
        processor = midi_io()

        # Parse MIDI file
        if verbose:
            print(f"  Parsing MIDI file...")
        processor.midi_msg(midi_path)

        # Generate audio
        if verbose:
            print(f"  Synthesizing audio...")
        audio = processor.reco()

        # Write WAV file
        write(wav_path, sample_rate, audio)

        if verbose:
            duration = len(audio) / sample_rate
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Sample rate: {sample_rate} Hz")
            channels = audio.shape[1] if len(audio.shape) > 1 else 1
            print(f"  Channels: {channels}")
            print(f"✓ Conversion complete!")

        return wav_path

    except Exception as e:
        raise RuntimeError(f"MIDI to WAV conversion failed: {e}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert MIDI files to WAV audio"
    )
    parser.add_argument('input', help='Input MIDI file path')
    parser.add_argument('--output', '-o', help='Output WAV file path (default: INPUT.wav)')
    parser.add_argument('--sample-rate', type=int, default=44100,
                        help='Sample rate in Hz (default: 44100)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Set output path
    if args.output is None:
        from pathlib import Path
        input_path = Path(args.input)
        args.output = str(input_path.with_suffix('.wav'))

    try:
        wav_path = midi_to_wav(args.input, args.output,
                               verbose=args.verbose,
                               sample_rate=args.sample_rate)

        if not args.verbose:
            print(f"✓ Created: {wav_path}")

        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
