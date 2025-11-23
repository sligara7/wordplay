"""
Controller Manager Module

Responsibility: Track and manage MIDI controller state

Input: Controller events from parser
Output: Current controller values for any channel at any time
"""

from typing import Dict, List
import numpy as np


class ControllerManager:
    """
    Manage MIDI controller state for all channels.

    Tracks:
    - Volume (CC 7)
    - Pan (CC 10)
    - Expression (CC 11)
    - Sustain Pedal (CC 64)
    - Modulation (CC 1)
    - Pitch Bend
    - Program Number
    """

    # Controller numbers (MIDI standard)
    CC_MODULATION = 1
    CC_VOLUME = 7
    CC_PAN = 10
    CC_EXPRESSION = 11
    CC_SUSTAIN_PEDAL = 64

    def __init__(self):
        """Initialize controller state for all 16 channels."""
        self.state = {}
        for ch in range(16):
            self.state[ch] = {
                'volume': 100,           # CC 7
                'pan': 64,               # CC 10 (0=left, 64=center, 127=right)
                'expression': 127,       # CC 11
                'sustain_pedal': 0,      # CC 64 (0=off, >63=on)
                'modulation': 0,         # CC 1
                'pitch_bend': 0,         # -8192 to +8191
                'program': 0             # Program number
            }

    def apply_events(self, program_changes: List[Dict],
                    controllers: List[Dict],
                    pitch_bends: List[Dict]):
        """
        Apply all MIDI events to update controller state.

        Note: This applies events in order, so later events override earlier ones.
        For time-varying control, use get_state_at_time() instead.

        Args:
            program_changes: List of program change events
            controllers: List of controller events
            pitch_bends: List of pitch bend events
        """
        # Apply program changes
        for pc in program_changes:
            ch = pc['channel']
            self.state[ch]['program'] = pc['program']

        # Apply controller changes
        for ctrl in controllers:
            ch = ctrl['channel']
            cc = ctrl['controller']
            val = ctrl['value']

            if cc == self.CC_VOLUME:
                self.state[ch]['volume'] = val
            elif cc == self.CC_PAN:
                self.state[ch]['pan'] = val
            elif cc == self.CC_EXPRESSION:
                self.state[ch]['expression'] = val
            elif cc == self.CC_SUSTAIN_PEDAL:
                self.state[ch]['sustain_pedal'] = val
            elif cc == self.CC_MODULATION:
                self.state[ch]['modulation'] = val

        # Apply pitch bends (keep latest per channel)
        for pb in pitch_bends:
            ch = pb['channel']
            self.state[ch]['pitch_bend'] = pb['pitch']

    def get_state(self, channel: int) -> Dict:
        """
        Get current controller state for a channel.

        Args:
            channel: MIDI channel (0-15)

        Returns:
            Dict with controller values
        """
        return self.state[channel].copy()

    def calculate_effective_velocity(self, channel: int, velocity: int) -> int:
        """
        Calculate effective velocity considering volume and expression.

        Args:
            channel: MIDI channel
            velocity: Original note velocity (0-127)

        Returns:
            Modified velocity (0-127)
        """
        state = self.state[channel]

        volume_scale = state['volume'] / 127.0
        expression_scale = state['expression'] / 127.0

        effective_velocity = int(velocity * volume_scale * expression_scale)

        return np.clip(effective_velocity, 1, 127)

    def calculate_pitch_bend_semitones(self, channel: int,
                                      bend_range: float = 2.0) -> float:
        """
        Calculate pitch bend in semitones.

        Args:
            channel: MIDI channel
            bend_range: Bend range in semitones (default ±2)

        Returns:
            Pitch shift in semitones
        """
        pitch_bend = self.state[channel]['pitch_bend']

        # pitch_bend ranges from -8192 to +8191
        # Normalize to -1.0 to +1.0
        normalized = pitch_bend / 8192.0

        return normalized * bend_range

    def should_extend_duration(self, channel: int) -> bool:
        """
        Check if sustain pedal is engaged.

        Args:
            channel: MIDI channel

        Returns:
            True if sustain pedal is on
        """
        return self.state[channel]['sustain_pedal'] > 63

    def get_pan_stereo_gains(self, channel: int) -> tuple[float, float]:
        """
        Calculate left/right stereo gains from pan.

        Args:
            channel: MIDI channel

        Returns:
            (left_gain, right_gain) tuple
        """
        pan = self.state[channel]['pan']

        # Pan: 0=left, 64=center, 127=right
        # Normalize to 0-1
        pan_normalized = pan / 127.0

        # Constant power panning
        left_gain = np.cos(pan_normalized * np.pi / 2)
        right_gain = np.sin(pan_normalized * np.pi / 2)

        return left_gain, right_gain
