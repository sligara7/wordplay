# Modular MIDI Synthesizer Architecture

## Overview

This is a **modular, separation-of-concerns** MIDI synthesizer designed for clarity, maintainability, and extensibility.

Each module has a **single, well-defined responsibility** and can be used independently or composed together.

---

## Architecture Diagram

```
MIDI File
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MIDIParser                                                  │
│ • Reads MIDI files                                          │
│ • Extracts notes, controllers, tempo changes               │
│ • Converts ticks → seconds                                  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ ControllerManager                                           │
│ • Tracks controller state (volume, pan, expression, etc.)  │
│ • Manages pitch bend per channel                           │
│ • Calculates effective velocity                            │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ InstrumentEngine                                            │
│ • Synthesizes individual notes                             │
│ • Family-specific synthesis (piano, organ, brass, etc.)    │
│ • Randomized harmonics (like reco.py)                      │
│ • Piano inharmonicity                                       │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ AudioMixer                                                  │
│ • Mixes notes with proper timing                           │
│ • Applies stereo panning                                    │
│ • Handles overlapping notes                                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ EffectsProcessor                                            │
│ • Reverb (comb filter-based)                               │
│ • Chorus (LFO-modulated delay)                             │
│ • Stereo widening                                           │
│ • Compression                                               │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MasterProcessor                                             │
│ • Soft limiting                                             │
│ • Peak normalization                                        │
│ • Dithering (for 16-bit export)                            │
│ • Audio analysis                                            │
└─────────────────────────────────────────────────────────────┘
    ↓
WAV File
```

---

## Module Descriptions

### 1. `midi_parser.py` - MIDI File Parsing

**Responsibility:** Read MIDI files and extract structured event data

**Input:** MIDI file path

**Output:** Dictionary with notes, controllers, tempo changes, etc.

**Key Methods:**
- `parse_file(midi_path)` → Returns structured dict with all events

**Data Structures:**
```python
{
    'notes': [
        {'channel': 0, 'note': 60, 'velocity': 80, 'start': 0.0, 'duration': 0.5},
        ...
    ],
    'program_changes': [{'time': 0.0, 'channel': 0, 'program': 0}, ...],
    'controllers': [{'time': 0.0, 'channel': 0, 'controller': 7, 'value': 100}, ...],
    'pitch_bends': [{'time': 0.0, 'channel': 0, 'pitch': 0}, ...],
    'tempo_changes': [(tick, tempo_microseconds), ...],
    'duration': 10.5,  # seconds
    'initial_tempo_bpm': 120.0,
    'ticks_per_beat': 480
}
```

---

### 2. `controller_manager.py` - MIDI Controller State

**Responsibility:** Track and manage MIDI controller state for all channels

**Input:** Controller events from parser

**Output:** Current controller values for any channel at any time

**Tracks:**
- Volume (CC 7)
- Pan (CC 10)
- Expression (CC 11)
- Sustain Pedal (CC 64)
- Modulation (CC 1)
- Pitch Bend
- Program Number

**Key Methods:**
- `apply_events(program_changes, controllers, pitch_bends)` - Update state
- `get_state(channel)` → Returns current state dict
- `calculate_effective_velocity(channel, velocity)` → Considers volume/expression
- `calculate_pitch_bend_semitones(channel)` → Convert pitch bend to semitones
- `get_pan_stereo_gains(channel)` → Returns (left_gain, right_gain)

---

### 3. `instrument_engine.py` - Sound Synthesis

**Responsibility:** Generate audio for individual notes

**Input:** MIDI note number, velocity, duration, instrument program

**Output:** Audio waveform for that note

**Features:**
- Supports all General MIDI programs (0-127)
- Family-specific synthesis:
  - **Piano:** Inharmonicity + randomized harmonics
  - **Organ:** Strong octaves (1, 2, 4, 8)
  - **Woodwinds:** Odd harmonics (1, 3, 5, 7, 9)
  - **Brass:** External synthesizer integration
  - **Strings:** External synthesizer integration
  - **Synth:** Bright with many harmonics
- Percussion (channel 9)
- Pitch bend support

**Key Methods:**
- `synthesize_note(midi_note, velocity, duration, program, channel)` → Returns audio array

**Harmonics Approach:**
- Uses randomized harmonics (inspired by reco.py)
- Each note gets cached harmonic structure
- Piano adds inharmonicity: `f_h = freq * h * sqrt(1 + B * h^2)`

---

### 4. `audio_mixer.py` - Note Mixing

**Responsibility:** Mix individual notes into final audio stream

**Input:** List of note events with audio waveforms

**Output:** Mixed stereo (or mono) audio

**Features:**
- Precise timing (sample-accurate)
- Stereo panning
- Overlapping note handling
- Per-channel mixing
- Clipping detection

**Key Methods:**
- `mix_notes(notes, note_audio, total_duration, pan_per_channel, stereo)` → Mixed audio
- `mix_channels_separately(...)` → Per-channel buffers
- `check_clipping(audio)` → Clipping statistics

---

### 5. `effects_processor.py` - Audio Effects

**Responsibility:** Apply audio effects (reverb, chorus, etc.)

**Input:** Dry audio waveform

**Output:** Processed audio with effects

**Effects:**
- **Reverb:** Parallel comb filters + allpass diffusion (Freeverb-inspired)
- **Chorus:** LFO-modulated delay
- **Stereo Widening:** Mid-side processing
- **Compression:** Simple dynamic range compression

**Key Methods:**
- `apply_reverb(audio, room_size, damping, wet)` → Reverbed audio
- `apply_chorus(audio, rate, depth, wet)` → Chorused audio
- `apply_stereo_widening(audio, width)` → Widened stereo
- `apply_compression(audio, threshold, ratio, ...)` → Compressed audio

**Reverb Algorithm:**
```
Input → [Comb Filter 1] ┐
        [Comb Filter 2] ├→ Sum → Allpass Chain → Output
        [Comb Filter 3] │
        [...]          ┘
```

---

### 6. `master_processor.py` - Final Processing

**Responsibility:** Final audio processing and output preparation

**Input:** Mixed audio

**Output:** Mastered audio ready for export

**Features:**
- Soft limiting (tanh-based, prevents harsh clipping)
- Peak normalization
- RMS normalization
- Dithering (TPDF for 16-bit export)
- Audio analysis (peak, RMS, LUFS, dynamic range)
- Format conversion (float32 → int16)

**Key Methods:**
- `master(audio, target_peak, use_limiter, use_dither)` → Mastered audio
- `soft_limit(audio, threshold, ceiling)` → Smooth saturation
- `normalize(audio, target_peak)` → Peak normalization
- `analyze_audio(audio)` → Statistics dict
- `to_int16(audio, apply_dither)` → Convert to int16

---

## Main Orchestrator: `synthesizer.py`

**Purpose:** High-level interface that coordinates all modules

**Usage:**
```python
from modules.synthesizer import MIDISynthesizer

synth = MIDISynthesizer(sample_rate=44100)
audio = synth.synthesize_file('input.mid')
synth.save_wav('output.wav', audio)
```

**Or one-liner:**
```python
synth.synthesize_and_save('input.mid', 'output.wav')
```

**Command-line:**
```bash
python -m modules.synthesizer input.mid output.wav --reverb-wet 0.4 --chorus
```

---

## Design Principles

### 1. **Separation of Concerns**
Each module has ONE responsibility:
- Parser → Parse MIDI
- Controller Manager → Track state
- Instrument Engine → Synthesize notes
- Mixer → Mix with timing
- Effects → Apply effects
- Master → Final processing

### 2. **Single Responsibility Principle**
No module does more than one thing. For example:
- `InstrumentEngine` synthesizes notes but doesn't parse MIDI
- `AudioMixer` mixes notes but doesn't apply effects
- `MasterProcessor` finalizes audio but doesn't synthesize

### 3. **Loose Coupling**
Modules communicate through simple data structures:
- Parser returns a dict (not a complex object)
- Synthesizer returns numpy arrays (standard format)
- No circular dependencies

### 4. **Composability**
You can use modules independently:
```python
# Use just the parser
parser = MIDIParser()
data = parser.parse_file('song.mid')
print(f"Duration: {data['duration']}s")

# Use just the instrument engine
engine = InstrumentEngine()
audio = engine.synthesize_note(60, 80, 1.0)  # Middle C
```

### 5. **Testability**
Each module can be tested in isolation:
```python
# Test instrument engine
def test_piano_inharmonicity():
    engine = InstrumentEngine()
    audio = engine._synth_piano(60, 80, 1.0)
    assert len(audio) == 44100  # 1 second at 44.1kHz
```

---

## Comparison with reco.py

### What reco.py Does Well (Kept)
✅ **Randomized harmonics** - Each note gets unique harmonic structure
✅ **Program change support** - Tracked and used
✅ **Tempo changes** - Full support
✅ **Instrument decay table** - Family-specific behavior

### What Modular Version Adds (New)
✅ **MIDI controllers** - Volume, pan, expression, sustain pedal, pitch bend
✅ **Audio effects** - Reverb, chorus, stereo widening
✅ **Piano inharmonicity** - Physical modeling for realistic piano
✅ **Soft limiting** - Prevents harsh clipping
✅ **Modular architecture** - Easy to maintain and extend
✅ **Clear documentation** - Every module documented

---

## Extension Points

### Adding a New Instrument Family

1. Edit `instrument_engine.py`:
```python
def _synth_new_instrument(self, midi_note, velocity, duration):
    # Custom synthesis here
    ...
    return audio
```

2. Add to dispatch in `synthesize_note()`:
```python
elif family == 'new_family':
    return self._synth_new_instrument(midi_note, velocity, duration)
```

### Adding a New Effect

1. Edit `effects_processor.py`:
```python
def apply_new_effect(self, audio, param1, param2, wet=0.5):
    # Effect algorithm here
    ...
    return audio * (1 - wet) + processed * wet
```

2. Use in `synthesizer.py`:
```python
if self.new_effect_enabled:
    mixed_audio = self.effects.apply_new_effect(mixed_audio, ...)
```

### Adding Real-time Processing

Replace `AudioMixer` with streaming version:
```python
class StreamingMixer:
    def mix_notes_streaming(self, notes, note_audio):
        # Yield chunks instead of returning full array
        for chunk in self._process_chunks():
            yield chunk
```

---

## Performance Characteristics

| Module | Time Complexity | Space Complexity | Notes |
|--------|----------------|------------------|-------|
| MIDIParser | O(events) | O(events) | Linear scan of MIDI file |
| ControllerManager | O(events) | O(channels) | 16 channels max |
| InstrumentEngine | O(duration × sample_rate) | O(duration × sample_rate) | Per note |
| AudioMixer | O(notes × avg_duration) | O(total_duration) | Additive mixing |
| EffectsProcessor | O(samples × filters) | O(delay_samples) | Convolution |
| MasterProcessor | O(samples) | O(samples) | Linear pass |

**Total:** ~O(notes × duration) for full synthesis

---

## File Structure

```
midi_synth/
├── modules/
│   ├── __init__.py                  # Module exports
│   ├── midi_parser.py               # 202 lines - MIDI parsing
│   ├── controller_manager.py        # 175 lines - Controller state
│   ├── instrument_engine.py         # 394 lines - Sound synthesis
│   ├── audio_mixer.py               # 267 lines - Mixing
│   ├── effects_processor.py         # 313 lines - Effects
│   ├── master_processor.py          # 298 lines - Mastering
│   └── synthesizer.py               # 316 lines - Orchestrator
├── example_usage.py                 # Usage examples
├── MODULAR_ARCHITECTURE.md          # This file
├── COMPARISON_WITH_RECO.md          # Comparison with reco.py
└── ENHANCEMENTS.md                  # Enhancement documentation
```

**Total:** ~2,000 lines of well-documented, modular code

---

## Future Enhancements

### Short-term:
- [ ] Pre-rendering/caching (like reco.py) for repeated notes
- [ ] More instrument families (ethnic, sound FX)
- [ ] External sample loading (soundfonts)
- [ ] Multi-band compression

### Medium-term:
- [ ] Real-time synthesis (streaming)
- [ ] MIDI output (audio → MIDI)
- [ ] LFO modulation for vibrato
- [ ] Arpeggiator

### Long-term:
- [ ] VST plugin wrapper
- [ ] Machine learning instrument models
- [ ] Spatial audio (surround sound)
- [ ] Interactive GUI

---

## Usage Examples

See `example_usage.py` for:
1. Simple synthesis
2. Custom effects
3. Modular approach (using components directly)
4. MIDI analysis
5. Dry vs wet comparison

---

## Contributing

When adding features, follow these principles:

1. **One module = One responsibility**
2. **Document all public methods**
3. **Use type hints**
4. **Keep modules under 500 lines** (if growing, split it)
5. **Write examples** in `example_usage.py`

---

## Conclusion

This modular architecture provides:
- ✅ **Clarity** - Each module has one job
- ✅ **Maintainability** - Easy to find and fix bugs
- ✅ **Extensibility** - Add features without breaking existing code
- ✅ **Testability** - Test modules in isolation
- ✅ **Reusability** - Use components independently

**Best MIDI synthesizer** = **Best architecture** + **Best algorithms**

This codebase achieves both! 🎹✨
