"""
Autocorrelation-based Fundamental Frequency Detection

Uses autocorrelation of the frequency spectrum to identify fundamental frequencies
from harmonic series. This is a proven pitch detection technique that's robust to
missing fundamentals.

Key idea: If harmonics exist at f₀, 2f₀, 3f₀, 4f₀, etc., the autocorrelation
of the spectrum will show strong peaks at lags corresponding to f₀ spacing.
"""
import numpy as np
from typing import List, Dict, Optional
from scipy.signal import find_peaks


class AutocorrelationAnalyzer:
    """
    Detect fundamental frequencies using spectral autocorrelation.

    This technique:
    1. Takes the spectrum at each time sample
    2. Computes autocorrelation along the frequency dimension
    3. Finds peaks in autocorrelation (these indicate harmonic spacing)
    4. Converts peak lags to fundamental frequencies
    """

    def __init__(self,
                 spectral_data: np.ndarray,
                 frequencies: np.ndarray,
                 sample_rate: int,
                 window_length: int,
                 min_autocorr_peak: float = 0.3,
                 min_frequency: float = 80.0,
                 max_frequency: float = 1000.0):
        """
        Initialize autocorrelation analyzer.

        Args:
            spectral_data: 2D array [num_frequencies, num_time_samples]
            frequencies: Array of frequency values for each bin
            sample_rate: Audio sample rate in Hz
            window_length: Analysis window length in samples
            min_autocorr_peak: Minimum autocorrelation value for peak detection
            min_frequency: Minimum fundamental frequency to detect (Hz)
            max_frequency: Maximum fundamental frequency to detect (Hz)
        """
        self.spectral_data = spectral_data
        self.frequencies = frequencies
        self.sample_rate = sample_rate
        self.window_length = window_length
        self.min_autocorr_peak = min_autocorr_peak
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency

        # Normalize spectral data
        max_val = np.max(spectral_data)
        if max_val > 0:
            self.spectral_data = spectral_data / max_val

        self.num_frequencies = spectral_data.shape[0]
        self.num_time_samples = spectral_data.shape[1]

        # Calculate frequency resolution (Hz per bin)
        self.freq_resolution = (frequencies[-1] - frequencies[0]) / len(frequencies)

    def lag_to_frequency(self, lag: int) -> float:
        """
        Convert autocorrelation lag (in bins) to fundamental frequency.

        Args:
            lag: Lag in number of frequency bins

        Returns:
            Fundamental frequency in Hz
        """
        # lag (bins) * freq_resolution (Hz/bin) = spacing between harmonics (Hz)
        # spacing between harmonics = fundamental frequency
        return lag * self.freq_resolution

    def frequency_to_lag(self, freq: float) -> int:
        """
        Convert frequency to expected autocorrelation lag.

        Args:
            freq: Frequency in Hz

        Returns:
            Expected lag in bins
        """
        return int(round(freq / self.freq_resolution))

    def find_fundamentals_at_time(self, time_idx: int,
                                    intensity_threshold: float = 0.05) -> List[Dict]:
        """
        Find fundamental frequencies at a specific time using autocorrelation.

        Args:
            time_idx: Time sample index
            intensity_threshold: Minimum spectral intensity to consider

        Returns:
            List of detected fundamentals with metadata
        """
        # Get spectrum at this time
        spectrum = self.spectral_data[:, time_idx].copy()

        # Filter out low-intensity bins
        spectrum[spectrum < intensity_threshold] = 0

        # Check if there's any significant energy
        if np.max(spectrum) < intensity_threshold:
            return []

        # Compute autocorrelation
        autocorr = np.correlate(spectrum, spectrum, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # Keep only positive lags

        # Normalize autocorrelation
        if autocorr[0] > 0:
            autocorr = autocorr / autocorr[0]

        # Calculate lag range corresponding to our frequency range
        min_lag = self.frequency_to_lag(self.min_frequency)
        max_lag = self.frequency_to_lag(self.max_frequency)

        # Clamp to valid range
        min_lag = max(1, min_lag)  # Skip lag=0 (always a peak)
        max_lag = min(len(autocorr) - 1, max_lag)

        if min_lag >= max_lag:
            return []

        # Find peaks in autocorrelation within our frequency range
        # Only look at the relevant lag range
        search_region = autocorr[min_lag:max_lag+1]

        # Find peaks
        peaks, properties = find_peaks(
            search_region,
            height=self.min_autocorr_peak,
            distance=min_lag // 2  # Peaks should be reasonably separated
        )

        # Convert peaks back to full autocorr indices
        peaks = peaks + min_lag

        # Extract fundamental frequencies
        fundamentals = []
        for peak_idx, peak_height in zip(peaks, properties['peak_heights']):
            freq = self.lag_to_frequency(peak_idx)

            # Verify frequency is in our range
            if self.min_frequency <= freq <= self.max_frequency:
                # Find the strongest frequency bin near this fundamental
                freq_bin_idx = np.argmin(np.abs(self.frequencies - freq))

                fundamentals.append({
                    'frequency': freq,
                    'autocorr_strength': float(peak_height),
                    'freq_bin_idx': freq_bin_idx,
                    'time_idx': time_idx,
                    'time_seconds': (time_idx * self.window_length) / self.sample_rate,
                    'spectral_intensity': float(spectrum[freq_bin_idx]) if freq_bin_idx < len(spectrum) else 0.0
                })

        # Sort by autocorrelation strength (strongest first)
        fundamentals.sort(key=lambda x: x['autocorr_strength'], reverse=True)

        return fundamentals

    def analyze_all_times(self,
                          intensity_threshold: float = 0.05,
                          min_duration_samples: int = 2) -> List[Dict]:
        """
        Analyze all time samples to find fundamentals.

        Args:
            intensity_threshold: Minimum spectral intensity
            min_duration_samples: Minimum duration for a note

        Returns:
            List of detected note events
        """
        print(f"Analyzing {self.num_time_samples} time samples using autocorrelation...")

        # Detect fundamentals at each time sample
        all_fundamentals = []
        for time_idx in range(self.num_time_samples):
            fundamentals = self.find_fundamentals_at_time(time_idx, intensity_threshold)
            all_fundamentals.extend(fundamentals)

        print(f"  Found {len(all_fundamentals)} fundamental detections")

        if not all_fundamentals:
            return []

        # Group detections by frequency (merge nearby frequencies)
        # This consolidates detections of the same note across time
        note_events = self._consolidate_detections(all_fundamentals, min_duration_samples)

        print(f"  Consolidated into {len(note_events)} note events")

        return note_events

    def _consolidate_detections(self, detections: List[Dict],
                                 min_duration_samples: int) -> List[Dict]:
        """
        Consolidate individual detections into sustained note events.

        Args:
            detections: List of fundamental detections
            min_duration_samples: Minimum duration to keep

        Returns:
            List of consolidated note events
        """
        if not detections:
            return []

        # Sort by time, then by frequency
        detections.sort(key=lambda x: (x['time_idx'], x['frequency']))

        # Group detections into continuous note events
        # Notes within 5% frequency and consecutive/near-consecutive time = same note
        note_events = []
        current_note = None

        for detection in detections:
            if current_note is None:
                # Start new note
                current_note = {
                    'frequency': detection['frequency'],
                    'start_time_idx': detection['time_idx'],
                    'end_time_idx': detection['time_idx'],
                    'detections': [detection],
                    'max_autocorr': detection['autocorr_strength'],
                    'max_intensity': detection['spectral_intensity']
                }
            else:
                # Check if this detection continues the current note
                freq_diff = abs(detection['frequency'] - current_note['frequency']) / current_note['frequency']
                time_diff = detection['time_idx'] - current_note['end_time_idx']

                if freq_diff < 0.05 and time_diff <= 3:  # Within 5% frequency and 3 samples
                    # Continue current note
                    current_note['end_time_idx'] = detection['time_idx']
                    current_note['detections'].append(detection)
                    current_note['max_autocorr'] = max(current_note['max_autocorr'],
                                                        detection['autocorr_strength'])
                    current_note['max_intensity'] = max(current_note['max_intensity'],
                                                         detection['spectral_intensity'])
                else:
                    # End current note and start new one
                    note_events.append(current_note)
                    current_note = {
                        'frequency': detection['frequency'],
                        'start_time_idx': detection['time_idx'],
                        'end_time_idx': detection['time_idx'],
                        'detections': [detection],
                        'max_autocorr': detection['autocorr_strength'],
                        'max_intensity': detection['spectral_intensity']
                    }

        # Add final note
        if current_note is not None:
            note_events.append(current_note)

        # Filter by duration and convert to final format
        filtered_events = []
        for note in note_events:
            duration_samples = note['end_time_idx'] - note['start_time_idx'] + 1

            if duration_samples >= min_duration_samples:
                onset_time = (note['start_time_idx'] * self.window_length) / self.sample_rate
                offset_time = ((note['end_time_idx'] + 1) * self.window_length) / self.sample_rate

                # Convert frequency to MIDI note
                midi_note = self._frequency_to_midi(note['frequency'])

                filtered_events.append({
                    'midi_note': midi_note,
                    'frequency': note['frequency'],
                    'onset_time_seconds': onset_time,
                    'duration_seconds': offset_time - onset_time,
                    'velocity': min(127, int(64 + note['max_intensity'] * 63)),  # Scale to MIDI velocity
                    'confidence': note['max_autocorr'],
                    'num_detections': len(note['detections'])
                })

        return filtered_events

    def _frequency_to_midi(self, freq: float) -> int:
        """
        Convert frequency to MIDI note number.

        Args:
            freq: Frequency in Hz

        Returns:
            MIDI note number (0-127)
        """
        # MIDI note = 69 + 12 * log2(freq / 440)
        # 69 = A4 (440 Hz)
        if freq <= 0:
            return 0

        midi_float = 69 + 12 * np.log2(freq / 440.0)
        midi_note = int(round(midi_float))

        # Clamp to valid MIDI range
        return max(0, min(127, midi_note))


if __name__ == '__main__':
    print("Autocorrelation Analyzer - use from audio_to_midi_pipeline.py")
