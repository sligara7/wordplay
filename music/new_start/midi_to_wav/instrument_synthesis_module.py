"""
Audio Synthesis Module

Tools for creating and manipulating audio signals, including 
instrument synthesis based on MIDI data.
"""

import numpy as np
from typing import Dict, Tuple, Optional, List, Union
from spectral_analysis_module import SpectralAnalyzer
from midi_parser import MidiParser
from instrument_lookup import InstrumentLookup

from signal_processing import SignalProcessor


class InstrumentSynthesizer:
    """
    Synthesizes instruments from MIDI data.
    
    This class uses spectral analysis and signal processing to create
    instrument sounds based on MIDI files and perform transformations.
    """
    
    def __init__(self, 
                note_offset: int = 21, 
                sample_freq: int = 44100, 
                perc_chan_0: int = 9, 
                perc_chan_1: int = 16,
                max_value: int = 32767, 
                min_value: int = -32768,
                standard_A4: float = 440.0, 
                note_sec: float = 10.0,
                time_step: float = 1/25,
                max_velocity: int = 127,
                cycles: int = 4,
                increments: int = 12,
                standard_keys: int = 88):
        """
        Initialize the instrument synthesizer.
        
        Args:
            Various parameters controlling the synthesis process
        """
        self.midi_parser = MidiParser(note_offset, perc_chan_0, perc_chan_1)
        self.standard_keys = standard_keys
        
        self.signal_processor = SignalProcessor(
            note_offset, sample_freq, max_value, min_value,
            standard_A4, note_sec, time_step, max_velocity
        )
        
        # Create two spectral analyzers with different frequency resolutions
        self.analyzer_low_res = SpectralAnalyzer(
            sample_freq, cycles, standard_A4, note_begin=0, 
            note_end=standard_keys, increments=1
        )
            
        self.analyzer_high_res = SpectralAnalyzer(
            sample_freq, cycles, standard_A4, note_begin=-1, 
            note_end=standard_keys+1, increments=increments
        )
        
        # Will be populated during processing
        self.song = None
        self.dummy = None
        self.spectral_low_res = None
        self.spectral_high_res = None

    def place_note(self, channel: int, note: int) -> None:
        """
        Place a note in the synthesized audio at the appropriate time.
        
        Args:
            channel: MIDI channel
            note: MIDI note number
        """
        # For each velocity of this note
        for velocity in self.midi_parser.msg[channel][note]:
            # Generate the note signal
            note_signal = self.signal_processor.create_note(
                self.midi_parser.inst[channel], note, velocity
            )
            
            # For each occurrence of this note at this velocity
            for timing in self.midi_parser.msg[channel][note][velocity]:
                # Convert time to sample indices
                start_idx = round(timing[0] * self.signal_processor.sf)
                end_idx = round(timing[1] * self.signal_processor.sf)
                next_avail_idx = round(timing[2] * self.signal_processor.sf)
                
                # Shape the note to fit the time constraints
                shaped_note, end_boundary = self.signal_processor.shape_note(
                    note_signal, start_idx, end_idx, next_avail_idx
                )
                
                # Add the shaped note to the song
                self.song[start_idx:end_boundary, :] += shaped_note[:, np.newaxis]
                
                # Mark the note in the dummy matrix for visualization
                p = divmod(start_idx, self.analyzer_low_res.xlen)
                q = divmod(end_boundary, self.analyzer_low_res.xlen)
                p0 = p[0]
                q0 = q[0]
                self.dummy[note, p0:q0] = 1.0
    
    def synthesize_midi(self, midi_file_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Synthesize audio from a MIDI file.
        
        Args:
            midi_file_path: Path to the MIDI file to synthesize
            
        Returns:
            Tuple of (synthesized_audio, low_res_spectral, high_res_spectral)
        """
        # Parse the MIDI file
        self.midi_parser.parse_file(midi_file_path)
        
        # Initialize output array for the synthesized audio
        song_length = int(self.signal_processor.sf * self.midi_parser.song_length) + 1
        self.song = np.zeros([song_length, 2], dtype=np.float64)
        
        # Initialize dummy matrix for visualization
        self.dummy = self.analyzer_low_res.reshape_signal(self.song[:, 0])[:self.standard_keys, :]
        
        # Process each channel and note
        for channel in self.midi_parser.msg:
            # Skip percussion channels
            if channel == self.midi_parser.percussion_channel_1 or channel == self.midi_parser.percussion_channel_2:
                continue
                
            # Process each note in this channel
            for note in self.midi_parser.msg[channel]:
                self.place_note(channel, note)
        
        # Scale the output signal
        self.song = self.signal_processor.scale(self.song)
        
        # Perform spectral analysis on the synthesized audio
        low_res_spectral = []
        high_res_spectral = []
        
        for channel in range(self.song.shape[1]):
            # Analyze with low resolution
            real, imag, amp = self.analyzer_low_res.analyze(self.song[:, channel])
            low_res_spectral.append(amp)
            
            # Analyze with high resolution
            real, imag, amp = self.analyzer_high_res.analyze(self.song[:, channel])
            high_res_spectral.append(amp)
        
        # Calculate maximum amplitudes across channels
        self.spectral_low_res = np.max(np.stack(low_res_spectral), axis=0)
        self.spectral_low_res = self.spectral_low_res * self.dummy  # Apply note mask
        
        self.spectral_high_res = np.max(np.stack(high_res_spectral), axis=0)
        
        return self.song, self.spectral_low_res, self.spectral_high_res