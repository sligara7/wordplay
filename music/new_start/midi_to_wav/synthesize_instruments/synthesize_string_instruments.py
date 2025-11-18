"""
String Instrument Synthesis Module

Implements Karplus-Strong and other algorithms for realistic string instrument synthesis.
"""

import numpy as np
from typing import Dict, Optional, Union
from .audio_effects import AudioEffects, EffectType


class StringInstrumentSynthesizer:
    """
    Synthesizer for realistic string instrument sounds.
    
    Uses Karplus-Strong algorithm and other techniques to generate
    realistic plucked and bowed string instrument sounds.
    """
    
    def __init__(self, sample_rate: int = 44100, max_value: int = 32767):
        """
        Initialize the string instrument synthesizer.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            max_value: Maximum amplitude value (default: 32767)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value
        self.standard_A4 = 440.0  # Reference frequency for A4
        
        # Initialize effects processor
        self.effects = AudioEffects(sample_rate=sample_rate)
        
        # Define string instruments by MIDI program number
        self.string_instruments = set([
            # Guitars (MIDI programs 25-32)
            25, 26, 27, 28, 29, 30, 31, 32, 
            # Basses (MIDI programs 33-38)
            33, 34, 35, 36, 37, 38, 
            # Bowed strings (MIDI programs 41-46)
            41, 42, 43, 44, 45, 46, 
            # Harp (MIDI program 47)
            47,
            # Misc. String instruments (MIDI programs 105-108)
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
            Synthesized plucked string sound as a numpy array (-1.0 to 1.0 range)
        """
        # Calculate buffer size N based on frequency
        N = int(round(self.sample_rate / frequency))
        if N <= 1:
            N = 2  # Minimum buffer size
            
        # Calculate number of samples needed
        num_samples = int(duration * self.sample_rate)
        
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
        filter_coeff = 0.5  # Average of current and previous sample
        
        # Karplus-Strong algorithm: loop through and compute each sample
        for i in range(num_samples):
            # Get the current output from the delay line
            output[i] = delay_line[0]
            
            # Update delay line - shift values
            for j in range(N-1):
                delay_line[j] = delay_line[j+1]
            
            # Apply low-pass filter for feedback
            delay_line[N-1] = velocity_damping * (filter_coeff * delay_line[0] + 
                                                 filter_coeff * output[i])
            
            # Introduce slight nonlinearity for more realistic behavior
            if abs(delay_line[N-1]) > 0.9:
                delay_line[N-1] *= 0.99
        
        # Apply overall envelope for more realistic decay
        t = np.linspace(0, 1, num_samples)
        envelope = np.exp(-3 * t)  # Exponential decay
        
        # Add a short attack portion
        attack_samples = int(0.002 * self.sample_rate)  # 2ms attack
        if attack_samples > 0 and attack_samples < num_samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples) * envelope[:attack_samples]
        
        # Apply envelope to output
        output = output * envelope
        
        return output
    
    def create_string_note(self, instrument: int, note: int, velocity: int, 
                          duration: float = 5.0, effects: Optional[Dict] = None) -> np.ndarray:
        """
        Create a synthesized string instrument note, optionally with effects.
        
        Args:
            instrument: MIDI program number
            note: MIDI note number
            velocity: Note velocity (0-127)
            duration: Duration in seconds
            effects: Optional effects configuration dict:
                {
                    'type': EffectType or string name,
                    'intensity': float (0.0-1.0),
                    'parameters': dict of effect parameters
                }
            
        Returns:
            Synthesized audio signal (16-bit PCM range)
        """
        if not self.is_string_instrument(instrument):
            raise ValueError(f"Program {instrument} is not a string instrument")
        
        # Calculate frequency from MIDI note number
        frequency = self.standard_A4 * 2 ** ((note - 69) / 12)
        
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
            duration=duration,
            damping=damping,
            noise_type=noise_type,
            velocity=velocity
        )
        
        # Apply effects if specified
        if effects:
            effect_type = effects.get('type', EffectType.CLEAN)
            intensity = effects.get('intensity', 0.5)
            parameters = effects.get('parameters', {})
            
            signal = self.effects.apply_effect(
                signal, effect_type, intensity, parameters
            )
        
        # Scale to 16-bit PCM range
        signal = signal * self.max_value
        
        return signal.astype(np.int16)


# Example usage:
"""
from scipy.io.wavfile import write

# Create synthesizer
synth = StringInstrumentSynthesizer()

# Clean acoustic guitar
guitar = synth.create_string_note(
    instrument=25,  # Nylon string guitar
    note=60,        # Middle C
    velocity=100    # Medium-loud
)

# Overdriven electric guitar with effects
distorted = synth.create_string_note(
    instrument=30,  # Distortion guitar
    note=48,        # C3
    velocity=120,   # Loud
    effects={
        'type': 'OVERDRIVE',
        'intensity': 0.8,
        'parameters': {
            'drive': 1.5,
            'tone': 0.7
        }
    }
)

# Save to files
write('guitar.wav', synth.sample_rate, guitar)
write('distorted.wav', synth.sample_rate, distorted)
"""