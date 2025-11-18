#!/usr/bin/env python3
"""
Music Theory Correction Pass

Holistic analysis of detected fundamentals using complete temporal DAG
and music theory to:
1. Consolidate overlapping notes of same pitch into sustained notes
2. Resolve low-note ambiguities using key/chord context
3. Correct octave errors using melodic contour
4. Generate note_on/note_off times for MIDI

Concept: After detecting all fundamentals, analyze the entire song's structure
before finalizing note events. This is a "second pass" that uses the complete
musical context to make better decisions.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict


class MusicTheoryCorrectionPass:
    """
    Consolidate and correct fundamental detections using music theory.

    This is a holistic "second pass" that analyzes the complete temporal
    structure after initial detection.
    """

    def __init__(self,
                 consolidation_window_seconds: float = 0.15,
                 min_note_duration_seconds: float = 0.08):
        """
        Initialize correction pass.

        Args:
            consolidation_window_seconds: Time window for merging overlapping notes
            min_note_duration_seconds: Minimum duration for a valid note
        """
        self.consolidation_window = consolidation_window_seconds
        self.min_duration = min_note_duration_seconds

    def correct_and_consolidate(self,
                                fundamentals: List[Dict],
                                detected_key: Optional[str] = None,
                                detected_chords: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Main correction pass - consolidate notes and apply music theory.

        Args:
            fundamentals: List of detected fundamentals from harmonic analyzer
            detected_key: Detected musical key (optional)
            detected_chords: List of detected chords with times (optional)

        Returns:
            List of consolidated note events with note_on/note_off times
        """
        if not fundamentals:
            return []

        # Step 1: Group fundamentals by pitch (consolidate same notes over time)
        notes_by_pitch = self._group_by_pitch(fundamentals)

        # Step 2: Consolidate overlapping detections into sustained notes
        consolidated_notes = []
        for pitch, pitch_fundamentals in notes_by_pitch.items():
            sustained_notes = self._consolidate_pitch_detections(pitch_fundamentals)
            consolidated_notes.extend(sustained_notes)

        # Step 3: Apply octave correction using melodic contour
        # DISABLED: Current implementation has cascading error problem
        # TODO: Implement global octave correction using key-based reference range
        # consolidated_notes = self._correct_octave_errors(consolidated_notes)

        # Step 4: Apply music theory corrections
        if detected_key or detected_chords:
            consolidated_notes = self._apply_music_theory_corrections(
                consolidated_notes, detected_key, detected_chords
            )

        # Step 5: Filter out notes that are too short
        consolidated_notes = [n for n in consolidated_notes
                            if n['duration_seconds'] >= self.min_duration]

        # Step 5: Sort by onset time
        consolidated_notes.sort(key=lambda n: n['onset_time_seconds'])

        return consolidated_notes

    def _group_by_pitch(self, fundamentals: List[Dict]) -> Dict[str, List[Dict]]:
        """Group fundamentals by pitch (note name)."""
        by_pitch = defaultdict(list)
        for fund in fundamentals:
            pitch = fund.get('note')
            if pitch:
                by_pitch[pitch].append(fund)
        return by_pitch

    def _consolidate_pitch_detections(self, pitch_fundamentals: List[Dict]) -> List[Dict]:
        """
        Consolidate multiple detections of same pitch into sustained notes.

        If B3 detected at t=1.0s, t=1.055s, t=1.11s with gap < consolidation_window,
        merge into single sustained B3 from 1.0s to 1.165s.

        Args:
            pitch_fundamentals: All fundamentals of same pitch

        Returns:
            List of consolidated note events with onset/offset times
        """
        if not pitch_fundamentals:
            return []

        # Sort by time
        sorted_funds = sorted(pitch_fundamentals, key=lambda f: f.get('time_seconds', 0))

        consolidated = []
        current_note = None

        for fund in sorted_funds:
            time = fund.get('time_seconds', 0)

            if current_note is None:
                # Start new note
                current_note = {
                    'note': fund['note'],
                    'frequency': fund['frequency'],
                    'onset_time_seconds': time,
                    'offset_time_seconds': time + 0.05,  # Initial estimate
                    'max_intensity': fund.get('intensity', 0),
                    'avg_confidence': fund.get('confidence', 1.0),
                    'num_detections': 1,
                    'chord': fund.get('chord'),
                    'key': fund.get('key')
                }
            else:
                # Check if this detection continues the current note
                gap = time - current_note['offset_time_seconds']

                if gap <= self.consolidation_window:
                    # Continue existing note (extend offset time)
                    current_note['offset_time_seconds'] = time + 0.05
                    current_note['max_intensity'] = max(
                        current_note['max_intensity'],
                        fund.get('intensity', 0)
                    )
                    current_note['avg_confidence'] = (
                        current_note['avg_confidence'] * current_note['num_detections'] +
                        fund.get('confidence', 1.0)
                    ) / (current_note['num_detections'] + 1)
                    current_note['num_detections'] += 1
                else:
                    # Gap too large - finish current note and start new one
                    current_note['duration_seconds'] = (
                        current_note['offset_time_seconds'] -
                        current_note['onset_time_seconds']
                    )
                    consolidated.append(current_note)

                    # Start new note
                    current_note = {
                        'note': fund['note'],
                        'frequency': fund['frequency'],
                        'onset_time_seconds': time,
                        'offset_time_seconds': time + 0.05,
                        'max_intensity': fund.get('intensity', 0),
                        'avg_confidence': fund.get('confidence', 1.0),
                        'num_detections': 1,
                        'chord': fund.get('chord'),
                        'key': fund.get('key')
                    }

        # Add final note
        if current_note:
            current_note['duration_seconds'] = (
                current_note['offset_time_seconds'] -
                current_note['onset_time_seconds']
            )
            consolidated.append(current_note)

        return consolidated

    def _correct_octave_errors(self, notes: List[Dict]) -> List[Dict]:
        """
        Correct octave errors using melodic contour analysis.

        Principles:
        - Melodies prefer stepwise motion (small intervals)
        - Octave jumps are rare in melodies
        - If note sequence is C4 → C2 → C4, middle note likely C3
        - Use voice leading and harmonic context

        Args:
            notes: Consolidated note events

        Returns:
            Notes with corrected octaves
        """
        if len(notes) < 3:
            return notes

        # Sort by onset time
        sorted_notes = sorted(notes, key=lambda n: n['onset_time_seconds'])

        # Analyze melodic intervals and correct octave errors
        corrected_notes = [sorted_notes[0]]  # Keep first note as-is

        for i in range(1, len(sorted_notes)):
            current_note = sorted_notes[i].copy()
            previous_note = corrected_notes[-1]

            # Get MIDI note numbers
            current_midi = self._note_name_to_midi(current_note['note'])
            previous_midi = self._note_name_to_midi(previous_note['note'])

            # Calculate interval (semitones)
            interval = abs(current_midi - previous_midi)

            # If interval is very large (> 19 semitones = more than octave + fifth),
            # check if it should be adjusted by octaves
            if interval > 19:
                # Get pitch class (note without octave)
                current_pc = self._get_pitch_class(current_note['note'])

                # Find the octave that minimizes interval to previous note
                best_octave = self._find_best_octave(
                    current_pc,
                    previous_midi,
                    max_interval=12  # Prefer intervals within an octave
                )

                # Update note to corrected octave
                corrected_midi = best_octave
                corrected_note_name = self._midi_to_note_name(corrected_midi)
                current_note['note'] = corrected_note_name

                # Also check if we need to look ahead for context
                if i < len(sorted_notes) - 1:
                    next_note = sorted_notes[i + 1]
                    next_midi = self._note_name_to_midi(next_note['note'])

                    # If corrected note creates smoother voice leading, keep it
                    interval_to_next = abs(corrected_midi - next_midi)
                    if interval_to_next > 19:
                        # Try to find octave that works better with both neighbors
                        better_octave = self._find_octave_for_neighbors(
                            current_pc, previous_midi, next_midi
                        )
                        if better_octave != corrected_midi:
                            corrected_midi = better_octave
                            current_note['note'] = self._midi_to_note_name(corrected_midi)

            corrected_notes.append(current_note)

        return corrected_notes

    def _get_pitch_class(self, note_name: str) -> str:
        """Extract pitch class (note without octave) from note name."""
        return ''.join(c for c in note_name if not c.isdigit() and c != '-')

    def _find_best_octave(self, pitch_class: str, reference_midi: int, max_interval: int = 12) -> int:
        """
        Find the octave for pitch_class that minimizes interval to reference note.

        Args:
            pitch_class: Note name without octave (e.g., 'C', 'F#')
            reference_midi: MIDI number of reference note
            max_interval: Maximum preferred interval in semitones

        Returns:
            MIDI number in best octave
        """
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
            'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10
        }

        pc_value = note_map.get(pitch_class, 0)

        # Try octaves from reference_midi - 24 to reference_midi + 24
        best_midi = reference_midi
        best_interval = float('inf')

        for octave_offset in range(-2, 3):  # Try ±2 octaves
            candidate_midi = (reference_midi // 12 + octave_offset) * 12 + pc_value

            # Ensure in valid MIDI range
            if candidate_midi < 21 or candidate_midi > 108:
                continue

            interval = abs(candidate_midi - reference_midi)

            # Prefer smaller intervals
            if interval < best_interval:
                best_interval = interval
                best_midi = candidate_midi

        return best_midi

    def _find_octave_for_neighbors(self, pitch_class: str, prev_midi: int, next_midi: int) -> int:
        """Find octave that minimizes total interval to both neighbors."""
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
            'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10
        }

        pc_value = note_map.get(pitch_class, 0)

        best_midi = prev_midi
        best_total_interval = float('inf')

        # Try octaves around both neighbors
        avg_midi = (prev_midi + next_midi) // 2

        for octave_offset in range(-2, 3):
            candidate_midi = (avg_midi // 12 + octave_offset) * 12 + pc_value

            if candidate_midi < 21 or candidate_midi > 108:
                continue

            total_interval = abs(candidate_midi - prev_midi) + abs(candidate_midi - next_midi)

            if total_interval < best_total_interval:
                best_total_interval = total_interval
                best_midi = candidate_midi

        return best_midi

    def _midi_to_note_name(self, midi_num: int) -> str:
        """Convert MIDI number to note name (e.g., 60 → 'C4')."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_num // 12) - 1
        note = notes[midi_num % 12]
        return f"{note}{octave}"

    def _apply_music_theory_corrections(self,
                                       notes: List[Dict],
                                       detected_key: Optional[str],
                                       detected_chords: Optional[List[Dict]]) -> List[Dict]:
        """
        Apply music theory corrections to consolidated notes.

        - Resolve ambiguous low notes using key/chord
        - Boost confidence of notes that fit theory
        - Flag notes that don't fit for potential removal

        Args:
            notes: Consolidated note events
            detected_key: Detected musical key
            detected_chords: List of chord detections with times

        Returns:
            Corrected note events
        """
        if not notes:
            return notes

        corrected = []

        for note in notes:
            onset_time = note['onset_time_seconds']

            # Find chord active at this time
            active_chord = None
            if detected_chords:
                for chord in detected_chords:
                    if chord['time'] <= onset_time < chord['time'] + 2.0:  # 2s chord window
                        active_chord = chord
                        break

            # Check if note fits key
            fits_key = self._note_fits_key(note['note'], detected_key) if detected_key else None

            # Check if note fits chord
            fits_chord = self._note_fits_chord(note['note'], active_chord) if active_chord else None

            # Adjust confidence based on music theory fit
            theory_boost = 0.0
            if fits_chord:
                theory_boost += 0.2  # Strong evidence
            if fits_key:
                theory_boost += 0.1  # Moderate evidence

            note['theory_validated'] = fits_chord or fits_key or False
            note['avg_confidence'] = min(1.0, note['avg_confidence'] + theory_boost)

            # Keep note if it has decent confidence or fits theory
            if note['avg_confidence'] >= 0.4 or note['theory_validated']:
                corrected.append(note)

        return corrected

    def _note_fits_key(self, note_name: str, key: str) -> bool:
        """Check if note is in the scale of the detected key."""
        if not key or '_' not in key:
            return False

        # Extract pitch class from note (remove octave)
        pitch_class = ''.join(c for c in note_name if not c.isdigit())

        # Define key scales
        major_intervals = [0, 2, 4, 5, 7, 9, 11]
        minor_intervals = [0, 2, 3, 5, 7, 8, 10]

        # Parse key
        parts = key.split('_')
        if len(parts) < 2:
            return False

        root = parts[0]
        mode = parts[1]

        # Get root pitch class number
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
            'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10
        }

        root_pc = note_map.get(root, 0)
        note_pc = note_map.get(pitch_class, -1)

        if note_pc == -1:
            return False

        # Get scale intervals
        intervals = major_intervals if mode == 'major' else minor_intervals

        # Calculate scale pitch classes
        scale_pcs = [(root_pc + interval) % 12 for interval in intervals]

        return note_pc in scale_pcs

    def _note_fits_chord(self, note_name: str, chord: Dict) -> bool:
        """Check if note is in the detected chord."""
        if not chord or 'notes' not in chord:
            return False

        # Extract pitch class from note (remove octave)
        pitch_class = ''.join(c for c in note_name if not c.isdigit())

        # Check if pitch class matches any chord note
        for chord_note in chord['notes']:
            chord_pc = ''.join(c for c in chord_note if not c.isdigit())
            if pitch_class == chord_pc:
                return True

        return False

    def get_statistics(self, notes: List[Dict]) -> Dict:
        """Get statistics about consolidated notes."""
        if not notes:
            return {}

        return {
            'total_notes': len(notes),
            'avg_duration': np.mean([n['duration_seconds'] for n in notes]),
            'avg_confidence': np.mean([n['avg_confidence'] for n in notes]),
            'theory_validated': sum(1 for n in notes if n.get('theory_validated', False)),
            'avg_detections_per_note': np.mean([n['num_detections'] for n in notes]),
            'time_coverage': max(n['offset_time_seconds'] for n in notes) if notes else 0
        }

    def convert_to_onset_detector_format(self, notes: List[Dict]) -> List[Dict]:
        """
        Convert consolidated notes to onset detector format for MIDI generation.

        Note: This replaces the onset detector since we already have onset/offset times.

        Returns:
            List of note events compatible with MidiGenerator
        """
        events = []

        for note in notes:
            # Convert note name to MIDI number
            midi_note = self._note_name_to_midi(note['note'])

            # Convert confidence to velocity (40-127 range)
            velocity = int(40 + note['avg_confidence'] * 87)
            velocity = max(40, min(127, velocity))

            events.append({
                'note': note['note'],
                'midi_note': midi_note,
                'onset_time_seconds': note['onset_time_seconds'],
                'offset_time_seconds': note['offset_time_seconds'],
                'duration_seconds': note['duration_seconds'],
                'velocity': velocity,
                'frequency': note['frequency'],
                'confidence': note['avg_confidence']
            })

        return events

    def _note_name_to_midi(self, note_name: str) -> int:
        """Convert note name (e.g., 'C4') to MIDI number."""
        note_map = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
            'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10
        }

        # Extract pitch class and octave
        pitch_class = ''.join(c for c in note_name if not c.isdigit() and c not in ['-'])
        octave_str = ''.join(c for c in note_name if c.isdigit() or c == '-')

        try:
            octave = int(octave_str)
        except (ValueError, TypeError):
            octave = 4  # Default to middle C octave

        # Calculate MIDI note number
        # MIDI: C-1 = 0, C0 = 12, C4 (middle C) = 60
        midi_note = (octave + 1) * 12 + note_map.get(pitch_class, 0)

        return max(0, min(127, midi_note))
