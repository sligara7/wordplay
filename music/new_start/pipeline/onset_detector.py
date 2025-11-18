#!/usr/bin/env python3
"""
Onset Detection for Phase 1: Timing & Dynamics

Implements multiple onset detection methods:
1. Energy-based (RMS envelope)
2. Spectral flux
3. Combined approach

Goal: Onset timing error < 50ms
"""

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d


class OnsetDetector:
    """
    Multi-method onset detection.

    Detects note onsets (attacks) in audio using energy and spectral features.
    """

    def __init__(self, sample_rate=44100, hop_length=512, onset_threshold=0.3):
        """
        Initialize onset detector.

        Args:
            sample_rate: Audio sample rate
            hop_length: Hop length for frame analysis
            onset_threshold: Threshold for onset detection (0-1, higher = fewer onsets)
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.onset_threshold = onset_threshold

    def detect_onsets_energy(self, audio):
        """
        Detect onsets using energy envelope (RMS).

        Simple and fast method based on amplitude changes.

        Args:
            audio: Audio signal (mono, float32)

        Returns:
            onset_times: Array of onset times in seconds
        """
        # Compute RMS energy in overlapping windows
        frame_length = self.hop_length * 2
        rms = np.array([
            np.sqrt(np.mean(audio[i:i+frame_length]**2))
            for i in range(0, len(audio) - frame_length, self.hop_length)
        ])

        # Smooth the energy envelope
        rms = self._smooth(rms, window_size=3)

        # Find peaks in energy (onsets)
        onset_frames = self._find_peaks(rms, threshold=self.onset_threshold)

        # Convert frames to time
        onset_times = self._frames_to_time(onset_frames)

        return onset_times

    def detect_onsets_spectral_flux(self, audio):
        """
        Detect onsets using spectral flux.

        Measures changes in frequency content - more robust for pitched instruments.

        Args:
            audio: Audio signal (mono, float32)

        Returns:
            onset_times: Array of onset times in seconds
        """
        # Compute STFT
        f, t, Zxx = signal.stft(
            audio,
            fs=self.sample_rate,
            nperseg=self.hop_length * 2,
            noverlap=self.hop_length
        )

        # Magnitude spectrogram
        mag = np.abs(Zxx)

        # Spectral flux: sum of positive differences between consecutive frames
        flux = np.zeros(mag.shape[1])
        for i in range(1, mag.shape[1]):
            diff = mag[:, i] - mag[:, i-1]
            flux[i] = np.sum(diff[diff > 0])  # Only positive changes

        # Normalize
        if np.max(flux) > 0:
            flux = flux / np.max(flux)

        # Smooth
        flux = self._smooth(flux, window_size=3)

        # Find peaks
        onset_frames = self._find_peaks(flux, threshold=self.onset_threshold)

        # Convert frames to time
        onset_times = self._frames_to_time(onset_frames)

        return onset_times

    def detect_onsets_combined(self, audio):
        """
        Detect onsets using combined energy + spectral flux.

        Uses both methods and combines results for better accuracy.

        Args:
            audio: Audio signal (mono, float32)

        Returns:
            onset_times: Array of onset times in seconds
        """
        # Get onsets from both methods
        energy_onsets = self.detect_onsets_energy(audio)
        spectral_onsets = self.detect_onsets_spectral_flux(audio)

        # Combine: Keep onsets that appear in either method
        all_onsets = np.concatenate([energy_onsets, spectral_onsets])
        all_onsets = np.sort(all_onsets)

        # Merge onsets within 50ms of each other
        merged_onsets = self._merge_close_onsets(all_onsets, tolerance=0.05)

        return merged_onsets

    def detect_onsets_spectral_data(self, spectral_data, time_per_slice):
        """
        Detect onsets from pre-computed spectral data.

        Uses the existing spectral analyzer output for integration with current pipeline.

        Args:
            spectral_data: Spectral matrix (frequencies, time)
            time_per_slice: Duration of each time slice

        Returns:
            onset_times: Array of onset times in seconds
        """
        # Sum energy across all frequencies for each time slice
        energy = np.sum(spectral_data, axis=0)

        # Normalize
        if np.max(energy) > 0:
            energy = energy / np.max(energy)

        # Spectral flux: changes in spectral content
        flux = np.zeros(spectral_data.shape[1])
        for i in range(1, spectral_data.shape[1]):
            diff = spectral_data[:, i] - spectral_data[:, i-1]
            flux[i] = np.sum(diff[diff > 0])

        # Normalize
        if np.max(flux) > 0:
            flux = flux / np.max(flux)

        # Combine energy and flux
        combined = 0.5 * energy + 0.5 * flux

        # Smooth
        combined = self._smooth(combined, window_size=3)

        # Find peaks
        onset_frames = self._find_peaks(combined, threshold=self.onset_threshold)

        # Convert frames to time
        onset_times = onset_frames * time_per_slice

        return onset_times

    def _smooth(self, signal, window_size=3):
        """
        Smooth signal using moving average.

        Args:
            signal: 1D signal
            window_size: Window size for smoothing

        Returns:
            Smoothed signal
        """
        if window_size <= 1:
            return signal

        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(signal, kernel, mode='same')
        return smoothed

    def _find_peaks(self, signal, threshold=0.3):
        """
        Find peaks in signal using local maxima.

        Args:
            signal: 1D signal
            threshold: Minimum peak height (0-1)

        Returns:
            peak_indices: Indices of peaks
        """
        # Find local maxima
        max_filter = maximum_filter1d(signal, size=5, mode='constant')
        is_peak = (signal == max_filter) & (signal > threshold)

        peak_indices = np.where(is_peak)[0]

        return peak_indices

    def _merge_close_onsets(self, onsets, tolerance=0.05):
        """
        Merge onsets that are very close together.

        Args:
            onsets: Array of onset times
            tolerance: Merge onsets within this time (seconds)

        Returns:
            merged_onsets: Array of merged onset times
        """
        if len(onsets) == 0:
            return onsets

        merged = [onsets[0]]

        for onset in onsets[1:]:
            if onset - merged[-1] > tolerance:
                merged.append(onset)

        return np.array(merged)

    def _frames_to_time(self, frames):
        """
        Convert frame indices to time in seconds.

        Args:
            frames: Frame indices

        Returns:
            times: Times in seconds
        """
        times = frames * self.hop_length / self.sample_rate
        return times


class VelocityEstimator:
    """
    Velocity estimation from audio amplitude.

    Goal: Velocity correlation > 0.7 with ground truth
    """

    def __init__(self, sample_rate=44100):
        """
        Initialize velocity estimator.

        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate

    def estimate_velocity(self, audio, onset_time, window_duration=0.05):
        """
        Estimate MIDI velocity for a note onset.

        Args:
            audio: Audio signal (mono, float32)
            onset_time: Time of onset in seconds
            window_duration: Duration of attack window in seconds (default 50ms)

        Returns:
            velocity: MIDI velocity (0-127)
        """
        # Get audio segment around onset
        onset_sample = int(onset_time * self.sample_rate)
        window_samples = int(window_duration * self.sample_rate)

        # Extract window
        start = max(0, onset_sample)
        end = min(len(audio), onset_sample + window_samples)
        window = audio[start:end]

        if len(window) == 0:
            return 64  # Default velocity

        # Compute RMS energy
        rms = np.sqrt(np.mean(window**2))

        # Map to MIDI velocity (0-127)
        # Calibration: typical RMS ranges from 0.01 (quiet) to 0.5 (loud)
        # Use logarithmic scaling for better perceptual mapping
        if rms < 0.001:
            velocity = 1
        else:
            # Log scaling: velocity = 127 * log10(rms / min_rms) / log10(max_rms / min_rms)
            min_rms = 0.001
            max_rms = 0.5
            log_rms = np.log10(np.clip(rms, min_rms, max_rms))
            log_min = np.log10(min_rms)
            log_max = np.log10(max_rms)

            velocity = int(127 * (log_rms - log_min) / (log_max - log_min))
            velocity = np.clip(velocity, 1, 127)

        return velocity

    def estimate_velocities(self, audio, onset_times):
        """
        Estimate velocities for multiple onsets.

        Args:
            audio: Audio signal
            onset_times: Array of onset times

        Returns:
            velocities: Array of MIDI velocities
        """
        velocities = []

        for onset_time in onset_times:
            velocity = self.estimate_velocity(audio, onset_time)
            velocities.append(velocity)

        return np.array(velocities)


if __name__ == "__main__":
    print("Onset Detection & Velocity Estimation")
    print("For Phase 1: Timing & Dynamics")
    print()
    print("Usage:")
    print("  from onset_detector import OnsetDetector, VelocityEstimator")
    print()
    print("  # Detect onsets")
    print("  detector = OnsetDetector(sample_rate=44100)")
    print("  onset_times = detector.detect_onsets_combined(audio)")
    print()
    print("  # Estimate velocities")
    print("  estimator = VelocityEstimator(sample_rate=44100)")
    print("  velocities = estimator.estimate_velocities(audio, onset_times)")
