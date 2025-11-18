"""
Percussion Synthesis Module

Provides classes and methods for synthesizing common percussion instruments
using various synthesis techniques.
"""

import numpy as np
from typing import Dict, Optional, Union, Tuple


class PercussionSynthesizer:
    """
    Synthesizer for various percussion instruments.
    
    This class provides methods to generate realistic percussion sounds
    using various synthesis techniques like filtered noise, FM synthesis,
    and Karplus-Strong for toms and other resonant percussion.
    """
    
    def __init__(self, sample_rate: int = 44100, max_value: int = 32767):
        """
        Initialize the percussion synthesizer.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            max_value: Maximum amplitude value (default: 32767 for 16-bit audio)
        """
        self.sample_rate = sample_rate
        self.max_value = max_value
        
        # MIDI note mappings for General MIDI percussion channel (channel 10)
        # Standard mapping used in most MIDI devices and DAWs
        self.percussion_map = {
            35: "acoustic_bass_drum",
            36: "bass_drum",
            37: "side_stick",
            38: "acoustic_snare",
            39: "hand_clap",
            40: "electric_snare",
            41: "low_floor_tom",
            42: "closed_hihat",
            43: "high_floor_tom",
            44: "pedal_hihat",
            45: "low_tom",
            46: "open_hihat",
            47: "low_mid_tom",
            48: "high_mid_tom",
            49: "crash_cymbal1",
            50: "high_tom",
            51: "ride_cymbal1",
            52: "chinese_cymbal",
            53: "ride_bell",
            54: "tambourine",
            55: "splash_cymbal",
            56: "cowbell",
            57: "crash_cymbal2",
            58: "vibraslap",
            59: "ride_cymbal2",
            60: "high_bongo",
            61: "low_bongo",
            62: "mute_high_conga",
            63: "open_high_conga",
            64: "low_conga",
            65: "high_timbale",
            66: "low_timbale",
            67: "high_agogo",
            68: "low_agogo",
            69: "cabasa",
            70: "maracas",
            71: "short_whistle",
            72: "long_whistle",
            73: "short_guiro",
            74: "long_guiro",
            75: "claves",
            76: "high_woodblock",
            77: "low_woodblock",
            78: "mute_cuica",
            79: "open_cuica",
            80: "mute_triangle",
            81: "open_triangle"
        }
        
        # Map friendly names to synthesis functions for easy lookup
        self._drum_type_map = {
            # Basic drum kit
            "bass_drum": "kick",
            "acoustic_bass_drum": "kick",
            "kick": "kick",
            "acoustic_snare": "snare",
            "electric_snare": "snare",
            "snare": "snare",
            "closed_hihat": "closed_hihat",
            "pedal_hihat": "closed_hihat",
            "open_hihat": "open_hihat",
            "crash_cymbal1": "crash",
            "crash_cymbal2": "crash",
            "splash_cymbal": "crash",
            "chinese_cymbal": "crash",
            "ride_cymbal1": "ride",
            "ride_cymbal2": "ride",
            "ride_bell": "ride_bell",
            
            # Toms
            "high_tom": "high_tom",
            "high_mid_tom": "high_mid_tom",
            "low_mid_tom": "low_mid_tom",
            "low_tom": "low_tom",
            "high_floor_tom": "low_tom",
            "low_floor_tom": "very_low_tom",
            
            # Percussion
            "cowbell": "cowbell",
            "claves": "claves",
            "hand_clap": "clap",
            "tambourine": "tambourine",
            "side_stick": "rim_shot",
            "high_bongo": "high_bongo",
            "low_bongo": "low_bongo",
            "mute_high_conga": "mute_conga",
            "open_high_conga": "open_high_conga",
            "low_conga": "low_conga",
            "high_timbale": "high_timbale",
            "low_timbale": "low_timbale",
            "high_agogo": "high_agogo",
            "low_agogo": "low_agogo",
            "cabasa": "cabasa",
            "maracas": "maracas",
            "short_whistle": "short_whistle",
            "long_whistle": "long_whistle",
            "short_guiro": "short_guiro",
            "long_guiro": "long_guiro",
            "high_woodblock": "high_woodblock",
            "low_woodblock": "low_woodblock",
            "mute_cuica": "mute_cuica",
            "open_cuica": "open_cuica",
            "mute_triangle": "mute_triangle",
            "open_triangle": "open_triangle"
        }
    
    def synthesize_midi_percussion(self, note: int, velocity: int, duration: float = 1.0) -> np.ndarray:
        """
        Synthesize percussion instrument based on MIDI note number.
        
        Args:
            note: MIDI note number (35-81 for percussion channel)
            velocity: MIDI velocity (0-127)
            duration: Sound duration in seconds
            
        Returns:
            Synthesized percussion sound as numpy array (16-bit PCM range)
            
        Raises:
            ValueError: If note is not a valid percussion note
        """
        if note not in self.percussion_map:
            raise ValueError(f"Invalid percussion note number: {note}. Valid range is 35-81.")
            
        # Get instrument name from percussion map
        instrument_name = self.percussion_map[note]
        
        # Map to synthesis type
        synthesis_type = self._drum_type_map.get(instrument_name, "kick")  # Default to kick
        
        # Synthesize the percussion sound
        return self.synthesize_drum(synthesis_type, velocity, duration)
    
    def synthesize_drum(self, drum_type: str, velocity: int, 
                      duration: float = 1.0) -> np.ndarray:
        """
        Synthesize a drum or cymbal sound.
        
        Args:
            drum_type: Type of drum ('kick', 'snare', 'hihat', 'tom', etc.)
            velocity: MIDI velocity (0-127)
            duration: Sound duration in seconds
            
        Returns:
            Synthesized drum sound as numpy array (16-bit PCM range)
        """
        # Scale velocity for amplitude
        amp = velocity / 127.0
        
        # Generate sample array
        samples = int(self.sample_rate * duration)
        t = np.arange(samples) / self.sample_rate
        
        if drum_type == 'kick':
            # Kick drum - Sine with pitch envelope + noise attack
            freq_start = 150
            freq_end = 50
            freq = freq_start * np.exp(-7 * t)  # Frequency envelope
            
            # Body component
            body = np.sin(2 * np.pi * np.cumsum(freq / self.sample_rate))
            body_env = np.exp(-5 * t)
            
            # Attack component
            attack = np.random.uniform(-1, 1, samples) * np.exp(-50 * t)
            
            # Combine components
            signal = (body * body_env * 0.8 + attack * 0.2) * amp
            
        elif drum_type == 'snare':
            # Snare - Noise + resonant tone
            # Tone component
            tone_freq = 180
            tone = np.sin(2 * np.pi * tone_freq * t)
            tone_env = np.exp(-15 * t)
            
            # Noise component (snare wires)
            noise = np.random.uniform(-1, 1, samples)
            noise_env = np.exp(-10 * t)
            
            # Combine components
            signal = (tone * tone_env * 0.3 + noise * noise_env * 0.7) * amp
            
        elif drum_type in ['closed_hihat', 'hihat', 'hi-hat']:
            # Hi-hat - Filtered noise with fast decay
            noise = np.random.uniform(-1, 1, samples)
            
            # Apply bandpass filter (simulation)
            noise = self._simple_bandpass(noise, low_cutoff=0.1, high_cutoff=0.8)
            
            # Apply appropriate envelope
            env = np.exp(-30 * t)
            
            signal = noise * env * amp
            
        elif drum_type == 'open_hihat':
            # Open Hi-hat - Similar to closed but with longer decay
            noise = np.random.uniform(-1, 1, samples)
            
            # Apply bandpass filter (simulation)
            noise = self._simple_bandpass(noise, low_cutoff=0.1, high_cutoff=0.8)
            
            # Apply appropriate envelope
            env = np.exp(-8 * t)
            
            signal = noise * env * amp
            
        elif drum_type in ['crash', 'splash_cymbal', 'chinese_cymbal']:
            # Crash cymbal - Complex filtered noise with long decay
            noise = np.random.uniform(-1, 1, samples)
            
            # Enhance high frequencies
            noise_hp = self._simple_highpass(noise, cutoff=0.1)
            
            # Resonant peak simulation
            resonance = np.sin(2 * np.pi * 4000 * t) * np.exp(-2 * t) * 0.1
            
            # Long, complex decay envelope
            env = np.exp(-2 * t)
            
            signal = (noise_hp * env + resonance) * amp
            
        elif drum_type in ['ride', 'ride_cymbal1', 'ride_cymbal2']:
            # Ride cymbal - Higher pitched with more pronounced attack
            noise = np.random.uniform(-1, 1, samples)
            
            # Apply bandpass filter focused on higher frequencies
            noise = self._simple_bandpass(noise, low_cutoff=0.2, high_cutoff=0.9)
            
            # More metallic character with multiple resonances
            resonances = np.zeros_like(t)
            for freq in [3000, 6000, 9000]:
                resonances += np.sin(2 * np.pi * freq * t) * np.exp(-3 * t) * 0.05
                
            # Medium decay envelope with slight modulation
            env = np.exp(-4 * t) * (0.8 + 0.2 * np.sin(2 * np.pi * 8 * t))
            
            signal = (noise * env + resonances) * amp
            
        elif drum_type == 'ride_bell':
            # Ride bell - More focused, pitched sound
            # Generate pitched component with harmonics
            bell_freq = 2000
            bell_tone = np.sin(2 * np.pi * bell_freq * t)
            bell_tone += 0.5 * np.sin(2 * np.pi * bell_freq * 2.1 * t)  # Non-harmonic for bell-like sound
            bell_tone += 0.3 * np.sin(2 * np.pi * bell_freq * 3.3 * t)
            
            # Envelope with long decay
            bell_env = np.exp(-3 * t)
            
            # Small amount of noise
            noise = np.random.uniform(-1, 1, samples) * np.exp(-10 * t) * 0.1
            
            signal = (bell_tone * bell_env + noise) * amp
            
        elif 'tom' in drum_type:
            # Determine tom pitch based on type
            if 'high' in drum_type:
                freq = 200
            elif 'mid' in drum_type:
                freq = 130
            elif 'very_low' in drum_type:
                freq = 80
            else:  # low tom
                freq = 100
                
            # Tom drum - Sine sweep with noise attack
            freq_env = freq * np.exp(-5 * t)  # Frequency envelope
            
            # Body component
            body = np.sin(2 * np.pi * np.cumsum(freq_env / self.sample_rate))
            body_env = np.exp(-4 * t)
            
            # Attack component - less than kick drum
            attack = np.random.uniform(-1, 1, samples) * np.exp(-40 * t) * 0.3
            
            # Combine components
            signal = (body * body_env + attack) * amp
            
        elif drum_type == 'cowbell':
            # Cowbell - Two main resonant frequencies with metallic character
            f1, f2 = 560, 845  # Characteristic cowbell frequencies
            
            # Generate the two main modes
            tone1 = np.sin(2 * np.pi * f1 * t)
            tone2 = np.sin(2 * np.pi * f2 * t)
            
            # Combine with slight detuning for more natural sound
            tone = tone1 + tone2 + 0.2 * np.sin(2 * np.pi * f1 * 1.01 * t)
            
            # Apply envelope
            env = np.exp(-10 * t)  # Sharp attack, medium decay
            
            signal = tone * env * amp
            
        elif drum_type == 'claves':
            # Claves - Short, woody click with specific resonance
            freq = 2500
            
            # Generate main tone
            tone = np.sin(2 * np.pi * freq * t)
            
            # Very short envelope
            env = np.exp(-60 * t)
            
            signal = tone * env * amp
            
        elif drum_type == 'clap':
            # Hand clap - Multiple noise bursts
            noise = np.random.uniform(-1, 1, samples)
            
            # Create multiple attack transients
            env = np.zeros_like(t)
            for delay in [0, 0.005, 0.01, 0.015]:
                idx = int(delay * self.sample_rate)
                if idx < len(env):
                    env[idx:] += np.exp(-30 * (t[:len(env)-idx]))
            
            # Apply bandpass filtering
            filtered_noise = self._simple_bandpass(noise, low_cutoff=0.05, high_cutoff=0.5)
            
            signal = filtered_noise * env * amp
            
        else:
            # Default to simple noise-based percussion
            # Generate filtered noise
            noise = np.random.uniform(-1, 1, samples)
            
            # Apply bandpass filter with midrange focus
            filtered = self._simple_bandpass(noise, low_cutoff=0.1, high_cutoff=0.6)
            
            # Apply envelope - medium attack, medium decay
            env = np.exp(-15 * t)
            
            signal = filtered * env * amp
        
        # Scale to 16-bit PCM range
        return (signal * self.max_value).astype(np.int16)
    
    def _simple_bandpass(self, signal: np.ndarray, low_cutoff: float = 0.1, 
                        high_cutoff: float = 0.5) -> np.ndarray:
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
    
    def create_drum_kit_sample(self, 
                              kit_type: str = 'basic', 
                              sample_rate: int = 44100,
                              duration: float = 1.0) -> Dict[int, np.ndarray]:
        """
        Create a complete set of drum kit samples.
        
        Args:
            kit_type: Type of drum kit ('basic', 'rock', 'electronic')
            sample_rate: Sample rate to use
            duration: Maximum duration for each sample
            
        Returns:
            Dictionary mapping MIDI note numbers to synthesized samples
        """
        # Ensure we use the specified sample rate
        old_sample_rate = self.sample_rate
        self.sample_rate = sample_rate
        
        # Dictionary to hold all drum samples
        drum_samples = {}
        
        # Define velocity based on kit type
        if kit_type == 'rock':
            velocity = 120  # Louder for rock
        elif kit_type == 'electronic':
            velocity = 110  # Medium for electronic
        else:  # basic
            velocity = 100  # Standard
            
        # Generate all percussion samples in the GM map
        for note, name in self.percussion_map.items():
            drum_samples[note] = self.synthesize_midi_percussion(note, velocity, duration)
            
        # Restore original sample rate
        self.sample_rate = old_sample_rate
        
        return drum_samples


# Example usage:
# if __name__ == "__main__":
#     import matplotlib.pyplot as plt
#     from scipy.io.wavfile import write
    
#     # Create synthesizer
#     synth = PercussionSynthesizer(sample_rate=44100)
    
#     # Generate a few drum sounds
#     kick = synth.synthesize_drum("kick", velocity=100)
#     snare = synth.synthesize_drum("snare", velocity=100)
#     hihat = synth.synthesize_drum("closed_hihat", velocity=80)
#     crash = synth.synthesize_drum("crash", velocity=100)
    
#     # Or use MIDI notes directly
#     kick_midi = synth.synthesize_midi_percussion(36, velocity=100)  # Bass drum
#     snare_midi = synth.synthesize_midi_percussion(38, velocity=100)  # Acoustic snare
    
#     # Write to WAV files
#     write("kick.wav", synth.sample_rate, kick)
#     write("snare.wav", synth.sample_rate, snare)
#     write("hihat.wav", synth.sample_rate, hihat)
#     write("crash.wav", synth.sample_rate, crash)
    
    # Create and save a complete drum kit
    # drum_kit = synth.create_drum_kit_sample(kit_type='rock')
    # for note, sample in drum_kit.items():
    #     name = synth.percussion_map[note]
    #     write(f"kit_{name}.wav", synth.sample_rate, sample)