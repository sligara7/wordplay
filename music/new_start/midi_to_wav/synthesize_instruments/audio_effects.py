"""
Audio Effects Module

Provides a collection of digital audio effects that can be applied to any audio signal.
Includes distortion, modulation, and time-based effects.
"""

import numpy as np
from typing import Dict, Optional, Union
from enum import Enum


class EffectType(Enum):
    """Enumeration of available audio effects"""
    CLEAN = 0
    OVERDRIVE = 1
    DISTORTION = 2
    FUZZ = 3
    DELAY = 4
    REVERB = 5
    CHORUS = 6
    TREMOLO = 7
    WAH = 8


class AudioEffects:
    """
    Audio effects processor for applying various effects to audio signals.
    
    This class provides methods to apply various audio effects like distortion,
    overdrive, delay, etc. to audio signals represented as numpy arrays.
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize the audio effects processor.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate
    
    def apply_effect(self, signal: np.ndarray, effect_type: Union[EffectType, str], 
                    intensity: float = 0.5, parameters: Optional[Dict] = None) -> np.ndarray:
        """
        Apply audio effects to a signal.
        
        Args:
            signal: Input audio signal as numpy array (-1.0 to 1.0 range)
            effect_type: Type of effect to apply (EffectType enum or string name)
            intensity: Effect intensity from 0.0 to 1.0
            parameters: Optional dictionary with effect-specific parameters
            
        Returns:
            Processed audio signal
        """
        if parameters is None:
            parameters = {}
        
        # Handle string effect names
        if isinstance(effect_type, str):
            try:
                effect_type = EffectType[effect_type.upper()]
            except KeyError:
                raise ValueError(f"Unknown effect type: {effect_type}")
            
        # Apply the requested effect
        if effect_type == EffectType.CLEAN:
            return signal
            
        elif effect_type == EffectType.OVERDRIVE:
            return self._apply_overdrive(signal, intensity, parameters)
            
        elif effect_type == EffectType.DISTORTION:
            return self._apply_distortion(signal, intensity, parameters)
            
        elif effect_type == EffectType.FUZZ:
            return self._apply_fuzz(signal, intensity, parameters)
            
        elif effect_type == EffectType.DELAY:
            return self._apply_delay(signal, intensity, parameters)
            
        elif effect_type == EffectType.REVERB:
            return self._apply_reverb(signal, intensity, parameters)
            
        elif effect_type == EffectType.CHORUS:
            return self._apply_chorus(signal, intensity, parameters)
            
        elif effect_type == EffectType.TREMOLO:
            return self._apply_tremolo(signal, intensity, parameters)
            
        elif effect_type == EffectType.WAH:
            return self._apply_wah(signal, intensity, parameters)
            
        # Default case
        return signal
    
    def _apply_overdrive(self, signal: np.ndarray, intensity: float, 
                        parameters: Dict) -> np.ndarray:
        """
        Apply overdrive effect (soft clipping).
        
        Overdrive provides a "warm" distortion that preserves dynamics.
        At low intensities, it adds subtle harmonics; at high intensities,
        it approaches distortion but still retains some dynamic range.
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - drive: Additional drive amount (default: 1.0)
                - tone: Tone control, higher values boost treble (default: 0.5)
                
        Returns:
            Processed signal with overdrive effect
        """
        # Get parameters with defaults
        drive = parameters.get('drive', 1.0) * 4.0
        tone = parameters.get('tone', 0.5)
        
        # Normalize signal to -1 to 1 range for processing
        max_val = max(np.max(np.abs(signal)), 1)
        normalized = signal / max_val
        
        # Scale input gain based on intensity
        gain = 1.0 + intensity * drive * 4.0
        input_signal = normalized * gain
        
        # Soft clipping function (cubic soft clipper)
        # For |x| < 1/3: y = 2*x
        # For |x| >= 1/3: y = sign(x) * (3 - (2 - 3|x|)²) / 3
        output = np.zeros_like(input_signal)
        
        # Apply different transfer functions based on signal level
        mask_low = np.abs(input_signal) < 1/3
        mask_high = ~mask_low
        
        output[mask_low] = 2 * input_signal[mask_low]
        
        x_high = input_signal[mask_high]
        sign_high = np.sign(x_high)
        output[mask_high] = sign_high * (3 - (2 - 3 * np.abs(x_high))**2) / 3
        
        # Apply tone control (simple high shelf filter)
        if tone > 0.5:
            # Boost high frequencies
            highpass = self._simple_highpass(output, cutoff=0.2)
            output = output + (tone - 0.5) * 2 * highpass
        elif tone < 0.5:
            # Cut high frequencies
            highpass = self._simple_highpass(output, cutoff=0.1)
            output = output - (0.5 - tone) * 2 * highpass
            
        # Rescale to original amplitude range
        return output * max_val
    
    def _apply_distortion(self, signal: np.ndarray, intensity: float, 
                         parameters: Dict) -> np.ndarray:
        """
        Apply distortion effect (hard clipping).
        
        Distortion provides aggressive clipping and compression,
        creating a more aggressive, saturated sound with less dynamics.
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - drive: Additional drive amount (default: 1.0)
                - tone: Tone control, higher values boost treble (default: 0.5)
                
        Returns:
            Processed signal with distortion effect
        """
        # Get parameters with defaults
        drive = parameters.get('drive', 1.0) * 8.0
        tone = parameters.get('tone', 0.5)
        
        # Normalize signal to -1 to 1 range for processing
        max_val = max(np.max(np.abs(signal)), 1)
        normalized = signal / max_val
        
        # Scale input gain based on intensity
        gain = 1.0 + intensity * drive * 10.0
        input_signal = normalized * gain
        
        # Hard clipping function with adjustable threshold
        threshold = 0.6 / (intensity + 0.2)
        output = np.clip(input_signal, -threshold, threshold)
        output = output / threshold  # Renormalize to -1 to 1
        
        # Add harmonics via waveshaping
        output = np.tanh(output * 2) * 0.7  # Additional saturation
        
        # Apply tone control
        if tone > 0.5:
            # Boost high frequencies
            highpass = self._simple_highpass(output, cutoff=0.15)
            output = output + (tone - 0.5) * 2 * highpass
        elif tone < 0.5:
            # Cut high frequencies
            highpass = self._simple_highpass(output, cutoff=0.05)
            output = output - (0.5 - tone) * 2 * highpass
            
        # Rescale to original amplitude range
        return output * max_val
    
    def _apply_fuzz(self, signal: np.ndarray, intensity: float, 
                   parameters: Dict) -> np.ndarray:
        """
        Apply fuzz effect (extreme distortion).
        
        Fuzz creates an extreme, broken-up sound with additional harmonics
        and unique character. Often associated with psychedelic and garage rock.
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - drive: Additional drive amount (default: 1.0)
                - octave: Amount of octave-up effect (default: 0.0)
                - grit: Amount of gritty harmonics (default: 0.5)
                
        Returns:
            Processed signal with fuzz effect
        """
        # Get parameters with defaults
        drive = parameters.get('drive', 1.0) * 10.0
        octave = parameters.get('octave', 0.0)
        grit = parameters.get('grit', 0.5)
        
        # Normalize signal to -1 to 1 range for processing
        max_val = max(np.max(np.abs(signal)), 1)
        normalized = signal / max_val
        
        # Scale input gain based on intensity
        gain = 1.0 + intensity * drive * 15.0
        input_signal = normalized * gain
        
        # Base fuzz effect (asymmetric clipping)
        output = np.sign(input_signal) * (1 - np.exp(-np.abs(input_signal)))
        
        # Add gate noise for "grit"
        if grit > 0:
            noise = np.random.normal(0, 0.05 * grit, size=len(output))
            gate = np.abs(output) > 0.1  # Only add noise where signal is present
            output = output + noise * gate
        
        # Add octave-up (full-wave rectification with mix)
        if octave > 0:
            rectified = np.abs(output)  # Full-wave rectification for octave up
            output = output * (1 - octave) + rectified * octave
            
        # Soft limit the output
        output = np.tanh(output * 1.5)
        
        # Apply low-pass filter based on intensity (fuzz often cuts high frequencies)
        cutoff = 0.3 - intensity * 0.2
        output = self._simple_lowpass(output, cutoff=cutoff)
        
        # Rescale to original amplitude range
        return output * max_val
    
    def _apply_delay(self, signal: np.ndarray, intensity: float, 
                    parameters: Dict) -> np.ndarray:
        """
        Apply delay/echo effect.
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - time: Delay time in seconds (default: 0.3)
                - feedback: Feedback amount (default: 0.4)
                
        Returns:
            Processed signal with delay effect
        """
        time = parameters.get('time', 0.3)
        feedback = parameters.get('feedback', 0.4) * intensity
        
        # Convert delay time to samples
        delay_samples = int(self.sample_rate * time)
        
        # Initialize output buffer
        output = np.copy(signal)
        
        # Simple implementation with a fixed number of repeats
        repeats = 5
        for i in range(1, repeats + 1):
            # Calculate the delay for this repeat
            current_delay = delay_samples * i
            
            # Calculate the gain for this repeat
            current_gain = feedback ** i
            
            # Add delayed signal
            if current_delay < len(signal):
                # Delay fits within signal
                output[current_delay:] += signal[:-current_delay] * current_gain
            else:
                # Delay extends beyond signal
                break
                
        # Normalize to prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 1.0:
            output = output / max_val
            
        return output
    
    def _apply_reverb(self, signal: np.ndarray, intensity: float,
                     parameters: Dict) -> np.ndarray:
        """
        Apply reverb effect (simplified implementation).
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - room_size: Size of the room (0.0 to 1.0, default: 0.5)
                - damping: Damping factor (0.0 to 1.0, default: 0.5)
                
        Returns:
            Processed signal with reverb effect
        """
        room_size = parameters.get('room_size', 0.5)
        damping = parameters.get('damping', 0.5)
        
        # Calculate delay times based on room size (simple model)
        base_delay = int(0.01 * self.sample_rate)  # 10ms base delay
        delays = [
            int(base_delay * (1 + room_size * 3)), 
            int(base_delay * (1.5 + room_size * 4)),
            int(base_delay * (2 + room_size * 5)),
            int(base_delay * (2.5 + room_size * 7))
        ]
        
        # Calculate gains for each delay line
        gains = [
            0.5 * intensity,
            0.35 * intensity,
            0.25 * intensity,
            0.15 * intensity
        ]
        
        # Apply damping to the gains
        gains = [g * (1 - damping * 0.5) for g in gains]
        
        # Create output buffer
        output = np.copy(signal)
        
        # Apply multiple delay lines with different times and gains
        for delay, gain in zip(delays, gains):
            if delay < len(signal):
                # Simple delay with feedback
                delayed = np.zeros_like(signal)
                delayed[delay:] = signal[:-delay] * gain
                
                # Low-pass filter the delayed signal (simulates damping)
                filtered = self._simple_lowpass(delayed, cutoff=0.5 - damping * 0.3)
                
                # Add to output
                output += filtered
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 1.0:
            output = output / max_val
            
        return output
    
    def _apply_chorus(self, signal: np.ndarray, intensity: float,
                     parameters: Dict) -> np.ndarray:
        """
        Apply chorus effect.
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - rate: Modulation rate in Hz (default: 0.5)
                - depth: Modulation depth (default: 0.5)
                
        Returns:
            Processed signal with chorus effect
        """
        rate = parameters.get('rate', 0.5)
        depth = parameters.get('depth', 0.5) * intensity
        
        # Create output buffer
        output = np.copy(signal)
        
        # Time array for modulation
        t = np.arange(len(signal)) / self.sample_rate
        
        # Create two modulated voices
        for voice in range(2):
            phase = voice * np.pi  # Different phase for each voice
            
            # Calculate modulated delay
            mod = depth * 0.005 * np.sin(2 * np.pi * rate * t + phase)  # +/- 5ms max
            
            # Convert to samples
            delay_samples = np.round(mod * self.sample_rate).astype(int)
            
            # Create modulated copy
            modulated = np.zeros_like(signal)
            
            # Apply variable delay
            for i in range(len(signal)):
                index = i - delay_samples[i]
                if 0 <= index < len(signal):
                    modulated[i] = signal[index]
            
            # Mix with original
            output += modulated * (0.5 * intensity)
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 1.0:
            output = output / max_val
            
        return output
    
    def _apply_tremolo(self, signal: np.ndarray, intensity: float,
                      parameters: Dict) -> np.ndarray:
        """
        Apply tremolo effect (amplitude modulation).
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - rate: Modulation rate in Hz (default: 5.0)
                - wave: Waveform type ('sine', 'triangle', 'square', default: 'sine')
                
        Returns:
            Processed signal with tremolo effect
        """
        rate = parameters.get('rate', 5.0)
        wave_type = parameters.get('wave', 'sine')
        
        # Time array for modulation
        t = np.arange(len(signal)) / self.sample_rate
        
        # Create modulation waveform
        if wave_type == 'sine':
            # Sine wave modulation
            mod = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t)
        elif wave_type == 'triangle':
            # Triangle wave modulation
            mod = np.abs((t * rate * 2) % 2 - 1)
        elif wave_type == 'square':
            # Square wave modulation
            mod = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * rate * t))
        else:
            # Default to sine
            mod = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t)
        
        # Scale modulation depth by intensity
        mod = 1.0 - intensity * (1.0 - mod)
        
        # Apply amplitude modulation
        output = signal * mod
        
        return output
    
    def _apply_wah(self, signal: np.ndarray, intensity: float,
                  parameters: Dict) -> np.ndarray:
        """
        Apply wah-wah effect (sweeping bandpass filter).
        
        Args:
            signal: Input signal (-1.0 to 1.0 range)
            intensity: Effect intensity (0.0 to 1.0)
            parameters: Optional parameters dict
                - rate: Sweep rate in Hz (default: 2.0)
                - range_min: Minimum cutoff (default: 0.05)
                - range_max: Maximum cutoff (default: 0.8)
                
        Returns:
            Processed signal with wah effect
        """
        rate = parameters.get('rate', 2.0)
        range_min = parameters.get('range_min', 0.05)
        range_max = parameters.get('range_max', 0.8)
        
        # Scale range by intensity
        range_min = range_min + (0.2 - range_min) * (1 - intensity)
        range_max = range_max * intensity
        
        # Time array for modulation
        t = np.arange(len(signal)) / self.sample_rate
        
        # Calculate time-varying cutoff frequency
        cutoff = range_min + (range_max - range_min) * 0.5 * (1 + np.sin(2 * np.pi * rate * t))
        
        # Initialize output buffer
        output = np.zeros_like(signal)
        
        # State variables for filter
        y1 = 0
        y2 = 0
        
        # Apply time-varying bandpass filter
        for i in range(len(signal)):
            # Calculate filter coefficients for current cutoff
            resonance = 0.5 + 0.5 * intensity
            f = cutoff[i]
            q = resonance * 10
            
            # Simple bandpass coefficients (simplified for demonstration)
            b0 = f * 0.5
            a1 = -2 * (1 - f)
            a2 = (1 - f - f * q)
            
            # Apply filter
            y0 = b0 * signal[i] - a1 * y1 - a2 * y2
            output[i] = y0
            
            # Update state
            y2 = y1
            y1 = y0
        
        # Normalize output level
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * np.max(np.abs(signal))
            
        return output
    
    def _simple_highpass(self, signal: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
        """
        Simple first-order high-pass filter.
        
        Args:
            signal: Input signal
            cutoff: Normalized cutoff frequency (0.0 to 1.0)
            
        Returns:
            Filtered signal
        """
        filtered = np.zeros_like(signal)
        alpha = cutoff  # Simplified coefficient
        
        # First-order high-pass filter
        filtered[0] = signal[0]
        for i in range(1, len(signal)):
            filtered[i] = alpha * filtered[i-1] + alpha * (signal[i] - signal[i-1])
            
        return filtered
    
    def _simple_lowpass(self, signal: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
        """
        Simple first-order low-pass filter.
        
        Args:
            signal: Input signal
            cutoff: Normalized cutoff frequency (0.0 to 1.0)
            
        Returns:
            Filtered signal
        """
        filtered = np.zeros_like(signal)
        alpha = 1.0 - cutoff  # Simplified coefficient
        
        # First-order low-pass filter
        filtered[0] = signal[0]
        for i in range(1, len(signal)):
            filtered[i] = alpha * filtered[i-1] + (1.0 - alpha) * signal[i]
            
        return filtered
    
    def _simple_bandpass(self, signal: np.ndarray, low_cutoff: float = 0.1, 
                        high_cutoff: float = 0.4) -> np.ndarray:
        """
        Simple bandpass filter (combination of high-pass and low-pass).
        
        Args:
            signal: Input signal
            low_cutoff: Normalized low cutoff frequency (0.0 to 1.0)
            high_cutoff: Normalized high cutoff frequency (0.0 to 1.0)
            
        Returns:
            Filtered signal
        """
        # Apply high-pass then low-pass
        temp = self._simple_highpass(signal, low_cutoff)
        return self._simple_lowpass(temp, high_cutoff)
    
# write apply_effects method to use AudioEffects class
def apply_effects(signal: np.ndarray, effect_type: Union[EffectType, str], 
                  intensity: float = 0.5, parameters: Optional[Dict] = None) -> np.ndarray:
    """
    Apply audio effects to a signal using the AudioEffects class.
    
    Args:
        signal: Input audio signal as numpy array (-1.0 to 1.0 range)
        effect_type: Type of effect to apply (EffectType enum or string name)
        intensity: Effect intensity from 0.0 to 1.0
        parameters: Optional dictionary with effect-specific parameters
        
    Returns:
        Processed audio signal
    """
    effects_processor = AudioEffects()
    return effects_processor.apply_effect(signal, effect_type, intensity, parameters)