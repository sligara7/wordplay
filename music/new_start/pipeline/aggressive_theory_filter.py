"""
Aggressive Music Theory Filtering

Implements three levels of filtering aggressiveness:
1. SOFT: Multiplicative bonuses/penalties (default)
2. MEDIUM: Hard penalty for out-of-key chords
3. HARD: Only consider in-key chords (strict filtering)

Goal: Reduce spurious sus4/complex chord detections by using
music theory constraints more forcefully.

KNOWN LIMITATION:
- Currently detects ONE key for the entire song
- Songs with modulations (key changes mid-song) will have the minority
  key's chords filtered out in HARD mode
- Examples: "I Wanna Dance with Somebody" (Whitney Houston) modulates up
  a whole tone, "Man in the Mirror" (Michael Jackson) shifts up a semitone
- Future: Implement sliding window key detection to handle modulations

TODO: Add support for detecting key changes (modulation detection)
      - Sliding window approach: detect key in ~4-second windows
      - Merge consecutive same-key windows
      - Apply different keys to different sections
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import sys
sys.path.append('..')
from music_theory_graph import MusicTheoryGraph


class AggressiveTheoryFilter:
    """
    Aggressive music theory filtering for chord detection.

    Uses multiplicative scoring and hard constraints to enforce
    music theory rules.
    """

    def __init__(self,
                 snr_threshold=6.5,
                 top_k_candidates=10,
                 filter_mode='SOFT'):
        """
        Initialize aggressive filter.

        Args:
            snr_threshold: Minimum SNR for detection
            top_k_candidates: Number of top SNR candidates to consider
            filter_mode: 'SOFT', 'MEDIUM', or 'HARD'
                SOFT: Multiplicative bonuses (in-key: 1.5×, good-prog: 1.3×)
                MEDIUM: Out-of-key penalty (0.5×) + progression bonuses
                HARD: Only in-key chords considered
        """
        self.snr_threshold = snr_threshold
        self.top_k = top_k_candidates
        self.filter_mode = filter_mode

        # Initialize music theory graph
        self.theory = MusicTheoryGraph()

        # Scoring multipliers (for SOFT/MEDIUM modes)
        if filter_mode == 'SOFT':
            self.in_key_bonus = 1.5        # 50% bonus
            self.out_of_key_penalty = 1.0   # No penalty
            self.good_prog_bonus = 1.3      # 30% bonus
            self.bad_prog_penalty = 0.9     # 10% penalty
        elif filter_mode == 'MEDIUM':
            self.in_key_bonus = 2.0         # 100% bonus
            self.out_of_key_penalty = 0.5   # 50% penalty
            self.good_prog_bonus = 1.5      # 50% bonus
            self.bad_prog_penalty = 0.7     # 30% penalty
        else:  # HARD
            # Hard mode doesn't use multipliers (strict filtering)
            self.in_key_bonus = 1.0
            self.out_of_key_penalty = 1.0
            self.good_prog_bonus = 1.0
            self.bad_prog_penalty = 1.0

        # Common chord progressions (root movement patterns)
        self.progression_scores = {
            # Strong progressions (good)
            ('I', 'V'): 'good',    # Tonic to dominant
            ('V', 'I'): 'good',    # Dominant to tonic (authentic cadence)
            ('IV', 'I'): 'good',   # Plagal cadence
            ('ii', 'V'): 'good',   # Pre-dominant to dominant
            ('V', 'vi'): 'good',   # Deceptive cadence
            ('I', 'IV'): 'good',
            ('I', 'vi'): 'good',
            ('vi', 'IV'): 'good',
            ('IV', 'V'): 'good',
            ('vi', 'ii'): 'good',
            ('ii', 'I'): 'good',

            # Neutral (same chord)
            ('I', 'I'): 'neutral',
            ('V', 'V'): 'neutral',
            ('IV', 'IV'): 'neutral',
            ('ii', 'ii'): 'neutral',
            ('vi', 'vi'): 'neutral',

            # Weak/unusual progressions (bad)
            ('I', 'ii'): 'bad',
            ('V', 'IV'): 'bad',   # Retrograde (less common)
            ('I', 'iii'): 'bad',
        }

    def detect_with_aggressive_filtering(self,
                                         snr_matrix: np.ndarray,
                                         chord_names: List[str],
                                         time_per_slice: float) -> Dict:
        """
        Detect chords using aggressive music theory filtering.

        Args:
            snr_matrix: (num_templates, num_times) SNR values
            chord_names: List of chord names corresponding to template rows
            time_per_slice: Time duration of each slice in seconds

        Returns:
            Dict with detections, statistics, and comparison data
        """
        num_templates, num_times = snr_matrix.shape

        print("\n" + "="*80)
        print(f"AGGRESSIVE THEORY FILTERING ({self.filter_mode} MODE)")
        print("="*80)
        print(f"SNR matrix shape: {snr_matrix.shape}")
        print(f"Time slices: {num_times}")
        print(f"Templates: {num_templates}")
        print(f"Total duration: {num_times * time_per_slice:.2f}s")
        print(f"Filter mode: {self.filter_mode}")

        if self.filter_mode == 'SOFT':
            print(f"  In-key bonus: {self.in_key_bonus}×")
            print(f"  Good progression bonus: {self.good_prog_bonus}×")
        elif self.filter_mode == 'MEDIUM':
            print(f"  In-key bonus: {self.in_key_bonus}×")
            print(f"  Out-of-key penalty: {self.out_of_key_penalty}×")
            print(f"  Good progression bonus: {self.good_prog_bonus}×")
            print(f"  Bad progression penalty: {self.bad_prog_penalty}×")
        else:  # HARD
            print(f"  Hard filtering: Only in-key chords considered")
        print()

        # Step 1: Detect overall key from SNR patterns
        detected_key = self._detect_key_from_snr(snr_matrix, chord_names)
        print(f"Detected key: {detected_key}")
        print()

        # Step 2: Get scale chords for detected key
        key_chords = self._get_key_chords(detected_key)
        print(f"Scale chords in {detected_key}: {len(key_chords)} chords")

        # Count in-key templates
        in_key_template_count = sum(1 for name in chord_names if name in key_chords)
        print(f"In-key templates: {in_key_template_count}/{len(chord_names)} ({100*in_key_template_count/len(chord_names):.1f}%)")
        print()

        # Step 3: Process each time slice with aggressive filtering
        detections = []
        previous_chord = None

        # Statistics
        num_changed_by_theory = 0
        num_in_key = 0
        num_filtered_out = 0
        num_good_progressions = 0
        num_bad_progressions = 0

        print("Processing time slices with aggressive filtering...")

        for time_idx in range(num_times):
            time_seconds = time_idx * time_per_slice

            # Get SNR values for this time
            snr_values = snr_matrix[:, time_idx]

            # Get top-K candidates
            top_k_indices = np.argsort(snr_values)[-self.top_k:][::-1]
            top_k_snrs = snr_values[top_k_indices]

            # Filter: only consider candidates above threshold
            valid_mask = top_k_snrs > self.snr_threshold
            if not np.any(valid_mask):
                num_filtered_out += 1
                continue

            top_k_indices = top_k_indices[valid_mask]
            top_k_snrs = top_k_snrs[valid_mask]

            # Build candidate list
            candidates = []
            for idx, snr in zip(top_k_indices, top_k_snrs):
                chord_name = chord_names[idx]
                root, chord_type, octave = self._parse_chord_name(chord_name)

                is_in_key = chord_name in key_chords

                # HARD mode: Skip out-of-key chords completely
                if self.filter_mode == 'HARD' and not is_in_key:
                    continue

                candidates.append({
                    'chord': chord_name,
                    'snr': snr,
                    'root': root,
                    'chord_type': chord_type,
                    'octave': octave,
                    'in_key': is_in_key,
                    'template_idx': idx
                })

            # If HARD mode filtered everything out, skip this time
            if not candidates:
                num_filtered_out += 1
                continue

            # Score each candidate
            scored_candidates = []
            for candidate in candidates:
                # Start with SNR as base score
                score = candidate['snr']

                # Apply in-key bonus/penalty (SOFT/MEDIUM modes)
                if self.filter_mode in ['SOFT', 'MEDIUM']:
                    if candidate['in_key']:
                        score *= self.in_key_bonus
                    else:
                        score *= self.out_of_key_penalty

                # Apply progression bonus/penalty
                prog_quality = None
                if previous_chord:
                    prev_root, prev_type, _ = self._parse_chord_name(previous_chord)

                    # Get Roman numeral functions
                    prev_func = self._get_chord_function(prev_root, prev_type, detected_key)
                    curr_func = self._get_chord_function(candidate['root'], candidate['chord_type'], detected_key)

                    # Look up progression quality
                    prog_key = (prev_func, curr_func)
                    prog_quality = self.progression_scores.get(prog_key, 'neutral')

                    # Apply multipliers
                    if prog_quality == 'good':
                        score *= self.good_prog_bonus
                    elif prog_quality == 'bad' and self.filter_mode in ['MEDIUM', 'HARD']:
                        score *= self.bad_prog_penalty

                scored_candidates.append({
                    **candidate,
                    'total_score': score,
                    'prog_quality': prog_quality
                })

            # Choose best candidate by total score
            if scored_candidates:
                best = max(scored_candidates, key=lambda x: x['total_score'])

                # Also get pure SNR winner for comparison
                best_snr_candidate = max(scored_candidates, key=lambda x: x['snr'])

                # Track statistics
                if best['in_key']:
                    num_in_key += 1

                if best['chord'] != best_snr_candidate['chord']:
                    num_changed_by_theory += 1

                if best.get('prog_quality') == 'good':
                    num_good_progressions += 1
                elif best.get('prog_quality') == 'bad':
                    num_bad_progressions += 1

                detections.append({
                    'time': time_seconds,
                    'chord': best['chord'],
                    'snr': best['snr'],
                    'total_score': best['total_score'],
                    'in_key': best['in_key'],
                    'key': detected_key,
                    'prog_quality': best.get('prog_quality')
                })

                previous_chord = best['chord']

        print(f"✓ Detected {len(detections)} chord events")
        print()

        # Print statistics
        total_processed = num_times - num_filtered_out
        print(f"{self.filter_mode} MODE STATISTICS:")
        print(f"  Time slices processed: {total_processed}/{num_times}")
        print(f"  Time slices filtered out: {num_filtered_out}/{num_times} ({100*num_filtered_out/num_times if num_times > 0 else 0:.1f}%)")
        print(f"  Chords in detected key: {num_in_key}/{len(detections)} ({100*num_in_key/len(detections) if len(detections) > 0 else 0:.1f}%)")
        print(f"  Times theory changed winner: {num_changed_by_theory}/{len(detections)} ({100*num_changed_by_theory/len(detections) if len(detections) > 0 else 0:.1f}%)")
        print(f"  Good progressions: {num_good_progressions}")
        print(f"  Bad progressions: {num_bad_progressions}")
        print()

        # Step 4: Merge consecutive same chords
        merged = self._merge_consecutive_chords(detections, time_per_slice)

        print(f"✓ Merged into {len(merged)} chord segments")
        print()

        return {
            'detections': merged,
            'key': detected_key,
            'stats': {
                'num_in_key': num_in_key,
                'num_changed_by_theory': num_changed_by_theory,
                'num_filtered_out': num_filtered_out,
                'num_good_progressions': num_good_progressions,
                'num_bad_progressions': num_bad_progressions,
                'total_detections': len(detections),
                'total_segments': len(merged)
            }
        }

    def _detect_key_from_snr(self, snr_matrix: np.ndarray, chord_names: List[str]) -> str:
        """
        Detect musical key by analyzing which chords have highest total SNR.

        NOTE: This detects ONE key for the entire song by summing SNR across
        ALL time slices. Songs with modulations (key changes) will have one
        "winner" key, and chords in other sections may be filtered out.
        """
        key_scores = {}

        all_keys = [
            'C_major', 'C#_major', 'D_major', 'D#_major', 'E_major', 'F_major',
            'F#_major', 'G_major', 'G#_major', 'A_major', 'A#_major', 'B_major',
            'C_minor', 'C#_minor', 'D_minor', 'D#_minor', 'E_minor', 'F_minor',
            'F#_minor', 'G_minor', 'G#_minor', 'A_minor', 'A#_minor', 'B_minor',
        ]

        for key in all_keys:
            key_chords = self._get_key_chords(key)

            # Sum SNR for all chords in this key
            total_snr = 0.0
            for i, chord_name in enumerate(chord_names):
                if chord_name in key_chords:
                    # Sum across all time for this chord
                    total_snr += np.sum(snr_matrix[i, :])

            key_scores[key] = total_snr

        # Return key with highest score
        best_key = max(key_scores.items(), key=lambda x: x[1])
        return best_key[0]

    def _get_key_chords(self, key: str) -> set:
        """Get all chords that belong to a given key."""
        if not key or '_' not in key:
            return set()

        parts = key.split('_')
        root = parts[0]
        mode = parts[1] if len(parts) > 1 else 'major'

        # Get scale intervals
        if mode == 'major':
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]
            chord_qualities = ['major', 'minor', 'minor', 'major', 'major', 'minor', 'dim']
        else:  # minor
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]
            chord_qualities = ['minor', 'dim', 'major', 'minor', 'minor', 'major', 'major']

        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        root_num = note_map.get(root, 0)

        # Build scale chords
        key_chords = set()
        for interval, quality in zip(scale_intervals, chord_qualities):
            scale_note_num = (root_num + interval) % 12
            scale_note = notes[scale_note_num]

            # Add chords for all octaves
            for octave in [2, 3, 4, 5, 6]:
                chord_name = f"{scale_note}_{quality}_oct{octave}"
                key_chords.add(chord_name)

        # Also include 7th chords built on scale degrees
        seventh_chord_map = {
            'major': ['maj7', 'min7', 'min7', 'maj7', 'dom7', 'min7', 'min7'],
            'minor': ['min7', 'min7', 'maj7', 'min7', 'min7', 'maj7', 'dom7']
        }

        seventh_qualities = seventh_chord_map.get(mode, [])
        for interval, quality in zip(scale_intervals, seventh_qualities):
            scale_note_num = (root_num + interval) % 12
            scale_note = notes[scale_note_num]

            for octave in [2, 3, 4, 5, 6]:
                chord_name = f"{scale_note}_{quality}_oct{octave}"
                key_chords.add(chord_name)

        return key_chords

    def _parse_chord_name(self, chord_name: str) -> Tuple[str, str, int]:
        """Parse chord name into (root, chord_type, octave)."""
        parts = chord_name.split('_')
        root = parts[0]
        octave_str = [p for p in parts if p.startswith('oct')]
        octave = int(octave_str[0].replace('oct', '')) if octave_str else 4
        chord_type = '_'.join([p for p in parts[1:] if not p.startswith('oct')])
        return root, chord_type, octave

    def _get_chord_function(self, root: str, chord_type: str, key: str) -> str:
        """Get Roman numeral function of chord in given key."""
        if not key or '_' not in key:
            return 'I'

        key_root = key.split('_')[0]
        key_mode = key.split('_')[1] if len(key.split('_')) > 1 else 'major'

        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }

        key_root_num = note_map.get(key_root, 0)
        chord_root_num = note_map.get(root, 0)

        interval = (chord_root_num - key_root_num) % 12

        # Map interval to scale degree
        if key_mode == 'major':
            interval_to_degree = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
        else:
            interval_to_degree = {0: 1, 2: 2, 3: 3, 5: 4, 7: 5, 8: 6, 10: 7}

        degree = interval_to_degree.get(interval, 1)

        # Map degree + quality to Roman numeral
        if key_mode == 'major':
            if degree in [1, 4, 5] and 'major' in chord_type:
                return {1: 'I', 4: 'IV', 5: 'V'}[degree]
            elif degree in [2, 3, 6] and 'minor' in chord_type:
                return {2: 'ii', 3: 'iii', 6: 'vi'}[degree]
            elif degree == 7 and 'dim' in chord_type:
                return 'vii°'
        else:
            if degree in [3, 6, 7] and 'major' in chord_type:
                return {3: 'III', 6: 'VI', 7: 'VII'}[degree]
            elif degree in [1, 4, 5] and 'minor' in chord_type:
                return {1: 'i', 4: 'iv', 5: 'v'}[degree]
            elif degree == 2 and 'dim' in chord_type:
                return 'ii°'

        return 'I'

    def _merge_consecutive_chords(self, detections: List[Dict], time_per_slice: float) -> List[Dict]:
        """Merge consecutive detections of same chord into segments."""
        if not detections:
            return []

        segments = []
        current_segment = None

        for det in detections:
            if current_segment is None:
                current_segment = {
                    'start_time': det['time'],
                    'chord': det['chord'],
                    'key': det['key'],
                    'in_key': det['in_key'],
                    'snr_values': [det['snr']],
                    'num_slices': 1
                }
            elif det['chord'] == current_segment['chord']:
                current_segment['snr_values'].append(det['snr'])
                current_segment['num_slices'] += 1
            else:
                current_segment['duration'] = current_segment['num_slices'] * time_per_slice
                current_segment['avg_snr'] = np.mean(current_segment['snr_values'])
                segments.append(current_segment)

                current_segment = {
                    'start_time': det['time'],
                    'chord': det['chord'],
                    'key': det['key'],
                    'in_key': det['in_key'],
                    'snr_values': [det['snr']],
                    'num_slices': 1
                }

        if current_segment:
            current_segment['duration'] = current_segment['num_slices'] * time_per_slice
            current_segment['avg_snr'] = np.mean(current_segment['snr_values'])
            segments.append(current_segment)

        return segments


if __name__ == "__main__":
    print("Aggressive Music Theory Filtering")
    print("Three modes: SOFT (bonuses), MEDIUM (penalties), HARD (strict)")
