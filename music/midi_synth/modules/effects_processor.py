"""
Effects Processor Module

Responsibility: Apply audio effects (reverb, chorus, etc.)

Input: Dry audio waveform
Output: Processed audio with effects
"""

import numpy as np
from typing import Optional


class EffectsProcessor:
    """
    Apply audio effects to waveforms.

    Supports:
    - Reverb (comb filter-based)
    - Chorus (LFO-modulated delay)
    - Stereo widening
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize effects processor.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate

    def apply_reverb(self, audio: np.ndarray,
                     room_size: float = 0.5,
                     damping: float = 0.5,
                     wet: float = 0.3) -> np.ndarray:
        """
        Apply reverb using parallel comb filters.

        Args:
            audio: Input audio (mono or stereo)
            room_size: Room size (0.0 to 1.0)
            damping: High frequency damping (0.0 to 1.0)
            wet: Wet/dry mix (0.0 = dry, 1.0 = wet)

        Returns:
            Audio with reverb applied
        """
        if audio.ndim == 1:
            # Mono input
            reverb = self._reverb_mono(audio, room_size, damping)
            return audio * (1 - wet) + reverb * wet
        else:
            # Stereo input
            left = self._reverb_mono(audio[:, 0], room_size, damping)
            right = self._reverb_mono(audio[:, 1], room_size, damping * 1.1)
            reverb = np.column_stack([left, right])
            return audio * (1 - wet) + reverb * wet

    def _reverb_mono(self, audio: np.ndarray,
                     room_size: float,
                     damping: float) -> np.ndarray:
        """
        Mono reverb using comb filters.

        Uses Freeverb-inspired parameters.
        """
        # Comb filter delay times (in samples)
        # Based on Freeverb's tuning
        base_delays = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116]

        # Scale by room size
        delays = [int(d * (0.5 + room_size * 0.5)) for d in base_delays]

        # Initialize output
        output = np.zeros_like(audio)

        # Apply parallel comb filters
        for delay_samples in delays:
            output += self._comb_filter(audio, delay_samples, damping)

        # Normalize
        output /= len(delays)

        # Apply allpass filters for diffusion
        output = self._allpass_filter(output, 556)
        output = self._allpass_filter(output, 441)
        output = self._allpass_filter(output, 341)
        output = self._allpass_filter(output, 225)

        return output

    def _comb_filter(self, audio: np.ndarray,
                     delay_samples: int,
                     damping: float) -> np.ndarray:
        """
        Comb filter with damping.

        Args:
            audio: Input audio
            delay_samples: Delay in samples
            damping: Damping factor (0.0 to 1.0)

        Returns:
            Filtered audio
        """
        output = np.zeros_like(audio)
        buffer = np.zeros(delay_samples)
        buffer_idx = 0

        # Feedback coefficient
        feedback = 0.84

        # Damping filter state
        filter_state = 0.0

        for i in range(len(audio)):
            # Get delayed sample
            delayed = buffer[buffer_idx]

            # Apply damping (one-pole lowpass)
            filter_state = delayed * (1 - damping) + filter_state * damping

            # Comb filter
            output[i] = audio[i] + filter_state * feedback

            # Update buffer
            buffer[buffer_idx] = output[i]
            buffer_idx = (buffer_idx + 1) % delay_samples

        return output

    def _allpass_filter(self, audio: np.ndarray,
                       delay_samples: int) -> np.ndarray:
        """
        Allpass filter for diffusion.

        Args:
            audio: Input audio
            delay_samples: Delay in samples

        Returns:
            Filtered audio
        """
        output = np.zeros_like(audio)
        buffer = np.zeros(delay_samples)
        buffer_idx = 0

        # Allpass coefficient
        gain = 0.5

        for i in range(len(audio)):
            delayed = buffer[buffer_idx]

            # Allpass formula
            output[i] = -audio[i] + delayed + gain * (audio[i] - gain * delayed)

            buffer[buffer_idx] = audio[i]
            buffer_idx = (buffer_idx + 1) % delay_samples

        return output

    def apply_chorus(self, audio: np.ndarray,
                    rate: float = 1.5,
                    depth: float = 0.002,
                    wet: float = 0.5) -> np.ndarray:
        """
        Apply chorus effect using LFO-modulated delay.

        Args:
            audio: Input audio (mono or stereo)
            rate: LFO rate in Hz
            depth: Modulation depth in seconds
            wet: Wet/dry mix (0.0 = dry, 1.0 = wet)

        Returns:
            Audio with chorus applied
        """
        if audio.ndim == 1:
            # Mono input - create pseudo-stereo
            chorus = self._chorus_mono(audio, rate, depth)
            return audio * (1 - wet) + chorus * wet
        else:
            # Stereo input
            left = self._chorus_mono(audio[:, 0], rate, depth)
            right = self._chorus_mono(audio[:, 1], rate * 1.1, depth)
            chorus = np.column_stack([left, right])
            return audio * (1 - wet) + chorus * wet

    def _chorus_mono(self, audio: np.ndarray,
                    rate: float,
                    depth: float) -> np.ndarray:
        """
        Mono chorus using modulated delay.

        Args:
            audio: Input audio
            rate: LFO rate in Hz
            depth: Modulation depth in seconds

        Returns:
            Chorused audio
        """
        samples = len(audio)

        # Generate LFO (sine wave)
        t = np.arange(samples) / self.sample_rate
        lfo = np.sin(2 * np.pi * rate * t)

        # Convert depth to samples
        depth_samples = depth * self.sample_rate

        # Modulated delay in samples
        delay = depth_samples * (1 + lfo) / 2

        # Apply variable delay
        output = np.zeros_like(audio)

        for i in range(samples):
            delay_amt = delay[i]

            # Linear interpolation for fractional delay
            idx = i - delay_amt

            if idx >= 1:
                idx_floor = int(np.floor(idx))
                idx_frac = idx - idx_floor

                if idx_floor < samples:
                    output[i] = (audio[idx_floor] * (1 - idx_frac) +
                               audio[min(idx_floor + 1, samples - 1)] * idx_frac)

        return output

    def apply_stereo_widening(self, audio: np.ndarray,
                             width: float = 0.5) -> np.ndarray:
        """
        Apply stereo widening effect.

        Args:
            audio: Stereo audio (N, 2)
            width: Widening amount (0.0 = mono, 1.0 = maximum width)

        Returns:
            Widened stereo audio

        Note:
            Input must be stereo (2 channels)
        """
        if audio.ndim == 1:
            # Mono input - just return as is
            return audio

        if audio.shape[1] != 2:
            # Not stereo
            return audio

        # Mid-side processing
        mid = (audio[:, 0] + audio[:, 1]) / 2
        side = (audio[:, 0] - audio[:, 1]) / 2

        # Widen by increasing side signal
        side_widened = side * (1 + width)

        # Convert back to left-right
        left = mid + side_widened
        right = mid - side_widened

        return np.column_stack([left, right])

    def apply_compression(self, audio: np.ndarray,
                         threshold: float = -20.0,
                         ratio: float = 4.0,
                         attack: float = 0.005,
                         release: float = 0.1) -> np.ndarray:
        """
        Apply simple dynamic range compression.

        Args:
            audio: Input audio
            threshold: Threshold in dB
            ratio: Compression ratio (e.g., 4.0 = 4:1)
            attack: Attack time in seconds
            release: Release time in seconds

        Returns:
            Compressed audio
        """
        # Convert threshold to linear
        threshold_lin = 10 ** (threshold / 20.0)

        # Attack/release coefficients
        attack_coef = np.exp(-1.0 / (attack * self.sample_rate))
        release_coef = np.exp(-1.0 / (release * self.sample_rate))

        # Process
        envelope = 0.0
        output = np.zeros_like(audio)

        samples = audio if audio.ndim == 1 else audio[:, 0]

        for i, sample in enumerate(samples):
            # Get amplitude
            amplitude = abs(sample)

            # Envelope follower
            if amplitude > envelope:
                envelope = attack_coef * envelope + (1 - attack_coef) * amplitude
            else:
                envelope = release_coef * envelope + (1 - release_coef) * amplitude

            # Calculate gain reduction
            if envelope > threshold_lin:
                gain = threshold_lin + (envelope - threshold_lin) / ratio
                gain = gain / envelope
            else:
                gain = 1.0

            # Apply gain
            if audio.ndim == 1:
                output[i] = sample * gain
            else:
                output[i, :] = audio[i, :] * gain

        return output
