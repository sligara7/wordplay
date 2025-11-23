#!/usr/bin/env python3
"""
Test Pitch Detection on Iowa Piano Samples

Tests Phase 2 pitch detection on single-note piano recordings with known pitch.

Iowa samples format: Piano.{dynamic}.{note}.aiff.wav
- Example: Piano.ff.C4.aiff.wav → Ground truth: C4 (MIDI 60)

Success criteria:
- Pitch accuracy > 95% (within ±1 semitone)
- Octave accuracy > 99% (correct octave)
"""

import sys
import numpy as np
from pathlib import Path
from scipy.io import wavfile
import random

from onset_detector import OnsetDetector
from pitch_detector import PitchDetector, freq_to_midi, midi_to_note_name, note_name_to_midi


def parse_iowa_filename(filename):
    """
    Parse Iowa piano sample filename.

    Format: Piano.{dynamic}.{note}.aiff.wav
    Example: Piano.ff.C4.aiff.wav

    Returns:
        Dict with dynamic, note_name, midi_note
    """
    stem = Path(filename).stem  # Remove .wav
    parts = stem.split('.')

    if len(parts) >= 3 and parts[0] == 'Piano':
        note_name = parts[2]  # C4, A4, Gb3, etc.
        midi_note = note_name_to_midi(note_name)

        return {
            'dynamic': parts[1],  # pp, mf, ff
            'note_name': note_name,
            'midi_note': midi_note,
            'filename': filename
        }
    else:
        return {
            'dynamic': 'unknown',
            'note_name': 'unknown',
            'midi_note': 0,
            'filename': filename
        }


def load_audio(wav_path):
    """Load and normalize audio file."""
    sample_rate, audio = wavfile.read(wav_path)

    # Store original dtype
    original_dtype = audio.dtype

    # Convert to mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    # Normalize
    if original_dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif original_dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype in [np.float32, np.float64]:
        if np.max(np.abs(audio)) > 2.0:
            audio = audio.astype(np.float32) / 32768.0
        else:
            audio = audio.astype(np.float32)

    return sample_rate, audio


def test_single_pitch(wav_path, onset_detector, pitch_detector, verbose=False):
    """
    Test pitch detection on a single Iowa piano sample.

    Args:
        wav_path: Path to piano WAV file
        onset_detector: OnsetDetector instance
        pitch_detector: PitchDetector instance
        verbose: Print details

    Returns:
        Dict with results
    """
    # Parse ground truth
    metadata = parse_iowa_filename(wav_path)
    gt_midi = metadata['midi_note']
    gt_note = metadata['note_name']

    # Load audio
    sample_rate, audio = load_audio(wav_path)

    # Detect onset
    onsets = onset_detector.detect_onsets_combined(audio, first_onset_only=True)

    if len(onsets) == 0:
        if verbose:
            print(f"✗ {gt_note:5s}: No onset detected")
        return {
            'filename': Path(wav_path).name,
            'gt_note': gt_note,
            'gt_midi': gt_midi,
            'detected_freq': 0,
            'detected_midi': 0,
            'detected_note': 'None',
            'onset_detected': False,
            'pitch_correct': False,
            'octave_correct': False,
            'semitone_error': 999
        }

    # Detect pitch
    onset_time = onsets[0]
    detected_freq = pitch_detector.detect_pitch(audio, onset_time, window_duration=0.1)

    if detected_freq == 0:
        if verbose:
            print(f"✗ {gt_note:5s}: Onset detected but no pitch")
        return {
            'filename': Path(wav_path).name,
            'gt_note': gt_note,
            'gt_midi': gt_midi,
            'detected_freq': 0,
            'detected_midi': 0,
            'detected_note': 'None',
            'onset_detected': True,
            'pitch_correct': False,
            'octave_correct': False,
            'semitone_error': 999
        }

    # Convert to MIDI
    detected_midi = freq_to_midi(detected_freq)
    detected_note = midi_to_note_name(detected_midi)

    # Evaluate
    semitone_error = abs(detected_midi - gt_midi)
    pitch_correct = semitone_error <= 1  # Within ±1 semitone
    octave_correct = (detected_midi % 12) == (gt_midi % 12)  # Same note, any octave

    if verbose:
        status = "✓" if pitch_correct else "✗"
        error_str = ""
        if semitone_error > 1:
            error_str = f" (error: {detected_midi - gt_midi:+d} semitones)"

        print(f"{status} {gt_note:5s} → {detected_note:5s} ({detected_freq:7.2f} Hz){error_str}")

    return {
        'filename': Path(wav_path).name,
        'gt_note': gt_note,
        'gt_midi': gt_midi,
        'detected_freq': detected_freq,
        'detected_midi': detected_midi,
        'detected_note': detected_note,
        'onset_detected': True,
        'pitch_correct': pitch_correct,
        'octave_correct': octave_correct,
        'semitone_error': semitone_error
    }


def test_pitch_on_iowa_samples(iowa_dir, samples_per_dynamic=30, sample_all_notes=False):
    """
    Test pitch detection on Iowa piano samples.

    Args:
        iowa_dir: Directory with Iowa piano WAV files
        samples_per_dynamic: Number of samples to test per dynamic
        sample_all_notes: If True, test all notes instead of random sampling

    Returns:
        Results dict
    """
    iowa_dir = Path(iowa_dir)

    print("="*80)
    print("TESTING PITCH DETECTION ON IOWA PIANO SAMPLES")
    print("="*80)
    print(f"Iowa samples: {iowa_dir}")
    print(f"Sampling: {'All notes' if sample_all_notes else f'{samples_per_dynamic} per dynamic'}")
    print()

    # Find all piano samples
    all_files = list(iowa_dir.glob("Piano.*.wav"))

    if not all_files:
        print(f"ERROR: No WAV files found in {iowa_dir}")
        return None

    print(f"Total Iowa samples available: {len(all_files)}")
    print()

    # Initialize detectors
    onset_detector = OnsetDetector(sample_rate=44100, onset_threshold=0.25)
    pitch_detector = PitchDetector(sample_rate=44100, fft_size=8192)

    # Select samples to test
    if sample_all_notes:
        # Test all samples
        test_files = all_files
    else:
        # Group by dynamic and sample
        by_dynamic = {}
        for f in all_files:
            metadata = parse_iowa_filename(f)
            dynamic = metadata['dynamic']
            if dynamic not in by_dynamic:
                by_dynamic[dynamic] = []
            by_dynamic[dynamic].append(f)

        test_files = []
        for dynamic in ['pp', 'mf', 'ff']:
            if dynamic in by_dynamic:
                n = min(samples_per_dynamic, len(by_dynamic[dynamic]))
                test_files.extend(random.sample(by_dynamic[dynamic], n))

    print(f"Testing {len(test_files)} samples...")
    print()

    # Test each sample
    all_results = []

    for wav_path in sorted(test_files):
        result = test_single_pitch(wav_path, onset_detector, pitch_detector, verbose=True)
        all_results.append(result)

    # Summary statistics
    print()
    print("="*80)
    print("PITCH DETECTION RESULTS")
    print("="*80)
    print()

    num_tested = len(all_results)
    num_onset_detected = sum(1 for r in all_results if r['onset_detected'])
    num_pitch_detected = sum(1 for r in all_results if r['detected_freq'] > 0)
    num_pitch_correct = sum(1 for r in all_results if r['pitch_correct'])
    num_octave_correct = sum(1 for r in all_results if r['octave_correct'])

    print(f"Samples tested: {num_tested}")
    print(f"Onsets detected: {num_onset_detected}/{num_tested} ({100*num_onset_detected/num_tested:.1f}%)")
    print(f"Pitches detected: {num_pitch_detected}/{num_tested} ({100*num_pitch_detected/num_tested:.1f}%)")
    print()

    if num_pitch_detected > 0:
        pitch_accuracy = 100 * num_pitch_correct / num_pitch_detected
        octave_accuracy = 100 * num_octave_correct / num_pitch_detected

        print(f"Pitch accuracy (±1 semitone): {num_pitch_correct}/{num_pitch_detected} = {pitch_accuracy:.1f}%")
        print(f"  {'✓ PASS' if pitch_accuracy > 95 else '✗ FAIL'} (goal: > 95%)")
        print()
        print(f"Octave accuracy: {num_octave_correct}/{num_pitch_detected} = {octave_accuracy:.1f}%")
        print(f"  {'✓ PASS' if octave_accuracy > 99 else '✗ FAIL'} (goal: > 99%)")
        print()

        # Analyze errors
        errors = [r for r in all_results if r['detected_freq'] > 0 and not r['pitch_correct']]

        if errors:
            print("Error analysis:")
            print(f"  Total errors: {len(errors)}")

            # Octave errors
            octave_errors = [e for e in errors if e['semitone_error'] % 12 == 0]
            print(f"  Octave errors: {len(octave_errors)} ({100*len(octave_errors)/len(errors):.1f}% of errors)")

            # Semitone error distribution
            semitone_errors = [r['semitone_error'] for r in all_results if r['detected_freq'] > 0]
            avg_error = np.mean(semitone_errors)
            max_error = np.max(semitone_errors)

            print(f"  Average semitone error: {avg_error:.2f}")
            print(f"  Maximum semitone error: {max_error}")

            # Show some examples
            print()
            print("Example errors:")
            for e in errors[:5]:
                print(f"    {e['gt_note']:5s} → {e['detected_note']:5s} "
                      f"(error: {e['detected_midi'] - e['gt_midi']:+d} semitones)")
        else:
            print("No errors! Perfect pitch detection!")

        print()
        print("="*80)

        if pitch_accuracy > 95 and octave_accuracy > 99:
            print("✓ PHASE 2 PITCH DETECTION GOALS ACHIEVED!")
        elif pitch_accuracy > 95:
            print("✓ Pitch accuracy goal achieved!")
            print("✗ Octave accuracy needs improvement")
        else:
            print("✗ Pitch detection needs improvement")
            print()
            print("Suggestions:")
            if len(octave_errors) > len(errors) * 0.5:
                print("  - Many octave errors: Improve harmonic analysis")
                print("  - Try larger FFT size for better freq resolution")
            else:
                print("  - Tune harmonic matching tolerance")
                print("  - Check spectral peak detection threshold")

        print("="*80)

        return {
            'pitch_accuracy': pitch_accuracy,
            'octave_accuracy': octave_accuracy,
            'num_tested': num_tested,
            'num_correct': num_pitch_correct,
            'all_results': all_results
        }
    else:
        print("No pitches detected!")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_pitch_iowa.py IOWA_DIR [SAMPLES_PER_DYNAMIC]")
        print()
        print("Options:")
        print("  SAMPLES_PER_DYNAMIC: Number to test per dynamic (default: 30)")
        print("  Use 'all' to test all samples")
        print()
        print("Example:")
        print("  python test_pitch_iowa.py /home/ajs7/Downloads/iowawav 30")
        print("  python test_pitch_iowa.py /home/ajs7/Downloads/iowawav all")
        sys.exit(1)

    iowa_dir = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == 'all':
        sample_all_notes = True
        samples_per_dynamic = 0
    else:
        sample_all_notes = False
        samples_per_dynamic = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    test_pitch_on_iowa_samples(iowa_dir, samples_per_dynamic=samples_per_dynamic,
                                sample_all_notes=sample_all_notes)
