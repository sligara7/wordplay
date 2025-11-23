"""
Audio Mixer Module

Responsibility: Mix individual notes into final audio stream

Input: List of note events with audio waveforms
Output: Mixed stereo audio
"""

import numpy as np
from typing import List, Dict, Optional, Tuple


class AudioMixer:
    """
    Mix individual note audio into stereo output.

    Handles:
    - Timing and synchronization
    - Stereo panning
    - Channel mixing
    - Overlapping notes
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio mixer.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate

    def mix_notes(self, notes: List[Dict],
                  note_audio: Dict[int, np.ndarray],
                  total_duration: float,
                  pan_per_channel: Optional[Dict[int, Tuple[float, float]]] = None,
                  stereo: bool = True) -> np.ndarray:
        """
        Mix all notes into final audio.

        Args:
            notes: List of note dicts with 'start', 'duration', 'channel', 'note', 'velocity'
            note_audio: Dict mapping note index to audio waveform
            total_duration: Total duration in seconds
            pan_per_channel: Optional dict of (left_gain, right_gain) per channel
            stereo: If True, output stereo; if False, mono

        Returns:
            Mixed audio array (mono or stereo)
        """
        # Calculate total samples
        total_samples = int(total_duration * self.sample_rate)

        # Initialize output buffer
        if stereo:
            output = np.zeros((total_samples, 2), dtype=np.float32)
        else:
            output = np.zeros(total_samples, dtype=np.float32)

        # Mix each note
        for idx, note in enumerate(notes):
            if idx not in note_audio:
                continue

            audio = note_audio[idx]
            start_time = note['start']
            channel = note['channel']

            # Calculate start sample
            start_sample = int(start_time * self.sample_rate)

            # Get panning for this channel
            if pan_per_channel and channel in pan_per_channel:
                left_gain, right_gain = pan_per_channel[channel]
            else:
                # Default: center pan
                left_gain, right_gain = 1.0, 1.0

            # Mix into output buffer
            if stereo:
                self._mix_stereo_note(output, audio, start_sample, left_gain, right_gain)
            else:
                self._mix_mono_note(output, audio, start_sample)

        return output

    def _mix_stereo_note(self, output: np.ndarray,
                        audio: np.ndarray,
                        start_sample: int,
                        left_gain: float,
                        right_gain: float):
        """
        Mix a single note into stereo output.

        Args:
            output: Output buffer (samples, 2)
            audio: Note audio (mono)
            start_sample: Starting sample position
            left_gain: Left channel gain
            right_gain: Right channel gain
        """
        end_sample = min(start_sample + len(audio), len(output))
        audio_len = end_sample - start_sample

        if audio_len <= 0:
            return

        # Mix with panning
        output[start_sample:end_sample, 0] += audio[:audio_len] * left_gain
        output[start_sample:end_sample, 1] += audio[:audio_len] * right_gain

    def _mix_mono_note(self, output: np.ndarray,
                      audio: np.ndarray,
                      start_sample: int):
        """
        Mix a single note into mono output.

        Args:
            output: Output buffer (samples,)
            audio: Note audio (mono)
            start_sample: Starting sample position
        """
        end_sample = min(start_sample + len(audio), len(output))
        audio_len = end_sample - start_sample

        if audio_len <= 0:
            return

        # Mix
        output[start_sample:end_sample] += audio[:audio_len]

    def mix_channels_separately(self, notes: List[Dict],
                                note_audio: Dict[int, np.ndarray],
                                total_duration: float) -> Dict[int, np.ndarray]:
        """
        Mix notes into separate channel buffers.

        Useful for per-channel processing before final mix.

        Args:
            notes: List of note dicts
            note_audio: Dict mapping note index to audio waveform
            total_duration: Total duration in seconds

        Returns:
            Dict mapping channel number to mixed audio for that channel
        """
        total_samples = int(total_duration * self.sample_rate)

        # Find all channels
        channels = set(note['channel'] for note in notes)

        # Initialize buffers for each channel
        channel_buffers = {}
        for ch in channels:
            channel_buffers[ch] = np.zeros(total_samples, dtype=np.float32)

        # Mix each note into its channel
        for idx, note in enumerate(notes):
            if idx not in note_audio:
                continue

            audio = note_audio[idx]
            channel = note['channel']
            start_sample = int(note['start'] * self.sample_rate)

            self._mix_mono_note(channel_buffers[channel], audio, start_sample)

        return channel_buffers

    def apply_channel_volumes(self, channel_buffers: Dict[int, np.ndarray],
                             volumes: Dict[int, float]) -> Dict[int, np.ndarray]:
        """
        Apply volume scaling to each channel.

        Args:
            channel_buffers: Dict of channel audio
            volumes: Dict of volume values (0.0 to 1.0)

        Returns:
            Dict of scaled channel audio
        """
        scaled = {}

        for ch, audio in channel_buffers.items():
            volume = volumes.get(ch, 1.0)
            scaled[ch] = audio * volume

        return scaled

    def merge_channels_to_stereo(self, channel_buffers: Dict[int, np.ndarray],
                                pan_per_channel: Dict[int, Tuple[float, float]]) -> np.ndarray:
        """
        Merge channel buffers into final stereo mix.

        Args:
            channel_buffers: Dict mapping channel to mono audio
            pan_per_channel: Dict of (left_gain, right_gain) per channel

        Returns:
            Stereo audio (samples, 2)
        """
        # Get length from first channel
        if not channel_buffers:
            return np.zeros((0, 2), dtype=np.float32)

        samples = len(next(iter(channel_buffers.values())))
        output = np.zeros((samples, 2), dtype=np.float32)

        # Mix each channel with panning
        for ch, audio in channel_buffers.items():
            if ch in pan_per_channel:
                left_gain, right_gain = pan_per_channel[ch]
            else:
                left_gain, right_gain = 1.0, 1.0

            output[:, 0] += audio * left_gain
            output[:, 1] += audio * right_gain

        return output

    def add_fade_in(self, audio: np.ndarray,
                   fade_duration: float = 0.01) -> np.ndarray:
        """
        Add fade-in to avoid clicks.

        Args:
            audio: Input audio
            fade_duration: Fade duration in seconds

        Returns:
            Audio with fade-in applied
        """
        fade_samples = int(fade_duration * self.sample_rate)

        if fade_samples <= 0 or fade_samples >= len(audio):
            return audio

        fade = np.linspace(0, 1, fade_samples)

        if audio.ndim == 1:
            audio[:fade_samples] *= fade
        else:
            audio[:fade_samples, :] *= fade[:, np.newaxis]

        return audio

    def add_fade_out(self, audio: np.ndarray,
                    fade_duration: float = 0.01) -> np.ndarray:
        """
        Add fade-out to avoid clicks.

        Args:
            audio: Input audio
            fade_duration: Fade duration in seconds

        Returns:
            Audio with fade-out applied
        """
        fade_samples = int(fade_duration * self.sample_rate)

        if fade_samples <= 0 or fade_samples >= len(audio):
            return audio

        fade = np.linspace(1, 0, fade_samples)

        if audio.ndim == 1:
            audio[-fade_samples:] *= fade
        else:
            audio[-fade_samples:, :] *= fade[:, np.newaxis]

        return audio

    def normalize_mix(self, audio: np.ndarray,
                     target_peak: float = 0.95) -> np.ndarray:
        """
        Normalize audio to target peak level.

        Args:
            audio: Input audio
            target_peak: Target peak level (0.0 to 1.0)

        Returns:
            Normalized audio
        """
        peak = np.max(np.abs(audio))

        if peak > 0:
            return audio * (target_peak / peak)
        else:
            return audio

    def check_clipping(self, audio: np.ndarray,
                      threshold: float = 1.0) -> Dict:
        """
        Check for clipping in audio.

        Args:
            audio: Input audio
            threshold: Clipping threshold

        Returns:
            Dict with clipping statistics
        """
        clipped = np.abs(audio) >= threshold
        num_clipped = np.sum(clipped)
        total_samples = audio.size

        if audio.ndim == 2:
            left_clipped = np.sum(clipped[:, 0])
            right_clipped = np.sum(clipped[:, 1])
        else:
            left_clipped = num_clipped
            right_clipped = 0

        return {
            'num_clipped': int(num_clipped),
            'total_samples': int(total_samples),
            'percentage': (num_clipped / total_samples * 100) if total_samples > 0 else 0.0,
            'left_clipped': int(left_clipped),
            'right_clipped': int(right_clipped),
            'peak': float(np.max(np.abs(audio)))
        }
