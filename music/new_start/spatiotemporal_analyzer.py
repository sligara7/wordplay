"""
Spatiotemporal Window Approach for Audio-to-MIDI Transcription

This module implements a temporal-first approach that:
1. Applies statistical filtering to remove noise
2. Extracts spatiotemporal windows (frequency × time) for each note
3. Compares octave-related windows to identify fundamentals vs harmonics
4. Uses temporal correlation as the primary organizing principle
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import networkx as nx
from scipy.stats import pearsonr


class SpatiotemporalAnalyzer:
    """
    Analyze audio using spatiotemporal windows to identify notes and harmonics.

    Key idea: Notes and their harmonics have correlated temporal evolution.
    By comparing frequency×time windows, we can identify harmonic relationships
    without the ambiguity of single-snapshot spectral analysis.
    """

    def __init__(self,
                 spectral_data: np.ndarray,
                 frequencies: np.ndarray,
                 sample_rate: int,
                 window_length: int,
                 increments: int = 12,
                 freq_window_size: int = 5,
                 stat_threshold_sigma: float = 0.5,
                 correlation_threshold: float = 0.8,
                 min_window_intensity: float = 0.1):
        """
        Initialize the spatiotemporal analyzer.

        Args:
            spectral_data: 2D array [num_frequencies, num_time_samples]
            frequencies: Array of frequency values for each bin
            sample_rate: Audio sample rate in Hz
            window_length: Analysis window length in samples
            increments: Number of subdivisions per semitone (default: 12)
            freq_window_size: Number of bins ± around center (default: 5 → m=11)
            stat_threshold_sigma: Statistical threshold in std devs (default: 0.5)
            correlation_threshold: Min correlation for harmonic relationship (default: 0.8)
            min_window_intensity: Minimum peak intensity for a window to be considered (default: 0.1)
        """
        # Normalize spectral data to [0, 1] range
        max_intensity = np.max(spectral_data)
        if max_intensity > 0:
            self.spectral_data = spectral_data / max_intensity
        else:
            self.spectral_data = spectral_data

        self.frequencies = frequencies
        self.sample_rate = sample_rate
        self.window_length = window_length
        self.increments = increments
        self.freq_window_size = freq_window_size
        self.stat_threshold_sigma = stat_threshold_sigma
        self.correlation_threshold = correlation_threshold
        self.min_window_intensity = min_window_intensity

        self.num_frequencies = spectral_data.shape[0]
        self.num_time_samples = spectral_data.shape[1]

        # Will be computed
        self.filtered_data = None
        self.semitone_windows = {}  # semitone_index -> spatiotemporal window
        self.harmonic_relationships = []  # List of (fundamental_idx, harmonic_idx, correlation)

    def apply_statistical_filter(self):
        """
        Apply statistical filtering to remove noise.

        For each time sample, keep only frequencies with intensity above
        median + sigma * std. This removes ~69% of noise if sigma=0.5.
        """
        print("Applying statistical filter (median + {:.1f}×std)...".format(
            self.stat_threshold_sigma))

        # Compute statistics per time sample
        medians = np.median(self.spectral_data, axis=0)  # shape: (num_time_samples,)
        stds = np.std(self.spectral_data, axis=0)
        thresholds = medians + self.stat_threshold_sigma * stds

        # Apply threshold with broadcasting
        mask = self.spectral_data >= thresholds[np.newaxis, :]
        self.filtered_data = np.where(mask, self.spectral_data, 0)

        # Report statistics
        total_elements = self.spectral_data.size
        kept_elements = np.sum(mask)
        filtered_pct = 100 * (1 - kept_elements / total_elements)

        print(f"  Filtered {filtered_pct:.1f}% of data points")
        print(f"  Kept {kept_elements:,} / {total_elements:,} elements")

    def frequency_to_semitone_index(self, freq: float) -> int:
        """
        Convert frequency to semitone index (where A0 = 0).

        Args:
            freq: Frequency in Hz

        Returns:
            Semitone index (0 = A0, 12 = A1, etc.)
        """
        A0 = 27.5
        semitones = 12 * np.log2(freq / A0)
        return int(round(semitones))

    def semitone_index_to_bin_index(self, semitone_idx: int) -> int:
        """
        Get the center frequency bin index for a semitone.

        With increments=12, each semitone has 12 bins. The center bin
        is at semitone_idx * increments + increments/2.

        Args:
            semitone_idx: Semitone index (0 = A0, 1 = A#0, 2 = B0, etc.)

        Returns:
            Center frequency bin index in spectral_data
        """
        # semitone_idx=0 corresponds to A0, which is at the start of our frequency array
        # Each semitone occupies 'increments' bins
        # Center bin is in the middle of each semitone's bin range
        center_bin = semitone_idx * self.increments + self.increments // 2

        return center_bin

    def extract_spatiotemporal_window(self, semitone_idx: int) -> Optional[Dict]:
        """
        Extract spatiotemporal window (frequency × time) for a semitone.

        The window includes:
        - Frequency dimension: center_bin ± freq_window_size
        - Temporal dimension: all consecutive time samples where any frequency
          in the window exceeds the statistical threshold

        Args:
            semitone_idx: Semitone index (0 = A0)

        Returns:
            Dictionary with window info, or None if no active region found:
            {
                'semitone_idx': int,
                'center_freq': float (Hz),
                'freq_bin_start': int,
                'freq_bin_end': int,
                'time_start': int,
                'time_end': int,
                'matrix': np.ndarray [m, n],
                'active_times': np.ndarray of time indices
            }
        """
        # Get center frequency bin
        center_bin = self.semitone_index_to_bin_index(semitone_idx)

        # Check bounds
        if center_bin < 0 or center_bin >= self.num_frequencies:
            return None

        # Define frequency window
        freq_start = max(0, center_bin - self.freq_window_size)
        freq_end = min(self.num_frequencies, center_bin + self.freq_window_size + 1)

        # Extract frequency slice
        freq_slice = self.filtered_data[freq_start:freq_end, :]

        # Find where ANY frequency in this window is active
        active_mask = np.any(freq_slice > 0, axis=0)
        active_times = np.where(active_mask)[0]

        if len(active_times) == 0:
            return None

        # Find contiguous segments
        # For now, take the full range (we'll refine this later)
        time_start = active_times[0]
        time_end = active_times[-1] + 1

        # Extract spatiotemporal matrix
        matrix = self.filtered_data[freq_start:freq_end, time_start:time_end]

        # Check if peak intensity meets minimum threshold
        max_intensity = np.max(matrix)
        if max_intensity < self.min_window_intensity:
            return None

        return {
            'semitone_idx': semitone_idx,
            'center_freq': self.frequencies[center_bin] if center_bin < len(self.frequencies) else None,
            'freq_bin_start': freq_start,
            'freq_bin_end': freq_end,
            'time_start': time_start,
            'time_end': time_end,
            'matrix': matrix,
            'active_times': active_times,
            'max_intensity': float(max_intensity)
        }

    def compare_octave_windows(self,
                                lower_window: Dict,
                                upper_window: Dict) -> Tuple[float, bool]:
        """
        Compare two spatiotemporal windows to determine if upper is harmonic of lower.

        Checks:
        1. Temporal alignment: upper starts at/after lower, ends at/before lower
        2. Correlation: spatial-temporal patterns are similar

        Args:
            lower_window: Spatiotemporal window for potential fundamental
            upper_window: Spatiotemporal window for potential harmonic

        Returns:
            (correlation_coefficient, is_likely_harmonic)
        """
        # Check temporal alignment
        lower_start = lower_window['time_start']
        lower_end = lower_window['time_end']
        upper_start = upper_window['time_start']
        upper_end = upper_window['time_end']

        # Harmonic should start at same time or after fundamental
        # Harmonic should end at same time or before fundamental
        temporal_alignment_ok = (upper_start >= lower_start and
                                 upper_end <= lower_end)

        if not temporal_alignment_ok:
            return 0.0, False

        # Find temporal intersection
        intersect_start = max(lower_start, upper_start)
        intersect_end = min(lower_end, upper_end)

        if intersect_start >= intersect_end:
            return 0.0, False

        # Extract overlapping regions
        lower_overlap = lower_window['matrix'][:, intersect_start-lower_start:intersect_end-lower_start]
        upper_overlap = upper_window['matrix'][:, intersect_start-upper_start:intersect_end-upper_start]

        # Flatten and compute correlation
        lower_flat = lower_overlap.flatten()
        upper_flat = upper_overlap.flatten()

        if len(lower_flat) < 2 or len(upper_flat) < 2:
            return 0.0, False

        # Handle cases where one is all zeros
        if np.std(lower_flat) == 0 or np.std(upper_flat) == 0:
            return 0.0, False

        corr, _ = pearsonr(lower_flat, upper_flat)

        is_harmonic = corr >= self.correlation_threshold

        return corr, is_harmonic

    def analyze(self) -> List[Dict]:
        """
        Main analysis pipeline.

        Returns:
            List of detected note events with fundamental/harmonic relationships
        """
        # Step 1: Statistical filtering
        self.apply_statistical_filter()

        # Step 2: Extract spatiotemporal windows for all semitones
        print("\nExtracting spatiotemporal windows...")

        # Analyze semitones from A0 (0) to C8 (87)
        for semitone_idx in range(0, 88):
            window = self.extract_spatiotemporal_window(semitone_idx)
            if window is not None:
                self.semitone_windows[semitone_idx] = window

        print(f"  Found {len(self.semitone_windows)} active semitone windows")

        # Step 3: Compare octave-related windows
        print("\nComparing octave relationships...")

        for semitone_idx in sorted(self.semitone_windows.keys()):
            # Check octave above (12 semitones higher)
            octave_above_idx = semitone_idx + 12

            if octave_above_idx in self.semitone_windows:
                lower_window = self.semitone_windows[semitone_idx]
                upper_window = self.semitone_windows[octave_above_idx]

                corr, is_harmonic = self.compare_octave_windows(lower_window, upper_window)

                if is_harmonic:
                    self.harmonic_relationships.append({
                        'fundamental_idx': semitone_idx,
                        'harmonic_idx': octave_above_idx,
                        'correlation': corr
                    })

        print(f"  Found {len(self.harmonic_relationships)} harmonic relationships")

        # Step 4: Identify fundamentals (semitones that are not harmonics of others)
        harmonic_indices = set(rel['harmonic_idx'] for rel in self.harmonic_relationships)
        fundamental_indices = set(self.semitone_windows.keys()) - harmonic_indices

        print(f"  Identified {len(fundamental_indices)} fundamental notes")

        # Step 5: Create note events
        note_events = []
        for semitone_idx in sorted(fundamental_indices):
            window = self.semitone_windows[semitone_idx]

            # Convert to note event format
            note_event = {
                'midi_note': semitone_idx + 21,  # Convert to MIDI note (A0 = 21)
                'frequency': window['center_freq'],
                'onset_time_seconds': window['time_start'] * self.window_length / self.sample_rate,
                'offset_time_seconds': window['time_end'] * self.window_length / self.sample_rate,
                'duration_seconds': (window['time_end'] - window['time_start']) * self.window_length / self.sample_rate,
                'velocity': 80,  # Use moderate velocity (64 is default, 80 is slightly louder)
                'confidence': 0.9,  # High confidence for spatiotemporal approach
                'semitone_idx': semitone_idx
            }
            note_events.append(note_event)

        return note_events


if __name__ == '__main__':
    print("Spatiotemporal Analyzer - use from audio_to_midi_pipeline.py")
