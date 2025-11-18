#!/usr/bin/env python3
"""
Simple MIDI to WAV Converter

Converts MIDI files to WAV using the gen_all.py synthesis engine.
"""

import sys
import os
import numpy as np
from scipy.io.wavfile import write

# Add midi_to_wav/other to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'midi_to_wav/other'))

from gen_all import make_instrument


def midi_to_wav(midi_path: str, wav_path: str, verbose: bool = False) -> str:
    """
    Convert MIDI file to WAV audio.

    Args:
        midi_path: Path to input MIDI file
        wav_path: Path for output WAV file
        verbose: Print progress messages

    Returns:
        Path to created WAV file
    """
    if verbose:
        print(f"Converting MIDI to WAV...")
        print(f"  Input:  {midi_path}")
        print(f"  Output: {wav_path}")

    # Create synthesizer
    synthesizer = make_instrument()

    # Synthesize audio from MIDI
    if verbose:
        print(f"  Synthesizing audio...")

    synthesizer.make_notes(midi_path)

    # Get the synthesized audio
    audio = synthesizer.song

    # Convert to int16
    # The signal.scale() method should have already scaled to [-1, 1]
    # Convert to [-32768, 32767] range
    audio_int16 = (audio * 32767).astype(np.int16)

    # Write to file
    sample_rate = int(synthesizer.signal.sf)
    write(wav_path, sample_rate, audio_int16)

    if verbose:
        duration = len(audio) / sample_rate
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Channels: {audio.shape[1]}")
        print(f"✓ Conversion complete!")

    return wav_path


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert MIDI files to WAV audio"
    )
    parser.add_argument('input', help='Input MIDI file path')
    parser.add_argument('--output', '-o', help='Output WAV file path (default: INPUT.wav)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Set output path
    if args.output is None:
        from pathlib import Path
        input_path = Path(args.input)
        args.output = str(input_path.with_suffix('.wav'))

    try:
        wav_path = midi_to_wav(args.input, args.output, verbose=args.verbose)

        if not args.verbose:
            print(f"✓ Created: {wav_path}")

        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
