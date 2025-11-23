#!/usr/bin/env python3
"""
Complete Pipeline2: MIDI → Synthesis → Spectral Analysis → MHT Detection

This is the integrated pipeline that implements the original design:
1. MIDI input (ground truth)
2. Synthesize to WAV (using synthesize_instruments)
3. Spectral analysis (using spectral_analyzer.py)
4. MHT detection (vectorized, rapid matrix-based approach)
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List

from midi_synthesizer import MIDISynthesizer
from mht_pipeline import MHTChordPipeline


class MusicAnalysisPipeline:
    """
    Complete music analysis pipeline using MHT-based chord detection.

    Pipeline flow:
        MIDI → Synthesized WAV → Spectral Data → MHT Detection → Validated Chords
    """

    def __init__(self,
                 sample_rate: int = 44100,
                 spectral_cycles: int = 4,
                 mht_threshold: float = 6.5,
                 chord_types: Optional[List[str]] = None,
                 template_type: str = 'gaussian',
                 sigma_hz: float = 10.0):
        """
        Initialize complete pipeline.

        Args:
            sample_rate: Audio sample rate (Hz)
            spectral_cycles: Number of cycles for spectral analysis window
            mht_threshold: SNR threshold for MHT detection
            chord_types: List of chord types to detect (default: all)
            template_type: 'binary' or 'gaussian' for chord templates
            sigma_hz: Gaussian spread for templates (Hz)
        """
        # Initialize components
        self.midi_synth = MIDISynthesizer(sample_rate=sample_rate)
        self.mht_pipeline = MHTChordPipeline(
            sample_rate=sample_rate,
            spectral_cycles=spectral_cycles,
            chord_types=chord_types,
            mht_threshold=mht_threshold,
            template_type=template_type,
            sigma_hz=sigma_hz
        )

        self.sample_rate = sample_rate

    def process_midi(self,
                    midi_path: str,
                    output_wav: Optional[str] = None,
                    verbose: bool = True) -> Dict:
        """
        Process MIDI file through complete pipeline.

        Args:
            midi_path: Path to MIDI file
            output_wav: Optional path to save synthesized WAV
            verbose: Print progress

        Returns:
            Dict with:
                - audio: Synthesized audio
                - midi_data: MIDI ground truth (notes, chords, timing)
                - spectral_data: 2D frequency-time matrix
                - detected_chords: MHT detection results
                - validation: Comparison with ground truth
        """
        if verbose:
            print("=" * 80)
            print("PIPELINE2: MHT-BASED MUSIC ANALYSIS")
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

        # Step 2: Spectral analysis + MHT detection
        if verbose:
            print("STEP 2: SPECTRAL ANALYSIS & MHT DETECTION")
            print("-" * 80)

        detection_result = self.mht_pipeline.process_audio(audio, verbose=verbose)

        if verbose:
            print()

        # Step 3: Validation (compare detected chords with MIDI ground truth)
        if verbose:
            print("STEP 3: VALIDATION")
            print("-" * 80)

        validation = self._validate_against_ground_truth(
            detected_chords=detection_result['detected_chords'],
            ground_truth_chords=midi_data['chords'],
            analysis_length=detection_result['analysis_length'],
            verbose=verbose
        )

        if verbose:
            print()
            print("=" * 80)
            print("PIPELINE COMPLETE")
            print("=" * 80)
            print()

        # Return complete results
        return {
            'audio': audio,
            'midi_data': midi_data,
            'spectral_data': detection_result['spectral_data'],
            'detected_chords': detection_result['detected_chords'],
            'frequencies': detection_result['frequencies'],
            'analysis_length': detection_result['analysis_length'],
            'validation': validation
        }

    def _validate_against_ground_truth(self,
                                      detected_chords: List[Dict],
                                      ground_truth_chords: List[Dict],
                                      analysis_length: float,
                                      time_tolerance: float = 0.5,
                                      verbose: bool = True) -> Dict:
        """
        Validate detected chords against MIDI ground truth.

        Args:
            detected_chords: List of detected chord dicts
            ground_truth_chords: List of ground truth chord dicts from MIDI
            analysis_length: Duration of each time slice (seconds)
            time_tolerance: Time window for matching chords (seconds)
            verbose: Print results

        Returns:
            Dict with validation metrics:
                - precision: % detected chords that are correct
                - recall: % ground truth chords that were detected
                - f1_score: Harmonic mean of precision and recall
                - matches: List of (detected, ground_truth) pairs
                - false_positives: Detected chords with no match
                - false_negatives: Ground truth chords not detected
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

        # Match detected chords to ground truth
        matches = []
        unmatched_detected = []
        matched_gt_indices = set()

        for det_chord in detected_chords:
            det_time = det_chord['time']
            det_name = det_chord['chord']

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

                # Check if chord names match
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
                    match_str = "✓" if m['chord_match'] else "✗"
                    print(f"    {match_str} {det['time']:.2f}s: "
                          f"Detected={det['chord']:15s} "
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
    """Command-line interface for pipeline2."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pipeline.py INPUT.mid [OUTPUT.wav]")
        print()
        print("Example:")
        print("  python pipeline.py song.mid song.wav")
        print()
        print("This will:")
        print("  1. Synthesize MIDI to WAV")
        print("  2. Perform spectral analysis")
        print("  3. Detect chords using MHT")
        print("  4. Validate against MIDI ground truth")
        sys.exit(1)

    input_midi = sys.argv[1]
    output_wav = sys.argv[2] if len(sys.argv) > 2 else None

    # Create pipeline
    pipeline = MusicAnalysisPipeline(
        sample_rate=44100,
        spectral_cycles=4,
        mht_threshold=6.5,
        chord_types=None,  # Detect all chord types
        template_type='gaussian',
        sigma_hz=10.0
    )

    # Process MIDI file
    result = pipeline.process_midi(input_midi, output_wav, verbose=True)

    # Summary
    print("SUMMARY")
    print("-" * 80)
    print(f"MIDI file: {input_midi}")
    print(f"Duration: {result['midi_data']['duration']:.2f}s")
    print(f"Tempo: {result['midi_data']['tempo_bpm']:.1f} BPM")
    print(f"Notes in MIDI: {len(result['midi_data']['notes'])}")
    print(f"Chords in MIDI: {len(result['midi_data']['chords'])}")
    print()
    print(f"Spectral time slices: {result['spectral_data'].shape[1]}")
    print(f"Detected chords: {len(result['detected_chords'])}")
    print()
    val = result['validation']
    print(f"Validation Metrics:")
    print(f"  Precision: {val['precision']:.1%}")
    print(f"  Recall: {val['recall']:.1%}")
    print(f"  F1 Score: {val['f1_score']:.1%}")
    print()

    if output_wav:
        print(f"Saved synthesized audio: {output_wav}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
