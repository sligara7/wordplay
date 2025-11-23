# Modular MIDI Synthesizer

A **professional-grade MIDI synthesizer** built with clean, modular architecture following separation of concerns principles.

## Quick Start

```python
from modules.synthesizer import MIDISynthesizer

# Create synthesizer
synth = MIDISynthesizer(reverb_enabled=True, chorus_enabled=False)

# Synthesize MIDI → WAV
synth.synthesize_and_save('input.mid', 'output.wav')
```

**Command-line:**
```bash
python -m modules.synthesizer input.mid output.wav --reverb-wet 0.3
```

---

## Features

### 🎹 **Instrument Support**
- **All General MIDI instruments** (0-127)
- **Family-specific synthesis:**
  - Piano with inharmonicity (physical modeling)
  - Organ with strong octaves
  - Woodwinds with odd harmonics
  - Brass, strings (with external synthesizer integration)
  - Synth lead/pad with bright harmonics
  - Percussion on channel 9
- **Randomized harmonics** (inspired by reco.py)
- **Pitch bend** support (±2 semitones default)

### 🎛️ **MIDI Controllers**
- Volume (CC 7)
- Pan (CC 10) with constant-power panning
- Expression (CC 11)
- Sustain Pedal (CC 64)
- Modulation (CC 1)
- Pitch bend
- Program changes

### 🎚️ **Audio Effects**
- **Reverb** - Comb filter + allpass diffusion (Freeverb-inspired)
- **Chorus** - LFO-modulated delay
- **Stereo Widening** - Mid-side processing
- **Compression** - Dynamic range control

### 🎼 **Mastering**
- **Soft limiting** - tanh-based smooth saturation
- **Peak normalization**
- **RMS normalization**
- **Dithering** - TPDF for 16-bit export
- **Audio analysis** - Peak, RMS, LUFS, dynamic range

---

## Architecture

### Modular Design - Separation of Concerns

```
┌────────────────┐
│  MIDI Parser   │  Parse MIDI files → structured events
└────────┬───────┘
         ↓
┌────────────────┐
│   Controller   │  Track state (volume, pan, expression, etc.)
│    Manager     │
└────────┬───────┘
         ↓
┌────────────────┐
│   Instrument   │  Synthesize individual notes
│     Engine     │
└────────┬───────┘
         ↓
┌────────────────┐
│  Audio Mixer   │  Mix notes with timing + stereo panning
└────────┬───────┘
         ↓
┌────────────────┐
│    Effects     │  Reverb, chorus, stereo widening
│   Processor    │
└────────┬───────┘
         ↓
┌────────────────┐
│    Master      │  Soft limiting, normalization, dithering
│   Processor    │
└────────┬───────┘
         ↓
    WAV File
```

### Six Independent Modules

| Module | Responsibility | Lines |
|--------|---------------|-------|
| `midi_parser.py` | Parse MIDI files | 202 |
| `controller_manager.py` | Track controller state | 175 |
| `instrument_engine.py` | Synthesize notes | 394 |
| `audio_mixer.py` | Mix with timing | 267 |
| `effects_processor.py` | Apply effects | 313 |
| `master_processor.py` | Final processing | 298 |
| `synthesizer.py` | Orchestrate all modules | 316 |

**Total:** ~2,000 lines of clean, documented code

---

## Installation

### Dependencies

```bash
pip install numpy mido scipy
```

Optional (for external instrument synthesizers):
```bash
# If synthesize_instruments package is available
# (provides brass, strings, percussion synthesis)
```

---

## Usage Examples

### Example 1: Simple Synthesis

```python
from modules.synthesizer import MIDISynthesizer

synth = MIDISynthesizer()
synth.synthesize_and_save('song.mid', 'song.wav')
```

### Example 2: Custom Effects

```python
synth = MIDISynthesizer(reverb_enabled=True, chorus_enabled=True)

audio = synth.synthesize_file(
    'song.mid',
    reverb_wet=0.4,    # More reverb
    chorus_wet=0.3,    # Add chorus
    target_peak=0.90   # Leave headroom
)

synth.save_wav('song_with_effects.wav', audio)
```

### Example 3: Modular Approach (Direct Control)

```python
from modules import (
    MIDIParser, ControllerManager, InstrumentEngine,
    AudioMixer, MasterProcessor
)

# Parse MIDI
parser = MIDIParser()
midi_data = parser.parse_file('song.mid')

# Setup controllers
controller_manager = ControllerManager()
controller_manager.apply_events(
    midi_data['program_changes'],
    midi_data['controllers'],
    midi_data['pitch_bends']
)

# Synthesize notes
engine = InstrumentEngine(sample_rate=44100)
note_audio = {}

for idx, note in enumerate(midi_data['notes']):
    channel = note['channel']
    state = controller_manager.get_state(channel)

    audio = engine.synthesize_note(
        note['note'], note['velocity'], note['duration'],
        program=state['program'], channel=channel
    )
    note_audio[idx] = audio

# Mix
mixer = AudioMixer(sample_rate=44100)
pan_per_channel = {
    ch: controller_manager.get_pan_stereo_gains(ch)
    for ch in range(16)
}

mixed = mixer.mix_notes(
    midi_data['notes'], note_audio, midi_data['duration'],
    pan_per_channel=pan_per_channel, stereo=True
)

# Master
master = MasterProcessor(sample_rate=44100)
final = master.master(mixed, target_peak=0.95, use_limiter=True)

# Analyze
stats = master.analyze_audio(final)
print(f"Peak: {stats['peak_db']:.2f} dB")
print(f"RMS: {stats['rms_db']:.2f} dB")
print(f"Dynamic range: {stats['dynamic_range_db']:.2f} dB")

# Save
import wave
with wave.open('output.wav', 'wb') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(44100)
    audio_int16 = master.to_int16(final)
    wav.writeframes(audio_int16.tobytes())
```

### Example 4: Analyze MIDI Without Synthesizing

```python
from modules import MIDIParser

parser = MIDIParser()
midi_data = parser.parse_file('song.mid')

print(f"Duration: {midi_data['duration']:.2f}s")
print(f"Notes: {len(midi_data['notes'])}")
print(f"Tempo: {midi_data['initial_tempo_bpm']:.2f} BPM")
print(f"Program changes: {len(midi_data['program_changes'])}")
```

---

## Testing

Run the test suite:

```bash
python test_modular_synth.py
```

Expected output:
```
============================================================
MODULAR MIDI SYNTHESIZER - TEST SUITE
============================================================
✓ MIDI Parser test PASSED
✓ Controller Manager test PASSED
✓ Instrument Engine test PASSED
✓ Audio Mixer test PASSED
✓ Effects Processor test PASSED
✓ Master Processor test PASSED
✓ Full Synthesis test PASSED

✓ ALL TESTS PASSED! 🎉
```

---

## Performance

### Speed
- **Synthesis:** ~1-2x realtime (depends on number of notes and effects)
- **Example:** 3-minute song with 500 notes ≈ 3-6 minutes synthesis time
- **Bottlenecks:** Effects (reverb, chorus) use Python loops (future optimization target)

### Optimization Opportunities
1. **Vectorize reverb** - Replace Python loops with numpy operations
2. **Note pre-rendering** - Cache repeated notes (like reco.py)
3. **Parallel synthesis** - Synthesize notes in parallel with multiprocessing
4. **JIT compilation** - Use Numba for hot loops

---

## Comparison with reco.py

### Features from reco.py (Kept) ✅
- Randomized harmonics (each note gets unique character)
- Program change support
- Tempo change handling
- Instrument decay tables

### New Features (Added) ✅
- **MIDI controllers** (volume, pan, expression, sustain, pitch bend)
- **Audio effects** (reverb, chorus)
- **Piano inharmonicity** (physical modeling)
- **Soft limiting** (prevents harsh clipping)
- **Modular architecture** (easy to maintain and extend)
- **Comprehensive documentation**

See `COMPARISON_WITH_RECO.md` for detailed analysis.

---

## Known Limitations

### 1. **Reverb Performance**
- Current reverb implementation uses Python loops (slow for long audio)
- **Workaround:** Disable reverb for quick tests (`reverb_enabled=False`)
- **Fix planned:** Vectorize comb filters using numpy

### 2. **No Sample Loading**
- Uses synthesis only (no soundfont/sample support)
- **Workaround:** External synthesizers can be integrated (brass, strings)
- **Future:** Add SF2 soundfont support

### 3. **Mono → Stereo Only**
- Each note is synthesized in mono, then panned to stereo
- **Future:** Add true stereo synthesis (e.g., piano sympathetic resonance)

---

## File Structure

```
midi_synth/
├── modules/
│   ├── __init__.py                  # Module exports
│   ├── midi_parser.py               # MIDI file parsing
│   ├── controller_manager.py        # Controller state tracking
│   ├── instrument_engine.py         # Sound synthesis
│   ├── audio_mixer.py               # Note mixing
│   ├── effects_processor.py         # Audio effects
│   ├── master_processor.py          # Mastering
│   └── synthesizer.py               # Main orchestrator
├── test_modular_synth.py            # Test suite
├── example_usage.py                 # Usage examples
├── create_test_midi.py              # Create test MIDI files
├── README.md                        # This file
├── MODULAR_ARCHITECTURE.md          # Detailed architecture docs
├── COMPARISON_WITH_RECO.md          # Comparison with reco.py
└── ENHANCEMENTS.md                  # Enhancement documentation
```

---

## Contributing

When adding features, follow these principles:

1. **One module = One responsibility**
2. **Document all public methods**
3. **Use type hints**
4. **Keep modules under 500 lines** (split if growing)
5. **Write examples** in `example_usage.py`
6. **Add tests** in `test_modular_synth.py`

---

## Future Enhancements

### Short-term
- [ ] Vectorize reverb for performance
- [ ] Add note pre-rendering/caching (like reco.py)
- [ ] More instrument families (ethnic, sound FX)
- [ ] Multi-band compression

### Medium-term
- [ ] Real-time synthesis (streaming)
- [ ] Soundfont (SF2) support
- [ ] LFO modulation for vibrato
- [ ] Arpeggiator

### Long-term
- [ ] VST plugin wrapper
- [ ] Machine learning instrument models
- [ ] Spatial audio (surround sound)
- [ ] Interactive GUI

---

## License

[Your License Here]

---

## Credits

Inspired by:
- **reco.py** - Randomized harmonics approach
- **Freeverb** - Reverb algorithm design
- **General MIDI Standard** - Instrument mapping

---

## Contact

[Your Contact Info]

---

**Status:** ✅ All tests passing, ready for production use!

**Best MIDI Synthesizer** = **Best Architecture** + **Best Algorithms** 🎹✨
