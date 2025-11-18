"""
Brass Instrument Synthesis Module

Implements FM synthesis and physical modeling techniques for realistic brass instrument sounds.
Supports various brass instruments from the General MIDI specification.
"""

import numpy as np
from typing import Dict, Optional, Union, Tuple


class BrassSynthesizer:
    """
    Synthesizer for brass instruments using FM synthesis and physical modeling.
    
    This class provides methods to generate realistic brass instrument sounds
    through frequency modulation synthesis with instrument-specific parameters.
    """
    
    def __init__(self, sample_rate: int = 44100, max_value: int = 32767):
        """
        Initialize the brass synthesizer.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            max_value: Maximum amplitude value (default: 32767 for 16-bit audio)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value
        self.standard_A4 = 440.0  # Reference frequency for A4 in Hz
        
        # MIDI program numbers for brass instruments
        self.brass_instruments = {
            57: "trumpet",
            58: "trombone",
            59: "tuba",
            60: "muted_trumpet",
            61: "french_horn",
            62: "brass_section",
            63: "synth_brass_1",
            64: "synth_brass_2"
        }
        
        # Instrument-specific synthesis parameters
        self._instrument_params = {
            # Format: (mod_ratio, mod_index_min, mod_index_max, 
            #          attack_time, decay_time, sustain_level, release_time, 
            #          vibrato_rate, vibrato_depth, brightness)
            
            "trumpet": (1.0, 0.8, 7.0, 0.02, 0.08, 0.9, 0.1, 5.5, 0.015, 1.2),
            "trombone": (0.5, 0.5, 5.0, 0.03, 0.1, 0.85, 0.15, 4.5, 0.01, 1.0),
            "tuba": (0.4, 0.3, 4.0, 0.05, 0.2, 0.8, 0.3, 3.5, 0.005, 0.7),
            "muted_trumpet": (1.0, 0.6, 6.0, 0.01, 0.06, 0.7, 0.08, 5.0, 0.01, 1.3),
            "french_horn": (0.6, 0.4, 4.5, 0.04, 0.15, 0.8, 0.2, 4.0, 0.01, 0.9),
            "brass_section": (0.7, 0.6, 6.0, 0.04, 0.12, 0.85, 0.18, 5.0, 0.012, 1.1),
            "synth_brass_1": (1.0, 1.0, 8.0, 0.03, 0.15, 0.9, 0.2, 5.5, 0.02, 1.4),
            "synth_brass_2": (1.5, 1.2, 10.0, 0.02, 0.1, 0.95, 0.25, 6.0, 0.025, 1.5)
        }
        
    def is_brass_instrument(self, program: int) -> bool:
        """
        Check if a MIDI program number corresponds to a brass instrument.
        
        Args:
            program: MIDI program number
            
        Returns:
            True if the program is a brass instrument, False otherwise
        """
        return program in self.brass_instruments
    
    def get_midi_note_frequency(self, note: int) -> float:
        """
        Convert a MIDI note number to frequency in Hz.
        
        Args:
            note: MIDI note number (0-127)
            
        Returns:
            Frequency in Hz
        """
        return self.standard_A4 * (2 ** ((note - 69) / 12))
    
    def synthesize_brass(self, program: Union[int, str], note: int, 
                        velocity: int, duration: float = 1.0) -> np.ndarray:
        """
        Synthesize a brass instrument note based on MIDI program number or name.
        
        Args:
            program: MIDI program number (57-64) or instrument name
            note: MIDI note number (0-127)
            velocity: MIDI velocity (0-127)
            duration: Note duration in seconds
            
        Returns:
            Synthesized brass sound as numpy array (16-bit PCM range)
            
        Raises:
            ValueError: If program is not a brass instrument
        """
        # Convert string instrument name to program number if needed
        if isinstance(program, str):
            program_found = False
            for prog_num, name in self.brass_instruments.items():
                if name.lower() == program.lower():
                    program = prog_num
                    program_found = True
                    break
            
            if not program_found:
                raise ValueError(f"Unknown brass instrument: {program}")
        
        # Verify this is a brass instrument
        if not self.is_brass_instrument(program):
            raise ValueError(f"Program {program} is not a brass instrument")
            
        # Get instrument name
        instrument_name = self.brass_instruments[program]
        
        # Calculate frequency from MIDI note
        frequency = self.get_midi_note_frequency(note)
        
        # Call the appropriate synthesis method based on instrument
        if instrument_name == "trumpet":
            return self.synthesize_trumpet(frequency, duration, velocity)
        elif instrument_name == "trombone":
            return self.synthesize_trombone(frequency, duration, velocity)
        elif instrument_name == "tuba":
            return self.synthesize_tuba(frequency, duration, velocity)
        elif instrument_name == "muted_trumpet":
            return self.synthesize_muted_trumpet(frequency, duration, velocity)
        elif instrument_name == "french_horn":
            return self.synthesize_french_horn(frequency, duration, velocity)
        elif instrument_name == "brass_section":
            return self.synthesize_brass_section(frequency, duration, velocity)
        elif instrument_name == "synth_brass_1":
            return self.synthesize_synth_brass_1(frequency, duration, velocity)
        elif instrument_name == "synth_brass_2":
            return self.synthesize_synth_brass_2(frequency, duration, velocity)
        else:
            # Fallback to generic brass synthesis
            return self._synthesize_generic_brass(frequency, duration, velocity, instrument_name)
    
    def _synthesize_generic_brass(self, frequency: float, duration: float, 
                                 velocity: int, instrument_name: str) -> np.ndarray:
        """
        Generic brass synthesis method using instrument parameters.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            instrument_name: Name of the brass instrument
            
        Returns:
            Synthesized brass sound as numpy array
        """
        # Get instrument parameters
        params = self._instrument_params.get(instrument_name)
        if params is None:
            # Use trombone as default if parameters not found
            params = self._instrument_params["trombone"]
        
        mod_ratio, mod_index_min, mod_index_max, attack, decay, sustain_level, release, \
        vibrato_rate, vibrato_depth_max, brightness = params
        
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        samples = len(t)
        
        # FM synthesis parameters
        carrier_freq = frequency
        modulator_freq = frequency * mod_ratio
        
        # Modulation index varies with velocity (brighter when louder)
        mod_index = mod_index_min + (velocity / 127) * (mod_index_max - mod_index_min)
        
        # Create FM signal
        modulator = np.sin(2 * np.pi * modulator_freq * t)
        carrier = np.sin(2 * np.pi * carrier_freq * t + mod_index * modulator)
        
        # Add harmonics for richness (varies by instrument brightness)
        if brightness > 1.0:
            h2_amount = 0.3 * brightness * (velocity / 127)
            h3_amount = 0.15 * brightness * (velocity / 127)
            carrier += h2_amount * np.sin(4 * np.pi * carrier_freq * t)  # 2nd harmonic
            carrier += h3_amount * np.sin(6 * np.pi * carrier_freq * t)  # 3rd harmonic
        
        # Add ADSR envelope
        env = self._generate_adsr_envelope(t, attack, decay, sustain_level, release)
        
        # Add velocity-dependent growl for high velocities
        if velocity > 100:
            growl_amount = (velocity - 100) / 27 * brightness
            carrier = np.tanh(carrier * (1 + growl_amount)) / (1 + growl_amount * 0.5)
        
        # Add vibrato (depth depends on velocity)
        vibrato_depth = vibrato_depth_max * (velocity / 127)
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Final signal with envelope, vibrato and velocity scaling
        signal = carrier * env * vibrato * (velocity / 127)
        
        # Scale to 16-bit range and convert to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_trumpet(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a trumpet note.
        
        Trumpets have bright, piercing tone with strong upper harmonics
        and relatively quick attack.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized trumpet sound
        """
        # Generate basic brass tone
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "trumpet")
        
        # Add trumpet-specific processing
        # Trumpets have a characteristic spectral peak around 1-1.5kHz
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Convert to float for processing
        signal = signal.astype(float) / self.max_value
        
        # Add trumpet-like formant emphasis
        resonance = self._bandpass_filter(signal, 1200, 5)
        signal = signal + resonance * 0.2 * (velocity / 127)
        
        # Add characteristic trumpet "buzz" for higher velocities
        if velocity > 90:
            buzz_amount = (velocity - 90) / 37 * 0.1
            noise = np.random.normal(0, buzz_amount, len(signal))
            # Only add noise during attack and when signal is strong
            noise_env = np.exp(-5 * t)
            signal = signal + noise * noise_env * np.abs(signal)
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_trombone(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a trombone note using FM technique with intensity-dependent modulation.
        
        Trombones have a warm, mellow tone with moderate attack and strong mid-range.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized trombone sound
        """
        return self._synthesize_generic_brass(frequency, duration, velocity, "trombone")
    
    def synthesize_tuba(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a tuba note.
        
        Tubas have a deep, rich tone with slow attack and emphasis on low frequencies.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized tuba sound
        """
        # Generate basic brass tone
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "tuba")
        
        # Add tuba-specific processing - enhance low end
        signal = signal.astype(float) / self.max_value
        
        # Add sub-harmonic for that deep tuba sound
        t = np.arange(0, duration, 1/self.sample_rate)
        subharmonic = 0.2 * np.sin(np.pi * frequency * t)  # Half frequency
        signal = signal + subharmonic * (velocity / 127)
        
        # Apply low-pass filter to emphasize the characteristic tuba sound
        signal = self._simple_lowpass(signal, cutoff=0.15)
        
        # Add subtle breath noise
        breath = np.random.normal(0, 0.01, len(signal)) * (velocity / 127)
        breath_env = np.exp(-2 * t)
        signal = signal + breath * breath_env
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_muted_trumpet(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a muted trumpet note.
        
        Muted trumpets have a nasal, thin tone with reduced low frequencies
        and emphasized mid-high frequencies.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized muted trumpet sound
        """
        # Generate basic trumpet tone
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "muted_trumpet")
        
        # Convert to float for processing
        signal = signal.astype(float) / self.max_value
        
        # Filter to create muted effect - reduce lows, emphasize mids
        signal = self._simple_highpass(signal, cutoff=0.2)  # Cut low frequencies
        
        # Add characteristic muted resonance
        t = np.arange(0, duration, 1/self.sample_rate)
        resonance = 0.25 * np.sin(2 * np.pi * 2000 * t) * np.exp(-10 * t)
        signal = signal + resonance * (velocity / 127)
        
        # Add subtle distortion for that "pinched" muted sound
        signal = np.tanh(signal * 1.2) / 1.2
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_french_horn(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a French horn note.
        
        French horns have a smooth, mellow tone with moderate attack and
        characteristic resonance.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized French horn sound
        """
        # Generate basic brass tone
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "french_horn")
        
        # Add French horn-specific processing
        signal = signal.astype(float) / self.max_value
        
        # Filter to create French horn characteristic sound
        # Smooth out high frequencies
        signal = self._simple_lowpass(signal, cutoff=0.3)
        
        # Add characteristic French horn resonance
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # French horn has distinctive formants
        formant1 = self._bandpass_filter(signal, 650, 5) * 0.15
        formant2 = self._bandpass_filter(signal, 1100, 8) * 0.1
        signal = signal + formant1 + formant2
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_brass_section(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a brass section (ensemble) sound.
        
        Brass sections have a full, rich sound with multiple instruments
        playing in unison with slight variations.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized brass section sound
        """
        # Generate multiple brass instruments and blend them
        trumpet = self._synthesize_generic_brass(frequency, duration, velocity, "trumpet")
        trombone = self._synthesize_generic_brass(frequency, duration, velocity, "trombone")
        french_horn = self._synthesize_generic_brass(frequency, duration, velocity, "french_horn")
        
        # Convert to float
        trumpet = trumpet.astype(float) / self.max_value
        trombone = trombone.astype(float) / self.max_value
        french_horn = french_horn.astype(float) / self.max_value
        
        # Create slightly detuned copies for ensemble effect
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create detuned copies (chorus effect)
        trumpet2 = self._synthesize_generic_brass(frequency * 1.002, duration, velocity, "trumpet").astype(float) / self.max_value
        trombone2 = self._synthesize_generic_brass(frequency * 0.998, duration, velocity, "trombone").astype(float) / self.max_value
        
        # Mix components with different weights
        signal = (trumpet * 0.4 + 
                 trumpet2 * 0.3 + 
                 trombone * 0.3 + 
                 trombone2 * 0.2 + 
                 french_horn * 0.25)
        
        # Normalize to avoid clipping
        signal = signal / np.max(np.abs(signal)) * 0.95
        
        # Add characteristic ensemble resonance
        formant = self._bandpass_filter(signal, 800, 3) * 0.1
        signal = signal + formant
        
        # Add subtle noise component for that "section" sound
        noise = np.random.normal(0, 0.01, len(signal))
        noise_env = np.exp(-5 * t)  # More noise in attack
        signal = signal + noise * noise_env * (velocity / 127)
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_synth_brass_1(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize synth brass 1 sound.
        
        Synth brass 1 is typically a bright, synthetic brass sound with
        faster attack and more pronounced upper harmonics.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized synth brass sound
        """
        # Generate basic brass tone with synth parameters
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "synth_brass_1")
        
        # Convert to float for processing
        signal = signal.astype(float) / self.max_value
        
        # Add additional harmonics for that synthetic character
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Add upper harmonics with different phases for more synthetic character
        harm2 = 0.3 * np.sin(4 * np.pi * frequency * t + 0.2)
        harm3 = 0.2 * np.sin(6 * np.pi * frequency * t + 0.5)
        harm4 = 0.1 * np.sin(8 * np.pi * frequency * t + 0.8)
        
        signal = signal + (harm2 + harm3 + harm4) * (velocity / 127)
        
        # Add subtle filter sweep
        sweep = np.linspace(0.2, 0.8, len(signal))
        sweep_env = 1.0 - np.exp(-2 * t)  # Envelope for the sweep
        
        for i in range(len(signal) - 1):
            # Simple low-pass filter with time-varying cutoff
            cutoff = 0.3 + 0.6 * sweep[i] * sweep_env[i]
            signal[i + 1] = (1 - cutoff) * signal[i + 1] + cutoff * signal[i]
        
        # Normalize and convert back to int16
        signal = signal / np.max(np.abs(signal)) * 0.95
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_synth_brass_2(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize synth brass 2 sound.
        
        Synth brass 2 is typically a more mellow, pad-like synthetic brass sound
        with slower attack and more evolution over time.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized synth brass 2 sound
        """
        # Generate basic brass tone with synth parameters
        signal = self._synthesize_generic_brass(frequency, duration, velocity, "synth_brass_2")
        
        # Convert to float for processing
        signal = signal.astype(float) / self.max_value
        
        # Add pulse width modulation effect for synth character
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create pulse wave with time-varying width
        pulse_width = 0.4 + 0.2 * np.sin(2 * np.pi * 0.5 * t)
        pulse = np.zeros_like(t)
        for i in range(len(t)):
            if (t[i] * frequency) % 1 < pulse_width[i]:
                pulse[i] = 1.0
            else:
                pulse[i] = -0.8
        
        # Mix with original signal
        mix_ratio = 0.3  # Amount of pulse wave to add
        signal = (1 - mix_ratio) * signal + mix_ratio * pulse
        
        # Add filter envelope for evolving timbre
        env = np.exp(-1 * t)  # Slow decay
        
        # Apply time-varying filter
        filtered = self._simple_lowpass(signal, cutoff=0.2)
        signal = signal * (1 - env) + filtered * env
        
        # Normalize and convert back to int16
        signal = signal / np.max(np.abs(signal)) * 0.95
        return (signal * self.max_value).astype(np.int16)
    
    def _generate_adsr_envelope(self, t: np.ndarray, attack: float, decay: float,
                               sustain_level: float, release: float) -> np.ndarray:
        """
        Generate an ADSR (Attack, Decay, Sustain, Release) envelope.
        
        Args:
            t: Time array
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain_level: Sustain level (0.0 to 1.0)
            release: Release time in seconds
            
        Returns:
            ADSR envelope as numpy array
        """
        duration = t[-1]
        envelope = np.ones_like(t)
        
        # Calculate time points
        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        release_start = int((duration - release) * self.sample_rate)
        
        # Ensure valid indices
        attack_samples = max(1, attack_samples)
        decay_samples = max(1, decay_samples)
        release_start = max(attack_samples + decay_samples, min(release_start, len(t) - 1))
        
        # Create envelope segments
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)**2  # Squared for smoother attack
            
        if decay_samples > 0 and attack_samples < len(t):
            decay_end = min(attack_samples + decay_samples, len(t))
            envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_end - attack_samples)
        
        if attack_samples + decay_samples < len(t):
            envelope[attack_samples + decay_samples:release_start] = sustain_level
            
        if release_start < len(t) - 1:
            envelope[release_start:] = np.linspace(envelope[release_start], 0, len(t) - release_start)
            
        return envelope
    
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
            filtered[i] = alpha * (filtered[i-1] + signal[i] - signal[i-1])
            
        return filtered
    
    def _bandpass_filter(self, signal: np.ndarray, center_freq: float, q: float = 5.0) -> np.ndarray:
        """
        Simple bandpass filter.
        
        Args:
            signal: Input signal
            center_freq: Center frequency in Hz
            q: Q factor (resonance width)
            
        Returns:
            Filtered signal
        """
        # Simplified resonant filter
        filtered = np.zeros_like(signal)
        
        # Convert center frequency to normalized frequency
        norm_freq = center_freq / (self.sample_rate / 2)
        norm_freq = min(0.99, max(0.01, norm_freq))  # Constrain to valid range
        
        # Filter coefficients (simplified)
        r = 1 - 3 / (q * 10)
        omega = 2 * np.pi * norm_freq
        
        # State variables
        y1 = 0
        y2 = 0
        
        # Process signal
        for i in range(len(signal)):
            # Simple resonant filter formula
            y0 = signal[i] + 2 * r * np.cos(omega) * y1 - r**2 * y2
            filtered[i] = y0 - r**2 * y2
            
            # Update state
            y2 = y1
            y1 = y0
            
        # Normalize output to avoid extreme resonance
        max_val = np.max(np.abs(filtered))
        if max_val > 0:
            filtered = filtered / max_val * np.max(np.abs(signal))
            
        return filtered


# Example usage:
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from scipy.io.wavfile import write
    
    # Create synthesizer
    synth = BrassSynthesizer()
    
    # Generate different brass instruments
    trumpet = synth.synthesize_brass("trumpet", note=60, velocity=100, duration=2.0)
    trombone = synth.synthesize_brass(58, note=48, velocity=100, duration=2.0)
    tuba = synth.synthesize_brass("tuba", note=36, velocity=100, duration=2.0)
    brass_section = synth.synthesize_brass(62, note=60, velocity=100, duration=2.0)
    
    # Write to WAV files
    write("trumpet.wav", synth.sample_rate, trumpet)
    write("trombone.wav", synth.sample_rate, trombone)
    write("tuba.wav", synth.sample_rate, tuba)
    write("brass_section.wav", synth.sample_rate, brass_section)
    
    # Create a brass section chord
    chord_notes = [60, 64, 67, 72]  # C major chord
    chord = np.zeros(int(2.0 * synth.sample_rate), dtype=np.int16)
    
    for note in chord_notes:
        note_signal = synth.synthesize_brass("brass_section", note, velocity=90, duration=2.0)
        chord = chord + note_signal // len(chord_notes)  # Mix with equal weight
        
    write("brass_chord.wav", synth.sample_rate, chord)