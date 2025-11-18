"""
Main Application Module

Provides high-level interfaces for the audio processing framework.
"""

import numpy as np
from scipy.io.wavfile import read, write
import matplotlib.pyplot as plt
from typing import Optional, Tuple

from .spectral import SpectralAnalyzer
from .midi import MidiParser
from .synthesis import InstrumentSynthesizer


def analyze_audio_file(file_path: str, show_plot: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Analyze an audio file and extract spectral information.
    
    Args:
        file_path: Path to the audio file
        show_plot: Whether to display a spectrogram plot
        
    Returns:
        Tuple of (audio_data, spectral_data)
    """
    # Read the audio file
    sample_rate, audio_data = read(file_path)
    print(f"Analyzing file: {file_path}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio_data.shape}")
    
    # Create analyzer
    analyzer = SpectralAnalyzer(samplefreq=sample_rate)
    
    # Extract left channel (or mono if single channel)
    left_channel = audio_data[:, 0] if len(audio_data.shape) > 1 else audio_data
    
    # Analyze the signal
    real_coefs, imag_coefs, amplitudes = analyzer.analyze(left_channel)
    
    # Apply noise filtering
    filtered_amplitudes = analyzer.filter_noise(amplitudes)
    
    if show_plot:
        plt.figure(figsize=(12, 8))
        plt.imshow(filtered_amplitudes, aspect='auto', origin='lower')
        plt.colorbar(label='Amplitude')
        plt.ylabel('Frequency Index')
        plt.xlabel('Time Frame')
        plt.title('Spectral Analysis')
        plt.tight_layout()
        plt.show()
    
    return audio_data, filtered_amplitudes


def reconstruct_audio(file_path: str, output_path: str, components: int = 50) -> None:
    """
    Analyze and reconstruct an audio file with spectral filtering.
    
    Args:
        file_path: Path to the input audio file
        output_path: Path for the reconstructed audio file
        components: Number of frequency components to keep
    """
    # Read the audio file
    sample_rate, audio_data = read(file_path)
    
    # Create analyzer
    analyzer = SpectralAnalyzer(samplefreq=sample_rate)
    
    # Extract channel data
    if len(audio_data.shape) > 1:
        # Process each channel separately for stereo
        channels = []
        for channel in range(audio_data.shape[1]):
            real_coefs, imag_coefs, amplitudes = analyzer.analyze(audio_data[:, channel])
            reconstructed = analyzer.reconstruct(real_coefs, imag_coefs, amplitudes, components)
            channels.append(reconstructed)
        
        # Combine channels
        result = np.column_stack(channels)
    else:
        # Process mono audio
        real_coefs, imag_coefs, amplitudes = analyzer.analyze(audio_data)
        result = analyzer.reconstruct(real_coefs, imag_coefs, amplitudes, components)
    
    # Write the result
    write(output_path, sample_rate, result)
    print(f"Reconstructed audio saved to {output_path}")


def synthesize_midi_file(midi_path: str, output_path: str) -> None:
    """
    Synthesize audio from a MIDI file.
    
    Args:
        midi_path: Path to the input MIDI file
        output_path: Path for the synthesized audio file
    """
    # Create synthesizer with default settings
    synthesizer = InstrumentSynthesizer()
    
    # Synthesize audio from MIDI
    audio, low_res_spectral, high_res_spectral = synthesizer.synthesize_midi(midi_path)
    
    # Convert float64 to int16
    audio_int = np.clip(audio, -32768, 32767).astype(np.int16)
    
    # Write to file
    write(output_path, synthesizer.signal_processor.sf, audio_int)
    print(f"Synthesized audio saved to {output_path}")
    
    # Display spectrogram
    plt.figure(figsize=(14, 9))
    
    plt.subplot(2, 1, 1)
    plt.imshow(low_res_spectral, aspect='auto', origin='lower')
    plt.colorbar(label='Amplitude')
    plt.title('Low Resolution Spectral Analysis')
    
    plt.subplot(2, 1, 2)
    plt.imshow(high_res_spectral, aspect='auto', origin='lower')
    plt.colorbar(label='Amplitude')
    plt.title('High Resolution Spectral Analysis')
    
    plt.tight_layout()
    plt.show()