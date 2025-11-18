#!/usr/bin/env python3
"""
Test Enhanced Synthesis

Compares original reco.py (Fourier) vs enhanced (realistic instruments)
"""

import numpy as np
import sys
from pathlib import Path

# Test if we can import the enhanced synthesizer
try:
    from reco_enhanced import midi_to_wav as enhanced_midi_to_wav
    ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced synthesis not available: {e}")
    ENHANCED_AVAILABLE = False

# Original synthesis
sys.path.insert(0, str(Path(__file__).parent.parent))
from midi_to_wav_simple import midi_to_wav as original_midi_to_wav


def test_synthesis(midi_file):
    """
    Test both synthesis methods.

    Args:
        midi_file: Path to test MIDI file
    """
    print("="*80)
    print("SYNTHESIS COMPARISON TEST")
    print("="*80)
    print()

    midi_path = Path(midi_file)
    if not midi_path.exists():
        print(f"ERROR: MIDI file not found: {midi_path}")
        return

    print(f"Test MIDI: {midi_path.name}")
    print()

    # Test 1: Original reco.py (Fourier)
    print("[1/2] Original Synthesis (Fourier-based via reco.py)")
    print("-" * 80)

    original_wav = midi_path.with_name(midi_path.stem + "_original.wav")

    try:
        import time
        start = time.time()
        original_midi_to_wav(str(midi_path), str(original_wav), verbose=True)
        elapsed = time.time() - start

        print(f"✓ Time: {elapsed:.2f}s")
        print(f"✓ Output: {original_wav}")
        print()

    except Exception as e:
        print(f"✗ Original synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 2: Enhanced synthesis (realistic instruments)
    if ENHANCED_AVAILABLE:
        print("[2/2] Enhanced Synthesis (Realistic instruments)")
        print("-" * 80)

        enhanced_wav = midi_path.with_name(midi_path.stem + "_enhanced.wav")

        try:
            start = time.time()
            enhanced_midi_to_wav(str(midi_path), str(enhanced_wav), verbose=True)
            elapsed = time.time() - start

            print(f"✓ Time: {elapsed:.2f}s")
            print(f"✓ Output: {enhanced_wav}")
            print()

        except Exception as e:
            print(f"✗ Enhanced synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            print()
    else:
        print("[2/2] Enhanced Synthesis - SKIPPED (not available)")
        print()

    # Comparison
    print("="*80)
    print("COMPARISON")
    print("="*80)
    print()
    print("Original (Fourier):")
    print("  + Fast")
    print("  + Simple, predictable")
    print("  - Sounds synthetic")
    print("  - Limited timbral variety")
    print()

    if ENHANCED_AVAILABLE:
        print("Enhanced (Realistic Instruments):")
        print("  + Realistic string sounds (Karplus-Strong)")
        print("  + Brass/woodwind models")
        print("  + Instrument-specific characteristics")
        print("  - Slightly slower")
        print()
    else:
        print("Enhanced synthesis not tested (import failed)")
        print()

    print("="*80)
    print("✓ Test complete!")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_enhanced_synthesis.py INPUT.mid")
        print()
        print("Compares original Fourier synthesis vs enhanced instrument synthesis")
        print()

        # Look for test MIDI files
        test_files = list(Path("..").glob("*.mid"))
        if test_files:
            print(f"Found {len(test_files)} MIDI files in parent directory:")
            for f in test_files[:5]:
                print(f"  - {f.name}")
            if len(test_files) > 5:
                print(f"  ... and {len(test_files) - 5} more")

        sys.exit(1)

    midi_file = sys.argv[1]
    test_synthesis(midi_file)
