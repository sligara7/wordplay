"""
Theory-Filtered Chord Detection

Applies music theory constraints to SNR matrix to intelligently select chords:
1. Key detection from SNR patterns
2. Chord progression validation
3. Harmonic context filtering
4. Voice leading smoothness

Instead of blindly taking argmax(SNR), we use music theory to choose
between competing high-SNR detections.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import sys
sys.path.append('..')
from music_theory_graph import MusicTheoryGraph


class TheoryFilteredChordDetector:
    """
    Intelligent chord detection using SNR matrix + music theory.

    Pipeline:
    1. Get SNR matrix from ultra-fast detector (660 × time)
    2. Detect key from overall SNR patterns
    3. For each time slice:
       a. Get top-K candidates (high SNR)
       b. Filter using key membership
       c. Validate progression with previous chord
       d. Choose best chord using combined score
    """

    def __init__(self,
                 snr_threshold=6.5,
                 top_k_candidates=5,
                 progression_weight=0.3,
                 key_weight=0.2):
        """
        Initialize theory-filtered detector.

        Args:
            snr_threshold: Minimum SNR for detection
            top_k_candidates: Number of top SNR candidates to consider
            progression_weight: Weight for progression probability (0-1)
            key_weight: Weight for key membership (0-1)
        """
        self.snr_threshold = snr_threshold
        self.top_k = top_k_candidates
        self.progression_weight = progression_weight
        self.key_weight = key_weight

        # Initialize music theory graph
        self.theory = MusicTheoryGraph()

        # Common chord progressions (root movement patterns)
        # These are functional relationships, not specific chords
        self.progression_scores = {
            # Strong progressions (high probability)
            ('I', 'V'): 1.0,    # Tonic to dominant
            ('V', 'I'): 2.0,    # Dominant to tonic (authentic cadence)
            ('IV', 'I'): 1.8,   # Plagal cadence
            ('ii', 'V'): 1.5,   # Pre-dominant to dominant
            ('V', 'vi'): 1.3,   # Deceptive cadence
            ('I', 'IV'): 1.2,
            ('I', 'vi'): 1.2,
            ('vi', 'IV'): 1.2,
            ('IV', 'V'): 1.5,

            # Moderate progressions
            ('I', 'I'): 0.8,    # Staying on same chord
            ('V', 'V'): 0.8,
            ('IV', 'IV'): 0.8,

            # Weak/unusual progressions (penalized)
            ('I', 'ii'): 0.5,
            ('V', 'IV'): 0.3,   # Retrograde (less common)
        }

        # Map chord types to Roman numeral functions in major keys
        self.chord_type_to_function_major = {
            'major': ['I', 'IV', 'V'],      # Major chords on 1, 4, 5
            'minor': ['ii', 'iii', 'vi'],   # Minor chords on 2, 3, 6
            'dim': ['vii°'],                # Diminished on 7
        }

    def detect_with_theory(self,
                          snr_matrix: np.ndarray,
                          chord_names: List[str],
                          time_per_slice: float) -> List[Dict]:
        """
        Detect chords using SNR matrix + music theory filtering.

        Args:
            snr_matrix: (num_templates, num_times) SNR values
            chord_names: List of chord names corresponding to template rows
            time_per_slice: Time duration of each slice in seconds

        Returns:
            List of chord detections with timing and scores
        """
        num_templates, num_times = snr_matrix.shape

        print("\n" + "="*80)
        print("THEORY-FILTERED CHORD DETECTION")
        print("="*80)
        print(f"SNR matrix shape: {snr_matrix.shape}")
        print(f"Time slices: {num_times}")
        print(f"Templates: {num_templates}")
        print(f"Total duration: {num_times * time_per_slice:.2f}s")
        print()

        # Step 1: Detect overall key from SNR patterns
        detected_key = self._detect_key_from_snr(snr_matrix, chord_names)
        print(f"Detected key: {detected_key}")
        print()

        # Step 2: Get scale chords for detected key
        key_chords = self._get_key_chords(detected_key)
        print(f"Scale chords in {detected_key}: {len(key_chords)} chords")
        print(f"Examples: {list(key_chords)[:10]}")
        print()

        # Step 3: Process each time slice with theory filtering
        detections = []
        previous_chord = None
        previous_function = None

        print("Processing time slices with theory filtering...")

        # Track statistics
        num_changed_by_theory = 0
        num_in_key = 0
        num_good_progressions = 0

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
                continue

            top_k_indices = top_k_indices[valid_mask]
            top_k_snrs = top_k_snrs[valid_mask]

            # Score each candidate using music theory
            candidate_scores = []
            for idx, snr in zip(top_k_indices, top_k_snrs):
                chord_name = chord_names[idx]

                # Parse chord
                root, chord_type, octave = self._parse_chord_name(chord_name)

                # Base score from SNR
                score = snr

                # Bonus for being in key
                if chord_name in key_chords:
                    score += self.key_weight * 3.0

                # Bonus for good progression from previous chord
                if previous_chord:
                    prev_root, prev_type, _ = self._parse_chord_name(previous_chord)

                    # Get Roman numeral functions
                    prev_func = self._get_chord_function(prev_root, prev_type, detected_key)
                    curr_func = self._get_chord_function(root, chord_type, detected_key)

                    # Look up progression score
                    prog_key = (prev_func, curr_func)
                    prog_score = self.progression_scores.get(prog_key, 0.5)

                    score += self.progression_weight * prog_score * 2.0

                candidate_scores.append({
                    'chord': chord_name,
                    'snr': snr,
                    'total_score': score,
                    'template_idx': idx
                })

            # Choose best candidate by total score
            if candidate_scores:
                best = max(candidate_scores, key=lambda x: x['total_score'])

                # Also get pure SNR winner for comparison
                best_snr_candidate = max(candidate_scores, key=lambda x: x['snr'])

                # Track statistics
                if best['chord'] in key_chords:
                    num_in_key += 1

                if best['chord'] != best_snr_candidate['chord']:
                    num_changed_by_theory += 1

                detections.append({
                    'time': time_seconds,
                    'chord': best['chord'],
                    'snr': best['snr'],
                    'total_score': best['total_score'],
                    'key': detected_key
                })

                previous_chord = best['chord']

        print(f"✓ Detected {len(detections)} chord events (with theory filtering)")
        print()

        # Print statistics
        print("Theory filtering statistics:")
        print(f"  Chords in detected key: {num_in_key}/{len(detections)} ({100*num_in_key/len(detections) if len(detections) > 0 else 0:.1f}%)")
        print(f"  Times theory changed winner: {num_changed_by_theory}/{len(detections)} ({100*num_changed_by_theory/len(detections) if len(detections) > 0 else 0:.1f}%)")
        print()

        # Step 4: Merge consecutive same chords
        merged = self._merge_consecutive_chords(detections, time_per_slice)

        print(f"✓ Merged into {len(merged)} chord segments")
        print()

        return merged

    def _detect_key_from_snr(self,
                            snr_matrix: np.ndarray,
                            chord_names: List[str]) -> str:
        """
        Detect musical key by analyzing which chords have highest total SNR.

        Strategy: Sum SNR for all chords in each possible key, choose key
        with highest total. This finds the key whose scale chords are most
        present in the audio.
        """
        # For each of 24 keys, sum SNR of all chords in that key
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
        """
        Get all chords that belong to a given key.

        Returns set of chord names (e.g., {'C_major_oct4', 'F_major_oct4', ...})
        """
        if not key or '_' not in key:
            return set()

        parts = key.split('_')
        root = parts[0]
        mode = parts[1] if len(parts) > 1 else 'major'

        # Get scale intervals
        if mode == 'major':
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
            chord_qualities = ['major', 'minor', 'minor', 'major', 'major', 'minor', 'dim']
        else:  # minor
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor
            chord_qualities = ['minor', 'dim', 'major', 'minor', 'minor', 'major', 'major']

        # Map note names to numbers
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

            # Add chords for all octaves (we have templates for oct2-6)
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
        """
        Parse chord name into components.

        Args:
            chord_name: e.g., "C_major_oct4", "F#_min7_oct3"

        Returns:
            (root, chord_type, octave) e.g., ("C", "major", 4)
        """
        parts = chord_name.split('_')

        # Root is first part
        root = parts[0]

        # Octave is last part
        octave_str = [p for p in parts if p.startswith('oct')]
        octave = int(octave_str[0].replace('oct', '')) if octave_str else 4

        # Chord type is everything in between
        chord_type = '_'.join([p for p in parts[1:] if not p.startswith('oct')])

        return root, chord_type, octave

    def _get_chord_function(self, root: str, chord_type: str, key: str) -> str:
        """
        Get Roman numeral function of chord in given key.

        Args:
            root: Chord root (e.g., "C", "F#")
            chord_type: Chord type (e.g., "major", "minor")
            key: Key context (e.g., "C_major")

        Returns:
            Roman numeral function (e.g., "I", "V", "vi")
        """
        if not key or '_' not in key:
            return 'I'  # Default

        key_root = key.split('_')[0]
        key_mode = key.split('_')[1] if len(key.split('_')) > 1 else 'major'

        # Note map
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }

        key_root_num = note_map.get(key_root, 0)
        chord_root_num = note_map.get(root, 0)

        # Calculate scale degree (1-7)
        interval = (chord_root_num - key_root_num) % 12

        # Map interval to scale degree in major/minor
        if key_mode == 'major':
            interval_to_degree = {
                0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7
            }
        else:  # minor
            interval_to_degree = {
                0: 1, 2: 2, 3: 3, 5: 4, 7: 5, 8: 6, 10: 7
            }

        degree = interval_to_degree.get(interval, 1)

        # Map degree + quality to Roman numeral
        if key_mode == 'major':
            if degree in [1, 4, 5] and 'major' in chord_type:
                numerals = {1: 'I', 4: 'IV', 5: 'V'}
                return numerals[degree]
            elif degree in [2, 3, 6] and 'minor' in chord_type:
                numerals = {2: 'ii', 3: 'iii', 6: 'vi'}
                return numerals[degree]
            elif degree == 7 and 'dim' in chord_type:
                return 'vii°'
        else:  # minor key
            if degree in [3, 6, 7] and 'major' in chord_type:
                numerals = {3: 'III', 6: 'VI', 7: 'VII'}
                return numerals[degree]
            elif degree in [1, 4, 5] and 'minor' in chord_type:
                numerals = {1: 'i', 4: 'iv', 5: 'v'}
                return numerals[degree]
            elif degree == 2 and 'dim' in chord_type:
                return 'ii°'

        # Default fallback
        return 'I'

    def _merge_consecutive_chords(self,
                                 detections: List[Dict],
                                 time_per_slice: float) -> List[Dict]:
        """
        Merge consecutive detections of same chord into segments.

        Args:
            detections: List of per-slice chord detections
            time_per_slice: Duration of each time slice

        Returns:
            List of chord segments with start_time, duration, chord
        """
        if not detections:
            return []

        segments = []
        current_segment = None

        for det in detections:
            if current_segment is None:
                # Start new segment
                current_segment = {
                    'start_time': det['time'],
                    'chord': det['chord'],
                    'key': det['key'],
                    'snr_values': [det['snr']],
                    'num_slices': 1
                }
            elif det['chord'] == current_segment['chord']:
                # Continue segment
                current_segment['snr_values'].append(det['snr'])
                current_segment['num_slices'] += 1
            else:
                # Finish current segment
                current_segment['duration'] = current_segment['num_slices'] * time_per_slice
                current_segment['avg_snr'] = np.mean(current_segment['snr_values'])
                segments.append(current_segment)

                # Start new segment
                current_segment = {
                    'start_time': det['time'],
                    'chord': det['chord'],
                    'key': det['key'],
                    'snr_values': [det['snr']],
                    'num_slices': 1
                }

        # Add final segment
        if current_segment:
            current_segment['duration'] = current_segment['num_slices'] * time_per_slice
            current_segment['avg_snr'] = np.mean(current_segment['snr_values'])
            segments.append(current_segment)

        return segments


if __name__ == "__main__":
    print("Theory-Filtered Chord Detector")
    print("Applies music theory to SNR matrix for intelligent chord detection")
