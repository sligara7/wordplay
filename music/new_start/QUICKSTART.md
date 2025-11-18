# Audio-to-MIDI Transcription - Quick Start Guide

## Installation

```bash
# Install required dependencies
pip install numpy scipy networkx mido

# Optional: For testing
pip install pytest
```

## Basic Usage

### Command Line Interface

```bash
# Basic transcription
python audio_to_midi_pipeline.py input.wav

# Specify output file
python audio_to_midi_pipeline.py input.wav --output output.mid

# With verbose output
python audio_to_midi_pipeline.py input.wav --verbose

# Adjust parameters for better detection
python audio_to_midi_pipeline.py input.wav \
    --intensity-threshold 0.03 \
    --confidence 0.25 \
    --tempo 140
```

### Command Line Options

```
Positional arguments:
  input                 Input WAV file path

Optional arguments:
  --output, -o PATH     Output MIDI file path (default: INPUT.mid)
  --intensity-threshold FLOAT
                        Minimum intensity for graph nodes (default: 0.05)
                        Lower = more notes detected
  --confidence FLOAT    Minimum confidence for fundamentals (default: 0.3)
                        Lower = more permissive detection
  --min-duration INT    Minimum sustained samples (default: 3)
                        Higher = filter out very short notes
  --tempo INT           MIDI tempo in BPM (default: 120)
  --verbose, -v         Print progress messages
```

### Python API

```python
from audio_to_midi_pipeline import transcribe

# Simple transcription
midi_path = transcribe(
    wav_path='input.wav',
    output_path='output.mid',
    verbose=True
)

# With custom parameters
midi_path = transcribe(
    wav_path='input.wav',
    output_path='output.mid',
    intensity_threshold=0.03,  # Lower threshold for quieter notes
    confidence_threshold=0.25,  # More permissive fundamental detection
    min_duration_samples=5,     # Filter very short notes
    tempo=140,                  # Set MIDI tempo
    verbose=True
)

print(f"Created MIDI file: {midi_path}")
```

## Parameter Tuning Guide

### Intensity Threshold (--intensity-threshold)

Controls which frequency-time points are included in the graph.

- **Lower values (0.01-0.03)**: Detect quieter notes, more sensitive
- **Default (0.05)**: Balanced detection
- **Higher values (0.1+)**: Only loud notes, reduces noise

**When to adjust:**
- Quiet audio → Lower threshold
- Noisy audio → Higher threshold
- Missing notes → Lower threshold

### Confidence Threshold (--confidence)

Controls which fundamental frequencies are kept after harmonic analysis.

- **Lower values (0.1-0.2)**: More permissive, may include harmonics
- **Default (0.3)**: Balanced fundamental detection
- **Higher values (0.5+)**: Very strict, only confident fundamentals

**When to adjust:**
- Complex chords → Lower threshold
- Solo instruments → Can use higher threshold
- Getting too many notes → Higher threshold

### Minimum Duration (--min-duration)

Number of time samples a note must be sustained to be included.

- **Lower values (1-2)**: Include very short notes (e.g., staccato)
- **Default (3)**: Filter out very brief transients
- **Higher values (5+)**: Only sustained notes

**When to adjust:**
- Fast passages → Lower value
- Sustained notes only → Higher value
- Too many transients → Higher value

### Tempo (--tempo)

Sets the MIDI file tempo. Does not affect detection, only playback speed.

- Common values: 60, 90, 120, 140, 160 BPM
- Default: 120 BPM

## Examples

### Example 1: Piano Recording

```bash
python audio_to_midi_pipeline.py piano.wav \
    --output piano.mid \
    --intensity-threshold 0.04 \
    --confidence 0.3 \
    --tempo 120 \
    --verbose
```

### Example 2: Quiet Guitar Recording

```bash
python audio_to_midi_pipeline.py guitar.wav \
    --output guitar.mid \
    --intensity-threshold 0.02 \
    --confidence 0.25 \
    --verbose
```

### Example 3: Fast Melody

```bash
python audio_to_midi_pipeline.py melody.wav \
    --output melody.mid \
    --min-duration 2 \
    --intensity-threshold 0.03 \
    --verbose
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/test_integration.py -v

# Generate synthetic test audio
python tests/generate_test_audio.py
```

## Pipeline Architecture

The transcription pipeline consists of 6 steps:

1. **WAV Validation** - Verify input file is valid WAV format
2. **Spectral Analysis** - Decompose audio into frequency-time-intensity matrix
3. **Graph Construction** - Build NetworkX graph with nodes (freq-time points) and edges (temporal/harmonic)
4. **Harmonic Analysis** - Use community detection to identify fundamental frequencies
5. **Onset Detection** - Analyze intensity derivatives to detect note beginnings
6. **MIDI Generation** - Convert note events to standard MIDI file

## Supported Audio Formats

- **Format**: WAV (WAVE)
- **Sample Rates**: 44100 Hz, 48000 Hz, 22050 Hz, 96000 Hz
- **Channels**: Mono or Stereo (left channel used for stereo)
- **Bit Depth**: 16-bit PCM recommended

## Output

- **Format**: Standard MIDI Format 1
- **Resolution**: 480 ticks per quarter note
- **Metadata**: Tempo, time signature (4/4), track name
- **Compatibility**: DAWs (Logic, Ableton, FL Studio), Music notation (MuseScore, Finale)

## Troubleshooting

### "No notes detected"

Try:
1. Lower `--intensity-threshold` to 0.01 or 0.02
2. Lower `--confidence` to 0.1 or 0.15
3. Check input audio isn't silent
4. Ensure audio is in supported format

### "Too many false notes"

Try:
1. Raise `--intensity-threshold` to 0.08 or 0.1
2. Raise `--confidence` to 0.4 or 0.5
3. Increase `--min-duration` to 5 or more

### "Missing some notes"

Try:
1. Lower `--intensity-threshold`
2. Lower `--confidence`
3. Decrease `--min-duration`
4. Check if notes are very quiet in the recording

## Technical Notes

- **Graph-based approach**: Uses NetworkX MultiDiGraph for spectral representation
- **Harmonic detection**: Louvain community detection algorithm
- **Onset detection**: Temporal intensity derivative analysis
- **Frequency range**: A0 (27.5 Hz) to C8 (4186 Hz)
- **Time resolution**: Depends on spectral window (default: ~46ms at 44.1kHz)

## References

- See `TESTING_SUMMARY.md` for test results
- See component docstrings for implementation details
- See `specs/` directory for architecture documentation
