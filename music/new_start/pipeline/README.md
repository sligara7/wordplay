# Audio-to-MIDI Pipeline - Core Components

This folder contains the **production-ready** audio-to-MIDI transcription pipeline with ultra-fast chord detection.

---

## Core Pipeline Files

### 1. Main Pipeline
**`audio_to_midi_pipeline_with_chords.py`** - Main entry point
- Complete audio-to-MIDI transcription
- Chord detection (PSF-based) + melody detection (autocorrelation)
- Command-line interface
- **Start here!**

### 2. Chord Detection
**`ultra_fast_detector.py`** - Ultra-fast PSF chord detector
- Matrix multiplication optimization (9,000+ chords/sec)
- SNR-based detection using 660 PSF templates
- Multi-octave chord recognition

**`multi_octave_psf_templates.pkl`** - Pre-computed PSF templates
- 660 templates (12 roots × 11 types × 5 octaves)
- Generated via `build_multi_octave_psf.py`
- Required for chord detection

**`build_multi_octave_psf.py`** - PSF template generator
- Generates chord spectral signatures
- Run once to create/update templates
- Takes ~4 minutes to generate all 660 templates

### 3. Spectral Analysis
**`spectral_analyzer.py`** - Custom Fourier-like spectral analysis
- Analyzes audio into frequency-time matrix
- Used by both chord and melody detection
- Core signal processing component

### 4. Melody Detection
**`autocorrelation_analyzer.py`** - Autocorrelation-based note detection
- Detects individual melody notes
- Fundamental frequency estimation
- Note event generation

### 5. MIDI Output
**`midi_generator.py`** - MIDI file generation
- Converts note events to MIDI format
- Supports tempo, velocity, timing
- Output: Standard MIDI file (.mid)

---

## Quick Start

### Basic Usage
```bash
# Transcribe audio to MIDI (chords + melody)
python audio_to_midi_pipeline_with_chords.py input.wav

# With verbose output
python audio_to_midi_pipeline_with_chords.py input.wav --verbose

# Chords only
python audio_to_midi_pipeline_with_chords.py input.wav --no-melody

# Melody only
python audio_to_midi_pipeline_with_chords.py input.wav --no-chords
```

### Full Options
```
python audio_to_midi_pipeline_with_chords.py INPUT.wav [OPTIONS]

Options:
  --output, -o PATH     Output MIDI file (default: INPUT.mid)
  --no-chords           Disable chord detection
  --no-melody           Disable melody detection
  --tempo BPM           MIDI tempo (default: 120)
  --verbose, -v         Verbose output
  --help, -h            Show help
```

---

## Pipeline Architecture

```
┌─────────────┐
│  WAV Audio  │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ Spectral Analysis    │  ← spectral_analyzer.py
│ (SpectralAnalyzer)   │
└──────┬───────────────┘
       │
       ├──────────────────────────┬─────────────────────────┐
       ↓                          ↓                         ↓
┌─────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│ PSF Templates   │     │ Chord Detection  │    │ Melody Detection │
│ (660 templates) │ →   │ (Ultra-Fast PSF) │    │ (Autocorrelation)│
└─────────────────┘     └────────┬─────────┘    └────────┬─────────┘
                                 │                       │
                                 ↓                       ↓
                        ┌─────────────────────────────────┐
                        │   Combine Chords + Melody       │
                        └─────────────┬───────────────────┘
                                      ↓
                              ┌───────────────┐
                              │ MIDI Generator│
                              └───────┬───────┘
                                      ↓
                              ┌───────────────┐
                              │  MIDI File    │
                              └───────────────┘
```

---

## Performance

### Processing Speed
- **Spectral analysis**: ~1s for 3 minutes audio
- **Chord detection**: **9,000+ chords/sec** ⚡
- **Melody detection**: ~0.5s for 3 minutes audio
- **Total**: **~100-170× faster than real-time**

### Example (test_amazing_grace.wav - 178 seconds)
```
Processing time: 1.7s total
Speedup: 171× real-time
Chords detected: 723 segments
Melody notes: 32
Total MIDI notes: 2,500
```

---

## Dependencies

### Required Python Packages
```
numpy
scipy
numba
networkx
matplotlib (for PSF generation/visualization)
```

### Install
```bash
pip install numpy scipy numba networkx matplotlib
```

---

## File Dependencies

### What Each File Needs

**audio_to_midi_pipeline_with_chords.py**:
- spectral_analyzer.py
- ultra_fast_detector.py
- autocorrelation_analyzer.py
- midi_generator.py
- build_multi_octave_psf.py (for loading templates)
- multi_octave_psf_templates.pkl

**ultra_fast_detector.py**:
- numpy
- numba
- multi_octave_psf_templates.pkl (loaded at runtime)

**build_multi_octave_psf.py**:
- spectral_analyzer.py
- numpy

**spectral_analyzer.py**:
- numpy
- scipy

**autocorrelation_analyzer.py**:
- numpy
- scipy

**midi_generator.py**:
- (standard library only)

---

## First-Time Setup

### 1. Install Dependencies
```bash
pip install numpy scipy numba networkx matplotlib
```

### 2. Verify PSF Templates
```bash
ls -lh multi_octave_psf_templates.pkl
# Should show ~50MB file
```

### 3. Test Pipeline
```bash
# Test on sample audio (if available)
python audio_to_midi_pipeline_with_chords.py test_audio.wav --verbose
```

### 4. (Optional) Regenerate PSF Templates
```bash
# Only needed if templates are missing or you want to customize
python build_multi_octave_psf.py
# Takes ~4 minutes, creates multi_octave_psf_templates.pkl
```

---

## Customization

### Adjust Chord Detection Threshold
Edit `ultra_fast_detector.py`:
```python
detector = UltraFastChordDetector(
    templates,
    threshold=6.5,  # Lower = more chords detected (more false positives)
                    # Higher = fewer chords (more false negatives)
    use_outlier_removal=True
)
```

### Adjust Spectral Analysis Resolution
Edit `audio_to_midi_pipeline_with_chords.py`:
```python
analyzer = SpectralAnalyzer(
    samplefreq=sample_rate,
    cycles=4,  # Higher = better frequency resolution, slower
    standard_A4=440.0,
    increments=12  # Frequency bins per semitone
)
```

### Customize Chord Types
Edit `build_multi_octave_psf.py`:
```python
CHORD_INTERVALS = {
    'major':     [0, 4, 7],
    'minor':     [0, 3, 7],
    # Add custom chord types here
    'custom':    [0, 5, 10],  # Your intervals
}
```
Then regenerate templates: `python build_multi_octave_psf.py`

---

## Troubleshooting

### "PSF templates not found"
```bash
# Generate templates
python build_multi_octave_psf.py
```

### "Module not found" errors
```bash
# Install dependencies
pip install numpy scipy numba networkx matplotlib
```

### Slow performance
- Check if PSF templates are loaded (should be instant)
- Verify numba is installed (provides JIT compilation)
- For long files (>10 min), processing time scales linearly

### No chords detected
- Lower threshold: Edit `ultra_fast_detector.py`, set `threshold=5.0`
- Check audio quality (clean signal works best)
- Try `--verbose` to see SNR values

### Too many/wrong chords detected
- Raise threshold: Set `threshold=8.0`
- May need music theory filtering (future enhancement)
- Complex harmonics can trigger false detections

---

## Technical Details

### PSF Template System
- **Templates**: 660 (12 roots × 11 types × 5 octaves)
- **Octaves**: 2-6 (covers 99% of musical range)
- **Chord types**: major, minor, dim, aug, sus2, sus4, maj7, min7, dom7, dom9, maj11
- **Generation method**: Pure sinusoids → spectral_analyzer → normalized

### Ultra-Fast Detection Algorithm
```python
# Single matrix multiplication computes ALL correlations
PSF_matrix (660 × 1081) @ spectral_data (1081 × time) = SNR_matrix (660 × time)

# For each time slice:
best_chord = argmax(SNR_matrix[:, time])
if SNR_matrix[best_chord, time] > threshold:
    detect_chord(best_chord)
```

### Why It's Fast
- **No loops**: Single matrix operation vs 660 × time iterations
- **Vectorized**: Numpy/BLAS optimizations
- **Precomputed**: Template norms calculated once
- **Numba JIT**: Just-in-time compilation for hot paths

---

## Output Format

### MIDI File Structure
- **Track 0**: Combined chords + melody
- **Note attributes**:
  - MIDI note number (0-127)
  - Onset time (seconds)
  - Duration (seconds)
  - Velocity (64-127, scaled by SNR for chords)

### Chord Representation
Chords are expanded to individual MIDI notes:
```
C_major_oct4 → MIDI notes [60, 64, 67] (C4, E4, G4)
```

---

## Limitations & Future Work

### Current Limitations
- Single MIDI track (chords + melody combined)
- No music theory validation (all detected chords included)
- Accuracy untested on ground truth
- May detect complex chords from harmonics

### Planned Enhancements
- [ ] Multi-track MIDI output (separate chord/melody tracks)
- [ ] Music theory filtering (validate chord progressions)
- [ ] Ground truth validation suite
- [ ] Real-time streaming mode
- [ ] GPU acceleration
- [ ] Web interface

---

## Version History

### v1.0 (Current)
- Ultra-fast PSF chord detection (9,000+ chords/sec)
- Matrix multiplication optimization
- 660 multi-octave PSF templates
- Integrated chord + melody detection
- 100-170× real-time processing

---

## Support

### Documentation
- See `../COMPREHENSIVE_PSF_SUMMARY.md` for full technical details
- See `../MATRIX_MULTIPLICATION_BREAKTHROUGH.md` for optimization details
- See `../INTEGRATION_COMPLETE.md` for integration notes

### Testing
- Test scripts in `../` (parent directory)
- Example audio files in `../wav_file/`

---

## License

(Your license here)

---

**The core audio-to-MIDI pipeline with ultra-fast chord detection!** 🎵⚡

For questions or issues, refer to the documentation files in the parent directory.
