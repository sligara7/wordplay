"""
Spectral analysis of audio signals using sine/cosine decomposition.

This module provides tools to analyze audio signals by decomposing them
into frequency components using a custom Fourier-like analysis.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import read


class SpectralAnalyzer:
    """
    Analyze signals by decomposing them into frequency components.
    
    This class implements techniques similar to Fourier analysis, calculating
    the spectral content of audio signals across a range of musical notes.
    """
    
    def __init__(self, 
                 samplefreq=44100, 
                 cycles=4, 
                 standard_A4=440.0, 
                 note_begin=-1, 
                 note_end=89, 
                 increments=12):
        """
        Initialize the spectral analyzer with musical parameters.
        
        Args:
            samplefreq (int): Sample frequency in Hz (default: 44100)
            cycles (int): Number of cycles to analyze (default: 4)
            standard_A4 (float): Frequency of A4 note in Hz (default: 440.0)
            note_begin (int): Starting note index, where 0 is A0 (default: -1)
            note_end (int): Ending note index (default: 89)
            increments (int): Subdivisions per semitone (default: 12)
        """
        self.sample_freq = samplefreq
        self.A0_freq = standard_A4 / 16  # Calculate A0 frequency from A4
        self.analysis_length = cycles / self.A0_freq  # Duration to analyze in seconds
        self.note_begin = note_begin
        self.note_end = note_end
        self.increments = increments
        
        # Build analysis tables
        self.table()
        self.window_length = self.cosine_table.shape[1]  # Length of analysis window in samples
    
    def note_freqs(self, note_idx):
        """
        Calculate frequency for a given note index.
        
        Args:
            note_idx (float): Note index, where 0 is A0, 12 is A1, etc.
                             Can be fractional for microtones.
                             
        Returns:
            float: Frequency in Hz
        """
        return self.A0_freq * 2 ** (note_idx / 12)

    def note_index(self):
        """
        Generate frequencies for all notes in the specified range.

        Creates an array of frequencies based on the note range and
        increments specified in the constructor.
        """
        # Create array of note indices with microtonal resolution
        # Offset by 0.5/increments to center bins on note frequencies
        note_indices = np.arange(self.note_begin - 0.5/self.increments, self.note_end, 1/self.increments)
        
        # Convert note indices to frequencies
        frequencies = []
        for note_idx in note_indices:
            frequencies.append(self.note_freqs(note_idx))
            
        self.frequencies = np.array(frequencies)

    def xinc(self):
        """
        Generate time points for the analysis window.
        
        Returns:
            numpy.ndarray: Array of time points in seconds
        """
        return np.arange(0, self.analysis_length, 1/self.sample_freq)

    def table(self):
        """
        Generate tables of sine and cosine values for all frequencies.
        
        Builds lookup tables for faster spectral analysis.
        """
        time_points = self.xinc()
        self.note_index()
        
        sine_waves = []
        cosine_waves = []
        
        # Generate sine and cosine waves for each frequency
        for frequency in self.frequencies:
            sine_waves.append(np.sin(2*np.pi*frequency*time_points))    
            cosine_waves.append(np.cos(2*np.pi*frequency*time_points))
            
        # Store as numpy arrays for efficient computation
        self.cosine_table = np.array(cosine_waves)
        self.sine_table = np.array(sine_waves)

    def stacksig(self, signal):
        """
        Reshape input signal for analysis, zero-padding if necessary.
        
        Args:
            signal (numpy.ndarray): Input audio signal
            
        Returns:
            numpy.ndarray: Reshaped signal in columns for efficient processing
        """
        # Calculate how many analysis windows fit in the signal
        blocks, remainder = divmod(signal.shape[0], self.window_length)
        
        if remainder != 0:
            # If signal doesn't align with window size, zero-pad the end
            padding = np.zeros(self.window_length - remainder)
            padded_signal = np.hstack((signal, padding))
            # Reshape to have each analysis window as a column
            return np.reshape(padded_signal, [self.window_length, -1], order='F')
        else:
            # Signal aligns perfectly with window size
            return np.reshape(signal, [self.window_length, -1], order='F')
    
    def dotop(self, signal):
        """
        Decompose signal into spectral components.
        
        This method performs spectral analysis on the input signal,
        computing amplitude values for each frequency in the analysis range.
        
        Args:
            signal (numpy.ndarray): Input audio signal
            
        Returns:
            numpy.ndarray: 2D array of spectral amplitudes [frequency, time]
        """
        # Convert signal to float64 and reshape for analysis
        reshaped_signal = self.stacksig(signal.astype(dtype=np.float64))
        
        # Calculate real (cosine) coefficients
        real_coefs = np.dot(self.cosine_table, reshaped_signal) * 2 / self.window_length
        
        # Calculate imaginary (sine) coefficients
        imag_coefs = np.dot(self.sine_table, reshaped_signal) * 2 / self.window_length
        
        # Compute magnitude (amplitude) of spectral components
        amplitudes = np.sqrt(np.square(real_coefs) + np.square(imag_coefs))
        
        return amplitudes


def analyze_audio_file(file_path):
    """
    Analyze an audio file and visualize its spectral content.
    
    Args:
        file_path (str): Path to the audio file
    """
    # Read audio file
    sample_rate, audio_data = read(file_path)
    print(f"Analyzing file: {file_path}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio_data.shape}")
    
    # Create spectral analyzer
    analyzer = SpectralAnalyzer(samplefreq=sample_rate)
    
    # Analyze left channel (or mono if single channel)
    left_channel = audio_data[:, 0] if len(audio_data.shape) > 1 else audio_data
    left_spectrum = analyzer.dotop(left_channel)
    
    # If stereo, analyze right channel
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        right_spectrum = analyzer.dotop(audio_data[:, 1])
    
    # Visualize the spectrum of the left channel
    plt.figure(figsize=(12, 8))
    plt.imshow(left_spectrum, aspect='auto', origin='lower', 
               extent=[0, left_spectrum.shape[1], 0, len(analyzer.frequencies)])
    plt.colorbar(label='Amplitude')
    plt.ylabel('Frequency Index')
    plt.xlabel('Time Frame')
    plt.title('Spectral Analysis')
    plt.tight_layout()
    plt.show()
    
    return analyzer, left_spectrum


if __name__ == "__main__":
    # Example usage
    file_path = '/home/ajs7/Music/CdL.wav'
    analyzer, spectrum = analyze_audio_file(file_path)
    
    # Additional test code (commented out)
    """
    # Test with a synthetic signal
    x = np.arange(0, 7, 1/44100)
    
    # Create a sine wave at A0 * 8 frequency (220 Hz)
    q = np.sin(2*np.pi*27.5*8*x)
    
    # Scale to 16-bit audio range
    q[q>0] = q[q>0] * 32767
    q[q<0] = q[q<0] * 32768
    
    # Analyze this test signal
    r = analyzer.dotop(q)
    """