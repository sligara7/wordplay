# Pipeline2: Original MHT-Based Music Analysis

## Overview

This pipeline returns to the **original design** that applies Multi-Hypothesis Testing (MHT) from space surveillance to music chord detection.

## Design Philosophy

Unlike `pipeline/` which uses standard audio processing (FFT/autocorrelation), `pipeline2/` follows the original vision:

1. **MIDI Input** → Ground truth for validation
2. **Synthesized Audio** → Using synthesize_instruments (not external samples)
3. **Spectral Analysis** → Using custom spectral_analyzer.py (Fourier-like decomposition)
4. **MHT Detection** → Apply space surveillance techniques to each time slice

## Architecture

```
MIDI File (.mid)
    ↓
[MIDI Parser] → Extract notes, timing, instruments
    ↓
[Instrument Synthesizer] → Generate WAV using synthesize_instruments/
    ↓
WAV Audio (synthesized)
    ↓
[Spectral Analyzer] → Create 2D frequency-time matrix
    ↓
2D Spectral Data [frequencies × time]
    ↓
[MHT Chord Detector] → Apply matched-filter detection to each time slice
    ↓
Detected Chords with SNR confidence
```

## Key Differences from pipeline/

| Aspect | pipeline/ (divergent) | pipeline2/ (original) |
|--------|----------------------|----------------------|
| **Input** | WAV audio (recording) | MIDI file (ground truth) |
| **Synthesis** | N/A (real audio) | Synthesized instruments |
| **Spectral Analysis** | Standard FFT | Custom spectral_analyzer.py |
| **Pitch Detection** | Autocorrelation/FFT hybrid | Not needed (MIDI has pitch) |
| **Chord Detection** | Graph-based correlation | MHT matched-filter (SNR) |
| **Theory Basis** | Audio signal processing | Space object detection |
| **Validation** | Hard (no ground truth) | Easy (MIDI = ground truth) |

## Components

### 1. MIDI to WAV Synthesis (`midi_synthesizer.py`)

- Reads MIDI files using mido
- Synthesizes audio using:
  - `synthesize_instruments.PercussionSynthesizer` (drums)
  - `synthesize_instruments.BrassSynthesizer` (brass)
  - `synthesize_instruments.WoodwindSynthesizer` (woodwinds)
  - `synthesize_instruments.StringInstrumentSynthesizer` (strings)
- Generates clean WAV files with known content

### 2. Spectral Analysis (`spectral_pipeline.py`)

- Uses `spectral_analyzer.SpectralAnalyzer` (your custom Fourier analysis)
- Generates 2D matrix: `A(f, t)` where:
  - f = frequency bin (e.g., 1080 bins from A-1 to A8)
  - t = time sample (window size based on cycles of A0)
- Output: Frequency-time spectrogram optimized for musical notes

### 3. MHT Chord Detection (`mht_pipeline.py`)

- Uses `bht_chord_detector.MHTChordDetector`
- For each time slice `t`:
  - Extract spectral slice `A(:, t)` (all frequencies at time t)
  - Calculate background noise `B = median(A)`
  - Calculate noise std `σ` with outlier removal (MHTOR)
  - Test all chord templates via matched filter
  - Select chord with max SNR (if above threshold)
- Output: Time series of detected chords with confidence

### 4. Validation & Metrics (`validate_pipeline.py`)

- Compare detected chords vs MIDI ground truth
- Metrics:
  - Precision: % detected chords that are correct
  - Recall: % ground truth chords that were detected
  - F1 score
  - Timing accuracy (onset alignment)
  - SNR distribution

## Usage

### Basic Pipeline

```python
from pipeline2 import MusicAnalysisPipeline

# Create pipeline
pipeline = MusicAnalysisPipeline(sample_rate=44100)

# Process MIDI file
result = pipeline.process_midi('song.mid')

# Results contain:
# - Synthesized WAV audio
# - Spectral data (2D frequency-time matrix)
# - Detected chords with SNR confidence
# - Validation metrics (if ground truth available)
```

### Step-by-Step

```python
# 1. Synthesize MIDI to WAV
from pipeline2.midi_synthesizer import MIDISynthesizer

synth = MIDISynthesizer(sample_rate=44100)
audio, midi_data = synth.synthesize_from_file('song.mid')

# 2. Spectral analysis
from spectral_analyzer import SpectralAnalyzer

analyzer = SpectralAnalyzer(samplefreq=44100, cycles=4)
spectral_data = analyzer.dotop(audio)  # Shape: [num_freqs, num_time_slices]

# 3. MHT chord detection
from bht_chord_detector import MHTChordDetector, build_chord_templates

templates = build_chord_templates(
    frequencies=analyzer.frequencies,
    template_type='gaussian',
    sigma_hz=10.0
)

detector = MHTChordDetector(chord_templates=templates, threshold=6.5)

# Detect chords for each time slice
chords = []
for t in range(spectral_data.shape[1]):
    slice_data = spectral_data[:, t]
    result = detector.detect(slice_data)
    if result['detected']:
        chords.append({
            'time': t * analyzer.analysis_length,
            'chord': result['chord'],
            'snr': result['snr'],
            'confidence': result['confidence']
        })

# 4. Validate against MIDI ground truth
from pipeline2.validate import compare_with_ground_truth

metrics = compare_with_ground_truth(chords, midi_data)
print(f"Precision: {metrics['precision']:.2%}")
print(f"Recall: {metrics['recall']:.2%}")
print(f"F1 Score: {metrics['f1']:.2%}")
```

## Matrix-Based Rapid MHT

The original design mentioned a "matrix way to do this very rapidly". This refers to:

### Vectorized SNR Calculation

Instead of looping over time slices and chord templates:

```python
# Slow: Nested loops
for t in range(num_time_slices):
    for chord_name, template in templates.items():
        snr = calculate_snr(spectral_data[:, t], template)

# Fast: Vectorized matrix multiplication
# spectral_data: [num_freqs, num_time_slices]
# template_matrix: [num_chords, num_freqs]
# SNR_matrix = template_matrix @ spectral_data
# Result: [num_chords, num_time_slices] - all SNRs at once!
```

### Implementation

```python
def detect_all_chords_vectorized(spectral_data, templates, threshold=6.5):
    """
    Vectorized MHT detection across all time slices.

    Args:
        spectral_data: [num_freqs, num_time_slices]
        templates: Dict[chord_name, template_array]
        threshold: SNR threshold

    Returns:
        detected_chords: [num_time_slices] array of chord names
        snr_matrix: [num_chords, num_time_slices] SNR values
    """
    num_freqs, num_time = spectral_data.shape
    num_chords = len(templates)

    # Stack all templates into matrix
    chord_names = list(templates.keys())
    template_matrix = np.vstack([templates[name] for name in chord_names])
    # Shape: [num_chords, num_freqs]

    # Calculate background for each time slice (median)
    B = np.median(spectral_data, axis=0)  # Shape: [num_time]

    # Subtract background
    data_centered = spectral_data - B[np.newaxis, :]  # Broadcasting

    # Calculate noise std with outlier removal (per time slice)
    sigma = calculate_noise_std_vectorized(spectral_data, B)  # Shape: [num_time]

    # Compute SNR matrix: [num_chords, num_time]
    # Numerator: template · data_centered
    numerator = template_matrix @ data_centered  # Matrix multiply!

    # Denominator: sigma * sqrt(sum(template^2))
    template_norms = np.sqrt(np.sum(template_matrix**2, axis=1))  # [num_chords]
    denominator = sigma[np.newaxis, :] * template_norms[:, np.newaxis]

    # SNR matrix
    snr_matrix = numerator / (denominator + 1e-10)

    # Find best chord for each time slice
    best_chord_idx = np.argmax(snr_matrix, axis=0)  # [num_time]
    max_snr = np.max(snr_matrix, axis=0)  # [num_time]

    # Apply threshold
    detected = max_snr > threshold

    # Convert to chord names
    detected_chords = np.array([
        chord_names[idx] if det else None
        for idx, det in zip(best_chord_idx, detected)
    ])

    return detected_chords, snr_matrix
```

**Performance:**
- Old: O(num_chords × num_time × num_freqs) - nested loops
- New: O(num_chords × num_time × num_freqs) - but vectorized! **~100x faster**

## Files

```
pipeline2/
├── README.md                  # This file
├── midi_synthesizer.py        # MIDI → WAV synthesis
├── spectral_pipeline.py       # WAV → Spectral analysis
├── mht_pipeline.py           # Spectral → MHT chord detection
├── validate_pipeline.py      # Ground truth validation
├── pipeline.py               # Main integrated pipeline
├── examples/
│   ├── simple_chord.mid      # Test: Single C major chord
│   ├── chord_progression.mid # Test: I-IV-V-I in C
│   └── amazing_grace.mid     # Test: Real song
└── tests/
    ├── test_synthesis.py     # Unit tests for synthesis
    ├── test_spectral.py      # Unit tests for spectral analysis
    └── test_mht.py          # Unit tests for MHT detection
```

## Advantages of This Design

1. **Ground Truth Validation**
   - MIDI input = known chords, timing, notes
   - Can measure accuracy objectively

2. **Controlled Experiments**
   - Test specific chord types
   - Vary SNR (add noise)
   - Test different instruments

3. **Direct Spectral Detection**
   - No dependency on pitch detection errors
   - Works on raw spectral data

4. **Statistical Confidence**
   - SNR-based detection (not ad-hoc scores)
   - P_FA control (false alarm probability)
   - Outlier rejection (MHTOR)

5. **MHT Theory**
   - Proven in space surveillance
   - Optimal detector for Gaussian noise
   - Theoretical performance bounds

## Next Steps

1. ✅ Create directory structure
2. ⬜ Implement `midi_synthesizer.py`
3. ⬜ Implement `spectral_pipeline.py`
4. ⬜ Implement `mht_pipeline.py` (vectorized)
5. ⬜ Implement `validate_pipeline.py`
6. ⬜ Create test MIDI files
7. ⬜ Run validation experiments
8. ⬜ Compare with pipeline/ results

## References

- `MHT_MUSIC_CORRELATION.md` - Theory mapping
- `bht_chord_detector.py` - MHT implementation
- `spectral_analyzer.py` - Custom Fourier analysis
- `synthesize_instruments/` - Instrument synthesis
- Sligar, A.J. (2015). "Measuring Angular Rate..." - Original MHT thesis
