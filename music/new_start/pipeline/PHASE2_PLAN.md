# Phase 2: Melody Extraction

## Goals

Extract pitch information from audio to identify which notes are being played.

### Success Criteria

1. **Pitch Accuracy > 95%** - Correctly identify MIDI note number within ±1 semitone
2. **Octave Accuracy > 99%** - Rarely make octave errors (common failure mode)
3. **Works on real piano** - Tested on Iowa and other real recordings

### Scope

- **Start with monophonic** (single note at a time) - easier to validate
- **Extend to polyphonic** (multiple notes) later if needed
- **Focus on piano** - percussive instrument with clear attack and harmonic structure

## Background: Pitch Detection Methods

### 1. Time-Domain Methods

**Autocorrelation**
- Find repeating patterns in the waveform
- Peak at lag = period → frequency = sample_rate / lag
- Pros: Simple, works well for clear periodic signals
- Cons: Can confuse fundamental with harmonics (octave errors)

**YIN / PYIN**
- Improved autocorrelation with better octave error handling
- Industry standard for monophonic pitch tracking
- Pros: Very accurate, handles vibrato well
- Cons: More complex, slower

### 2. Frequency-Domain Methods

**FFT Peak Detection**
- Find peaks in frequency spectrum
- Fundamental = lowest significant peak
- Pros: Fast, intuitive
- Cons: Needs harmonic filtering to avoid octave errors

**Harmonic Product Spectrum (HPS)**
- Downsample spectrum by 2x, 3x, 4x and multiply together
- Fundamental frequency peak is reinforced
- Pros: Good at finding true fundamental
- Cons: Can still make errors on complex timbres

**Cepstrum Analysis**
- FFT of log(FFT) - finds periodicity in spectrum
- Peak in quefrency domain = fundamental period
- Pros: Robust to harmonics
- Cons: More complex, harder to tune

## Recommended Approach for Phase 2

### Hybrid: Spectral Peak + Harmonic Validation

We'll use a multi-step approach that leverages our existing spectral analysis:

1. **Spectral Peak Detection** - Find prominent frequencies in each time slice
2. **Harmonic Analysis** - Check if detected peaks form harmonic series
3. **Fundamental Selection** - Identify the true fundamental (not a harmonic)
4. **Pitch Tracking** - Smooth pitch estimates over time

### Why This Approach?

- **Builds on existing code** - Uses spectral_analyzer.py output
- **Graph-friendly** - Can represent pitch candidates as nodes
- **Interpretable** - Easy to debug and visualize
- **Accurate** - Harmonic validation reduces octave errors

## Implementation Plan

### Step 1: Spectral Peak Detection

Extract peaks from spectrum for each time slice:

```python
def find_spectral_peaks(spectrum, frequencies, min_prominence=0.1):
    """Find significant peaks in spectrum."""
    peaks, properties = find_peaks(
        spectrum,
        prominence=min_prominence * np.max(spectrum),
        distance=5  # Minimum frequency separation
    )
    peak_freqs = frequencies[peaks]
    peak_mags = spectrum[peaks]
    return peak_freqs, peak_mags
```

### Step 2: Harmonic Series Detection

Check if peaks form a harmonic series:

```python
def detect_harmonic_series(peak_freqs, peak_mags, tolerance=0.02):
    """
    Find fundamental frequency from harmonic series.

    For each candidate fundamental f0:
    - Check if peaks exist at 2*f0, 3*f0, 4*f0, ...
    - Score based on how many harmonics are present
    - True fundamental will have the most harmonics
    """
    # Try each peak as potential fundamental
    candidates = []

    for i, f0 in enumerate(peak_freqs):
        harmonic_count = 1  # The fundamental itself
        harmonic_energy = peak_mags[i]

        # Check for harmonics at 2*f0, 3*f0, 4*f0, ...
        for h in range(2, 8):  # Check up to 7th harmonic
            expected_freq = f0 * h

            # Find if any peak is close to this harmonic
            for pf, pm in zip(peak_freqs, peak_mags):
                if abs(pf - expected_freq) / expected_freq < tolerance:
                    harmonic_count += 1
                    harmonic_energy += pm
                    break

        candidates.append({
            'f0': f0,
            'harmonic_count': harmonic_count,
            'harmonic_energy': harmonic_energy,
            'score': harmonic_count * harmonic_energy
        })

    # Best candidate is the one with most harmonics
    best = max(candidates, key=lambda x: x['score'])
    return best['f0']
```

### Step 3: Frequency to MIDI Note

Convert detected frequency to MIDI note number:

```python
def freq_to_midi(freq):
    """
    Convert frequency (Hz) to MIDI note number.

    MIDI note 69 = A4 = 440 Hz
    12 semitones per octave
    """
    if freq <= 0:
        return 0

    midi_note = 69 + 12 * np.log2(freq / 440.0)
    return round(midi_note)

def midi_to_note_name(midi_note):
    """Convert MIDI note to name (e.g., 60 -> C4)."""
    notes = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    octave = (midi_note // 12) - 1
    note = notes[midi_note % 12]
    return f"{note}{octave}"
```

### Step 4: Integration with Onset Detection

For each detected onset:
1. Get the spectral data for that time slice
2. Detect peaks in the spectrum
3. Find the fundamental frequency using harmonic analysis
4. Convert to MIDI note number

## Testing Strategy

### Test 1: Single-Note Piano Samples (Iowa)

Use Iowa piano samples where we know the ground truth note:
- `Piano.ff.C4.aiff.wav` → should detect MIDI note 60 (C4)
- `Piano.mf.A4.aiff.wav` → should detect MIDI note 69 (A4)

**Success**: > 95% of notes detected within ±1 semitone

### Test 2: Chromatic Scale

Test all 88 piano keys to check for systematic errors:
- Low notes (A0-C2): Watch for octave errors
- Mid notes (C3-C5): Should be most accurate
- High notes (C6-C8): Watch for harmonic confusion

### Test 3: Real MIDI Synthesis

Synthesize MIDI files and compare detected pitches to ground truth.

## Expected Challenges

1. **Octave Errors** - Mistaking fundamental for 2nd harmonic or vice versa
   - Solution: Harmonic series validation

2. **Missing Fundamental** - Fundamental frequency not present in spectrum
   - Solution: Infer from harmonic spacing

3. **Inharmonicity** - Piano strings are slightly inharmonic (especially low notes)
   - Solution: Wider tolerance in harmonic matching

4. **Multiple Notes** - Polyphonic audio
   - Phase 2 starts with monophonic; handle polyphony later

## Success Metrics

```
Pitch Detection Metrics:
- Pitch Accuracy: % of notes within ±1 semitone
- Octave Accuracy: % of notes with correct octave
- Note Accuracy: % of notes exactly correct
- Missed Notes: % of onsets with no pitch detected

Goal: > 95% pitch accuracy on single-note piano samples
```

## Timeline

1. **Implement pitch detection** - spectral peaks + harmonic analysis
2. **Test on Iowa samples** - single notes with known pitch
3. **Tune and refine** - fix octave errors and edge cases
4. **Validate on real MIDI** - test on synthesized music
5. **Phase 2 complete** when pitch accuracy > 95%

Then we can move to Phase 3 (combining timing, dynamics, and pitch into full MIDI transcription).
