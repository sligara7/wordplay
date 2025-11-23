"""
Master Processor Module

Responsibility: Final audio processing and output preparation

Input: Mixed audio
Output: Mastered audio ready for export
"""

import numpy as np
from typing import Optional


class MasterProcessor:
    """
    Final mastering and output preparation.

    Handles:
    - Soft limiting (avoid harsh clipping)
    - Peak normalization
    - Dithering (for 16-bit export)
    - Format conversion
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize master processor.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate

    def master(self, audio: np.ndarray,
              target_peak: float = 0.95,
              use_limiter: bool = True,
              use_dither: bool = False) -> np.ndarray:
        """
        Apply mastering chain.

        Args:
            audio: Input audio (float32, -1.0 to 1.0)
            target_peak: Target peak level (0.0 to 1.0)
            use_limiter: Apply soft limiter
            use_dither: Apply dithering for 16-bit export

        Returns:
            Mastered audio (float32)
        """
        # Apply soft limiting if requested
        if use_limiter:
            audio = self.soft_limit(audio, threshold=0.95, ceiling=1.0)

        # Normalize to target peak
        audio = self.normalize(audio, target_peak=target_peak)

        # Apply dithering if requested
        if use_dither:
            audio = self.apply_dither(audio)

        return audio

    def soft_limit(self, audio: np.ndarray,
                   threshold: float = 0.95,
                   ceiling: float = 1.0) -> np.ndarray:
        """
        Apply soft limiting to prevent harsh clipping.

        Uses tanh-based soft clipping for smooth saturation.

        Args:
            audio: Input audio
            threshold: Level above which limiting starts (0.0 to 1.0)
            ceiling: Maximum output level

        Returns:
            Limited audio
        """
        # Calculate gain to bring threshold to 1.0
        # This ensures tanh curve maps threshold → ceiling
        scale = 1.0 / threshold

        # Apply soft clipping using tanh
        limited = np.tanh(audio * scale) * ceiling

        return limited.astype(np.float32)

    def hard_clip(self, audio: np.ndarray,
                 ceiling: float = 1.0) -> np.ndarray:
        """
        Apply hard clipping (not recommended, use soft_limit instead).

        Args:
            audio: Input audio
            ceiling: Clipping threshold

        Returns:
            Clipped audio
        """
        return np.clip(audio, -ceiling, ceiling)

    def normalize(self, audio: np.ndarray,
                 target_peak: float = 0.95) -> np.ndarray:
        """
        Normalize audio to target peak level.

        Args:
            audio: Input audio
            target_peak: Target peak level (0.0 to 1.0)

        Returns:
            Normalized audio
        """
        current_peak = np.max(np.abs(audio))

        if current_peak > 0:
            gain = target_peak / current_peak
            return audio * gain
        else:
            return audio

    def normalize_rms(self, audio: np.ndarray,
                     target_rms_db: float = -20.0) -> np.ndarray:
        """
        Normalize based on RMS level instead of peak.

        Useful for consistent perceived loudness.

        Args:
            audio: Input audio
            target_rms_db: Target RMS level in dB

        Returns:
            Normalized audio
        """
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio ** 2))

        if current_rms > 0:
            # Convert target from dB to linear
            target_rms_linear = 10 ** (target_rms_db / 20.0)

            # Calculate gain
            gain = target_rms_linear / current_rms

            # Limit gain to prevent excessive amplification
            gain = min(gain, 10.0)  # Max +20dB

            return audio * gain
        else:
            return audio

    def apply_dither(self, audio: np.ndarray,
                    bit_depth: int = 16) -> np.ndarray:
        """
        Apply triangular dithering for bit depth reduction.

        Reduces quantization noise artifacts when converting to integer formats.

        Args:
            audio: Input audio (float32)
            bit_depth: Target bit depth (typically 16)

        Returns:
            Dithered audio (still float32)
        """
        # Triangular PDF dither (TPDF)
        # This is optimal for reducing quantization errors

        # Calculate quantization step
        max_value = 2 ** (bit_depth - 1)
        lsb = 1.0 / max_value

        # Generate triangular dither
        # TPDF = sum of two uniform random variables
        dither1 = np.random.uniform(-lsb, lsb, audio.shape)
        dither2 = np.random.uniform(-lsb, lsb, audio.shape)
        dither = (dither1 + dither2) / 2

        # Add dither
        return audio + dither

    def to_int16(self, audio: np.ndarray,
                apply_dither: bool = True) -> np.ndarray:
        """
        Convert float32 audio to int16 for WAV export.

        Args:
            audio: Input audio (float32, -1.0 to 1.0)
            apply_dither: Apply dithering before conversion

        Returns:
            Audio as int16 array
        """
        if apply_dither:
            audio = self.apply_dither(audio, bit_depth=16)

        # Clip to valid range
        audio = np.clip(audio, -1.0, 1.0)

        # Scale to int16 range
        max_value = 32767
        audio_int16 = (audio * max_value).astype(np.int16)

        return audio_int16

    def calculate_lufs(self, audio: np.ndarray) -> float:
        """
        Calculate approximate LUFS (Loudness Units Full Scale).

        This is a simplified calculation, not ITU-R BS.1770 compliant.

        Args:
            audio: Input audio

        Returns:
            Approximate LUFS value
        """
        # K-weighting filter (simplified - just high-shelf)
        # Real LUFS requires proper K-weighting filter

        # For now, use RMS as approximation
        rms = np.sqrt(np.mean(audio ** 2))

        if rms > 0:
            # Convert to dB
            lufs_approx = 20 * np.log10(rms) - 0.691
            return float(lufs_approx)
        else:
            return -np.inf

    def analyze_audio(self, audio: np.ndarray) -> dict:
        """
        Analyze audio and return statistics.

        Args:
            audio: Input audio

        Returns:
            Dict with audio statistics
        """
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
        crest_factor = peak / rms if rms > 0 else 0
        lufs = self.calculate_lufs(audio)

        # Check for clipping
        clipped = np.sum(np.abs(audio) >= 1.0)
        total_samples = audio.size

        # Dynamic range estimate
        # (difference between peak and average quiet level)
        sorted_abs = np.sort(np.abs(audio.flatten()))
        quiet_level = sorted_abs[int(len(sorted_abs) * 0.1)]  # 10th percentile
        dynamic_range_db = peak_db - (20 * np.log10(quiet_level) if quiet_level > 0 else -np.inf)

        return {
            'peak': float(peak),
            'peak_db': float(peak_db),
            'rms': float(rms),
            'rms_db': float(rms_db),
            'crest_factor': float(crest_factor),
            'lufs_approx': float(lufs),
            'clipped_samples': int(clipped),
            'clipping_percentage': float(clipped / total_samples * 100) if total_samples > 0 else 0.0,
            'dynamic_range_db': float(dynamic_range_db),
            'duration_seconds': float(len(audio) / self.sample_rate) if audio.ndim == 1 else float(audio.shape[0] / self.sample_rate)
        }

    def dc_offset_removal(self, audio: np.ndarray) -> np.ndarray:
        """
        Remove DC offset from audio.

        Args:
            audio: Input audio

        Returns:
            Audio with DC offset removed
        """
        if audio.ndim == 1:
            # Mono
            offset = np.mean(audio)
            return audio - offset
        else:
            # Stereo - remove offset per channel
            offset = np.mean(audio, axis=0)
            return audio - offset

    def apply_gentle_compression(self, audio: np.ndarray,
                                 threshold_db: float = -12.0,
                                 ratio: float = 2.0,
                                 knee_db: float = 6.0) -> np.ndarray:
        """
        Apply gentle mastering compression with soft knee.

        Args:
            audio: Input audio
            threshold_db: Compression threshold in dB
            ratio: Compression ratio (e.g., 2.0 = 2:1)
            knee_db: Soft knee width in dB

        Returns:
            Compressed audio
        """
        # Convert threshold to linear
        threshold_lin = 10 ** (threshold_db / 20.0)
        knee_lin = 10 ** (knee_db / 20.0)

        # Process
        output = np.zeros_like(audio)
        samples = audio if audio.ndim == 1 else audio.reshape(-1)

        for i, sample in enumerate(samples):
            amplitude = abs(sample)

            if amplitude <= threshold_lin - knee_lin / 2:
                # Below threshold - no compression
                gain = 1.0
            elif amplitude >= threshold_lin + knee_lin / 2:
                # Above knee - full compression
                gain = threshold_lin + (amplitude - threshold_lin) / ratio
                gain = gain / amplitude
            else:
                # Within knee - soft transition
                # Quadratic interpolation
                x = amplitude - (threshold_lin - knee_lin / 2)
                knee_range = knee_lin
                progress = x / knee_range
                compressed_gain = 1.0 + progress * (1.0 / ratio - 1.0)
                gain = compressed_gain

            if audio.ndim == 1:
                output[i] = sample * gain
            else:
                idx = np.unravel_index(i, audio.shape)
                output[idx] = sample * gain

        return output
