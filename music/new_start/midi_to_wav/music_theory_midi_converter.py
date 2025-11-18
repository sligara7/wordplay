"""
Music Theory Enhanced MIDI Converter

Extends the spectral to MIDI converter by applying music theory knowledge 
to filter and enhance note detection using scale, chord, and harmony rules.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Set
from collections import defaultdict, Counter
from scipy import signal
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo, second2tick

# Change this line:
from spectral_to_midi_converter import SpectralToMIDIConverter

class MusicTheoryMIDIConverter(SpectralToMIDIConverter):
    """
    Extends SpectralToMIDIConverter with music theory knowledge for improved note detection.
    
    This class applies scale detection, chord recognition, and harmonic context
    to filter spectral data and produce more musically coherent MIDI output.
    """
    
    def __init__(self, 
                # Music theory specific parameters
                amplitude_threshold=0.05,
                key_bias_strength=0.7,
                chord_bias_strength=0.8,
                temporal_window=5,
                min_note_duration=0.1,
                velocity_scaling=100.0,
                # Parent class parameters
                sample_freq=44100, 
                cycles=4, 
                standard_A4=440.0, 
                note_begin=-1, 
                note_end=89, 
                increments=12,
                **kwargs):
        """Initialize with all parent class parameters plus music theory parameters"""
        # Only pass valid parameters to parent class
        super().__init__(
            sample_freq=sample_freq,
            cycles=cycles,
            standard_A4=standard_A4,
            note_begin=note_begin,
            note_end=note_end,
            increments=increments
        )
        
        # Define common scales (semitones from root)
        self.scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],  # Natural minor
            'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
            'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
            'pentatonic_major': [0, 2, 4, 7, 9],
            'pentatonic_minor': [0, 3, 5, 7, 10],
            'blues': [0, 3, 5, 6, 7, 10]
        }
        
        # Define common chord structures (semitones from root)
        self.chord_types = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'diminished': [0, 3, 6],
            'augmented': [0, 4, 8],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            'major7': [0, 4, 7, 11],
            'minor7': [0, 3, 7, 10],
            'dominant7': [0, 4, 7, 10],
            'diminished7': [0, 3, 6, 9],
            'half_diminished7': [0, 3, 6, 10],
            'minor_major7': [0, 3, 7, 11],
            'augmented7': [0, 4, 8, 10],
            'add9': [0, 4, 7, 14],
            'add11': [0, 4, 7, 17]
        }
        
        # Common chord progressions by degree (in major keys)
        self.common_progressions = [
            ['I', 'IV', 'V'],          # Most basic progression
            ['I', 'V', 'vi', 'IV'],    # Pop progression
            ['ii', 'V', 'I'],          # Jazz cadence
            ['I', 'vi', 'IV', 'V'],    # 50s progression
            ['I', 'IV', 'V', 'IV']     # Shuttle
        ]
        
        # Roman numeral to scale degree mapping (for major keys)
        self.numeral_to_degree = {
            'I': 0, 'II': 2, 'III': 4, 'IV': 5, 'V': 7, 'VI': 9, 'VII': 11,
            'i': 0, 'ii': 2, 'iii': 4, 'iv': 5, 'v': 7, 'vi': 9, 'vii': 11
        }
        
        # Parameters for music theory filtering
        self.key_bias_strength = kwargs.get('key_bias_strength', 0.7)
        self.chord_bias_strength = kwargs.get('chord_bias_strength', 0.8)
        self.temporal_window = kwargs.get('temporal_window', 5)
        self.amplitude_threshold = kwargs.get('amplitude_threshold', 0.05)
        self.min_note_duration = kwargs.get('min_note_duration', 0.1)
        self.velocity_scaling = kwargs.get('velocity_scaling', 100.0)
        
        # Add additional parameters needed for note detection
        self.analyzer = self  # For compatibility with existing code

    def detect_key_from_notes(self, note_counts: Dict[int, int], confidence_threshold: float = 0.6) -> Tuple[int, str, float]:
        """
        Detect the musical key based on note frequency distribution.
        
        Args:
            note_counts: Dictionary mapping MIDI note numbers to occurrence count
            confidence_threshold: Minimum confidence to set a detected key
            
        Returns:
            Tuple of (root_note, scale_type, confidence)
        """
        if not note_counts:
            return None, None, 0.0
            
        # Convert to pitch classes (0-11) and count
        pitch_class_counts = defaultdict(int)
        for note, count in note_counts.items():
            pitch_class = note % 12
            pitch_class_counts[pitch_class] += count
            
        # Total number of notes
        total_notes = sum(pitch_class_counts.values())
        if total_notes == 0:
            return None, None, 0.0
            
        # Krumhansl-Schmuckler key profiles (correlation values with each key)
        # Higher values indicate stronger association with the key
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        # Calculate correlation of note distribution with each key profile
        best_key = None
        best_type = None
        best_correlation = -1.0
        
        # Check all possible keys (12 roots × 2 types)
        for root in range(12):
            major_correlation = 0
            minor_correlation = 0
            
            for offset in range(12):
                # Calculate the pitch class in this key
                pitch_class = (offset + root) % 12
                count = pitch_class_counts.get(pitch_class, 0)
                
                # Normalize by total notes
                note_weight = count / total_notes if total_notes > 0 else 0
                
                # Add weighted contributions to correlation
                major_correlation += note_weight * major_profile[offset]
                minor_correlation += note_weight * minor_profile[offset]
                
            # Check if this is the best correlation so far
            if major_correlation > best_correlation:
                best_correlation = major_correlation
                best_key = root
                best_type = 'major'
                
            if minor_correlation > best_correlation:
                best_correlation = minor_correlation
                best_key = root
                best_type = 'minor'
        
        # Normalize correlation to 0-1 scale
        confidence = min(1.0, best_correlation / 6.0)  # 6.0 is approximate max correlation
        
        # Only update detected key if confidence meets threshold
        if confidence >= confidence_threshold:
            return best_key, best_type, confidence
        else:
            return None, None, confidence
    
    def detect_chord_from_notes(self, active_notes: Set[int]) -> Tuple[int, str, float]:
        """
        Identify the most likely chord based on active notes.
        
        Args:
            active_notes: Set of active MIDI note numbers
            
        Returns:
            Tuple of (root_note, chord_type, confidence)
        """
        if not active_notes:
            return None, None, 0.0
            
        # Convert to pitch classes
        pitch_classes = set(note % 12 for note in active_notes)
        if len(pitch_classes) < 2:  # Need at least 2 notes for a chord
            return None, None, 0.0
            
        best_match = None
        best_root = None
        best_score = 0
        
        # Try each pitch class as potential root
        for root in range(12):
            for chord_name, intervals in self.chord_types.items():
                # Generate expected pitch classes for this chord
                chord_pitch_classes = set((root + interval) % 12 for interval in intervals)
                
                # Calculate how many notes match the chord
                matches = len(pitch_classes.intersection(chord_pitch_classes))
                
                # Calculate how many notes are not in the chord
                non_chord_tones = len(pitch_classes - chord_pitch_classes)
                
                # Calculate how many chord tones are missing
                missing_chord_tones = len(chord_pitch_classes - pitch_classes)
                
                # Score this chord (prioritize matches, penalize non-chord tones and missing chord tones)
                score = matches - 0.5 * non_chord_tones - 0.3 * missing_chord_tones
                
                # Prioritize common chord types if scores are close
                if chord_name in ['major', 'minor', 'dominant7']:
                    score += 0.1
                
                if score > best_score:
                    best_score = score
                    best_root = root
                    best_match = chord_name
        
        # Calculate confidence based on match quality
        if best_score > 0:
            # Normalize confidence (3.0 would be a perfect match for a triad)
            confidence = min(1.0, best_score / 3.0)
            return best_root, best_match, confidence
        else:
            return None, None, 0.0
    
    def is_note_in_scale(self, note: int, key_root: int, scale_type: str) -> bool:
        """
        Check if a note belongs to a particular scale.
        
        Args:
            note: MIDI note number
            key_root: Root note of the scale (0-11)
            scale_type: Type of scale ('major', 'minor', etc.)
            
        Returns:
            True if the note is in the scale, False otherwise
        """
        if key_root is None or scale_type not in self.scales:
            return True  # If no key is detected, accept all notes
            
        pitch_class = note % 12
        scale_intervals = self.scales[scale_type]
        scale_notes = [(key_root + interval) % 12 for interval in scale_intervals]
        
        return pitch_class in scale_notes
    
    def is_note_in_chord(self, note: int, chord_root: int, chord_type: str) -> bool:
        """
        Check if a note belongs to a particular chord.
        
        Args:
            note: MIDI note number
            chord_root: Root note of the chord (0-11)
            chord_type: Type of chord ('major', 'minor', etc.)
            
        Returns:
            True if the note is in the chord, False otherwise
        """
        if chord_root is None or chord_type not in self.chord_types:
            return True  # If no chord is detected, accept all notes
            
        pitch_class = note % 12
        chord_intervals = self.chord_types[chord_type]
        chord_notes = [(chord_root + interval) % 12 for interval in chord_intervals]
        
        return pitch_class in chord_notes
    
    def update_musical_context(self, active_notes: Dict[int, float]):
        """
        Update the current musical context (key, chord) based on active notes.
        
        Args:
            active_notes: Dictionary mapping MIDI note numbers to their amplitudes
        """
        # Count note occurrences (weighted by amplitude)
        note_counts = {}
        for note, amplitude in active_notes.items():
            # Weight by amplitude but ensure some minimum count
            note_counts[note] = max(1, int(amplitude * 10))
        
        # Detect key if we have enough notes
        if len(note_counts) >= 3:
            root, scale_type, confidence = self.detect_key_from_notes(note_counts)
            if confidence > 0.6:  # Only update if reasonably confident
                self.detected_key = (root, scale_type)
                self.key_confidence = confidence
        
        # Detect chord
        active_note_set = set(active_notes.keys())
        if len(active_note_set) >= 2:
            chord_root, chord_type, confidence = self.detect_chord_from_notes(active_note_set)
            if confidence > 0.5:  # Only update if reasonably confident
                self.current_chord = (chord_root, chord_type)
                # Keep a history of detected chords for progression analysis
                self.chord_history.append((chord_root, chord_type))
                if len(self.chord_history) > 10:  # Limit history size
                    self.chord_history.pop(0)
    
    def apply_music_theory_filter(self, frequencies: np.ndarray, 
                                 amplitudes: np.ndarray, 
                                 threshold_factor: float = 1.0) -> np.ndarray:
        """
        Apply music theory knowledge to filter detected frequencies.
        
        Args:
            frequencies: Array of detected frequencies
            amplitudes: Array of corresponding amplitudes
            threshold_factor: Factor to adjust amplitude threshold
            
        Returns:
            Filtered amplitudes array
        """
        filtered_amplitudes = amplitudes.copy()
        
        # Skip filtering if no context is available
        if self.detected_key is None and self.current_chord is None:
            return filtered_amplitudes
            
        # Convert frequencies to MIDI notes and apply music theory filter
        for i, freq in enumerate(frequencies):
            if freq <= 0 or amplitudes[i] <= 0:
                continue
                
            # Get the MIDI note for this frequency
            midi_note, _ = self.frequency_to_midi_note(freq)
            
            # Check if note is in current key
            in_key = True
            if self.detected_key:
                key_root, scale_type = self.detected_key
                in_key = self.is_note_in_scale(midi_note, key_root, scale_type)
            
            # Check if note is in current chord
            in_chord = True
            if self.current_chord:
                chord_root, chord_type = self.current_chord
                in_chord = self.is_note_in_chord(midi_note, chord_root, chord_type)
            
            # Apply biasing:
            # - Boost chord tones
            # - Slightly boost scale tones
            # - Attenuate out-of-scale tones
            if in_chord:
                # Boost chord tones
                filtered_amplitudes[i] *= (1.0 + self.chord_bias_strength)
            elif in_key:
                # Slight boost for scale tones that aren't chord tones
                filtered_amplitudes[i] *= (1.0 + 0.2 * self.key_bias_strength)
            else:
                # Attenuate out-of-scale tones
                filtered_amplitudes[i] *= (1.0 - self.key_bias_strength)
        
        return filtered_amplitudes
    
    def detect_notes_from_spectrum(self, 
                                  real_coefs: np.ndarray, 
                                  imag_coefs: np.ndarray, 
                                  amplitudes: np.ndarray,
                                  frame_duration: float,
                                  top_n: int = 5) -> List[Dict]:
        """
        Detect musical notes from spectral data with music theory filtering.
        
        Extends the parent method by adding music theory context before note detection.
        
        Args:
            real_coefs: Real coefficients from spectral analysis
            imag_coefs: Imaginary coefficients from spectral analysis
            amplitudes: Amplitude values from spectral analysis
            frame_duration: Duration of each analysis frame (seconds)
            top_n: Number of strongest notes to detect per frame
            
        Returns:
            List of MIDI message dictionaries representing notes
        """
        # Filter noise from amplitudes
        filtered_amplitudes = self.analyzer.filter_noise(amplitudes, std_multiplier=1.5)
        
        # Number of time frames
        num_frames = amplitudes.shape[1]
        
        # Track active notes across frames 
        active_notes = {}  # {midi_note: (start_time, velocity, frequency)}
        active_notes_by_frame = []  # Store active notes for each frame
        midi_messages = []
        
        # Process each time frame
        for frame_idx in range(num_frames):
            frame_time = frame_idx * frame_duration
            
            # Get amplitudes for this frame
            frame_amplitudes = filtered_amplitudes[:, frame_idx]
            
            # Keep track of all detected notes and their amplitudes in this frame
            frame_notes = {}
            
            # Find the top N strongest frequencies in this frame
            if np.max(frame_amplitudes) > self.amplitude_threshold:
                # Get indices of top N amplitudes
                top_indices = np.argsort(frame_amplitudes)[-top_n:]
                
                # Update detected notes for this frame
                for idx in top_indices:
                    if frame_amplitudes[idx] > self.amplitude_threshold:
                        frequency = self.analyzer.freq[idx]
                        midi_note, _ = self.frequency_to_midi_note(frequency)
                        
                        # Store note and its amplitude
                        frame_notes[midi_note] = frame_amplitudes[idx]
                
                # Update musical context using detected notes
                self.update_musical_context(frame_notes)
                
                # Apply music theory filtering to the amplitudes
                filtered_frame_amps = self.apply_music_theory_filter(
                    self.analyzer.freq, 
                    frame_amplitudes
                )
                
                # Get indices of top N amplitudes after music theory filtering
                top_indices = np.argsort(filtered_frame_amps)[-top_n:]
                
                # Add note-on messages for new notes
                for idx in top_indices:
                    if filtered_frame_amps[idx] > self.amplitude_threshold:
                        frequency = self.analyzer.freq[idx]
                        midi_note, pitch_bend = self.frequency_to_midi_note(frequency)
                        
                        # Calculate velocity (0-127) from amplitude
                        velocity = min(127, max(1, int(filtered_frame_amps[idx] * self.velocity_scaling)))
                        
                        # If this note is not already active, add note-on message
                        if midi_note not in active_notes:
                            active_notes[midi_note] = (frame_time, velocity, frequency)
                            
                            # Create note-on message
                            midi_messages.append({
                                'type': 'note_on',
                                'time': frame_time,
                                'note': midi_note,
                                'velocity': velocity,
                                'pitch_bend': pitch_bend,
                                'frequency': frequency
                            })
            
            # Store active notes for this frame (for context tracking)
            active_notes_by_frame.append(frame_notes)
            if len(active_notes_by_frame) > self.temporal_window:
                active_notes_by_frame.pop(0)
            
            # Check for notes that ended (amplitude dropped below threshold)
            notes_to_end = []
            for midi_note, (start_time, velocity, frequency) in active_notes.items():
                # Find the corresponding frequency index
                freq_idx = np.abs(self.analyzer.freq - frequency).argmin()
                
                # Check if amplitude dropped below threshold
                if frame_amplitudes[freq_idx] < self.amplitude_threshold:
                    notes_to_end.append(midi_note)
            
            # Create note-off messages for ended notes
            for midi_note in notes_to_end:
                start_time, velocity, frequency = active_notes.pop(midi_note)
                
                # Only create note-off if the note was active for at least min_note_duration
                if frame_time - start_time >= self.min_note_duration:
                    midi_messages.append({
                        'type': 'note_off',
                        'time': frame_time,
                        'note': midi_note,
                        'velocity': 0  # Standard MIDI note-off velocity
                    })
        
        # Add note-off messages for any remaining active notes at the end
        final_time = num_frames * frame_duration
        for midi_note, (start_time, velocity, frequency) in active_notes.items():
            # Only create note-off if the note was active for at least min_note_duration
            if final_time - start_time >= self.min_note_duration:
                midi_messages.append({
                    'type': 'note_off',
                    'time': final_time,
                    'note': midi_note,
                    'velocity': 0
                })
        
        # Sort messages by time
        midi_messages.sort(key=lambda x: x['time'])
        
        return midi_messages
    
    def analyze_chord_progression(self) -> List[str]:
        """
        Analyze the detected chord history to identify chord progressions.
        
        Returns:
            List of chord progression names that match the detected progression
        """
        if not self.chord_history or not self.detected_key:
            return []
            
        key_root, key_type = self.detected_key
        
        # Convert chord history to Roman numerals relative to the key
        roman_numerals = []
        for chord_root, chord_type in self.chord_history:
            # Calculate scale degree (0-11) relative to key
            degree = (chord_root - key_root) % 12
            
            # Convert to Roman numeral
            numeral = None
            if key_type == 'major':
                if degree == 0:  # I - Tonic
                    numeral = 'I' if chord_type == 'major' else 'i'
                elif degree == 2:  # II - Supertonic
                    numeral = 'II' if chord_type == 'major' else 'ii'
                elif degree == 4:  # III - Mediant
                    numeral = 'III' if chord_type == 'major' else 'iii'
                elif degree == 5:  # IV - Subdominant
                    numeral = 'IV' if chord_type == 'major' else 'iv'
                elif degree == 7:  # V - Dominant
                    numeral = 'V' if chord_type == 'major' else 'v'
                elif degree == 9:  # VI - Submediant
                    numeral = 'VI' if chord_type == 'major' else 'vi'
                elif degree == 11:  # VII - Leading tone
                    numeral = 'VII' if chord_type == 'major' else 'vii'
            elif key_type == 'minor':
                # Similar logic for minor keys
                # (simplified for this implementation)
                if degree == 0:
                    numeral = 'i' if chord_type == 'minor' else 'I'
                elif degree == 2:
                    numeral = 'ii°' if chord_type == 'diminished' else 'ii'
                elif degree == 3:
                    numeral = 'III' if chord_type == 'major' else 'iii'
                elif degree == 5:
                    numeral = 'iv' if chord_type == 'minor' else 'IV'
                elif degree == 7:
                    numeral = 'V' if chord_type == 'major' or chord_type == 'dominant7' else 'v'
                elif degree == 8:
                    numeral = 'VI' if chord_type == 'major' else 'vi'
                elif degree == 10:
                    numeral = 'VII' if chord_type == 'major' else 'vii'
            
            if numeral:
                roman_numerals.append(numeral)
        
        # Look for known progressions in the sequence
        matched_progressions = []
        for prog_name, progression in enumerate(self.common_progressions):
            # Check if progression is a subsequence of our chord history
            prog_len = len(progression)
            hist_len = len(roman_numerals)
            
            for i in range(hist_len - prog_len + 1):
                if roman_numerals[i:i+prog_len] == progression:
                    matched_progressions.append(f"Progression {prog_name + 1}")
        
        return matched_progressions
    
    def chord_name(self, root: int, chord_type: str) -> str:
        """
        Get a human-readable chord name.
        
        Args:
            root: Root note of chord (0-11)
            chord_type: Type of chord ('major', 'minor', etc.)
            
        Returns:
            String with chord name (e.g., "C major", "F# minor")
        """
        if root is None:
            return "Unknown"
            
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        chord_names = {
            'major': '', 
            'minor': 'm', 
            'diminished': 'dim', 
            'augmented': 'aug',
            'sus2': 'sus2', 
            'sus4': 'sus4',
            'major7': 'maj7', 
            'minor7': 'm7', 
            'dominant7': '7',
            'diminished7': 'dim7', 
            'half_diminished7': 'm7b5'
        }
        
        return f"{note_names[root]}{chord_names.get(chord_type, chord_type)}"
    
    def process_audio_to_midi(self, audio_data: np.ndarray, 
                             combine_notes: bool = True, 
                             quantize: bool = False,
                             tempo: float = 120.0) -> List[Dict]:
        """
        Complete pipeline to process audio to MIDI messages with music theory filtering.
        
        Args:
            audio_data: Audio signal as numpy array
            combine_notes: Whether to combine consecutive notes
            quantize: Whether to quantize note timings
            tempo: Tempo in BPM (used for quantization)
            
        Returns:
            List of MIDI message dictionaries
        """
        # Reset musical context
        self.detected_key = None
        self.current_chord = None
        self.chord_history = []
        
        # Perform spectral analysis
        real_coefs, imag_coefs, amplitudes = self.analyze_audio(audio_data)
        
        # Calculate frame duration
        frame_duration = self.analyzer.xlen / self.sf
        
        # Detect notes with music theory filtering
        midi_messages = self.detect_notes_from_spectrum(
            real_coefs, imag_coefs, amplitudes, 
            frame_duration=frame_duration
        )
        
        # Optional: Combine consecutive notes
        if combine_notes:
            midi_messages = self.combine_consecutive_notes(midi_messages)
        
        # Optional: Quantize timing
        if quantize:
            midi_messages = self.quantize_timing(midi_messages, tempo=tempo)
        
        # Add detected musical context as metadata messages
        if self.detected_key:
            key_root, scale_type = self.detected_key
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            midi_messages.append({
                'type': 'meta',
                'meta_type': 'key_signature',
                'time': 0,
                'key': f"{note_names[key_root]} {scale_type}",
                'confidence': self.key_confidence
            })
        
        # Add chord progression information
        if self.chord_history:
            chord_names = [self.chord_name(root, chord_type) for root, chord_type in self.chord_history]
            midi_messages.append({
                'type': 'meta',
                'meta_type': 'chord_progression',
                'time': 0,
                'chords': chord_names
            })
            
            # Add detected progressions
            progressions = self.analyze_chord_progression()
            if progressions:
                midi_messages.append({
                    'type': 'meta',
                    'meta_type': 'detected_progressions',
                    'time': 0,
                    'progressions': progressions
                })
        
        return midi_messages

    def quantize_timing(self, messages: List[Dict], tempo: float = 120.0, 
                    grid_resolution: str = '16th') -> List[Dict]:
        """
        Quantize timing of MIDI messages to align with musical grid.
        
        Args:
            messages: List of MIDI message dictionaries
            tempo: Tempo in BPM
            grid_resolution: Grid resolution ('4th', '8th', '16th', '32nd')
            
        Returns:
            List of MIDI messages with quantized timing
        """
        # Calculate beat duration in seconds
        beat_duration = 60.0 / tempo  # Quarter note duration
        
        # Set grid size based on resolution
        grid_sizes = {
            '4th': 1.0,      # Quarter note
            '8th': 0.5,      # Eighth note
            '16th': 0.25,    # Sixteenth note
            '32nd': 0.125    # Thirty-second note
        }
        
        # Get grid division as fraction of a beat
        grid_division = grid_sizes.get(grid_resolution, 0.25)  # Default to 16th notes
        
        # Calculate grid size in seconds
        grid_size = beat_duration * grid_division
        
        # Create a copy of messages to avoid modifying the original
        quantized_messages = []
        
        for msg in messages:
            # Create a copy of the message
            new_msg = msg.copy()
            
            # Quantize the time
            original_time = msg['time']
            grid_position = round(original_time / grid_size)
            new_msg['time'] = grid_position * grid_size
            
            quantized_messages.append(new_msg)
        
        # Sort messages by time
        quantized_messages.sort(key=lambda x: x['time'])
        
        # Fix note durations - ensure note_off comes after corresponding note_on
        notes_on = {}  # track active notes
        for i, msg in enumerate(quantized_messages):
            if msg['type'] == 'note_on':
                # Store index of note_on message
                if msg['note'] not in notes_on:
                    notes_on[msg['note']] = []
                notes_on[msg['note']].append((i, msg['time']))
            elif msg['type'] == 'note_off':
                # Find corresponding note_on
                if msg['note'] in notes_on and notes_on[msg['note']]:
                    note_on_idx, note_on_time = notes_on[msg['note']].pop(0)
                    # If quantization caused note_off to be at or before note_on
                    if msg['time'] <= note_on_time:
                        # Move note_off to next grid position
                        quantized_messages[i]['time'] = note_on_time + grid_size
        
        # Final sort to account for any adjusted note_off times
        quantized_messages.sort(key=lambda x: x['time'])
        
        return quantized_messages

    def combine_consecutive_notes(self, messages: List[Dict], max_gap: float = 0.05) -> List[Dict]:
        """
        Combine consecutive notes of the same pitch that are separated by small gaps.
        
        Args:
            messages: List of MIDI message dictionaries
            max_gap: Maximum gap between notes to combine (seconds)
            
        Returns:
            New list with consecutive notes combined
        """
        # Sort messages by time
        messages = sorted(messages, key=lambda x: x['time'])
        
        # Group messages by note number
        notes_by_pitch = {}
        result_messages = []
        
        # First pass: collect all non-note messages and organize notes by pitch
        for msg in messages:
            if msg['type'] not in ('note_on', 'note_off'):
                result_messages.append(msg)  # Keep non-note messages
                continue
                
            # Group by note pitch
            note_num = msg['note']
            if note_num not in notes_by_pitch:
                notes_by_pitch[note_num] = []
            notes_by_pitch[note_num].append(msg)
        
        # Second pass: process each pitch separately
        for note_num, note_msgs in notes_by_pitch.items():
            # Sort by time
            note_msgs.sort(key=lambda x: x['time'])
            
            i = 0
            while i < len(note_msgs) - 2:  # Need at least note_on + note_off + next note_on
                # Check if we have a sequence of note_off followed by note_on for same pitch
                if (note_msgs[i]['type'] == 'note_on' and 
                    note_msgs[i+1]['type'] == 'note_off' and 
                    note_msgs[i+2]['type'] == 'note_on'):
                    
                    # If the gap is small enough, combine the notes
                    gap = note_msgs[i+2]['time'] - note_msgs[i+1]['time']
                    if gap <= max_gap:
                        # Remove the note_off and next note_on
                        off_msg = note_msgs.pop(i+1)  # Remove note_off
                        on_msg = note_msgs.pop(i+1)   # Remove next note_on (now at i+1)
                        
                        # Keep the highest velocity between the two note_on messages
                        note_msgs[i]['velocity'] = max(note_msgs[i]['velocity'], on_msg['velocity'])
                        
                        # Continue without incrementing i since we need to check for more consecutive notes
                        continue
                
                i += 1
        
        # Collect all processed notes
        for note_msgs in notes_by_pitch.values():
            result_messages.extend(note_msgs)
        
        # Sort all messages by time again
        result_messages.sort(key=lambda x: x['time'])
        
        return result_messages

    def frequency_to_midi_note(self, frequency: float) -> Tuple[int, float]:
        """
        Convert a frequency to a MIDI note number and pitch bend value.
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            Tuple of (midi_note, pitch_bend) where pitch_bend is in semitones
        """
        # Convert frequency to floating point MIDI note number
        exact_note = self.freq_to_note(frequency)
        
        # Get the integer MIDI note (closest note)
        midi_note = int(round(exact_note))
        
        # Calculate pitch bend in semitones (-1 to +1)
        pitch_bend = exact_note - midi_note
        
        return midi_note, pitch_bend

    def filter_noise(self, amplitudes, std_multiplier=1.5):
        """
        Filter out noise from amplitude data by thresholding based on standard deviation.
        
        Args:
            amplitudes: Array of amplitude values
            std_multiplier: Multiplier for standard deviation threshold
            
        Returns:
            Filtered amplitude array with noise set to zero
        """
        # Make a copy to avoid modifying the original
        filtered = amplitudes.copy()
        
        # Calculate mean and standard deviation for each frequency bin
        mean = np.mean(filtered, axis=1, keepdims=True)
        std = np.std(filtered, axis=1, keepdims=True)
        
        # Create a threshold based on mean and standard deviation
        threshold = mean + std_multiplier * std
        
        # Zero out values below the threshold
        filtered[filtered < threshold] = 0.0
        
        return filtered
    
    def detect_percussion(self, audio_data: np.ndarray, sensitivity: float = 0.7) -> List[Dict]:
        """
        Detect percussion events in audio data using spectral analysis.
        
        Args:
            audio_data: Input audio signal as numpy array
            sensitivity: Detection sensitivity (0.0-1.0)
            
        Returns:
            List of percussion events with timestamps, type, and confidence
        """
        from scipy import signal
        import numpy as np
        from collections import defaultdict
        
        # Ensure audio is mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Define percussion frequency bands
        percussion_bands = {
            'kick': (40, 200),
            'snare': (200, 1200),
            'hi_hat': (5000, 15000),
            'tom': (180, 600),
            'cymbal': (8000, 16000)
        }
        
        # Create frame size matching our spectral analysis window
        frame_size = self.xlen
        hop_size = frame_size // 4  # 75% overlap
        
        # Prepare output
        percussion_events = []
        
        # Process audio in frames
        for start_idx in range(0, len(audio_data) - frame_size, hop_size):
            frame_time = start_idx / self.sf  # Time in seconds
            frame = audio_data[start_idx:start_idx + frame_size]
            
            # Calculate spectrum using our existing method
            _, _, amplitudes = self.analyze(frame)
            
            # Map amplitude bins to frequencies
            freq_amplitudes = defaultdict(float)
            for i, freq in enumerate(self.freq):
                if i < len(amplitudes):
                    freq_amplitudes[freq] = amplitudes[i, 0]
            
            # Check each percussion type
            for drum_type, (low_freq, high_freq) in percussion_bands.items():
                # Find amplitudes in this frequency range
                band_energy = 0
                band_count = 0
                for freq, amp in freq_amplitudes.items():
                    if low_freq <= freq <= high_freq:
                        band_energy += amp
                        band_count += 1
                
                # Skip if no frequencies in this band
                if band_count == 0:
                    continue
                    
                # Average energy in band
                avg_energy = band_energy / band_count
                
                # Detect onset based on energy and sensitivity threshold
                # (In a real implementation, we'd compare with previous frames)
                threshold = np.mean(amplitudes) * (1 + sensitivity)
                
                if avg_energy > threshold:
                    # Calculate confidence based on how much above threshold
                    confidence = min(1.0, (avg_energy / threshold) - 0.9)
                    
                    # Only add events with reasonable confidence
                    if confidence > 0.2:
                        percussion_events.append({
                            'time': frame_time,
                            'type': drum_type,
                            'confidence': confidence,
                            'velocity': min(127, int(confidence * 127))
                        })
        
        # Filter overlapping events - keep highest confidence for each time/type
        filtered_events = {}
        for event in percussion_events:
            # Round time to nearest 30ms for clustering
            time_key = round(event['time'] * 33) / 33
            event_key = (time_key, event['type'])
            
            if event_key not in filtered_events or filtered_events[event_key]['confidence'] < event['confidence']:
                filtered_events[event_key] = event
        
        # Sort by time and return
        return sorted(filtered_events.values(), key=lambda x: x['time'])

    def detect_beat_structure(self, percussion_events: List[Dict], 
                            min_tempo: float = 60, 
                            max_tempo: float = 200) -> Dict:
        """
        Analyze percussion events to detect tempo and beat structure.
        
        Args:
            percussion_events: List of detected percussion events
            min_tempo: Minimum tempo to detect in BPM
            max_tempo: Maximum tempo to detect in BPM
            
        Returns:
            Dictionary containing tempo, beat positions, and confidence
        """
        import numpy as np
        from collections import defaultdict
        
        if not percussion_events:
            return {'tempo': 0, 'beat_positions': [], 'confidence': 0}
        
        # Extract kick and snare events as they typically define the beat
        kick_times = [e['time'] for e in percussion_events if e['type'] == 'kick']
        snare_times = [e['time'] for e in percussion_events if e['type'] == 'snare']
        
        # Combine with emphasis on kicks (which often mark the downbeat)
        all_hit_times = kick_times + snare_times
        if not all_hit_times:
            return {'tempo': 0, 'beat_positions': [], 'confidence': 0}
        
        # Calculate intervals between consecutive hits
        intervals = []
        for i in range(1, len(all_hit_times)):
            interval = all_hit_times[i] - all_hit_times[i-1]
            # Filter out too short intervals (flams, rolls, etc)
            if 60/max_tempo <= interval <= 60/min_tempo:
                intervals.append(interval)
        
        if not intervals:
            return {'tempo': 0, 'beat_positions': [], 'confidence': 0}
        
        # Count occurrences of similar intervals to find the beat
        interval_counts = defaultdict(int)
        for interval in intervals:
            # Group intervals by rounding to nearest 25ms
            rounded = round(interval * 40) / 40
            interval_counts[rounded] += 1
        
        # Find most common interval (beat duration)
        beat_interval = max(interval_counts, key=interval_counts.get)
        beat_count = interval_counts[beat_interval]
        
        # Calculate confidence based on consistency
        consistency = beat_count / len(intervals)
        
        # Calculate tempo in BPM
        tempo = 60 / beat_interval
        
        # Project beats across the entire audio duration
        if kick_times:
            # Start from first kick as reference
            first_beat_time = kick_times[0]
        else:
            first_beat_time = all_hit_times[0]
        
        # Generate beat positions
        audio_duration = max(e['time'] for e in percussion_events) + 1
        num_beats = int(audio_duration / beat_interval) + 1
        beat_positions = [first_beat_time + i * beat_interval for i in range(num_beats)]
        
        return {
            'tempo': tempo,
            'beat_positions': beat_positions,
            'confidence': consistency
        }

    def write_to_midi(self, midi_messages: List[Dict], filename: str, tempo: float = 120.0):
        """
        Convert MIDI message dictionaries to a standard MIDI file.
        
        Args:
            midi_messages: List of MIDI message dictionaries
            filename: Output MIDI filename
            tempo: Default tempo in BPM (used if not specified in messages)
        """
        mid = MidiFile(type=1)  # Type 1 supports multiple tracks
        
        # Create a track for metadata
        meta_track = MidiTrack()
        mid.tracks.append(meta_track)
        
        # Add default tempo
        meta_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo)))
        
        # Look for key signature and other metadata
        key_sig = None
        time_sig = None
        detected_tempo = None
        
        for msg in midi_messages:
            if msg.get('type') == 'meta':
                meta_type = msg.get('meta_type')
                if meta_type == 'key_signature' and 'key' in msg:
                    key_sig = msg['key']
                elif meta_type == 'time_signature' and 'numerator' in msg and 'denominator' in msg:
                    time_sig = (msg['numerator'], msg['denominator'])
                elif meta_type == 'tempo' and 'bpm' in msg:
                    detected_tempo = msg['bpm']
        
        # Add key signature if detected
        if key_sig:
            # Simple mapping for common keys, could be expanded
            key_map = {
                'C major': 'C', 'G major': 'G', 'D major': 'D', 'A major': 'A',
                'E major': 'E', 'B major': 'B', 'F# major': 'F#', 'C# major': 'C#',
                'F major': 'F', 'Bb major': 'Bb', 'Eb major': 'Eb', 'Ab major': 'Ab',
                'A minor': 'Am', 'E minor': 'Em', 'B minor': 'Bm', 'F# minor': 'F#m',
                'C# minor': 'C#m', 'G# minor': 'G#m', 'D# minor': 'D#m', 'A# minor': 'A#m',
                'D minor': 'Dm', 'G minor': 'Gm', 'C minor': 'Cm', 'F minor': 'Fm'
            }
            meta_track.append(MetaMessage('key_signature', key=key_map.get(key_sig, 'C')))
        
        # Add time signature if detected
        if time_sig:
            meta_track.append(MetaMessage('time_signature', 
                                        numerator=time_sig[0], 
                                        denominator=time_sig[1]))
        
        # Update tempo if detected
        if detected_tempo:
            meta_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(detected_tempo)))
        
        # Create track for notes
        note_track = MidiTrack()
        mid.tracks.append(note_track)
        
        # Add program change (instrument selection)
        note_track.append(Message('program_change', program=0, time=0))  # Default to piano
        
        # Convert absolute times to delta times
        last_time = 0
        sorted_msgs = sorted([m for m in midi_messages 
                            if m.get('type') in ('note_on', 'note_off')], 
                            key=lambda x: x['time'])
        
        for msg in sorted_msgs:
            # Calculate delta time in ticks
            delta_time = int(second2tick(msg['time'] - last_time, 
                                        mid.ticks_per_beat, 
                                        bpm2tempo(tempo)))
            
            # Create MIDI message
            if msg['type'] == 'note_on':
                velocity = msg.get('velocity', 64)
                note_track.append(Message('note_on', 
                                        note=msg['note'], 
                                        velocity=velocity, 
                                        time=delta_time))
            elif msg['type'] == 'note_off':
                note_track.append(Message('note_off', 
                                        note=msg['note'], 
                                        velocity=0,  # Standard for note-off
                                        time=delta_time))
            
            # Update last time for next delta calculation
            last_time = msg['time']
        
        # Add end of track marker
        note_track.append(MetaMessage('end_of_track', time=0))
        
        # Save the MIDI file
        mid.save(filename)
        print(f"MIDI file saved to {filename}")




# Example usage:
if __name__ == "__main__":
    # Create converter with music theory filtering
    converter = MusicTheoryMIDIConverter(
        amplitude_threshold=0.05,
        key_bias_strength=0.7,  # How strongly to favor notes in key
        chord_bias_strength=0.8  # How strongly to favor chord tones
    )
    
    # Load an audio file (example)
    import scipy.io.wavfile as wavfile
    sample_rate, audio_data = wavfile.read("/home/ajs7/Music/cdl.wav")
    
    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Process audio to MIDI messages
    midi_messages = converter.process_audio_to_midi(
        audio_data, 
        combine_notes=True, 
        quantize=True,
        tempo=120.0
    )
    
    converter.write_to_midi(
        midi_messages=midi_messages,
        filename="/home/ajs7/Music/output_song2.mid",
        tempo=120.0
    )

    # Print the detected key and chords
    for msg in midi_messages:
        if msg.get('type') == 'meta':
            print(f"Detected {msg.get('meta_type')}: {msg}")
    
    # Print note data
    note_messages = [msg for msg in midi_messages if msg.get('type') in ('note_on', 'note_off')]
    print(f"Detected {len(note_messages)} note events")
    
    # Print first few note messages
    for msg in note_messages[:10]:
        print(msg)