# Roadmap to Perfect Audio-to-MIDI Transcription

**Goal**: Take any audio (radio song, live recording) and produce an accurate MIDI transcription that sounds nearly identical when re-synthesized.

**Current State**: We can detect chords with high accuracy (100% in-key, 0 spurious detections), but we're missing melody, timing precision, dynamics, and multiple voices.

---

## Table of Contents

1. [Current Capabilities](#current-capabilities)
2. [Gap Analysis: A.wav vs B.wav](#gap-analysis)
3. [Roadmap Phases](#roadmap-phases)
4. [Measurable Goals](#measurable-goals)
5. [Testing Strategy](#testing-strategy)
6. [Technical Approaches](#technical-approaches)

---

## Current Capabilities

### What Works Well ✅

1. **Chord Detection (HARD Mode)**
   - 100% in-key chord detection
   - 0 spurious sus4/complex chords
   - Accurate key detection (C# major for Clair de Lune)
   - 95-99% detection rate
   - ~7× real-time processing (CdL: 461s in 66s)

2. **Spectral Analysis**
   - Multi-octave PSF templates (660 chords × 5 octaves)
   - Fast matrix multiplication (6000-8000 slices/sec)
   - Good frequency resolution (1081 frequency bins)

3. **Music Theory Integration**
   - Key detection from SNR patterns
   - Chord progression validation
   - Roman numeral analysis

4. **Synthesis**
   - Enhanced instrument synthesis (strings, brass, woodwinds)
   - Fallback to simple synthesis
   - Good audio quality

### What's Missing ❌

1. **Melody Detection**: Only detecting chords, not individual melody notes
2. **Timing Precision**: Coarse time windows (~145ms per slice)
3. **Dynamics (Velocity)**: Fixed velocity (80), no loudness detection
4. **Polyphonic Note Separation**: Can't separate simultaneous notes in different voices
5. **Instrument Recognition**: No timbre/instrument classification
6. **Modulation Detection**: Single key for entire song
7. **Note Duration**: Chord segments, not individual note lengths
8. **Voicing/Inversions**: Chord names only, not specific note arrangements

---

## Gap Analysis: A.wav vs B.wav

### Quantitative Differences (CdL.mid Example)

| Metric | A.wav (Original) | B.wav (Detected) | Ratio |
|--------|------------------|------------------|-------|
| **Notes** | 1,491 | 1,739 | 1.17× |
| **Events** | 1,491 individual notes | 617 chord segments | 0.41× |
| **Temporal resolution** | Per-note timing | ~0.75s per segment | ~5× coarser |
| **Velocity range** | 0-127 (varied) | 80 (fixed) | 1 value |
| **Voicing** | Original inversions | Root position triads | Simplified |

### Qualitative Differences

**A.wav (Original)**:
- Complete melody + harmony
- Expressive dynamics (soft/loud)
- Precise rhythmic timing
- Multiple voices (melody, bass, inner voices)
- Original articulation

**B.wav (Detected)**:
- Harmonic backing only (no melody)
- Flat dynamics
- Quantized timing (coarse)
- Single chord voicing per segment
- Sustained chords (no articulation)

**Perceptual Result**: B.wav sounds like a "chord chart playback" - harmonically correct but missing melodic content and expression.

---

## Roadmap Phases

### Phase 1: Improve Timing & Dynamics (Foundation)
**Goal**: Accurate onset detection and velocity estimation

**Tasks**:
1. Implement onset detection (energy-based + spectral flux)
2. Add velocity estimation from amplitude envelopes
3. Improve temporal resolution (reduce time slice duration)
4. Separate note-on/note-off detection

**Expected Improvement**:
- B.wav has correct rhythm and dynamics
- Still chord-only, but more expressive

**Measurable Goals**:
- Onset timing error < 50ms (currently ~145ms)
- Velocity correlation > 0.7 with ground truth
- Tempo detection accuracy > 95%

---

### Phase 2: Melody Extraction (Critical)
**Goal**: Separate melody from harmony

**Tasks**:
1. Implement melody salience detection (highest energy in high frequencies)
2. Add pitch tracking for monophonic melodies
3. Separate melody voice from chord voicing
4. Detect melodic contours and note transitions

**Expected Improvement**:
- B.wav has melody + chords
- Major qualitative leap in similarity

**Measurable Goals**:
- Melody pitch accuracy > 85% (correct notes)
- Melody presence recall > 80% (find melody when present)
- F-measure for melody notes > 0.80

---

### Phase 3: Polyphonic Note Separation (Advanced)
**Goal**: Separate multiple simultaneous notes (bass, inner voices, melody)

**Tasks**:
1. Implement source separation (CNN-based or NMF)
2. Add multi-pitch detection per time frame
3. Voice assignment (soprano/alto/tenor/bass)
4. Track individual note trajectories over time

**Expected Improvement**:
- B.wav has all voices (4-part harmony)
- Approaching original complexity

**Measurable Goals**:
- Multi-pitch detection F-measure > 0.75
- Voice assignment accuracy > 70%
- Polyphonic transcription accuracy > 65%

---

### Phase 4: Duration & Articulation (Refinement)
**Goal**: Accurate note durations and articulation

**Tasks**:
1. Implement note offset detection (energy decay)
2. Add sustain vs. staccato classification
3. Detect legato connections
4. Estimate note release times

**Expected Improvement**:
- B.wav has correct note lengths
- Proper phrasing and articulation

**Measurable Goals**:
- Duration error < 100ms mean absolute error
- Staccato/legato classification accuracy > 80%
- Note overlap detection F-measure > 0.70

---

### Phase 5: Modulation & Key Changes (Completeness)
**Goal**: Handle key changes within songs

**Tasks**:
1. Implement sliding window key detection
2. Add modulation point detection
3. Apply different keys to different sections
4. Handle chromatic passages

**Expected Improvement**:
- B.wav correct for songs like "Man in the Mirror" (modulates up semitone)
- Handles complex pop arrangements

**Measurable Goals**:
- Key change detection recall > 90%
- Key change timing error < 2 seconds
- Cross-key transcription accuracy maintained > 80%

---

### Phase 6: Instrument Recognition (Enhancement)
**Goal**: Identify and separate instruments

**Tasks**:
1. Train instrument classifier (MFCCs + CNN)
2. Add instrument-specific transcription models
3. Separate tracks by instrument
4. Generate multi-track MIDI

**Expected Improvement**:
- B.wav has correct instrument timbres
- Multi-track MIDI output (drums, bass, guitar, vocals, etc.)

**Measurable Goals**:
- Instrument classification accuracy > 85%
- Instrument-separated transcription accuracy > 70% per instrument
- Multi-track F-measure > 0.75

---

## Measurable Goals

### Metrics Hierarchy

#### Level 1: Frame-Level Metrics (Basic)
- **Onset Detection F-measure**: Precision/recall of note starts
- **Pitch Accuracy**: % frames with correct pitch
- **Chroma Accuracy**: 12-bin pitch class accuracy

#### Level 2: Note-Level Metrics (Intermediate)
- **Note Onset Precision/Recall**: Correct notes within 50ms window
- **Note Offset Precision/Recall**: Correct note endings
- **Pitch Precision/Recall**: Correct MIDI note numbers
- **Multi-Pitch F-measure**: For polyphonic music

#### Level 3: Transcription Metrics (Advanced)
- **MIREX Transcription Accuracy**: Official MIR benchmark
  - Frame-level: precision, recall, F-measure
  - Note-level: precision, recall, F-measure
- **Edit Distance**: Levenshtein distance between MIDI sequences
- **Perceptual Similarity**: SSIM on spectrograms

#### Level 4: Perceptual Metrics (Ultimate)
- **Spectrogram Cosine Similarity**: A.wav vs B.wav
- **Mel-Cepstral Distortion**: Timbre similarity
- **Human Listening Tests**: ABX preference tests
- **MUSHRA Scores**: Multi-stimulus rating (1-100)

---

## Testing Strategy

### Test Suite Structure

```
tests/
├── unit/
│   ├── test_onset_detection.py
│   ├── test_pitch_tracking.py
│   ├── test_melody_extraction.py
│   └── test_polyphonic_separation.py
├── integration/
│   ├── test_full_pipeline.py
│   └── test_roundtrip_quality.py
├── datasets/
│   ├── simple/          # Single instrument, monophonic
│   ├── chords/          # Current test set (working well)
│   ├── melody/          # Melody + accompaniment
│   ├── polyphonic/      # Multiple voices
│   └── complex/         # Full arrangements
└── benchmarks/
    ├── musicnet/        # Classical (180K labeled notes)
    ├── maestro/         # Piano (1200 hours)
    └── mirex/           # MIR benchmark
```

### Incremental Testing Approach

**Phase 1: Synthetic Test Cases**
- Generate MIDI → Synthesize → Transcribe → Compare
- Controlled test: Known ground truth
- Metrics: 100% achievable on synthetic data

**Phase 2: Simple Real Audio**
- Single instrument (piano, guitar)
- Monophonic melodies
- Clean recordings
- Goal: 90%+ accuracy

**Phase 3: Complex Real Audio**
- Multiple instruments
- Polyphonic music
- Background noise
- Goal: 75%+ accuracy

**Phase 4: Radio-Quality Audio**
- Compressed audio (MP3)
- Mixed/mastered
- Real-world use case
- Goal: 60-70% accuracy (state-of-the-art)

---

## Technical Approaches

### Phase 1: Timing & Dynamics

#### Onset Detection
```python
# Energy-based onset detection
def detect_onsets_energy(audio, sample_rate):
    """Detect note onsets using energy envelope."""
    # Compute energy in sliding windows
    hop_length = 512
    energy = librosa.feature.rms(y=audio, hop_length=hop_length)[0]

    # Find peaks in energy (onsets)
    onsets = librosa.onset.onset_detect(
        onset_envelope=energy,
        sr=sample_rate,
        hop_length=hop_length,
        backtrack=True
    )

    onset_times = librosa.frames_to_time(onsets, sr=sample_rate, hop_length=hop_length)
    return onset_times

# Metric: Onset F-measure
def evaluate_onset_detection(detected_onsets, ground_truth_onsets, tolerance=0.05):
    """
    Evaluate onset detection with tolerance window.

    Args:
        tolerance: Time window in seconds (default 50ms)

    Returns:
        precision, recall, f_measure
    """
    # Match detected to ground truth within tolerance
    tp = sum(1 for d in detected_onsets
             if any(abs(d - gt) < tolerance for gt in ground_truth_onsets))
    fp = len(detected_onsets) - tp
    fn = len(ground_truth_onsets) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f_measure
```

#### Velocity Estimation
```python
def estimate_velocity(audio, onset_time, sample_rate):
    """Estimate MIDI velocity from audio amplitude at onset."""
    # Get audio segment around onset (50ms window)
    onset_sample = int(onset_time * sample_rate)
    window = audio[onset_sample:onset_sample + int(0.05 * sample_rate)]

    # Compute RMS energy
    rms = np.sqrt(np.mean(window**2))

    # Map to MIDI velocity (0-127)
    # Calibrate with known dynamics
    velocity = int(np.clip(rms * 1000, 0, 127))  # Scaling factor TBD

    return velocity

# Metric: Velocity correlation
def evaluate_velocity(detected_velocities, ground_truth_velocities):
    """Pearson correlation between detected and ground truth velocities."""
    return np.corrcoef(detected_velocities, ground_truth_velocities)[0, 1]
```

**Test**:
1. Generate MIDI with varying velocities (ppp to fff)
2. Synthesize to audio
3. Detect onsets and estimate velocities
4. Compare: correlation > 0.7

---

### Phase 2: Melody Extraction

#### Melody Salience Detection
```python
def extract_melody(spectral_data, frequencies):
    """
    Extract melody using salience-based approach.

    Key idea: Melody is usually the highest-energy pitch in the treble range.
    """
    # Focus on melody range (E4-C7 = MIDI 64-96 = ~330-2093 Hz)
    melody_mask = (frequencies >= 330) & (frequencies <= 2093)
    melody_spectrum = spectral_data[melody_mask, :]
    melody_freqs = frequencies[melody_mask]

    # Find peak frequency in each time slice
    melody_indices = np.argmax(melody_spectrum, axis=0)
    melody_pitch_freqs = melody_freqs[melody_indices]

    # Convert to MIDI notes
    melody_notes = 69 + 12 * np.log2(melody_pitch_freqs / 440.0)

    # Filter out low-salience frames (no melody)
    salience = np.max(melody_spectrum, axis=0)
    threshold = np.percentile(salience, 50)
    melody_notes[salience < threshold] = -1  # No melody

    return melody_notes, salience

# Metric: Melody accuracy
def evaluate_melody(detected_melody, ground_truth_melody, tolerance=0.5):
    """
    Evaluate melody transcription accuracy.

    Args:
        tolerance: Semitone tolerance (0.5 = quarter tone)

    Returns:
        accuracy, precision, recall, f_measure
    """
    # Align sequences (handle timing shifts)
    # For simplicity, assume frame-aligned

    # Calculate metrics
    valid_frames = ground_truth_melody != -1
    detected_frames = detected_melody != -1

    # True positives: correct pitch within tolerance
    pitch_correct = np.abs(detected_melody - ground_truth_melody) < tolerance
    tp = np.sum(pitch_correct & valid_frames & detected_frames)

    fp = np.sum(detected_frames & ~valid_frames)
    fn = np.sum(valid_frames & ~detected_frames)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    accuracy = np.sum(pitch_correct & valid_frames) / np.sum(valid_frames) if np.sum(valid_frames) > 0 else 0

    return accuracy, precision, recall, f_measure
```

**Test**:
1. Use piano solo recordings (melody + accompaniment)
2. Ground truth: MIDI with melody on channel 1
3. Extract melody from audio
4. Compare: F-measure > 0.80

---

### Phase 3: Polyphonic Separation

#### Multi-Pitch Detection
```python
def detect_multi_pitch(spectral_data, frequencies, num_voices=4):
    """
    Detect multiple simultaneous pitches using non-maximum suppression.

    Returns:
        List of active pitches per time frame
    """
    pitches_per_frame = []

    for time_idx in range(spectral_data.shape[1]):
        spectrum = spectral_data[:, time_idx]

        # Find local peaks (candidates)
        peaks = find_spectral_peaks(spectrum, min_distance=20)

        # Sort by magnitude
        peak_strengths = spectrum[peaks]
        sorted_indices = np.argsort(peak_strengths)[::-1]

        # Take top N voices
        active_pitches = []
        for idx in sorted_indices[:num_voices]:
            peak_idx = peaks[idx]
            freq = frequencies[peak_idx]
            midi_note = 69 + 12 * np.log2(freq / 440.0)

            if peak_strengths[idx] > threshold:
                active_pitches.append(midi_note)

        pitches_per_frame.append(active_pitches)

    return pitches_per_frame

# Metric: Multi-pitch F-measure
def evaluate_multi_pitch(detected_pitches, ground_truth_pitches, tolerance=0.5):
    """
    Frame-wise multi-pitch evaluation.

    For each frame, compare sets of detected vs ground truth pitches.
    """
    total_tp, total_fp, total_fn = 0, 0, 0

    for det, gt in zip(detected_pitches, ground_truth_pitches):
        # Convert to sets for comparison
        det_set = set(det)
        gt_set = set(gt)

        # True positives: pitches in both sets (within tolerance)
        tp = sum(1 for d in det_set if any(abs(d - g) < tolerance for g in gt_set))
        fp = len(det_set) - tp
        fn = len(gt_set) - tp

        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f_measure
```

**Test**:
1. Use Bach chorales (4-part harmony, known ground truth)
2. Detect all 4 voices simultaneously
3. Compare: F-measure > 0.75

---

## Implementation Priority

### Immediate (Next Steps)

1. **Create evaluation framework**
   - Write test harness for metrics
   - Generate synthetic test data
   - Establish baseline measurements

2. **Implement Phase 1 (Timing & Dynamics)**
   - Start with onset detection
   - Most impactful for B.wav quality
   - Foundation for later phases

3. **Test on simple cases**
   - Single instrument MIDI files
   - Validate metrics work correctly

### Short-term (1-2 weeks)

4. **Add melody extraction (Phase 2)**
   - Major qualitative improvement
   - Critical for "radio song" goal

5. **Create comparison tools**
   - Visual spectrograms (A vs B)
   - Automatic metrics dashboard
   - MIDI diff viewer

### Medium-term (1 month)

6. **Polyphonic separation (Phase 3)**
   - Handles complex music
   - Approaches professional transcription quality

7. **Build test dataset**
   - Curate diverse examples
   - Label ground truth
   - Create benchmark suite

### Long-term (2-3 months)

8. **Refinement (Phases 4-6)**
   - Articulation, modulation, instruments
   - Handles edge cases
   - Production-ready quality

---

## Success Criteria

### Phase-by-Phase Goals

| Phase | Metric | Current | Target | Test Case |
|-------|--------|---------|--------|-----------|
| **Baseline** | Chord accuracy | 100% | 100% | Clair de Lune (PASS) |
| **Phase 1** | Onset F-measure | N/A | > 0.85 | Piano scales |
| **Phase 1** | Velocity correlation | N/A | > 0.70 | Dynamic MIDI |
| **Phase 2** | Melody F-measure | N/A | > 0.80 | Pop songs |
| **Phase 3** | Multi-pitch F-measure | N/A | > 0.75 | Bach chorales |
| **Phase 4** | Duration MAE | N/A | < 100ms | Staccato vs legato |
| **Phase 5** | Key change recall | N/A | > 0.90 | "Man in the Mirror" |
| **Phase 6** | Instrument accuracy | N/A | > 0.85 | Full band |

### Ultimate Success: "Radio Song Test"

**Definition**: Take a commercial recording (MP3 quality), transcribe to MIDI, re-synthesize to B.wav

**Success Criteria**:
1. **Spectral similarity > 0.75** (cosine similarity of mel-spectrograms)
2. **Note-level F-measure > 0.70** (when ground truth MIDI available)
3. **MUSHRA score > 60** (on 0-100 scale, via listening tests)
4. **Harmonic accuracy > 90%** (correct chords > 90% of time)
5. **Melodic contour accuracy > 85%** (up/down/same patterns correct)

**Test Songs** (diverse genres):
- Classical: Debussy "Clair de Lune" (done - chords only)
- Pop: Whitney Houston "I Wanna Dance with Somebody" (modulation test)
- Rock: Eagles "Hotel California" (guitar solo test)
- Jazz: Bill Evans "Waltz for Debby" (complex harmony)
- Electronic: Daft Punk "Get Lucky" (rhythm + synth)

---

## Next Immediate Actions

1. **Move working files to working_files directory** ✅ (updated script)

2. **Create evaluation framework**
   ```bash
   # Create test infrastructure
   mkdir -p tests/{unit,integration,datasets/{simple,chords,melody,polyphonic}}

   # Write first test
   python test_onset_detection.py  # To be created
   ```

3. **Generate synthetic test data**
   ```python
   # Create test MIDI files with known properties
   - simple_scale.mid (C major scale, quarter notes)
   - dynamic_test.mid (pp to ff crescendo)
   - melody_test.mid (melody + chords)
   ```

4. **Implement onset detection**
   ```python
   # Add to pipeline
   onset_times = detect_onsets(audio, sample_rate)
   ```

5. **Measure baseline**
   ```bash
   # Run current system, measure gaps
   python test_roundtrip_complete.py test.mid HARD working_files
   python evaluate_transcription.py working_files/test_detected.mid test.mid
   ```

---

## Conclusion

This roadmap provides a **structured, measurable path** from current chord detection (which works excellently) to full audio-to-MIDI transcription. Each phase builds on the previous, with clear metrics and test cases.

**Key Insights**:
- We've solved the hardest music theory problem (chords in key)
- Melody extraction is the next critical step
- Incremental testing prevents regressions
- Synthetic data validates algorithms before real-world testing
- State-of-the-art is 60-70% on radio songs - we can achieve this

**Timeline Estimate**:
- Phase 1: 1 week
- Phase 2: 2 weeks
- Phase 3: 3 weeks
- Phases 4-6: 4 weeks
- **Total: 10 weeks to production-ready system**

Let's start with Phase 1: Onset detection and velocity estimation!
