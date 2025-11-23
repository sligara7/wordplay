#!/usr/bin/env python3
"""
Pipeline2 V2: Using Existing UltraFastChordDetector and Multi-Octave PSFs

This version uses the PROVEN components from test_roundtrip_hard_mode.py:
- UltraFastChordDetector (ultra_fast_detector.py)
- Multi-octave PSF templates (multi_octave_psf_templates.pkl)
- spectral_analyzer.py

This is the ACTUAL implementation you were already using!
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from scipy.io import wavfile

# Import from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from spectral_analyzer import SpectralAnalyzer
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs

# Import local midi_synthesizer
from midi_synthesizer import MIDISynthesizer


class Pipeline2Complete:
    """
    Complete Pipeline2 using proven MHT components.

    Flow:
        MIDI → Synthesized WAV → Spectral Analysis → UltraFastChordDetector → Validation
    """

    def __init__(self,
                 sample_rate: int = 44100,
                 spectral_cycles: int = 4,
                 psf_template_file: str = "multi_octave_psf_templates.pkl",
                 mht_threshold: float = 6.5,
                 use_outlier_removal: bool = True):
        """
        Initialize pipeline with proven components.

        Args:
            sample_rate: Audio sample rate
            spectral_cycles: Cycles for spectral analysis
            psf_template_file: Path to PSF templates pickle
            mht_threshold: SNR threshold for detection
            use_outlier_removal: Use MHTOR outlier removal
        """
        self.sample_rate = sample_rate
        self.spectral_cycles = spectral_cycles
        self.mht_threshold = mht_threshold
        self.use_outlier_removal = use_outlier_removal

        # Initialize MIDI synthesizer
        self.midi_synth = MIDISynthesizer(sample_rate=sample_rate)

        # Load PSF templates
        psf_path = Path(__file__).parent.parent / psf_template_file

        if not psf_path.exists():
            raise FileNotFoundError(
                f"PSF template file not found: {psf_path}\n"
                f"Please run: python build_multi_octave_psf.py"
            )

        print(f"Loading PSF templates from {psf_path}...")
        templates, frequencies, metadata = load_multi_octave_psfs(str(psf_path))
        print(f"  Loaded {len(templates)} templates")
        print()

        # Initialize spectral analyzer
        self.spectral_analyzer = SpectralAnalyzer(
            samplefreq=sample_rate,
            cycles=spectral_cycles,
            standard_A4=440.0,
            increments=12
        )

        # Initialize UltraFastChordDetector
        self.detector = UltraFastChordDetector(
            psf_templates=templates,
            threshold=mht_threshold,
            use_outlier_removal=use_outlier_removal
        )

        print()

    def process_midi(self,
                    midi_path: str,
                    output_wav: Optional[str] = None,
                    verbose: bool = True) -> Dict:
        """
        Process MIDI file through complete pipeline.

        Args:
            midi_path: Path to MIDI file
            output_wav: Optional path to save WAV
            verbose: Print progress

        Returns:
            Dict with all results
        """
        if verbose:
            print("=" * 80)
            print("PIPELINE2 V2: MHT-BASED MUSIC ANALYSIS")
            print("=" * 80)
            print(f"Input: {midi_path}")
            print()

        # Step 1: MIDI → WAV synthesis
        if verbose:
            print("STEP 1: MIDI TO WAV SYNTHESIS")
            print("-" * 80)

        audio, midi_data = self.midi_synth.synthesize_from_file(
            midi_path,
            output_wav=output_wav,
            verbose=verbose
        )

        if verbose:
            print()

        # Step 2: Spectral analysis
        if verbose:
            print("STEP 2: SPECTRAL ANALYSIS")
            print("-" * 80)

        # Convert to int16 for spectral analyzer
        audio_int16 = (audio * 32767).astype(np.int16)

        spectral_data = self.spectral_analyzer.dotop(audio_int16)

        if verbose:
            print(f"  Spectral data shape: {spectral_data.shape}")
            print(f"  Frequencies: {len(self.spectral_analyzer.frequencies)}")
            print(f"  Time slices: {spectral_data.shape[1]}")
            print(f"  Analysis window: {self.spectral_analyzer.analysis_length:.3f}s")
            print()

        # Step 3: MHT chord detection
        if verbose:
            print("STEP 3: MHT CHORD DETECTION")
            print("-" * 80)

        results = self.detector.detect_all_time_slices(spectral_data)

        # Extract detected chords
        detected_chords = []
        time_per_slice = self.spectral_analyzer.analysis_length

        for t in range(results['num_time']):
            if results['detected_flags'][t]:
                detected_chords.append({
                    'time_slice': t,
                    'time': t * time_per_slice,
                    'chord': results['chord_names'][t],
                    'snr': results['best_snrs'][t]
                })

        if verbose:
            print(f"  Detected {len(detected_chords)} chords")
            print()

        # Step 4: Validation
        if verbose:
            print("STEP 4: VALIDATION")
            print("-" * 80)

        validation = self._validate_against_ground_truth(
            detected_chords=detected_chords,
            ground_truth_chords=midi_data['chords'],
            time_tolerance=time_per_slice * 2,  # Allow 2 time slices tolerance
            verbose=verbose
        )

        if verbose:
            print()
            print("=" * 80)
            print("PIPELINE COMPLETE")
            print("=" * 80)
            print()

        return {
            'audio': audio,
            'midi_data': midi_data,
            'spectral_data': spectral_data,
            'detected_chords': detected_chords,
            'snr_matrix': results['snr_matrix'],
            'validation': validation
        }

    def _validate_against_ground_truth(self,
                                      detected_chords: List[Dict],
                                      ground_truth_chords: List[Dict],
                                      time_tolerance: float = 0.5,
                                      verbose: bool = True) -> Dict:
        """
        Validate detected chords against MIDI ground truth.

        Since ground truth doesn't have octave info, we need to:
        1. Strip octave from detected chord names (e.g., "C_major_oct4" → "C_major")
        2. Match based on time window
        3. Compare chord types

        Args:
            detected_chords: List of detected chord dicts
            ground_truth_chords: List of ground truth chord dicts from MIDI
            time_tolerance: Time window for matching (seconds)
            verbose: Print results

        Returns:
            Dict with validation metrics
        """
        if len(ground_truth_chords) == 0:
            if verbose:
                print("  No ground truth chords found in MIDI")
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'matches': [],
                'false_positives': detected_chords,
                'false_negatives': []
            }

        # Strip octave info from detected chords
        def strip_octave(chord_name):
            """Strip _octX from chord name."""
            if chord_name and '_oct' in chord_name:
                return chord_name.rsplit('_oct', 1)[0]
            return chord_name

        # Match detected chords to ground truth
        matches = []
        unmatched_detected = []
        matched_gt_indices = set()

        for det_chord in detected_chords:
            det_time = det_chord['time']
            det_name = strip_octave(det_chord['chord'])

            # Find closest ground truth chord within tolerance
            best_match = None
            best_time_diff = float('inf')

            for gt_idx, gt_chord in enumerate(ground_truth_chords):
                gt_time = gt_chord['time']
                time_diff = abs(det_time - gt_time)

                if time_diff < time_tolerance and time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_match = (gt_idx, gt_chord)

            if best_match is not None:
                gt_idx, gt_chord = best_match
                gt_name = gt_chord['chord_name']

                # Check if chord names match (ignoring octave)
                chord_match = (det_name == gt_name)

                matches.append({
                    'detected': det_chord,
                    'ground_truth': gt_chord,
                    'time_diff': best_time_diff,
                    'chord_match': chord_match
                })

                matched_gt_indices.add(gt_idx)
            else:
                unmatched_detected.append(det_chord)

        # Find unmatched ground truth chords (false negatives)
        false_negatives = [
            gt_chord for i, gt_chord in enumerate(ground_truth_chords)
            if i not in matched_gt_indices
        ]

        # Calculate metrics
        num_correct = sum(1 for m in matches if m['chord_match'])
        num_detected = len(detected_chords)
        num_ground_truth = len(ground_truth_chords)

        precision = num_correct / num_detected if num_detected > 0 else 0.0
        recall = num_correct / num_ground_truth if num_ground_truth > 0 else 0.0
        f1_score = (2 * precision * recall / (precision + recall)
                   if (precision + recall) > 0 else 0.0)

        if verbose:
            print(f"  Ground truth chords: {num_ground_truth}")
            print(f"  Detected chords: {num_detected}")
            print(f"  Correct matches: {num_correct}")
            print(f"  False positives: {len(unmatched_detected)}")
            print(f"  False negatives: {len(false_negatives)}")
            print()
            print(f"  Precision: {precision:.1%}")
            print(f"  Recall: {recall:.1%}")
            print(f"  F1 Score: {f1_score:.1%}")
            print()

            if matches:
                print(f"  Sample matches (first 5):")
                for m in matches[:5]:
                    det = m['detected']
                    gt = m['ground_truth']
                    det_name_stripped = strip_octave(det['chord'])
                    match_str = "✓" if m['chord_match'] else "✗"
                    print(f"    {match_str} {det['time']:.2f}s: "
                          f"Detected={det_name_stripped:15s} "
                          f"GT={gt['chord_name']:15s} "
                          f"SNR={det['snr']:.1f}")

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'num_correct': num_correct,
            'num_detected': num_detected,
            'num_ground_truth': num_ground_truth,
            'matches': matches,
            'false_positives': unmatched_detected,
            'false_negatives': false_negatives
        }


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pipeline_v2.py INPUT.mid [OUTPUT.wav]")
        print()
        print("Example:")
        print("  python pipeline_v2.py examples/simple_c_major.mid test.wav")
        print()
        print("This uses the PROVEN components:")
        print("  - UltraFastChordDetector (vectorized MHT)")
        print("  - Multi-octave PSF templates")
        print("  - spectral_analyzer.py")
        sys.exit(1)

    input_midi = sys.argv[1]
    output_wav = sys.argv[2] if len(sys.argv) > 2 else None

    # Create pipeline
    pipeline = Pipeline2Complete(
        sample_rate=44100,
        spectral_cycles=4,
        psf_template_file="multi_octave_psf_templates.pkl",
        mht_threshold=6.5,
        use_outlier_removal=True
    )

    # Process
    result = pipeline.process_midi(input_midi, output_wav, verbose=True)

    # Summary
    print("SUMMARY")
    print("-" * 80)
    print(f"MIDI file: {input_midi}")
    print(f"Duration: {result['midi_data']['duration']:.2f}s")
    print(f"Notes in MIDI: {len(result['midi_data']['notes'])}")
    print(f"Chords in MIDI: {len(result['midi_data']['chords'])}")
    print(f"Detected chords: {len(result['detected_chords'])}")
    print()
    val = result['validation']
    print(f"Validation Metrics:")
    print(f"  Precision: {val['precision']:.1%}")
    print(f"  Recall: {val['recall']:.1%}")
    print(f"  F1 Score: {val['f1_score']:.1%}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
