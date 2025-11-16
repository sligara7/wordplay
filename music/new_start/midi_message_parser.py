"""
MIDI File Parser

This module provides tools for parsing MIDI files into structured dictionaries
for easier analysis and manipulation of musical data.
"""

import mido
from typing import Dict, List, Tuple, Optional, Any, Union


class MidiMessageParser:
    """
    Parse MIDI messages into structured dictionaries for analysis.
    
    This class extracts note events and program changes from MIDI files,
    organizing them by channel, note number, and velocity. It handles
    percussion channels differently and provides timing information.
    
    Reference:
        https://mido.readthedocs.io/en/stable/files/midi.html
    """
    
    def __init__(self, note_offset: int = 21, perc_chan_0: int = 9, perc_chan_1: int = 16, **kwargs):
        """
        Initialize the MIDI parser with configuration parameters.
        
        Args:
            note_offset: Offset value for non-percussion notes (default: 21)
            perc_chan_0: Primary percussion channel number (default: 9, GM standard)
            perc_chan_1: Secondary percussion channel number (default: 16)
            **kwargs: Additional keyword arguments for future extensibility
        """
        self.percussion_channel_1 = perc_chan_0
        self.percussion_channel_2 = perc_chan_1
        self.note_offset = note_offset
        self.midi_link: Optional[str] = None
        self.song_length: float = 0.0
        self.note_min: int = 127
        self.note_max: int = 0
        self.msg: Dict = {}  # Will contain note events by channel and note
        self.inst: Dict = {}  # Will contain program changes by channel

    def init_parse(self) -> None:
        """
        Parse the MIDI file and extract note and program change events.
        
        This method reads the MIDI file specified by self.midi_link and builds 
        dictionaries of note events and program changes. Note events include 
        velocity and timing information.
        
        Structure of self.msg:
        {
            channel: {
                note_number: [
                    [velocity, timestamp],
                    ...
                ],
                ...
            },
            ...
        }
        """
        midi_file = mido.MidiFile(self.midi_link)
        self.msg = {}
        self.inst = {}
        total_time = 0.0
        
        for message in midi_file:
            # Accumulate absolute time
            total_time += message.time
            
            if message.type == 'note_on':
                # Handle percussion channels differently (no note offset)
                if message.channel == self.percussion_channel_1 or message.channel == self.percussion_channel_2:
                    note = message.note 
                else:
                    # Apply note offset for non-percussion channels
                    note = message.note - self.note_offset
                    
                    # Track note range for non-percussion channels
                    if note > self.note_max:
                        self.note_max = note
                    if note < self.note_min:
                        self.note_min = note
            
                # Organize messages by channel and note
                if message.channel in self.msg:
                    if note in self.msg[message.channel]:
                        self.msg[message.channel][note].append([message.velocity, total_time])
                    else:
                        self.msg[message.channel][note] = [[message.velocity, total_time]]
                else:
                    self.msg[message.channel] = {note: [[message.velocity, total_time]]}
                        
            elif message.type == 'program_change': 
                # Track instrument/program changes by channel
                self.inst[message.channel] = message.program
        
        # Store total song duration
        self.song_length = total_time
            
    def velocity_dict(self, note_events: List) -> Dict:
        """
        Transform note events into a structured velocity dictionary.
        
        Takes a list of note velocity/time pairs and organizes them by velocity,
        calculating start time, end time, and next available time for each note.
        
        Args:
            note_events: List of [velocity, time] pairs for a specific note
            
        Returns:
            Dictionary with velocity as key and list of [start_time, end_time, next_available_time] as values
            
        Structure of returned dictionary:
        {
            velocity: [
                [start_time, end_time, next_available_time],
                ...
            ],
            ...
        }
        """
        result = {}
        
        # Process events with even number of elements (note-on/note-off pairs)
        if len(note_events) % 2 == 0:
            for i in range(0, len(note_events), 2):
                # Extract velocity and timing information
                velocity = note_events[i][0]
                start_time = note_events[i][1]
                end_time = note_events[i+1][1]
                
                # Calculate when the next note starts (or song end if this is the last note)
                if len(note_events) - i > 2:
                    next_available_time = note_events[i+2][1]
                else:
                    next_available_time = self.song_length
                
                # Store timing information indexed by velocity
                if velocity in result:
                    result[velocity].append([start_time, end_time, next_available_time])
                else:
                    result[velocity] = [[start_time, end_time, next_available_time]]
        
        # Handle single note events (possibly incomplete MIDI data)
        elif len(note_events) == 1:
            velocity = note_events[0][0]
            start_time = note_events[0][1]  # Use actual timestamp for start time
            
            # For single events, use the same time for start/end and song_length as next available
            result[velocity] = [[start_time, start_time, self.song_length]]
            
        # Handle invalid or empty note sequences
        else:
            # Return placeholder for invalid data
            result[0] = [[0.0, 0.0, 0.0]]
            
        return result
            
    def parse(self, midi_link: str) -> None:
        """
        Main entry point to parse a MIDI file.
        
        Processes the specified MIDI file and organizes its data into structured
        dictionaries accessible as instance attributes.
        
        Args:
            midi_link: Path to the MIDI file to be parsed
            
        After calling this method, the following attributes are populated:
            - self.msg: Dictionary of note events by channel and note
            - self.inst: Dictionary of program changes by channel
            - self.song_length: Total duration of the song in seconds
            - self.note_min: Lowest note number encountered (non-percussion)
            - self.note_max: Highest note number encountered (non-percussion)
        """
        # Reset note range tracking
        self.note_max = 0
        self.note_min = 127
        self.midi_link = midi_link
        
        # Parse the MIDI file
        self.init_parse()
        
        # Process each note's events into structured velocity dictionaries
        for channel in self.msg:
            for note in self.msg[channel]:
                self.msg[channel][note] = self.velocity_dict(self.msg[channel][note])


# Example usage (commented out)
"""
parser = MidiMessageParser()
parser.parse('/path/to/your/midi/file.mid')

# Access the parsed data
instruments = parser.inst
messages = parser.msg
duration = parser.song_length
note_range = (parser.note_min, parser.note_max)

print(f"Song duration: {duration:.2f} seconds")
print(f"Note range: {note_range}")
print(f"Channels with data: {list(messages.keys())}")
"""