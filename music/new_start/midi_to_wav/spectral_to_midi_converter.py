"""
Spectral Analysis for Music Transcription

This module provides tools for analyzing audio signals in the frequency domain 
specifically tailored for converting audio to MIDI data through custom 
Fourier-based frequency analysis.
"""

import numpy as np
from typing import Tuple, Optional, Union, List, Dict, Any
from dataclasses import dataclass


@dataclass
class AnalysisConfig:
    """Configuration parameters for spectral analysis."""
    sample_rate: int = 44100
    cycles: int = 4
    reference_a4: float = 440.0
    note_min: int = -1
    note_max: int = 89
    note_divisions: int = 12  # Divisions per semitone


class SpectralToMIDIConverter:
    """
    Analyzer that decomposes audio signals into musical note frequencies.
    
    This class uses a custom frequency decomposition method specifically
    designed for music transcription by analyzing frequency content at
    semitone and sub-semitone intervals.
    """
    
    def __init__(self, 
                 sample_freq: int = 44100, 
                 cycles: int = 4, 
                 standard_A4: float = 440.0, 
                 note_begin: int = -1, 
                 note_end: int = 89, 
                 increments: int = 12):
        """
        Initialize the spectral analyzer.
        
        Args:
            sample_freq: Sampling frequency in Hz
            cycles: Number of cycles of the lowest frequency to analyze
            standard_A4: Reference frequency for A4 note in Hz
            note_begin: Starting note index (relative to A0)
            note_end: Ending note index (relative to A0)
            increments: Number of increments per semitone
        """
        # Basic parameters
        self.config = AnalysisConfig(
            sample_rate=sample_freq,
            cycles=cycles,
            reference_a4=standard_A4,
            note_min=note_begin,
            note_max=note_end,
            note_divisions=increments
        )
        
        # Derived parameters
        self.sf = sample_freq
        self.A0 = standard_A4 / 16  # Base frequency (A0)
        self.length = cycles / self.A0  # Analysis window length in seconds
        
        # Analysis range
        self.nb = note_begin
        self.ne = note_end
        self.inc = increments
        
        # Initialize frequency tables
        self.freq = None  # Will be set in _initialize_tables
        self.s = None     # Sine table
        self.c = None     # Cosine table
        self.xlen = None  # Window length in samples
        
        # Run initialization
        self._initialize_tables()
    
    def note_to_freq(self, note_idx: float) -> float:
        """
        Convert a MIDI note number to frequency in Hz.
        
        Args:
            note_idx: MIDI note number (can be fractional for microtones)
            
        Returns:
            Frequency in Hz
        """
        return self.A0 * 2 ** (note_idx / 12)
    
    def freq_to_note(self, freq: float) -> float:
        """
        Convert a frequency in Hz to MIDI note number.
        
        Args:
            freq: Frequency in Hz
            
        Returns:
            MIDI note number (can be fractional)
        """
        return 12 * np.log2(freq / self.A0)

    def _generate_frequencies(self) -> np.ndarray:
        """
        Generate array of frequencies for all notes in the analysis range.
        
        Returns:
            Array of frequencies in Hz
        """
        note_indices = np.arange(self.nb, self.ne, 1/self.inc)
        frequencies = np.array([self.note_to_freq(idx) for idx in note_indices])
        return frequencies

    def _generate_time_points(self) -> np.ndarray:
        """
        Generate time points for the analysis window.
        
        Returns:
            Array of time points in seconds
        """
        return np.arange(0, self.length, 1/self.sf)

    def _initialize_tables(self) -> None:
        """Generate sine and cosine tables for all frequencies."""
        time_points = self._generate_time_points()
        self.freq = self._generate_frequencies()
        
        # Vectorized calculation of sine and cosine tables
        # Shape: [n_frequencies, n_timepoints]
        omega = 2 * np.pi * self.freq[:, np.newaxis] * time_points[np.newaxis, :]
        self.s = np.sin(omega)
        self.c = np.cos(omega)
        
        # Store window length
        self.xlen = self.c.shape[1]

    def reshape_signal(self, signal: np.ndarray) -> np.ndarray:
        """
        Reshape signal for analysis, zero-padding if necessary.
        
        Args:
            signal: Input audio signal
            
        Returns:
            Reshaped signal with columns representing analysis windows
        """
        # Ensure signal is 1D and float64
        if len(signal.shape) > 1:
            signal = signal.mean(axis=1)  # Convert stereo to mono if needed
        
        signal = signal.astype(np.float64)
        
        # Calculate padding
        blocks, remainder = divmod(len(signal), self.xlen)
        
        if remainder != 0:
            # Zero-pad if signal length isn't a multiple of window size
            padding = np.zeros(self.xlen - remainder)
            padded_signal = np.hstack((signal, padding))
            return np.reshape(padded_signal, [self.xlen, -1], order='F')
        else:
            return np.reshape(signal, [self.xlen, -1], order='F')
    
    def analyze(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Decompose signal into spectral components at musical note frequencies.
        
        Args:
            signal: Input audio signal
            
        Returns:
            Tuple of (real_coefficients, imaginary_coefficients, amplitudes) arrays
            Each array has shape [n_frequencies, n_windows]
        """
        # Reshape signal for analysis
        reshaped_signal = self.reshape_signal(signal)
        
        # Calculate coefficients using matrix multiplication for efficiency
        real_coefs = np.dot(self.c, reshaped_signal) * (2 / self.xlen)
        imag_coefs = np.dot(self.s, reshaped_signal) * (2 / self.xlen)
        
        # Calculate amplitude spectrum
        amplitudes = np.sqrt(np.square(real_coefs) + np.square(imag_coefs))
        
        return real_coefs, imag_coefs, amplitudes
    
    # Renamed from audio_processing to analyze_audio for consistency
    def analyze_audio(self, audio_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Analyze audio data to extract spectral components.
        
        Args:
            audio_data: Input audio signal
            
        Returns:
            Tuple of (real_coefficients, imaginary_coefficients, amplitudes)
        """
        return self.analyze(audio_data)
    
    # Keep audio_processing as an alias for backward compatibility
    def audio_processing(self, audio_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Alias for analyze_audio() - maintained for backward compatibility.
        """
        return self.analyze_audio(audio_data)
    
    def process_audio_to_midi(self, 
                             audio_data: np.ndarray, 
                             threshold: float = 0.05,
                             combine_notes: bool = True, 
                             quantize: bool = False,
                             tempo: float = 120.0) -> List[Dict[str, Any]]:
        """
        Convert audio data to MIDI events.
        
        Args:
            audio_data: Input audio signal
            threshold: Amplitude threshold for note detection
            combine_notes: Whether to combine consecutive notes of same pitch
            quantize: Whether to quantize note timings to musical grid
            tempo: Tempo in BPM for timing calculations
            
        Returns:
            List of MIDI events as dictionaries
        """
        # Perform spectral analysis
        real_coefs, imag_coefs, amplitudes = self.analyze_audio(audio_data)
        
        # Convert to MIDI (implementation details would go here)
        # This is a placeholder - the actual implementation would be much more complex
        midi_events = []
        
        return midi_events