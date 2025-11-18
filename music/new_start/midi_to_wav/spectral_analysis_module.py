"""
Spectral Analysis Module

Tools for analyzing audio signals in the frequency domain using
custom implementations of Fourier-like transforms.
"""

import numpy as np
from typing import Tuple, Optional, Union, List


class SpectralAnalyzer:
    """
    Analyze and reconstruct audio signals in the frequency domain.
    
    This class decomposes signals into sine and cosine components across a
    range of musical note frequencies and provides methods to reconstruct
    signals from these components.
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
        self.sf = sample_freq
        self.A0 = standard_A4 / 16  # Base frequency (A0)
        self.length = cycles / self.A0  # Analysis window length in seconds
        self.nb = note_begin
        self.ne = note_end
        self.inc = increments
        self._initialize_tables()
    
    def note_freqs(self, note_idx: float) -> float:
        """
        Calculate frequency for a given note index.
        
        Args:
            note_idx: MIDI note number (can be fractional for microtones)
            
        Returns:
            Frequency in Hz
        """
        return self.A0 * 2 ** (note_idx / 12)

    def _generate_frequencies(self):
        """Generate array of frequencies for all notes in the analysis range."""
        note_indices = np.arange(self.nb, self.ne, 1/self.inc)
        frequencies = [self.note_freqs(idx) for idx in note_indices]
        self.freq = np.array(frequencies)

    def _generate_time_points(self):
        """Generate time points for the analysis window."""
        return np.arange(0, self.length, 1/self.sf)

    def _initialize_tables(self):
        """Generate sine and cosine tables for all frequencies."""
        time_points = self._generate_time_points()
        self._generate_frequencies()
        
        # Generate sine and cosine values for each frequency
        sines = []
        cosines = []
        for frequency in self.freq:
            sines.append(np.sin(2*np.pi*frequency*time_points))
            cosines.append(np.cos(2*np.pi*frequency*time_points))
            
        self.s = np.array(sines)
        self.c = np.array(cosines)
        self.xlen = self.c.shape[1]  # Window length in samples

    def reshape_signal(self, signal: np.ndarray) -> np.ndarray:
        """
        Reshape signal for analysis, zero-padding if necessary.
        
        Args:
            signal: Input audio signal
            
        Returns:
            Reshaped signal with columns representing analysis windows
        """
        blocks, remainder = divmod(signal.shape[0], self.xlen)
        
        if remainder != 0:
            # Zero-pad if signal length isn't a multiple of window size
            padding = np.zeros(self.xlen - remainder)
            padded_signal = np.hstack((signal, padding))
            return np.reshape(padded_signal, [self.xlen, -1], order='F')
        else:
            return np.reshape(signal, [self.xlen, -1], order='F')
    
    def analyze(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Decompose signal into spectral components.
        
        Args:
            signal: Input audio signal
            
        Returns:
            Tuple of (real_coefficients, imaginary_coefficients, amplitudes) arrays
        """
        # Convert signal to float64 and reshape
        reshaped_signal = self.reshape_signal(signal.astype(dtype=np.float64))
        
        # Calculate coefficients
        real_coefs = np.dot(self.c, reshaped_signal) * 2 / self.xlen
        imag_coefs = np.dot(self.s, reshaped_signal) * 2 / self.xlen
        
        # Calculate amplitudes
        amplitudes = np.sqrt(np.square(real_coefs) + np.square(imag_coefs))
        
        return real_coefs, imag_coefs, amplitudes
    
    # def reconstruct(self, 
    #                real_coefs: np.ndarray, 
    #                imag_coefs: np.ndarray, 
    #                amplitudes: np.ndarray, 
    #                num_components: int = 50) -> np.ndarray:
    #     """
    #     Reconstruct audio from spectral components, keeping top components by amplitude.
        
    #     Args:
    #         real_coefs: Real (cosine) coefficients
    #         imag_coefs: Imaginary (sine) coefficients
    #         amplitudes: Amplitude values
    #         num_components: Number of highest amplitude components to keep
            
    #     Returns:
    #         Reconstructed audio signal as int16
    #     """
    #     # Find indices of top amplitudes for each time window
    #     indices = np.argsort(amplitudes, axis=0)[-num_components:, :]
        
    #     # Extract coefficients for top amplitudes
    #     top_real = np.take_along_axis(real_coefs, indices, axis=0)
    #     top_imag = np.take_along_axis(imag_coefs, indices, axis=0)
        
    #     # Initialize output signal
    #     window_size = self.xlen
    #     output = np.zeros(window_size * top_real.shape[1])
        
    #     # Calculate starting positions for each analysis window
    #     start_positions = np.arange(0, output.shape[0], window_size)
    #     start_positions_grid = np.tile(start_positions, [num_components, 1])
        
    #     # Get unique frequency indices
    #     unique_indices = np.unique(indices)
        
    #     # Reconstruct signal for each frequency
    #     for idx in unique_indices:
    #         frequency = self.freq[idx]
            
    #         # Generate sine and cosine basis functions
    #         cosine_wave = np.cos(2 * np.pi * frequency * np.arange(window_size) / self.sf)
    #         sine_wave = np.sin(2 * np.pi * frequency * np.arange(window_size) / self.sf)
            
    #         # Find where this frequency appears in the top components
    #         positions = np.argwhere(indices == idx)
            
    #         # Add weighted components to the output
    #         for m, n in positions:
    #             start_pos = start_positions_grid[m, n]
    #             end_pos = start_pos + window_size
                
    #             # Add weighted components
    #             output[start_pos:end_pos] += (cosine_wave * top_real[m, n] + 
    #                                           sine_wave * top_imag[m, n])
        
    #     # Scale to int16 range if necessary
    #     max_val = np.max(np.abs(output))
    #     if max_val > 32767:
    #         output = output / max_val * 32767
            
    #     return output.astype(np.int16)

    # def filter_noise(self, amplitudes: np.ndarray, std_multiplier: float = 2.0) -> np.ndarray:
    #     """
    #     Filter out noise by thresholding amplitudes.
        
    #     Args:
    #         amplitudes: Spectral amplitudes
    #         std_multiplier: Threshold as multiple of standard deviation above median
            
    #     Returns:
    #         Filtered amplitude array
    #     """
    #     median_value = np.median(amplitudes)
    #     std_value = np.std(amplitudes)
    #     threshold = median_value + std_multiplier * std_value
        
    #     filtered = amplitudes.copy()
    #     filtered[filtered < threshold] = 0
        
    #     return filtered