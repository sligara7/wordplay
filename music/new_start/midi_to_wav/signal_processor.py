import numpy as np
from typing import Tuple, List, Optional, Union, Dict
import random
from enum import Enum

from audio_processing.synthesize_instruments.audio_effects import EffectType
from audio_processing.synthesize_instruments.synthesize_string_instruments import StringInstrumentSynthesizer
from audio_processing.synthesize_instruments.synthesize_common_percussion import PercussionSynthesizer
from audio_processing.synthesize_instruments.synthesize_brass import BrassSynthesizer

class SignalProcessor:
    """
    Processes audio signals for synthesis and transformation.
    
    This class handles operations like shaping, scaling, and
    manipulating audio signals for instrument synthesis.
    """
    
    def __init__(self, 
                note_offset: int = 21, 
                sample_freq: int = 44100,
                max_value: int = 32767, 
                min_value: int = -32768,
                standard_A4: float = 440.0,
                note_duration: float = 10.0,
                time_step: float = 1/25,
                max_velocity: int = 127):
        """
        Initialize the signal processor.
        
        Args:
            note_offset: MIDI note offset
            sample_freq: Sample frequency in Hz
            max_value: Maximum signal value
            min_value: Minimum signal value
            standard_A4: Reference frequency for A4
            note_duration: Duration for synthesized notes in seconds
            time_step: Time step for envelope generation
            max_velocity: Maximum MIDI velocity value
        """
        self.note_offset = note_offset
        self.sf = sample_freq
        self.max_value = max_value
        self.min_value = min_value
        self.A4 = standard_A4
        self.note_duration = note_duration
        self.time_step = time_step
        self.max_velocity = max_velocity
        
        # Stringed instrument program numbers in General MIDI spec
        self.string_instruments = set([
            # Guitars
            25, 26, 27, 28, 29, 30, 31, 32, 
            # Basses
            33, 34, 35, 36, 37, 38, 
            # Bowed strings
            41, 42, 43, 44, 45, 46, 
            # Harp
            47,
            # Misc. String instruments
            105, 106, 107, 108
        ])
    
    def is_string_instrument(self, program: int) -> bool:
        """
        Check if the given program number corresponds to a stringed instrument.
        
        Args:
            program: MIDI program number
            
        Returns:
            True if it's a stringed instrument, False otherwise
        """
        return program in self.string_instruments
    
    def karplus_strong(self, frequency: float, duration: float, 
                       damping: float = 0.99, noise_type: str = 'white',
                       velocity: int = 127) -> np.ndarray:
        """
        Synthesize a plucked string sound using the Karplus-Strong algorithm.
        
        Args:
            frequency: Fundamental frequency of the string in Hz
            duration: Duration of the note in seconds
            damping: Damping factor for the string (0.0 to 1.0)
            noise_type: Type of noise to use ('white', 'pink', or 'balanced')
            velocity: MIDI velocity (0-127) affects brightness and attack
            
        Returns:
            Synthesized plucked string sound as a numpy array
        """
        # Calculate buffer size N based on frequency
        N = int(round(self.sf / frequency))
        if N <= 1:
            N = 2  # Minimum buffer size
            
        # Calculate number of samples needed
        num_samples = int(duration * self.sf)
        
        # Create the output buffer
        output = np.zeros(num_samples, dtype=float)
        
        # Initialize the delay line with noise
        if noise_type == 'white':
            delay_line = np.random.uniform(-1, 1, N)
        elif noise_type == 'pink':
            # Simple approximation of pink noise (more energy in lower frequencies)
            delay_line = np.random.uniform(-1, 1, N)
            delay_line = np.cumsum(delay_line)
            delay_line = delay_line / np.max(np.abs(delay_line))
        else:  # 'balanced' - good for plucked strings
            delay_line = np.random.uniform(-1, 1, N)
            # Apply low-pass filtering to initial noise
            for i in range(2, N):
                delay_line[i] = (delay_line[i] + delay_line[i-1] + delay_line[i-2]) / 3

        # Scale initial excitation based on velocity
        # Higher velocity = more high frequencies = brighter tone
        brightness = 0.5 + (0.5 * velocity / 127)
        delay_line = delay_line * (velocity / 127.0) * brightness
        
        # Calculate string parameters
        # Damping increases with lower velocity for more realism
        velocity_damping = damping * (0.9 + 0.1 * velocity / 127.0)
        
        # Low-pass filter coefficient for the feedback loop
        # This simulates the frequency-dependent energy loss in real strings
        filter_coeff = 0.5  # Average of current and previous sample
        
        # Karplus-Strong algorithm: loop through and compute each sample
        for i in range(num_samples):
            # Get the current output from the delay line
            output[i] = delay_line[0]
            
            # Update delay line - shift values
            for j in range(N-1):
                delay_line[j] = delay_line[j+1]
            
            # Apply low-pass filter for feedback
            # This is the core of the Karplus-Strong algorithm
            delay_line[N-1] = velocity_damping * (filter_coeff * delay_line[0] + 
                                                 filter_coeff * output[i])
            
            # Introduce slight nonlinearity for more realistic behavior
            # This simulates the nonlinear response of real strings
            if abs(delay_line[N-1]) > 0.9:
                delay_line[N-1] *= 0.99
        
        # Apply overall envelope for more realistic decay
        t = np.linspace(0, 1, num_samples)
        envelope = np.exp(-3 * t)  # Exponential decay
        
        # Add a short attack portion
        attack_samples = int(0.002 * self.sf)  # 2ms attack
        if attack_samples > 0 and attack_samples < num_samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples) * envelope[:attack_samples]
        
        # Apply envelope to output
        output = output * envelope
        
        return output
    
    def apply_effect(self, signal: np.ndarray, effect_type: EffectType, 
                    intensity: float = 0.5, parameters: Optional[Dict] = None) -> np.ndarray:
        """
        Apply audio effects to a signal.
        
        Args:
            signal: Input audio signal
            effect_type: Type of effect to apply
            intensity: Effect intensity from 0.0 to 1.0
            parameters: Optional dictionary with effect-specific parameters
            
        Returns:
            Processed audio signal
        """
        if parameters is None:
            parameters = {}
            
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
            signal: Input signal
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
            signal: Input signal
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
            signal: Input signal
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
            signal: Input signal
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
        delay_samples = int(self.sf * time)
        
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
        
    def _simple_highpass(self, signal: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
        """Simple first-order high-pass filter"""
        filtered = np.zeros_like(signal)
        alpha = cutoff  # Simplified coefficient
        
        # First-order high-pass filter
        filtered[0] = signal[0]
        for i in range(1, len(signal)):
            filtered[i] = alpha * filtered[i-1] + alpha * (signal[i] - signal[i-1])
            
        return filtered
    
    def _simple_lowpass(self, signal: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
        """Simple first-order low-pass filter"""
        filtered = np.zeros_like(signal)
        alpha = 1.0 - cutoff  # Simplified coefficient
        
        # First-order low-pass filter
        filtered[0] = signal[0]
        for i in range(1, len(signal)):
            filtered[i] = alpha * filtered[i-1] + (1.0 - alpha) * signal[i]
            
        return filtered
    
    def create_note(self, instrument: int, note: int, velocity: int, 
                   effect_type: Optional[EffectType] = None, 
                   effect_intensity: float = 0.5,
                   effect_params: Optional[Dict] = None) -> np.ndarray:
        """
        Generate a synthesized note for a specific instrument, with optional effects.
        
        Args:
            instrument: MIDI program number
            note: MIDI note number
            velocity: Note velocity (0-127)
            effect_type: Optional effect to apply (default: None)
            effect_intensity: Effect intensity from 0.0 to 1.0 (default: 0.5)
            effect_params: Optional parameters for the effect
            
        Returns:
            Synthesized audio signal for the note with effects applied
        """
        # Calculate frequency from MIDI note number
        frequency = self.A4 * 2 ** ((note - 69) / 12)
        
        # Use Karplus-Strong for string instruments
        if self.is_string_instrument(instrument):
            # Adjust parameters based on instrument type
            if instrument in (25, 26):  # Nylon/steel string guitar
                damping = 0.996
                noise_type = 'balanced'
            elif instrument in (27, 28, 29, 30, 31, 32):  # Electric guitars
                damping = 0.998
                noise_type = 'white'  # More brightness for electric
            elif instrument in (33, 34, 35, 36, 37, 38):  # Basses
                damping = 0.999  # Bass strings resonate longer
                noise_type = 'pink'  # More low frequency content for bass
            elif instrument in (41, 42, 43, 44, 45, 46):  # Bowed strings
                damping = 0.9995  # Very long sustain for bowed instruments
                noise_type = 'pink'
            else:  # Other string instruments
                damping = 0.997
                noise_type = 'balanced'
            
            # Generate the string sound using Karplus-Strong
            signal = self.karplus_strong(
                frequency=frequency,
                duration=self.note_duration,
                damping=damping,
                noise_type=noise_type,
                velocity=velocity
            )
            
        else:
            # For non-string instruments, use the original sine wave method
            duration = self.note_duration
            t = np.arange(0, duration, 1/self.sf)
            
            # Basic amplitude envelope
            envelope = np.ones_like(t)
            attack = int(0.01 * self.sf)
            release = int(0.1 * self.sf)
            
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            
            # Scale by velocity
            amplitude = velocity / self.max_velocity
            
            # Generate signal
            signal = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
        
        # Apply effect if specified
        if effect_type is not None:
            signal = self.apply_effect(signal, effect_type, effect_intensity, effect_params)
            
        # Scale to desired range
        signal = signal * self.max_value
        
        return signal.astype(np.int16)


    def shape_note(self, note_signal: np.ndarray, 
                  start_idx: int, end_idx: int, 
                  next_avail_idx: int) -> Tuple[np.ndarray, int]:
        """
        Shape a note signal to fit within specified time constraints.
        
        Args:
            note_signal: The synthesized note signal
            start_idx: Starting sample index
            end_idx: Ending sample index
            next_avail_idx: Next available sample index
            
        Returns:
            Tuple of (shaped_signal, end_index)
        """
        # Calculate duration in samples
        duration = end_idx - start_idx
        
        # Trim or pad the note signal to match the desired duration
        if len(note_signal) > duration:
            shaped_signal = note_signal[:duration]
        else:
            shaped_signal = np.pad(note_signal, (0, duration - len(note_signal)))
        
        return shaped_signal, end_idx
    
    def scale(self, signal: np.ndarray) -> np.ndarray:
        """
        Scale a signal to fit within the valid amplitude range.
        
        Args:
            signal: Input audio signal
            
        Returns:
            Scaled audio signal
        """
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            scale_factor = self.max_value / max_val
            scaled_signal = signal * scale_factor
            
            # Clip to ensure within range
            return np.clip(scaled_signal, self.min_value, self.max_value)
        return signal

# Example usage of the SignalProcessor class to create various guitar and bass sounds  
"""
processor = SignalProcessor()

# Clean electric guitar
clean_guitar = processor.create_note(
    instrument=28,  # Clean electric guitar
    note=60,        # C4
    velocity=100    # Medium-loud
)

# Overdriven electric guitar
overdriven_guitar = processor.create_note(
    instrument=28,  # Clean electric guitar
    note=60,        # C4
    velocity=100,   # Medium-loud
    effect_type=EffectType.OVERDRIVE,
    effect_intensity=0.6,
    effect_params={'drive': 1.2, 'tone': 0.7}
)

# Heavily distorted electric guitar
distorted_guitar = processor.create_note(
    instrument=28,  # Clean electric guitar
    note=60,        # C4
    velocity=100,   # Medium-loud
    effect_type=EffectType.DISTORTION,
    effect_intensity=0.8,
    effect_params={'drive': 1.5, 'tone': 0.6}
)

# Fuzz bass
fuzz_bass = processor.create_note(
    instrument=34,  # Fingered bass
    note=40,        # E2
    velocity=100,   # Medium-loud
    effect_type=EffectType.FUZZ,
    effect_intensity=0.7,
    effect_params={'drive': 1.3, 'octave': 0.3, 'grit': 0.6}
)

# "Experimental" distorted piano 
weird_piano = processor.create_note(
    instrument=1,   # Grand piano
    note=60,        # C4
    velocity=100,   # Medium-loud
    effect_type=EffectType.FUZZ,
    effect_intensity=0.5,
    effect_params={'drive': 0.8, 'octave': 0.2, 'grit': 0.4}
)

# Write to WAV files for testing
from scipy.io.wavfile import write
write('clean_guitar.wav', processor.sf, clean_guitar)
write('overdriven_guitar.wav', processor.sf, overdriven_guitar)
write('distorted_guitar.wav', processor.sf, distorted_guitar)
write('fuzz_bass.wav', processor.sf, fuzz_bass)
write('weird_piano.wav', processor.sf, weird_piano)
"""