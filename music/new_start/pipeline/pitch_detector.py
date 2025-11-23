#!/usr/bin/env python3
"""
Pitch Detection for Phase 2: Melody Extraction

Implements spectral peak detection with harmonic analysis to identify
the fundamental frequency (f0) of musical notes.

Uses the custom SpectralAnalyzer for musically-tuned frequency analysis.

Goal: Pitch accuracy > 95% (within ±1 semitone)
"""

import numpy as np
from scipy import signal
from scipy.signal import find_peaks
import sys
from pathlib import Path

# Add parent directory to path to import spectral_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))
from spectral_analyzer import SpectralAnalyzer


class PitchDetector:
    """
    Pitch detection using spectral peaks and harmonic series analysis.

    Detects fundamental frequency by finding peaks in the spectrum
    and validating which peak has the strongest harmonic series.
    """

    def __init__(self, sample_rate=44100, fft_size=4096, min_freq=27.5, max_freq=4186,
                 use_spectral_analyzer=False):
        """
        Initialize pitch detector.

        Args:
            sample_rate: Audio sample rate (Hz)
            fft_size: FFT size for spectral analysis (larger = better freq resolution)
            min_freq: Minimum detectable frequency (A0 = 27.5 Hz)
            max_freq: Maximum detectable frequency (C8 = 4186 Hz)
            use_spectral_analyzer: Use custom SpectralAnalyzer (recommended)
        """
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.use_spectral_analyzer = use_spectral_analyzer

        # Initialize SpectralAnalyzer if requested
        if use_spectral_analyzer:
            # Configure for full piano range with fine resolution
            self.spectral_analyzer = SpectralAnalyzer(
                samplefreq=sample_rate,
                cycles=4,  # 4 cycles for analysis window
                standard_A4=440.0,
                note_begin=-9,  # C0 (3 semitones below A0)
                note_end=89,    # Full piano range
                increments=1    # 1 subdivision per semitone
            )

    def detect_pitch(self, audio, onset_time, window_duration=None):
        """
        Detect pitch at a specific onset time.

        Uses SpectralAnalyzer if enabled, otherwise uses hybrid approach.

        Args:
            audio: Audio signal (mono, float32, normalized)
            onset_time: Time of note onset in seconds
            window_duration: Duration of analysis window (auto if None)

        Returns:
            Detected frequency in Hz (0 if no pitch detected)
        """
        if self.use_spectral_analyzer:
            return self._detect_pitch_spectral_analyzer(audio, onset_time)
        else:
            return self._detect_pitch_hybrid(audio, onset_time)

    def _detect_pitch_spectral_analyzer(self, audio, onset_time):
        """
        Detect pitch using the custom SpectralAnalyzer.

        This uses the user's original Fourier-like analysis tuned to
        musical frequencies.

        Args:
            audio: Audio signal (mono, float32)
            onset_time: Time of onset in seconds

        Returns:
            Detected frequency in Hz
        """
        # Extract a window around the onset for analysis
        # Use adaptive window: longer for low notes, shorter for high notes
        window_duration = 0.1  # 100ms default
        onset_sample = int(onset_time * self.sample_rate)
        window_samples = int(window_duration * self.sample_rate)

        start = max(0, onset_sample)
        end = min(len(audio), onset_sample + window_samples)
        window = audio[start:end]

        if len(window) < 100:
            return 0.0

        # Convert to int16 range (SpectralAnalyzer expects this)
        if window.dtype in [np.float32, np.float64]:
            window_int = (window * 32768.0).astype(np.int16)
        else:
            window_int = window

        # Analyze just this window
        spectral_data = self.spectral_analyzer.dotop(window_int)
        # spectral_data shape: [num_frequencies, num_time_slices]

        # Use the first time slice (right at onset)
        if spectral_data.shape[1] > 0:
            frequency_amplitudes = spectral_data[:, 0]
        else:
            return 0.0

        # Find the strongest peak
        max_freq_idx = np.argmax(frequency_amplitudes)
        detected_freq = self.spectral_analyzer.frequencies[max_freq_idx]

        # For piano, often the 2nd or 3rd harmonic is stronger than fundamental
        # Look for peaks and use harmonic series analysis
        peak_indices, properties = find_peaks(
            frequency_amplitudes,
            prominence=0.1 * np.max(frequency_amplitudes),
            height=0.05 * np.max(frequency_amplitudes)
        )

        if len(peak_indices) > 1:
            # Get peak frequencies
            peak_freqs = self.spectral_analyzer.frequencies[peak_indices]
            peak_amps = frequency_amplitudes[peak_indices]

            # Check if peaks form harmonic series
            # Try each peak as fundamental and score based on harmonic matches
            best_score = 0
            best_fundamental = detected_freq

            for i, f0_candidate in enumerate(peak_freqs):
                if f0_candidate < self.min_freq or f0_candidate > self.max_freq:
                    continue

                # Count how many peaks are near harmonics of this candidate
                score = peak_amps[i]  # Start with amplitude of this peak

                for h in range(2, 6):  # Check harmonics 2-5
                    expected_harmonic = f0_candidate * h

                    # Find if any peak is near this harmonic
                    for j, peak_freq in enumerate(peak_freqs):
                        if abs(peak_freq - expected_harmonic) / expected_harmonic < 0.05:
                            score += peak_amps[j] / h  # Weight by harmonic number
                            break

                if score > best_score:
                    best_score = score
                    best_fundamental = f0_candidate

            detected_freq = best_fundamental

        # Validate
        if detected_freq < self.min_freq or detected_freq > self.max_freq:
            return 0.0

        return detected_freq

    def _detect_pitch_hybrid(self, audio, onset_time):
        """
        Detect pitch using hybrid FFT + autocorrelation approach.

        Args:
            audio: Audio signal
            onset_time: Onset time in seconds

        Returns:
            Detected frequency in Hz
        """
        # Extract initial window to estimate frequency range
        onset_sample = int(onset_time * self.sample_rate)

        # Use FFT first to get rough estimate
        initial_window_samples = int(0.020 * self.sample_rate)  # 20ms
        start = max(0, onset_sample)
        end = min(len(audio), onset_sample + initial_window_samples)
        initial_window = audio[start:end]

        if len(initial_window) < 100:
            return 0.0

        # Quick FFT to determine frequency range
        rough_freq = self._detect_pitch_fft(initial_window)

        # Choose method based on rough frequency
        if rough_freq > 800:  # High note - use FFT with short window
            # Short window for high notes (20-50ms)
            window_dur = 0.030  # 30ms
            window_samples = int(window_dur * self.sample_rate)
            end = min(len(audio), onset_sample + window_samples)
            window = audio[start:end]

            if len(window) < 100:
                return 0.0

            pitch = self._detect_pitch_fft(window)

        else:  # Low/mid note - use autocorrelation with longer window
            # Longer window for low notes (100-150ms)
            window_dur = 0.100  # 100ms
            window_samples = int(window_dur * self.sample_rate)
            end = min(len(audio), onset_sample + window_samples)
            window = audio[start:end]

            if len(window) < 100:
                return 0.0

            pitch = self._detect_pitch_autocorrelation(window)

        return pitch

    def _detect_pitch_fft(self, window):
        """
        Detect pitch using FFT (frequency domain).

        Works well for high frequencies with large frequency separation.

        Args:
            window: Audio window

        Returns:
            Fundamental frequency (Hz), or 0 if none detected
        """
        # Apply window function
        windowed = window * np.hanning(len(window))

        # Compute FFT with zero padding for better resolution
        spectrum = np.fft.rfft(windowed, n=self.fft_size)
        magnitude = np.abs(spectrum)
        frequencies = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)

        # Find peaks
        peak_indices, _ = find_peaks(
            magnitude,
            prominence=0.1 * np.max(magnitude),
            distance=5
        )

        if len(peak_indices) == 0:
            # Fallback: just take max
            peak_idx = np.argmax(magnitude)
            freq = frequencies[peak_idx]
            if self.min_freq <= freq <= self.max_freq:
                return freq
            return 0.0

        # Get peak frequencies and magnitudes
        peak_freqs = frequencies[peak_indices]
        peak_mags = magnitude[peak_indices]

        # Filter to valid range
        valid = (peak_freqs >= self.min_freq) & (peak_freqs <= self.max_freq)
        peak_freqs = peak_freqs[valid]
        peak_mags = peak_mags[valid]

        if len(peak_freqs) == 0:
            return 0.0

        # Take the strongest peak in valid range
        strongest_idx = np.argmax(peak_mags)
        freq = peak_freqs[strongest_idx]

        return freq

    def _detect_pitch_autocorrelation(self, window):
        """
        Detect pitch using autocorrelation.

        Autocorrelation finds repeating patterns in the waveform,
        which correspond to the fundamental period. This works even
        when the fundamental frequency is missing from the spectrum.

        Args:
            window: Audio window

        Returns:
            Fundamental frequency (Hz), or 0 if none detected
        """
        # Compute autocorrelation
        autocorr = np.correlate(window, window, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # Keep only positive lags

        # Normalize
        if autocorr[0] > 0:
            autocorr = autocorr / autocorr[0]

        # Find valid lag range (based on min/max frequency)
        min_lag = int(self.sample_rate / self.max_freq)
        max_lag = int(self.sample_rate / self.min_freq)
        max_lag = min(max_lag, len(autocorr) - 1)

        if min_lag >= max_lag:
            return 0.0

        # Find peaks in autocorrelation
        # The first significant peak after lag 0 corresponds to the period
        autocorr_search = autocorr[min_lag:max_lag]

        if len(autocorr_search) == 0:
            return 0.0

        # Find peaks
        peaks, properties = find_peaks(
            autocorr_search,
            height=0.3,  # Minimum correlation (30%)
            prominence=0.1  # Peak must stand out
        )

        if len(peaks) == 0:
            return 0.0

        # Get the first strong peak (prefer fundamental over harmonics)
        # Sort peaks by correlation strength
        peak_strengths = autocorr_search[peaks]
        sorted_peak_indices = peaks[np.argsort(-peak_strengths)]  # Descending order

        # Take the first strong peak (likely the fundamental)
        best_peak_idx = sorted_peak_indices[0]
        period_lag = best_peak_idx + min_lag

        # Convert lag to frequency
        freq = self.sample_rate / period_lag

        # Validate frequency is in range
        if freq < self.min_freq or freq > self.max_freq:
            return 0.0

        return freq

    def _detect_pitch_from_spectrum(self, magnitude, frequencies):
        """
        Detect fundamental frequency from magnitude spectrum.

        Uses spectral peak detection + harmonic series validation.

        Args:
            magnitude: Magnitude spectrum
            frequencies: Frequency bins (Hz)

        Returns:
            Fundamental frequency (Hz), or 0 if none detected
        """
        # Find spectral peaks
        peak_freqs, peak_mags = self._find_spectral_peaks(magnitude, frequencies)

        if len(peak_freqs) == 0:
            return 0.0

        # Find fundamental using harmonic analysis
        f0 = self._find_fundamental_from_harmonics(peak_freqs, peak_mags)

        # Validate frequency is in valid range
        if f0 < self.min_freq or f0 > self.max_freq:
            return 0.0

        return f0

    def _find_spectral_peaks(self, magnitude, frequencies, min_prominence=0.05):
        """
        Find significant peaks in the magnitude spectrum.

        Args:
            magnitude: Magnitude spectrum
            frequencies: Frequency bins
            min_prominence: Minimum prominence (relative to max magnitude)

        Returns:
            peak_freqs: Array of peak frequencies (Hz)
            peak_mags: Array of peak magnitudes
        """
        # Find peaks in spectrum
        peak_indices, properties = find_peaks(
            magnitude,
            prominence=min_prominence * np.max(magnitude),
            distance=5  # Minimum bin separation (avoid duplicates)
        )

        # Extract frequencies and magnitudes
        peak_freqs = frequencies[peak_indices]
        peak_mags = magnitude[peak_indices]

        # Filter to valid frequency range
        valid = (peak_freqs >= self.min_freq) & (peak_freqs <= self.max_freq * 2)
        peak_freqs = peak_freqs[valid]
        peak_mags = peak_mags[valid]

        return peak_freqs, peak_mags

    def _find_fundamental_from_harmonics(self, peak_freqs, peak_mags, tolerance=0.03):
        """
        Find fundamental frequency by analyzing harmonic series.

        For each candidate fundamental, check if harmonics (2f, 3f, 4f, ...)
        are present in the peak list. The true fundamental will have the
        most complete harmonic series.

        Args:
            peak_freqs: Array of peak frequencies
            peak_mags: Array of peak magnitudes
            tolerance: Frequency matching tolerance (3% by default)

        Returns:
            Fundamental frequency (Hz)
        """
        if len(peak_freqs) == 0:
            return 0.0

        # Try each peak as a potential fundamental
        candidates = []

        for i, f0_candidate in enumerate(peak_freqs):
            # Skip if this peak is likely a harmonic of a lower peak
            # (i.e., if there's a peak at ~f0/2, this is probably the 2nd harmonic)
            is_likely_harmonic = False
            for j, lower_freq in enumerate(peak_freqs):
                if lower_freq < f0_candidate:
                    # Check if f0_candidate is near a harmonic of lower_freq
                    for h in [2, 3, 4, 5]:
                        expected = lower_freq * h
                        if abs(f0_candidate - expected) / expected < tolerance:
                            is_likely_harmonic = True
                            break
                if is_likely_harmonic:
                    break

            if is_likely_harmonic:
                continue

            # Count harmonics present for this fundamental
            harmonic_count = 1  # The fundamental itself
            harmonic_energy = peak_mags[i]

            # Check for harmonics at 2*f0, 3*f0, 4*f0, ...
            for h in range(2, 10):  # Check up to 9th harmonic
                expected_freq = f0_candidate * h

                if expected_freq > self.max_freq * 2:
                    break  # Beyond detectable range

                # Find if any peak matches this harmonic
                for pf, pm in zip(peak_freqs, peak_mags):
                    rel_error = abs(pf - expected_freq) / expected_freq
                    if rel_error < tolerance:
                        harmonic_count += 1
                        harmonic_energy += pm
                        break

            # Score this candidate
            # Weight both harmonic count and total energy
            score = harmonic_count * np.sqrt(harmonic_energy)

            candidates.append({
                'f0': f0_candidate,
                'harmonic_count': harmonic_count,
                'harmonic_energy': harmonic_energy,
                'score': score
            })

        if not candidates:
            # No valid fundamental found, return lowest peak
            return peak_freqs[0] if len(peak_freqs) > 0 else 0.0

        # Best candidate has highest score
        best = max(candidates, key=lambda x: x['score'])

        # Require at least 2 harmonics (fundamental + 1 harmonic)
        if best['harmonic_count'] < 2:
            # Fallback: return peak with highest magnitude
            max_idx = np.argmax(peak_mags)
            return peak_freqs[max_idx]

        return best['f0']

    def detect_pitches(self, audio, onset_times):
        """
        Detect pitches for multiple onsets.

        Args:
            audio: Audio signal
            onset_times: Array of onset times (seconds)

        Returns:
            Array of detected frequencies (Hz)
        """
        pitches = []

        for onset_time in onset_times:
            pitch = self.detect_pitch(audio, onset_time)
            pitches.append(pitch)

        return np.array(pitches)


def freq_to_midi(freq):
    """
    Convert frequency (Hz) to MIDI note number.

    MIDI note 69 = A4 = 440 Hz
    Each semitone is a factor of 2^(1/12)

    Args:
        freq: Frequency in Hz

    Returns:
        MIDI note number (0-127), rounded to nearest integer
    """
    if freq <= 0:
        return 0

    midi_note = 69 + 12 * np.log2(freq / 440.0)
    return round(midi_note)


def midi_to_freq(midi_note):
    """
    Convert MIDI note number to frequency (Hz).

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        Frequency in Hz
    """
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def midi_to_note_name(midi_note):
    """
    Convert MIDI note number to note name.

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        Note name (e.g., "C4", "A4", "Gb5")
    """
    notes = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    octave = (midi_note // 12) - 1
    note = notes[midi_note % 12]
    return f"{note}{octave}"


def note_name_to_midi(note_name):
    """
    Convert note name to MIDI note number.

    Args:
        note_name: Note name (e.g., "C4", "A4", "Gb5")

    Returns:
        MIDI note number (0-127)
    """
    notes = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

    # Handle sharps (convert to flats)
    note_name = note_name.replace('C#', 'Db').replace('D#', 'Eb')
    note_name = note_name.replace('F#', 'Gb').replace('G#', 'Ab')
    note_name = note_name.replace('A#', 'Bb')

    # Parse note and octave
    if len(note_name) >= 2:
        if note_name[1] == 'b':
            note = note_name[:2]
            octave = int(note_name[2:])
        else:
            note = note_name[0]
            octave = int(note_name[1:])

        note_idx = notes.index(note)
        midi_note = (octave + 1) * 12 + note_idx

        return midi_note

    return 0


if __name__ == "__main__":
    print("Pitch Detection for Phase 2: Melody Extraction")
    print()
    print("Usage:")
    print("  from pitch_detector import PitchDetector, freq_to_midi, midi_to_note_name")
    print()
    print("  # Detect pitch at onset")
    print("  detector = PitchDetector(sample_rate=44100)")
    print("  freq = detector.detect_pitch(audio, onset_time)")
    print("  midi_note = freq_to_midi(freq)")
    print("  note_name = midi_to_note_name(midi_note)")
    print()
    print("Conversion examples:")
    print(f"  A4 (440 Hz) = MIDI {freq_to_midi(440)} = {midi_to_note_name(freq_to_midi(440))}")
    print(f"  C4 (261.63 Hz) = MIDI {freq_to_midi(261.63)} = {midi_to_note_name(freq_to_midi(261.63))}")
    print(f"  MIDI 60 = {midi_to_freq(60):.2f} Hz = {midi_to_note_name(60)}")
    print(f"  MIDI 69 = {midi_to_freq(69):.2f} Hz = {midi_to_note_name(69)}")
