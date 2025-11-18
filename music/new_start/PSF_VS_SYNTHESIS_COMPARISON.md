# PSF Templates vs Chords.py: Synthesis vs Detection

## Overview

This document compares two different approaches to chord generation:
1. **chords.py**: Audio synthesis for MIDI→WAV playback
2. **PSF Templates**: Spectral signatures for matched-filter chord detection

---

## chords.py - SYNTHESIS (MIDI→WAV)

### Purpose
Generate playable audio waveforms for chord playback and synthesis.

### Method
```python
# Example: Major chord generation
majorchord = []
for ii in range(0, len(freq)-7):  # EVERY semitone position!
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:]  # Root + Major3rd + Perfect5th
    majorchord.append(d)
# Convert to playable waveform via mf.wave_array()
```

### Coverage
- **Frequency range**: Every semitone position across the entire frequency spectrum
- **Typical count**: ~1000+ positions (e.g., A0 to C8)
- **Root notes**: ALL semitones (not just 12 chromatic notes)
- **Octaves**: ALL octaves in the audible range

### Output
- **Type**: Time-domain audio waveforms
- **Format**: 1D array of audio samples
- **Use**: Can be played, saved as WAV, used for synthesis

### Chord Types (11 types)
```python
major:    [0, 4, 7]
minor:    [0, 3, 7]
dim:      [0, 3, 6]
maj7:     [0, 4, 7, 11]
min7:     [0, 3, 7, 10]
dom7:     [0, 4, 7, 10]
sus2:     [0, 2, 7]
sus4:     [0, 5, 7]
aug:      [0, 4, 8]
dom9:     [0, 4, 7, 10, 14]
maj11:    [0, 4, 7, 11, 14, 17]
```

### Applications
- MIDI playback
- Audio synthesis
- Sound generation
- Music production
- Testing/validation (generate known chords)

---

## PSF Templates - DETECTION (WAV→MIDI)

### Purpose
Generate spectral signatures for matched-filter chord detection/recognition.

### Method
```python
# Generate pure sinusoids → Analyze with spectral_analyzer → Use as template
def generate_chord_psf_via_analyzer(root_note, chord_type, octave=4):
    # 1. Generate pure chord audio
    chord_audio = generate_pure_chord_audio(root_note, chord_type, octave)

    # 2. Run through spectral analyzer (this is the KEY step!)
    analyzer = SpectralAnalyzer(samplefreq=44100, cycles=4)
    spectral_data = analyzer.dotop(chord_audio)

    # 3. Average and normalize
    psf = np.mean(spectral_data, axis=1)
    psf = psf / np.linalg.norm(psf)

    return psf  # This is the "Point Spread Function" for this chord
```

### Coverage
- **Root notes**: 12 chromatic notes (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
- **Octave**: Single octave (octave 4)
- **Total templates**: 132 (12 roots × 11 chord types)

### Output
- **Type**: Frequency-domain spectral templates
- **Format**: 1D array of normalized spectral amplitudes (1081 frequency bins)
- **Use**: Matched-filter correlation for chord detection

### Chord Types (Same 11 types as chords.py)
```python
CHORD_INTERVALS = {
    'major':     [0, 4, 7],
    'minor':     [0, 3, 7],
    'dim':       [0, 3, 6],
    'aug':       [0, 4, 8],
    'sus2':      [0, 2, 7],
    'sus4':      [0, 5, 7],
    'maj7':      [0, 4, 7, 11],
    'min7':      [0, 3, 7, 10],
    'dom7':      [0, 4, 7, 10],
    'dom9':      [0, 4, 7, 10, 14],
    'maj11':     [0, 4, 7, 11, 14, 17],
}
```

### Applications
- Chord detection/recognition
- Audio-to-MIDI transcription
- Real-time chord analysis
- Music information retrieval
- Signal processing

---

## Key Differences

| Aspect | chords.py (Synthesis) | PSF Templates (Detection) |
|--------|----------------------|---------------------------|
| **Purpose** | Generate playable audio | Detect/recognize chords |
| **Domain** | Time domain (waveforms) | Frequency domain (spectra) |
| **Coverage** | ~1000+ semitone positions | 132 templates (12 roots × 11 types) |
| **Octaves** | All octaves (A0-C8) | Single octave (octave 4) |
| **Output** | Audio samples | Spectral templates |
| **Direction** | MIDI → WAV | WAV → MIDI |
| **Use case** | Playback, synthesis | Recognition, transcription |
| **Representation** | Amplitude vs time | Amplitude vs frequency |

---

## Coverage Question: "Have we created every chord for every possible note PSF?"

### Short Answer
**YES** for the 12 chromatic root notes in octave 4.
**NO** for every semitone position across all octaves.

### Detailed Answer

**What we HAVE created (PSF templates)**:
- ✓ All 12 chromatic roots: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
- ✓ All 11 common chord types
- ✓ Total: 132 templates
- ✓ Octave: 4 only

**What chords.py HAS created (synthesis)**:
- ✓ All semitone positions across entire frequency range
- ✓ All 11 chord types
- ✓ Total: ~1000+ waveforms
- ✓ Octaves: All (A0 to C8)

### Do we NEED PSF templates for every octave?

**Probably NOT**, for these reasons:

1. **Harmonic structure is octave-invariant**
   - C3 major and C4 major have the same interval relationships
   - The spectral template will have peaks at different absolute frequencies, but similar harmonic ratios

2. **Spectral analyzer may capture harmonics**
   - If the analyzer includes harmonics, a C4 template might detect C3 chords (octave below has 2x harmonics)
   - Need to test this empirically

3. **Real music typically stays in mid-range**
   - Most chords in real music occur in octaves 2-5
   - Creating templates for octaves 3-5 would cover 95% of real-world cases

4. **Current test results (100% accuracy)**
   - Our tests used octave 4 templates to detect octave 4 chords
   - This worked perfectly (396/396 correct)
   - But we haven't tested cross-octave detection yet

---

## Next Steps

### Testing Needed
1. **Test cross-octave detection**
   - Generate C3 major chord → Test with C4 major PSF template
   - Generate C5 major chord → Test with C4 major PSF template
   - Determine if detector is naturally octave-invariant

2. **Test on real audio**
   - Current 100% accuracy is on pure sinusoids
   - Need to test on real instrument recordings
   - Need to test on polyphonic music

3. **Determine optimal octave coverage**
   - If cross-octave detection fails, generate templates for octaves 3, 4, 5
   - This would give 396 templates (12 × 11 × 3)

### Integration Paths

**Option A: Single-octave detector (current)**
- Use 132 templates (octave 4 only)
- Assume octave-invariance or accept octave-limited detection
- Fast and simple

**Option B: Multi-octave detector**
- Generate templates for octaves 2, 3, 4, 5
- Total: 528 templates (12 × 11 × 4)
- More robust but 4x slower

**Option C: Octave-normalized detection**
- Pre-process input spectrum to be octave-invariant
- Use 132 templates
- Requires additional signal processing

---

## Test Results Summary

### PSF Template Generation
```
Sample rate: 44100 Hz
Cycles: 4
Octave: 4
Chord types: 11
Root notes: 12
Total templates: 132

Frequency bins: 1081
Frequency range: 25.89 - 4687.34 Hz

Template generation time: 46.51 seconds
```

### Detection Accuracy (Comprehensive Test)
```
Total tests:        396 (11 types × 12 roots × 3 runs)
Detected:           396 (100.0%)
Correct:            396 (100.0%)
Accuracy:           100.0%
Repeatability:      132/132 (100.0%)

Testing time:       17.07 seconds
Rate:               23 tests/sec
```

### Per Chord Type Accuracy
```
Chord Type    Notes   Total  Correct   Accuracy    Avg SNR    SNR Std
--------------------------------------------------------------------------------
major             3      36       36     100.0%      33.05       0.15
minor             3      36       36     100.0%      32.98       0.15
dim               3      36       36     100.0%      33.04       0.13
aug               3      36       36     100.0%      32.97       0.13
sus2              3      36       36     100.0%      33.07       0.14
sus4              3      36       36     100.0%      33.06       0.14
maj7              4      36       36     100.0%      32.94       0.16
min7              4      36       36     100.0%      32.92       0.17
dom7              4      36       36     100.0%      32.95       0.15
dom9              5      36       36     100.0%      32.90       0.13
maj11             6      36       36     100.0%      32.86       0.12
```

**Key observation**: SNR decreases slightly with chord complexity (33.05 for major → 32.86 for maj11), but all well above threshold (6.5).

---

## Conclusion

**Synthesis (chords.py)** and **Detection (PSF templates)** serve complementary purposes:

1. **chords.py** creates ~1000+ playable waveforms for synthesis
2. **PSF templates** create 132 spectral signatures for detection

We have created a **complete set of PSF templates for chord detection** covering all 12 chromatic roots and 11 chord types. This achieves **100% accuracy** on pure sinusoid tests.

The question of whether we need templates for every octave (like chords.py creates waveforms for every octave) remains **open** and requires empirical testing on real audio data.

**Recommendation**: Test cross-octave detection first before generating additional templates.
