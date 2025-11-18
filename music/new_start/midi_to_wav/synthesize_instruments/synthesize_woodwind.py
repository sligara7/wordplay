"""
Woodwind Instrument Synthesis Module

Implements formant synthesis and physical modeling techniques for realistic woodwind instrument sounds.
Supports various woodwind instruments from the General MIDI specification.
"""

import numpy as np
from typing import Dict, Optional, Union, Tuple, List


class WoodwindSynthesizer:
    """
    Synthesizer for woodwind instruments using formant synthesis and physical modeling.
    
    This class provides methods to generate realistic woodwind sounds through
    spectral modeling and instrument-specific parameters.
    """
    
    def __init__(self, sample_rate: int = 44100, max_value: int = 32767):
        """
        Initialize the woodwind synthesizer.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            max_value: Maximum amplitude value (default: 32767 for 16-bit audio)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value
        self.standard_A4 = 440.0  # Reference frequency for A4 in Hz
        
        # MIDI program numbers for woodwind instruments
        self.woodwind_instruments = {
            # Pipe/flute family
            73: "piccolo",
            74: "flute", 
            75: "recorder",
            76: "pan_flute",
            77: "bottle_blow",
            78: "shakuhachi",
            79: "whistle",
            80: "ocarina",
            # Reed family
            65: "soprano_sax",
            66: "alto_sax",
            67: "tenor_sax",
            68: "baritone_sax",
            69: "oboe",
            70: "english_horn",
            71: "bassoon",
            72: "clarinet"
        }
        
        # Instrument-specific synthesis parameters
        # Format: (attack, decay, sustain, release, brightness, vibrato_rate, vibrato_depth, breath_noise)
        self._instrument_params = {
            "piccolo":      (0.03, 0.05, 0.9, 0.08, 1.4, 6.0, 0.018, 0.12),
            "flute":        (0.06, 0.10, 0.9, 0.15, 0.9, 5.5, 0.015, 0.10),
            "recorder":     (0.03, 0.05, 0.9, 0.10, 0.7, 4.5, 0.010, 0.08),
            "pan_flute":    (0.12, 0.15, 0.9, 0.20, 0.6, 4.0, 0.020, 0.15),
            "bottle_blow":  (0.08, 0.10, 0.8, 0.15, 0.6, 3.0, 0.010, 0.20),
            "shakuhachi":   (0.10, 0.15, 0.8, 0.30, 0.7, 3.5, 0.025, 0.25),
            "whistle":      (0.02, 0.03, 0.9, 0.05, 1.5, 7.0, 0.010, 0.05),
            "ocarina":      (0.05, 0.08, 0.9, 0.10, 0.8, 4.0, 0.015, 0.08),
            "soprano_sax":  (0.04, 0.10, 0.9, 0.12, 1.3, 5.0, 0.020, 0.15),
            "alto_sax":     (0.05, 0.12, 0.9, 0.15, 1.2, 4.5, 0.025, 0.12),
            "tenor_sax":    (0.06, 0.15, 0.9, 0.20, 1.1, 4.0, 0.025, 0.10),
            "baritone_sax": (0.08, 0.20, 0.9, 0.25, 1.0, 3.8, 0.020, 0.08),
            "oboe":         (0.08, 0.10, 0.9, 0.20, 1.1, 5.0, 0.015, 0.05),
            "english_horn": (0.10, 0.15, 0.9, 0.25, 0.9, 4.5, 0.015, 0.05),
            "bassoon":      (0.12, 0.20, 0.8, 0.30, 0.7, 4.0, 0.010, 0.07),
            "clarinet":     (0.05, 0.10, 0.9, 0.15, 0.8, 4.5, 0.010, 0.05)
        }
        
        # Dictionary of formant settings for different instruments
        # Format: [(frequency, gain, Q-factor), ...]
        self._formant_settings = {
            "piccolo": [(900, 1.0, 5), (2100, 0.8, 8), (3800, 0.6, 10), (5500, 0.4, 12)],
            "flute": [(800, 1.0, 5), (1800, 0.7, 8), (3000, 0.5, 10), (4200, 0.3, 12)],
            "recorder": [(700, 1.0, 4), (1500, 0.8, 7), (2300, 0.6, 9), (3200, 0.4, 10)],
            "pan_flute": [(600, 1.0, 6), (1400, 0.8, 8), (2400, 0.5, 12), (3800, 0.3, 15)],
            "bottle_blow": [(500, 1.0, 8), (1100, 0.7, 10), (2200, 0.4, 12)],
            "shakuhachi": [(400, 1.0, 6), (1200, 0.8, 8), (2400, 0.5, 10), (3500, 0.3, 12)],
            "whistle": [(1200, 1.0, 10), (2400, 0.6, 12), (4800, 0.3, 15)],
            "ocarina": [(600, 1.0, 8), (1500, 0.6, 10), (2800, 0.4, 12)],
            "soprano_sax": [(850, 1.0, 6), (1600, 0.8, 8), (2600, 0.7, 10), (4000, 0.5, 12)],
            "alto_sax": [(700, 1.0, 6), (1400, 0.8, 8), (2300, 0.7, 10), (3700, 0.5, 12)],
            "tenor_sax": [(550, 1.0, 6), (1100, 0.8, 8), (2000, 0.7, 10), (3200, 0.5, 12)],
            "baritone_sax": [(450, 1.0, 6), (900, 0.8, 8), (1800, 0.7, 10), (2800, 0.5, 12)],
            "oboe": [(700, 1.0, 5), (1200, 0.75, 8), (2500, 0.6, 10), (3800, 0.4, 15)],
            "english_horn": [(650, 1.0, 5), (1100, 0.75, 8), (2200, 0.6, 10), (3400, 0.4, 15)],
            "bassoon": [(450, 1.0, 6), (900, 0.7, 8), (1800, 0.5, 10), (2700, 0.3, 12)],
            "clarinet": [(600, 1.0, 5), (1500, 0.5, 8), (2500, 0.3, 10), (3800, 0.2, 12)]
        }
    
    def is_woodwind_instrument(self, program: int) -> bool:
        """
        Check if a MIDI program number corresponds to a woodwind instrument.
        
        Args:
            program: MIDI program number
            
        Returns:
            True if the program is a woodwind instrument, False otherwise
        """
        return program in self.woodwind_instruments
    
    def get_midi_note_frequency(self, note: int) -> float:
        """
        Convert a MIDI note number to frequency in Hz.
        
        Args:
            note: MIDI note number (0-127)
            
        Returns:
            Frequency in Hz
        """
        return self.standard_A4 * (2 ** ((note - 69) / 12))
    
    def synthesize_woodwind(self, program: Union[int, str], note: int, 
                           velocity: int, duration: float = 1.0) -> np.ndarray:
        """
        Synthesize a woodwind instrument note based on MIDI program number or name.
        
        Args:
            program: MIDI program number (65-80) or instrument name
            note: MIDI note number (0-127)
            velocity: MIDI velocity (0-127)
            duration: Note duration in seconds
            
        Returns:
            Synthesized woodwind sound as numpy array (16-bit PCM range)
            
        Raises:
            ValueError: If program is not a woodwind instrument
        """
        # Convert string instrument name to program number if needed
        if isinstance(program, str):
            program_found = False
            for prog_num, name in self.woodwind_instruments.items():
                if name.lower() == program.lower():
                    program = prog_num
                    program_found = True
                    break
            
            if not program_found:
                raise ValueError(f"Unknown woodwind instrument: {program}")
        
        # Verify this is a woodwind instrument
        if not self.is_woodwind_instrument(program):
            raise ValueError(f"Program {program} is not a woodwind instrument")
            
        # Get instrument name
        instrument_name = self.woodwind_instruments[program]
        
        # Calculate frequency from MIDI note
        frequency = self.get_midi_note_frequency(note)
        
        # Call the appropriate synthesis method
        if instrument_name == "flute":
            return self.synthesize_flute(frequency, duration, velocity)
        elif instrument_name == "oboe":
            return self.synthesize_oboe(frequency, duration, velocity)
        elif instrument_name == "clarinet":
            return self.synthesize_clarinet(frequency, duration, velocity)
        elif instrument_name == "bassoon":
            return self.synthesize_bassoon(frequency, duration, velocity)
        elif "sax" in instrument_name:
            return self.synthesize_saxophone(frequency, duration, velocity, instrument_name)
        else:
            # For other woodwinds, use generic synthesis with instrument-specific parameters
            return self._synthesize_generic_woodwind(frequency, duration, velocity, instrument_name)
    
    def _synthesize_generic_woodwind(self, frequency: float, duration: float, 
                                    velocity: int, instrument_name: str) -> np.ndarray:
        """
        Generic woodwind synthesis method using instrument parameters.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            instrument_name: Name of the woodwind instrument
            
        Returns:
            Synthesized woodwind sound as numpy array
        """
        # Get instrument parameters
        params = self._instrument_params.get(instrument_name)
        if params is None:
            # Use flute as default if parameters not found
            params = self._instrument_params["flute"]
        
        attack, decay, sustain_level, release, brightness, vibrato_rate, vibrato_depth_max, breath_amount = params
        
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Determine base waveform based on instrument family
        is_reed = instrument_name in ["oboe", "english_horn", "bassoon", "clarinet"] or "sax" in instrument_name
        
        if is_reed:
            # Reed instruments have richer harmonics - use pulse/sawtooth hybrid
            pulse_width = 0.2
            base_signal = np.where(np.mod(t * frequency, 1) < pulse_width, 1.0, -0.4)
        else:
            # Flute-like instruments are more sine-like with some harmonics
            phase = 2 * np.pi * frequency * t
            base_signal = 0.7 * np.sin(phase) + 0.2 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)
        
        # Apply formant filtering based on instrument
        formant_settings = self._formant_settings.get(instrument_name, 
                                                     self._formant_settings["flute"])
        
        signal = np.zeros_like(t)
        for freq, gain, q in formant_settings:
            # Apply bandpass filter for each formant
            filtered = self._bandpass_filter(base_signal, freq, q)
            signal += gain * filtered
        
        # Generate ADSR envelope
        env = self._generate_adsr_envelope(t, attack, decay, sustain_level, release)
        
        # Add vibrato (depth depends on velocity)
        vibrato_depth = vibrato_depth_max * (velocity / 127)
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Add breath noise
        noise_level = breath_amount * (0.5 + 0.5 * velocity / 127)
        noise = np.random.normal(0, noise_level, len(t))
        
        # Modulate noise with envelope
        noise = noise * env * 0.1
        
        # Combine components
        signal = (signal * env * vibrato + noise) * (velocity / 127)
        
        # Scale to 16-bit range and convert to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_flute(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a flute note.
        
        Flutes have a pure, airy tone with moderate attack and
        characteristic breathy component.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized flute sound
        """
        # Generate with base parameters
        signal = self._synthesize_generic_woodwind(frequency, duration, velocity, "flute")
        
        # Convert to float for processing
        signal = signal.astype(float) / self.max_value
        
        # Add flute-specific processing
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Flutes have a characteristic "chiff" at the start
        chiff_duration = min(0.08, duration * 0.1)  # 80ms or 10% of note
        chiff_samples = int(chiff_duration * self.sample_rate)
        
        if chiff_samples > 0:
            chiff = np.random.normal(0, 0.15, chiff_samples) * (velocity / 127)
            chiff_env = np.linspace(1, 0, chiff_samples)**2
            signal[:chiff_samples] += chiff * chiff_env
        
        # Enhance upper harmonics slightly for that flute "edge"
        harmonic = 0.1 * np.sin(2 * np.pi * frequency * 2 * t) * (velocity / 127)
        harmonic_env = np.ones_like(t)
        harmonic_env[:int(0.1 * self.sample_rate)] = np.linspace(0, 1, int(0.1 * self.sample_rate))
        signal += harmonic * harmonic_env
        
        # Apply subtle lowpass filtering to smooth the tone
        signal = self._simple_lowpass(signal, cutoff=0.3)
        
        # Convert back to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_oboe(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize an oboe note using formant filtering.
        
        Oboes have a distinctive nasal tone with strong formants and
        relatively quick attack.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized oboe sound
        """
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create base waveform with rich harmonics
        # Pulse wave with varying duty cycle works well for reed instruments
        pulse_width = 0.2
        base_signal = np.where(np.mod(t * frequency, 1) < pulse_width, 1.0, -0.4)
        
        # Apply formant filtering (characteristic oboe resonances)
        formant_freqs = [700, 1200, 2500, 3800]  # Hz
        formant_gains = [1.0, 0.75, 0.6, 0.4]
        formant_q = [5, 8, 10, 15]  # Q factors (resonance width)
        
        signal = np.zeros_like(t)
        for freq, gain, q in zip(formant_freqs, formant_gains, formant_q):
            # Apply bandpass filter for each formant
            filtered = self._bandpass_filter(base_signal, freq, q)
            signal += gain * filtered
        
        # Apply characteristic envelope
        # Oboes have moderate attack, long sustain
        env = self._generate_adsr_envelope(t, 0.08, 0.1, 0.9, 0.2)
        
        # Add subtle vibrato (common in oboe playing)
        vibrato_rate = 5.0  # Hz
        vibrato_depth = 0.015 * (velocity / 127)  # Deeper at higher velocities
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Add minimal breath noise
        noise = np.random.normal(0, 0.03, len(t)) * (velocity / 127)
        noise = noise * env
        
        # Apply envelope, vibrato and velocity scaling
        signal = (signal * env * vibrato + noise) * (velocity / 127)
        
        # Apply slight EQ to emphasize the nasal quality
        nasal_resonance = self._bandpass_filter(signal, 1500, 8) * 0.15
        signal += nasal_resonance
        
        # Scale to 16-bit range and convert to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_clarinet(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a clarinet note.
        
        Clarinets have a hollow, warm tone with predominantly odd harmonics
        and smooth attack.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized clarinet sound
        """
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create base signal with predominantly odd harmonics
        # (characteristic of cylindrical bore instruments)
        phase = 2 * np.pi * frequency * t
        base_signal = np.sin(phase)  # Fundamental
        
        # Add odd harmonics with decreasing amplitude
        for i in range(3, 10, 2):  # Odd harmonics: 3, 5, 7, 9
            base_signal += (1/i) * np.sin(i * phase)
        
        # Normalize base signal
        base_signal /= np.max(np.abs(base_signal))
        
        # Apply formant filtering for clarinet resonance
        formant_freqs = [600, 1500, 2500, 3800]
        formant_gains = [1.0, 0.5, 0.3, 0.2]
        formant_q = [5, 8, 10, 12]
        
        signal = np.zeros_like(t)
        for freq, gain, q in zip(formant_freqs, formant_gains, formant_q):
            filtered = self._bandpass_filter(base_signal, freq, q)
            signal += gain * filtered
        
        # Apply ADSR envelope - clarinets have a characteristically smooth attack
        env = self._generate_adsr_envelope(t, 0.05, 0.1, 0.9, 0.15)
        
        # Add subtle vibrato (less than oboe)
        vibrato_rate = 4.5  # Hz
        vibrato_depth = 0.01 * (velocity / 127)  # Subtle vibrato
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Add minimal breath noise
        noise = np.random.normal(0, 0.05, len(t)) * (velocity / 127)
        noise = noise * env * 0.1
        
        # Combine components
        signal = (signal * env * vibrato + noise) * (velocity / 127)
        
        # Scale to 16-bit range and convert to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_bassoon(self, frequency: float, duration: float, velocity: int) -> np.ndarray:
        """
        Synthesize a bassoon note.
        
        Bassoons have a rich, reedy tone with slower attack and release
        and complex harmonic structure.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            
        Returns:
            Synthesized bassoon sound
        """
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create base waveform - bassoon has rich harmonic structure
        pulse_width = 0.3 # Wider pulse width for bassoon's fuller tone
        base_signal = np.where(np.mod(t * frequency, 1) < pulse_width, 1.0, -0.4)
        
        # Apply formant filtering for bassoon's characteristic resonances
        formant_freqs = [450, 900, 1800, 2700]
        formant_gains = [1.0, 0.7, 0.5, 0.3]
        formant_q = [6, 8, 10, 12]
        
        signal = np.zeros_like(t)
        for freq, gain, q in zip(formant_freqs, formant_gains, formant_q):
            filtered = self._bandpass_filter(base_signal, freq, q)
            signal += gain * filtered
        
        # Bassoons have relatively slow attack and release
        env = self._generate_adsr_envelope(t, 0.12, 0.2, 0.8, 0.3)
        
        # Add subtle vibrato
        vibrato_rate = 4.0  # Hz
        vibrato_depth = 0.01 * (velocity / 127)
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Add breath noise component
        noise = np.random.normal(0, 0.07, len(t)) * (velocity / 127)
        noise = noise * env * 0.1
        
        # Combine components
        signal = (signal * env * vibrato + noise) * (velocity / 127)
        
        # Add very subtle subharmonic for richness
        subharmonic = 0.08 * np.sin(np.pi * frequency * t) * env
        signal += subharmonic
        
        # Apply subtle low-pass filtering for warmth
        signal = self._simple_lowpass(signal, cutoff=0.2)
        
        # Scale to 16-bit range and convert to int16
        return (signal * self.max_value).astype(np.int16)
    
    def synthesize_saxophone(self, frequency: float, duration: float, velocity: int, 
                            sax_type: str = "alto_sax") -> np.ndarray:
        """
        Synthesize a saxophone note.
        
        Saxophones have bright, rich tones with strong formants and
        potential for "growl" at high velocities.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Note duration in seconds
            velocity: Note velocity (0-127)
            sax_type: Type of saxophone ("soprano_sax", "alto_sax", "tenor_sax", "baritone_sax")
            
        Returns:
            Synthesized saxophone sound
        """
        # Get specific sax parameters
        if sax_type not in ["soprano_sax", "alto_sax", "tenor_sax", "baritone_sax"]:
            sax_type = "alto_sax"  # Default to alto sax
            
        # Generate sample times
        t = np.arange(0, duration, 1/self.sample_rate)
        
        # Create base waveform - saxophones have rich harmonics
        # Use a composite waveform
        phase = 2 * np.pi * frequency * t
        base_signal = 0.6 * np.sin(phase)  # Fundamental
        
        # Add harmonics with relative strengths
        base_signal += 0.3 * np.sin(2 * phase)
        base_signal += 0.2 * np.sin(3 * phase)
        base_signal += 0.15 * np.sin(4 * phase)
        base_signal += 0.1 * np.sin(5 * phase)
        base_signal += 0.05 * np.sin(6 * phase)
        
        # Normalize base signal
        base_signal /= np.max(np.abs(base_signal))
        
        # Apply formant filtering based on sax type
        formant_settings = self._formant_settings.get(sax_type, self._formant_settings["alto_sax"])
        
        signal = np.zeros_like(t)
        for freq, gain, q in formant_settings:
            filtered = self._bandpass_filter(base_signal, freq, q)
            signal += gain * filtered
        
        # Get ADSR parameters for this sax type
        params = self._instrument_params.get(sax_type, self._instrument_params["alto_sax"])
        attack, decay, sustain_level, release = params[:4]
        
        # Apply envelope
        env = self._generate_adsr_envelope(t, attack, decay, sustain_level, release)
        
        # Add vibrato - increases gradually after attack
        vibrato_rate = 5.0  # Hz
        vibrato_depth = 0.02 * (velocity / 127)
        vibrato_env = np.ones_like(t)
        vibrato_delay = int(0.3 * self.sample_rate)  # Delay vibrato onset
        if vibrato_delay < len(vibrato_env):
            vibrato_env[:vibrato_delay] = np.linspace(0, 1, vibrato_delay)**2
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t) * vibrato_env
        
        # Add breath noise
        noise = np.random.normal(0, 0.1, len(t)) * (velocity / 127)
        noise = noise * env * 0.1
        
        # Add "growl" effect for high velocities (common in sax playing)
        if velocity > 100:
            growl_amount = (velocity - 100) / 27 * 0.3  # Scale up to 30% at velocity 127
            growl_freq = 30  # Hz
            growl_mod = growl_amount * (0.5 + 0.5 * np.sin(2 * np.pi * growl_freq * t))
            
            # Apply amplitude modulation for growl
            growl_factor = 1.0 - growl_mod
            signal = signal * growl_factor
            
            # Add additional noise for growl texture
            growl_noise = np.random.normal(0, growl_amount * 0.2, len(t)) * env
            signal += growl_noise
        
        # Combine components
        signal = (signal * env * vibrato + noise) * (velocity / 127)
        
        # Add mild saturation for that sax "edge" at higher velocities
        if velocity > 90:
            drive = 1.0 + (velocity - 90) / 37 * 0.5  # Up to 1.5x drive at velocity 127
            signal = np.tanh(signal * drive) / drive
        
        # Scale to 16-bit range and convert to int16
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
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            
        if decay_samples > 0 and attack_samples < len(t):
            decay_end = min(attack_samples + decay_samples, len(t))
            envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_end - attack_samples)
        
        if attack_samples + decay_samples < len(t):
            envelope[attack_samples + decay_samples:release_start] = sustain_level
            
        if release_start < len(t) - 1:
            envelope[release_start:] = np.linspace(envelope[release_start], 0, len(t) - release_start)
            
        return envelope
    
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


# Example usage:
# if __name__ == "__main__":
#     import matplotlib.pyplot as plt
#     from scipy.io.wavfile import write
    
#     # Create synthesizer
#     synth = WoodwindSynthesizer()
    
#     # Generate different woodwind instruments
#     flute = synth.synthesize_woodwind("flute", note=72, velocity=90, duration=2.0)
#     oboe = synth.synthesize_woodwind(69, note=67, velocity=100, duration=2.0)
#     clarinet = synth.synthesize_woodwind("clarinet", note=60, velocity=85, duration=2.0)
#     saxophone = synth.synthesize_woodwind("alto_sax", note=65, velocity=110, duration=2.0)
    
#     # Write to WAV files
#     write("flute.wav", synth.sample_rate, flute)
#     write("oboe.wav", synth.sample_rate, oboe)
#     write("clarinet.wav", synth.sample_rate, clarinet)
#     write("saxophone.wav", synth.sample_rate, saxophone)
    
#     # Create a woodwind ensemble
#     notes = [60, 64, 67, 72]  # C major chord
#     instruments = ["flute", "oboe", "clarinet", "bassoon"]
#     ensemble = np.zeros(int(3.0 * synth.sample_rate), dtype=np.int16)
    
#     for note, instrument in zip(notes, instruments):
#         instr_signal = synth.synthesize_woodwind(instrument, note, velocity=95, duration=3.0)
#         ensemble = ensemble + instr_signal // len(instruments)
        
#     write("woodwind_ensemble.wav", synth.sample_rate, ensemble)