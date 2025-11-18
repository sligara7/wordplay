"""
General MIDI instrument and percussion definitions.

This module provides lookup tables and utilities for working with 
standard General MIDI instruments and percussion sounds.
"""

from typing import Tuple, Dict, Optional, Union


class InstrumentLookup:
    """
    Provides information about General MIDI instruments and percussion sounds.
    
    This class contains static lookup tables for standard GM instruments (programs 1-128)
    and percussion instruments (notes 35-81 on channel 10).
    """
    
    @classmethod
    def get_instrument_info(cls, program: int) -> Tuple[str, bool, bool]:
        """
        Get information about a General MIDI instrument.
        
        Args:
            program: GM instrument program number (1-128)
            
        Returns:
            Tuple of (instrument_name, has_decay, decay_interruptible)
        """
        # Return default values for missing or invalid program numbers
        if program not in cls.INSTRUMENTS:
            return ("unknown instrument", False, False)
            
        return cls.INSTRUMENTS[program]
    
    @classmethod
    def get_percussion_info(cls, note: int) -> Tuple[str, bool, bool]:
        """
        Get information about a General MIDI percussion instrument.
        
        Args:
            note: MIDI note number (35-81) for percussion sounds on channel 10
            
        Returns:
            Tuple of (instrument_name, has_decay, decay_interruptible)
        """
        # Return default values for missing or invalid note numbers
        if note not in cls.PERCUSSION_INSTRUMENTS:
            return ("unknown percussion", True, False)
            
        return cls.PERCUSSION_INSTRUMENTS[note]
    
    @classmethod
    def is_percussion_channel(cls, channel: int) -> bool:
        """
        Check if a MIDI channel is the standard percussion channel.
        
        Args:
            channel: MIDI channel number (0-15)
            
        Returns:
            True if the channel is the standard percussion channel (9 in zero-based indexing)
        """
        # Channel 10 in MIDI spec is 9 in zero-indexed systems
        return channel == 9
    
    # General MIDI Level 2 instruments with properties
    # Format: {program_number: (name, has_decay, decay_interruptible)}
    INSTRUMENTS = {
        1: ('acoustic grand piano', True, True),
        2: ('bright acoustic piano', True, True),
        3: ('electric grand piano', False, True),
        4: ('honky-tonk piano', True, True),
        5: ('electric piano 1', False, True),
        6: ('electric piano 2', False, True),
        7: ('harpsichord', True, True),
        8: ('clavinet', False, True),
        9: ('celesta', True, True),
        10: ('glockenspiel', True, True),
        11: ('music box', True, True),
        12: ('vibraphone', True, True),
        13: ('marimba', True, True),
        14: ('xylophone', True, True),
        15: ('tubular bells', True, True),
        16: ('dulcimer/santur', True, True),
        17: ('drawbar organ', False, True),
        18: ('percussive organ', False, True),
        19: ('rock organ', False, True),
        20: ('church organ', False, True),
        21: ('reed organ', False, True),
        22: ('accordion', False, False),
        23: ('harmonica', False, False),
        24: ('bandoneon', False, False),
        25: ('nylon string guitar', False, False),
        26: ('steel string guitar', False, False),
        27: ('jazz guitar', False, False),
        28: ('clean electric guitar', True, False),
        29: ('muted electric guitar', False, False),
        30: ('overdriven guitar', False, False),
        31: ('distortion guitar', False, False),
        32: ('guitar harmonics', True, False),
        33: ('acoustic bass', True, False),
        34: ('fingered bass', True, False),
        35: ('picked bass', True, False),
        36: ('fretless bass', True, False),
        37: ('slap bass 1', True, False),
        38: ('slap bass 2', True, False),
        39: ('synth bass 1', False, True),
        40: ('synth bass 2', False, True),
        41: ('violin', False, False),
        42: ('viola', False, False),
        43: ('cello', False, False),
        44: ('contrabass', False, False),
        45: ('tremolo strings', False, False),
        46: ('pizzicato strings', True, False),
        47: ('harp', True, True),
        48: ('timpani', True, False),
        49: ('string ensemble 1', False, False),
        50: ('string ensemble 2', False, False),
        51: ('synth strings 1', False, False),
        52: ('synth strings 2', False, False),
        53: ('choir aahs', False, False),
        54: ('voice oohs', False, False),
        55: ('synth voice', False, False),
        56: ('orchestra hit', False, False),
        57: ('trumpet', False, False),
        58: ('trombone', False, False),
        59: ('tuba', False, False),
        60: ('muted trumpet', False, False),
        61: ('french horn', False, False),
        62: ('brass section', False, False),
        63: ('synth brass 1', False, False),
        64: ('synth brass 2', False, False),
        65: ('soprano saxophone', False, False),
        66: ('alto saxophone', False, False),
        67: ('tenor saxophone', False, False),
        68: ('baritone saxophone', False, False),
        69: ('oboe', False, False),
        70: ('english horn', False, False),
        71: ('bassoon', False, False),
        72: ('clarinet', False, False),
        73: ('piccolo', False, False),
        74: ('flute', False, False),
        75: ('recorder', False, False),
        76: ('pan flute', False, False),
        77: ('blown bottle', False, False),
        78: ('shakuhachi', False, False),
        79: ('whistle', False, False),
        80: ('ocarina', False, False),
        81: ('square lead', False, False),
        82: ('sawtooth lead', False, False),
        83: ('calliope lead', False, False),
        84: ('chiffer lead', False, False),
        85: ('charang', True, False),
        86: ('voice lead', False, False),
        87: ('fifths lead', False, False),
        88: ('bass & lead', True, False),
        89: ('new age pad', True, True),
        90: ('warm pad', True, True),
        91: ('polysynth pad', False, True),
        92: ('choir pad', False, True),
        93: ('bowed pad', False, True),
        94: ('metallic pad', True, True),
        95: ('halo pad', False, True),
        96: ('sweep pad', False, True),
        97: ('rain effect', True, False),
        98: ('soundtrack effect', False, True),
        99: ('crystal effect', True, True),
        100: ('atmosphere effect', False, True),
        101: ('brightness effect', False, True),
        102: ('goblins effect', False, False),
        103: ('echoes effect', False, True),
        104: ('sci-fi effect', False, True),
        105: ('sitar', True, False),
        106: ('banjo', True, False),
        107: ('shamisen', True, False),
        108: ('koto', True, False),
        109: ('kalimba', True, True),
        110: ('bagpipe', False, False),
        111: ('fiddle', False, False),
        112: ('shanai', False, False),
        113: ('tinkle bell', True, True),
        114: ('agogo', True, False),
        115: ('steel drums', True, True),
        116: ('woodblock', True, False),
        117: ('taiko drum', True, False),
        118: ('melodic tom', True, False),
        119: ('synth drum', True, False),
        120: ('reverse cymbal', True, False),
        121: ('guitar fret noise', True, False),
        122: ('breath noise', True, False),
        123: ('seashore', False, True),
        124: ('bird tweet', False, False),
        125: ('telephone ring', False, False),
        126: ('helicopter', False, True),
        127: ('applause', False, True),
        128: ('gunshot', True, False)
    }
    
    # General MIDI percussion instruments (used on channel 10)
    # Format: {note_number: (name, has_decay, decay_interruptible)}
    PERCUSSION_INSTRUMENTS = {
        35: ('acoustic bass drum', True, False),
        36: ('bass drum', True, False),
        37: ('side stick', True, False),
        38: ('acoustic snare', True, False),
        39: ('hand clap', True, False),
        40: ('electric snare', True, False),
        41: ('low floor tom', True, False),
        42: ('closed hi-hat', True, False),
        43: ('high floor tom', True, False),
        44: ('pedal hi-hat', True, False),
        45: ('low tom', True, False),
        46: ('open hi-hat', True, False),
        47: ('low-mid tom', True, False),
        48: ('hi-mid tom', True, False),
        49: ('crash cymbal 1', True, False),
        50: ('high tom', True, False),
        51: ('ride cymbal 1', True, False),
        52: ('chinese cymbal', True, False),
        53: ('ride bell', True, False),
        54: ('tambourine', True, False),
        55: ('splash cymbal', True, False),
        56: ('cowbell', True, False),
        57: ('crash cymbal 2', True, False),
        58: ('vibraslap', True, False),
        59: ('ride cymbal 2', True, False),
        60: ('hi bongo', True, False),
        61: ('low bongo', True, False),
        62: ('mute hi conga', True, False),
        63: ('open hi conga', True, False),
        64: ('low conga', True, False),
        65: ('high timbale', True, False),
        66: ('low timbale', True, False),
        67: ('high agogo', True, False),
        68: ('low agogo', True, False),
        69: ('cabasa', True, False),
        70: ('maracas', True, False),
        71: ('short whistle', False, False),
        72: ('long whistle', False, False),
        73: ('short guiro', True, False),
        74: ('long guiro', True, False),
        75: ('claves', True, False),
        76: ('hi wood block', True, False),
        77: ('low wood block', True, False),
        78: ('mute cuica', False, False),
        79: ('open cuica', False, False),
        80: ('mute triangle', True, False),
        81: ('open triangle', True, False)
    }


# Example usage
if __name__ == "__main__":
    # Get info about a melodic instrument
    piano_info = InstrumentLookup.get_instrument_info(1)
    print(f"Instrument #1: {piano_info[0]}, has decay: {piano_info[1]}")
    
    # Get info about a percussion instrument
    snare_info = InstrumentLookup.get_percussion_info(38)
    print(f"Percussion #38: {snare_info[0]}, has decay: {snare_info[1]}")