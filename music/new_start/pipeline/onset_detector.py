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
from scipy.signal import find_peaks


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

        # Smooth the energy envelope (balance between noise reduction and onset preservation)
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

        # Smooth (balance between noise reduction and onset preservation)
        flux = self._smooth(flux, window_size=3)

        # Find peaks
        onset_frames = self._find_peaks(flux, threshold=self.onset_threshold)

        # Convert frames to time
        onset_times = self._frames_to_time(onset_frames)

        return onset_times

    def detect_onsets_combined(self, audio, first_onset_only=False):
        """
        Detect onsets using combined energy + spectral flux.

        Uses both methods and combines results for better accuracy.

        Args:
            audio: Audio signal (mono, float32)
            first_onset_only: If True, return only the first onset (for single-note recordings)

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

        # If requested, return only first onset (useful for single-note samples)
        if first_onset_only and len(merged_onsets) > 0:
            return np.array([merged_onsets[0]])

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

        # Smooth (balance between noise reduction and onset preservation)
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

    def _find_peaks(self, onset_signal, threshold=0.3):
        """
        Find peaks in signal using scipy's find_peaks with prominence.

        Uses prominence (how much a peak stands out) to filter spurious peaks.

        Args:
            onset_signal: 1D signal
            threshold: Minimum peak height (0-1)

        Returns:
            peak_indices: Indices of peaks
        """
        # Use scipy's find_peaks with prominence requirement
        # Prominence measures how much a peak stands out relative to surrounding signal
        # This filters out small bumps that aren't real onsets
        peak_indices, properties = find_peaks(
            onset_signal,
            height=threshold,            # Minimum peak height
            prominence=threshold * 0.15,  # Peak must stand out by 15% of threshold
            distance=3                   # Minimum 3 frames (~35ms) between peaks
        )

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

    def estimate_velocity(self, audio, onset_time, window_duration=0.015):
        """
        Estimate MIDI velocity for a note onset.

        Uses peak amplitude during attack transient (first 15ms after onset).
        This captures the initial strike intensity, not the sustain.

        Args:
            audio: Audio signal (mono, float32)
            onset_time: Time of onset in seconds
            window_duration: Duration of attack window in seconds (default 15ms)

        Returns:
            velocity: MIDI velocity (0-127)
        """
        # Get audio segment around onset (attack transient only)
        onset_sample = int(onset_time * self.sample_rate)
        window_samples = int(window_duration * self.sample_rate)

        # Extract window starting from onset
        start = max(0, onset_sample)
        end = min(len(audio), onset_sample + window_samples)
        window = audio[start:end]

        if len(window) == 0:
            return 64  # Default velocity

        # Use PEAK amplitude during attack (not RMS)
        # Peak amplitude better represents the strike intensity
        peak_amplitude = np.max(np.abs(window))

        # Map to MIDI velocity (0-127)
        # Real piano recordings have peak amplitudes roughly:
        # - p (piano/soft): 0.05 - 0.15
        # - mf (mezzo-forte): 0.15 - 0.4
        # - ff (fortissimo/loud): 0.4 - 1.0

        # Use power scaling (square root) for perceptual loudness
        # This compresses the dynamic range appropriately
        velocity = int(127 * np.sqrt(peak_amplitude))
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
