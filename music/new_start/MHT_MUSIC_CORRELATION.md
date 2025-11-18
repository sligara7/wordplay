# Applying Multi-Hypothesis Testing (MHT) to Music Chord Detection
## From Space Object Detection to Audio Signal Processing

*Adapting matched-filter detection algorithms from space surveillance to audio transcription*

---

## Executive Summary

This document maps the Binary Hypothesis Test (BHT) and Multi-Hypothesis Test (MHT) algorithms used for space object detection to the problem of **musical chord detection in spectral audio data**.

**Key Insight:** A single time sample of spectral data (vertical slice through frequency-time matrix) is analogous to a single image frame in telescope data. Just as MHT correlates a known Point Spread Function (PSF) with pixel intensities to detect space objects, we can correlate known chord templates with frequency amplitudes to detect musical chords.

---

## Conceptual Mapping

### Space Object Detection → Music Chord Detection

| Space Surveillance | Music Transcription |
|-------------------|---------------------|
| **Image frame** (2D array of pixels) | **Time slice** (1D array of frequency bins) |
| Pixel coordinates (x, y) | Frequency bin index (f) |
| Pixel intensity d(x,y) | Spectral amplitude A(f, t) |
| Space object | Musical chord/note |
| Point Spread Function (PSF) | Chord template (frequency pattern) |
| Background noise B | Noise floor (median amplitude) |
| Standard deviation σ | Spectral noise variance |
| Outliers (stars, cosmic rays) | Harmonics, transients, artifacts |
| 9 sub-pixel hypotheses | N chord templates (major, minor, etc.) |
| SNR threshold γ = 6 | Chord confidence threshold |
| Detection → object present | Detection → chord present |

---

## Current System vs. MHT-Based System

### Current Approach (chord_recognizer.py)

```python
# Current: Template matching with simple correlation
1. Group notes into 100ms time windows
2. Extract pitch classes from detected fundamentals
3. Match against predefined chord templates
4. Calculate correlation score (graph-based)
5. Filter based on threshold (0.5)
```

**Limitations:**
- Depends on **upstream fundamental detection** (already error-prone)
- No background noise modeling
- No SNR-based detection
- Simple correlation, not matched-filter

### Proposed MHT-Based Approach

```python
# Proposed: Direct matched-filter detection on spectral data
1. For each time slice t:
   a. Calculate background noise floor B (median of amplitudes)
   b. Calculate noise std deviation σ (with outlier removal)
   c. For each chord template h(f):
      - Compute SNR via matched filter
      - SNR = Σ[(A(f,t) - B) · h(f)] / (σ · sqrt(Σ h²(f)))
   d. Select chord with maximum SNR (M-ary hypothesis test)
   e. Declare chord present if SNR > threshold γ
```

**Advantages:**
- **Direct detection** on raw spectral data (no dependency on fundamental detection)
- **Noise modeling** (median-based background + variance)
- **Outlier rejection** (MHTOR removes harmonics/artifacts)
- **SNR-based confidence** (statistical detection theory)
- **Multi-hypothesis selection** (best chord among many templates)

---

## Mathematical Formulation

### 1. Spectral Data Representation

From `spectral_analyzer.py`, we have:

```
A(f, t) = spectral amplitude at frequency bin f, time sample t
```

Dimensions:
- f ∈ [0, N_freq-1] (e.g., 1080 frequency bins from A-1 to A8)
- t ∈ [0, N_time-1] (e.g., time samples every ~0.1 seconds)

### 2. Chord Templates as "PSF" Functions

Define chord template h_c(f) for chord type c:

```
h_c(f) = {
    1  if frequency f is in chord c
    0  otherwise
}
```

**Example: C Major chord**
```
Fundamental:  C  = f₀
Third:        E  = f₀ · 2^(4/12)  ≈ 1.26 · f₀
Fifth:        G  = f₀ · 2^(7/12)  ≈ 1.50 · f₀

h_Cmajor(f) = δ(f - fC) + δ(f - fE) + δ(f - fG)
```

More realistically, use **Gaussian-weighted templates** to account for spectral spread:

```
h_c(f) = Σ exp(-(f - f_note)² / (2σ_spread²))
         for each note in chord c
```

### 3. Background Noise Calculation (Analogous to BHT)

For each time sample t:

**Background level (median):**
```
B(t) = median{A(f, t) ∀ f ∈ [0, N_freq-1]}
```

**Standard deviation (with outlier removal per MHTOR):**
```
1. Compute squared deviations: D(f) = [A(f,t) - B(t)]²
2. Calculate mean and std dev of D(f):
   M = mean(D(f))
   S = std(D(f))
3. Reject outliers: Keep only f where D(f) < M + 3·S
4. Recompute σ(t) using only non-outlier frequencies
```

This removes:
- **Harmonics** (like bright stars in astronomy)
- **Transients** (like cosmic rays)
- **Artifacts** (like hot pixels)

### 4. Binary Hypothesis Test (BHT) for Single Chord

Test whether chord c is present at time t:

**H₀:** No chord (only noise)
**H₁:** Chord c present

**Log-Likelihood Ratio (from MHT.md equation 89-92):**

```
         N_freq
SNR_c =  Σ     [A(f,t) - B(t)] · h_c(f)     H₁
         f=1                                  ≷  γ
        ─────────────────────────────────    H₀
                    ___________
                   / N_freq
        σ(t) ·   \/   Σ     h²_c(f)
                     f=1
```

**Decision rule:**
- If SNR_c > γ (threshold), declare chord c present
- Else, no chord detected

### 5. Multi-Hypothesis Test (MHT) for Multiple Chords

Test N different chord hypotheses simultaneously:

**H₀:** No chord (noise only)
**H₁:** C major
**H₂:** C minor
**H₃:** C diminished
**H₄:** C augmented
...
**H_N:** Last chord template

**M-ary Detection:**
```
SNR_Mhord = max(SNR_c) for c ∈ {1, 2, ..., N}

If SNR_Mchord > γ_MHT:
    Best chord = argmax(SNR_c)
Else:
    No chord detected
```

**Threshold adjustment** (from MHT.md section 2.5):

Since we're testing N hypotheses instead of 1, false alarm probability increases by factor ~N. To maintain constant P_FA:

```
γ_MHT ≈ γ_BHT + Δγ

where Δγ accounts for multiple comparisons
```

For example:
- γ_BHT = 6.0 (for single hypothesis)
- γ_MHT = 6.2 (for 9 hypotheses in space case)
- For music with ~24 chord types: γ_MHT ≈ 6.4-6.6

---

## Implementation Strategy

### Phase 1: BHT for Single Chord Type

**File: `bht_chord_detector.py`**

```python
class BHTChordDetector:
    """
    Binary Hypothesis Test for single chord detection.

    Analogous to BHT point detector from space surveillance.
    """

    def __init__(self, chord_template, threshold=6.0):
        self.h = chord_template  # h(f) = chord template
        self.gamma = threshold

    def detect(self, spectral_slice):
        """
        Detect chord in single time slice.

        Args:
            spectral_slice: A(f) = 1D array of amplitudes

        Returns:
            (detected: bool, snr: float)
        """
        # 1. Calculate background (median)
        B = np.median(spectral_slice)

        # 2. Calculate noise std deviation
        sigma = self._calculate_noise_std(spectral_slice, B)

        # 3. Matched filter SNR
        numerator = np.sum((spectral_slice - B) * self.h)
        denominator = sigma * np.sqrt(np.sum(self.h**2))

        snr = numerator / (denominator + 1e-10)

        # 4. Threshold test
        detected = (snr > self.gamma)

        return detected, snr

    def _calculate_noise_std(self, A, B):
        """Calculate noise standard deviation."""
        return np.std(A - B)
```

### Phase 2: MHTOR for Outlier Removal

**Enhancement to BHT:**

```python
def _calculate_noise_std_with_outlier_removal(self, A, B):
    """
    Calculate noise std deviation with outlier removal.

    Implements MHTOR algorithm from MHT.md section 3.
    """
    # 1. Squared deviations
    D = (A - B)**2

    # 2. Mean and std dev of squared deviations
    M = np.mean(D)
    S = np.std(D)

    # 3. Reject outliers (3-sigma rule)
    outlier_threshold = M + 3*S
    mask = D < outlier_threshold

    # 4. Recompute sigma using only non-outliers
    sigma = np.sqrt(np.mean(D[mask]))

    return sigma
```

### Phase 3: MHT for Multiple Chord Templates

**File: `mht_chord_detector.py`**

```python
class MHTChordDetector:
    """
    Multi-Hypothesis Test for chord detection.

    Tests multiple chord templates and selects best match.
    """

    def __init__(self, chord_templates, threshold=6.2):
        """
        Args:
            chord_templates: Dict[chord_name, h(f)]
            threshold: MHT threshold (adjusted for multiple hypotheses)
        """
        self.templates = chord_templates  # e.g., {'C_major': h_Cmajor(f), ...}
        self.gamma_MHT = threshold

    def detect(self, spectral_slice):
        """
        Detect best matching chord via M-ary hypothesis test.

        Returns:
            {
                'detected': bool,
                'chord': str or None,
                'snr': float,
                'all_snrs': Dict[chord_name, snr]
            }
        """
        # 1. Calculate background and noise
        B = np.median(spectral_slice)
        sigma = self._calculate_noise_std_with_outlier_removal(
            spectral_slice, B
        )

        # 2. Calculate SNR for each chord template
        snrs = {}
        for chord_name, h in self.templates.items():
            snr = self._calculate_snr(spectral_slice, B, sigma, h)
            snrs[chord_name] = snr

        # 3. M-ary selection: max SNR
        best_chord = max(snrs, key=snrs.get)
        max_snr = snrs[best_chord]

        # 4. Threshold test
        detected = (max_snr > self.gamma_MHT)

        return {
            'detected': detected,
            'chord': best_chord if detected else None,
            'snr': max_snr,
            'all_snrs': snrs,
            'background': B,
            'noise_std': sigma
        }

    def _calculate_snr(self, A, B, sigma, h):
        """Calculate SNR for given template h."""
        numerator = np.sum((A - B) * h)
        denominator = sigma * np.sqrt(np.sum(h**2))
        return numerator / (denominator + 1e-10)
```

### Phase 4: Integration with Pipeline

**File: `audio_to_midi_pipeline.py` (modified)**

Replace current chord recognition with MHT detector:

```python
# Build chord templates
chord_templates = build_chord_templates(
    frequencies=analyzer.frequencies,
    chord_types=['major', 'minor', 'dim', 'aug', 'sus2', 'sus4',
                 'maj7', 'min7', 'dom7', 'dim7', 'halfdim7']
)

# Initialize MHT detector
mht_detector = MHTChordDetector(
    chord_templates=chord_templates,
    threshold=6.2  # Adjusted for ~12 roots × ~10 types = 120 hypotheses
)

# Detect chords at each time sample
detected_chords = []
for time_idx in range(spectral_data.shape[1]):
    spectral_slice = spectral_data[:, time_idx]

    result = mht_detector.detect(spectral_slice)

    if result['detected']:
        detected_chords.append({
            'time': time_idx * window_length / sample_rate,
            'chord': result['chord'],
            'snr': result['snr'],
            'confidence': min(result['snr'] / 10.0, 1.0)  # Normalize to [0,1]
        })
```

---

## Chord Template Generation

### Simple Binary Templates

```python
def build_chord_templates(frequencies, chord_types):
    """
    Build binary chord templates h_c(f).

    Args:
        frequencies: Array of frequency bins (from spectral_analyzer)
        chord_types: List of chord types to generate

    Returns:
        Dict[chord_name, template_array]
    """
    templates = {}

    # Chord interval definitions (semitones from root)
    chord_intervals = {
        'major':     [0, 4, 7],
        'minor':     [0, 3, 7],
        'dim':       [0, 3, 6],
        'aug':       [0, 4, 8],
        'sus2':      [0, 2, 7],
        'sus4':      [0, 5, 7],
        'maj7':      [0, 4, 7, 11],
        'min7':      [0, 3, 7, 10],
        'dom7':      [0, 4, 7, 10],
        'dim7':      [0, 3, 6, 9],
        'halfdim7':  [0, 3, 6, 10],
    }

    # Note names
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                  'F#', 'G', 'G#', 'A', 'A#', 'B']

    # For each root note
    for root_idx, root_name in enumerate(note_names):
        # For each chord type
        for chord_type, intervals in chord_intervals.items():
            chord_name = f"{root_name}_{chord_type}"

            # Create template
            template = np.zeros(len(frequencies))

            # Mark frequencies for each chord note
            for interval in intervals:
                pitch_class = (root_idx + interval) % 12

                # Find all octaves of this pitch class in frequency array
                for freq_idx, freq in enumerate(frequencies):
                    note_pc = freq_to_pitch_class(freq)
                    if note_pc == pitch_class:
                        template[freq_idx] = 1.0

            templates[chord_name] = template

    return templates
```

### Gaussian-Weighted Templates (More Realistic)

```python
def build_gaussian_chord_templates(frequencies, chord_types, sigma_hz=10.0):
    """
    Build Gaussian-weighted chord templates.

    Accounts for spectral spread and frequency resolution.
    """
    templates = {}

    # (same loop structure as above)
    for root_idx, root_name in enumerate(note_names):
        for chord_type, intervals in chord_intervals.items():
            chord_name = f"{root_name}_{chord_type}"

            template = np.zeros(len(frequencies))

            # For each note in chord
            for interval in intervals:
                pitch_class = (root_idx + interval) % 12

                # Get all frequencies of this pitch class (all octaves)
                target_freqs = get_frequencies_for_pitch_class(pitch_class)

                # Add Gaussian centered at each target frequency
                for target_freq in target_freqs:
                    gaussian = np.exp(-(frequencies - target_freq)**2 / (2 * sigma_hz**2))
                    template += gaussian

            # Normalize
            if np.sum(template**2) > 0:
                template = template / np.linalg.norm(template)

            templates[chord_name] = template

    return templates
```

---

## Expected Performance Improvements

### Current System Issues (from CHORD_RECOGNITION_RESULTS.md)

1. **Upstream dependency:** Requires fundamentals from HarmonicAnalyzer first
   - Problem: 321% over-detection (detecting harmonics as fundamentals)
   - Result: False chords based on erroneous input

2. **No noise modeling:** Simple correlation without background subtraction
   - Problem: Background noise inflates correlation scores
   - Result: False positives in noisy regions

3. **Key detection failing:** Returns None for both test files
   - Problem: Depends on pitch histogram which includes errors

### Expected Improvements with MHT

1. **Direct spectral detection:** No dependency on fundamental detection
   - Benefit: Bypasses 321% over-detection issue
   - Result: More accurate chord detection

2. **Noise modeling:** Median background + outlier removal
   - Benefit: Rejects noise, harmonics, artifacts
   - Result: Higher SNR, fewer false positives

3. **Statistical confidence:** SNR-based detection with P_FA control
   - Benefit: Quantifiable detection probability
   - Result: Tunable false alarm rate (e.g., P_FA = 10⁻⁹)

4. **Multi-hypothesis robustness:** Tests all chord types simultaneously
   - Benefit: Selects best match among many options
   - Result: Better disambiguation (e.g., C major vs C minor)

---

## Parameter Tuning

### SNR Threshold Selection

From space surveillance (MHT.md):
- γ_BHT = 6.0 → P_FA = 9.87 × 10⁻¹⁰ (for single hypothesis)
- γ_MHT = 6.2212 → P_FA = 9.87 × 10⁻¹⁰ (for 9 hypotheses)

For music with N chord templates:
- 12 roots × 11 chord types = 132 hypotheses
- Bonferroni correction: γ_music ≈ 6.0 + log(132)/10 ≈ 6.5

**Recommendation:** Start with γ = 6.5, tune based on validation data.

### Background Calculation Window

Space surveillance uses local window (Md × Md pixels).

For music:
- Option 1: **Frequency-local** background (median of nearby frequency bins)
  - Pros: Adapts to frequency-dependent noise
  - Cons: May include chord frequencies in background

- Option 2: **Time-local** background (median across time samples)
  - Pros: Tracks temporal noise variations
  - Cons: Smears out transients

- Option 3: **Global** background (median of entire spectral slice)
  - Pros: Simple, robust
  - Cons: Single value may not capture variations

**Recommendation:** Start with global median (Option 3), then explore frequency-local (Option 1).

### Outlier Removal Threshold

MHTOR uses 3-sigma rule: Reject D(f) > M + 3·S

For music:
- 3-sigma removes ~99.7% of Gaussian outliers
- May be too aggressive for music with strong harmonics

**Recommendation:**
- Start with 3-sigma
- Try 2.5-sigma or 4-sigma based on harmonic content
- Validate with synthetic chords (known ground truth)

---

## Validation Strategy

### Test Case 1: Synthetic Single Chord

Generate pure C major chord:
```python
# Generate C4 (261.63 Hz), E4 (329.63 Hz), G4 (392.00 Hz)
t = np.linspace(0, 1.0, 44100)
signal = (np.sin(2*np.pi*261.63*t) +
          np.sin(2*np.pi*329.63*t) +
          np.sin(2*np.pi*392.00*t))

# Add white noise
signal += 0.1 * np.random.randn(len(signal))

# Run MHT detector
spectral_data = analyzer.dotop(signal)
result = mht_detector.detect(spectral_data[:, 0])

# Expected: detected=True, chord='C_major', SNR > 6.5
```

### Test Case 2: Chord Progression

Generate I-IV-V-I progression in C major:
```python
chords = [
    ('C_major', 0.0, 1.0),   # C major, 0-1 sec
    ('F_major', 1.0, 2.0),   # F major, 1-2 sec
    ('G_major', 2.0, 3.0),   # G major, 2-3 sec
    ('C_major', 3.0, 4.0),   # C major, 3-4 sec
]

# Generate audio with these chords
# Run MHT detector on each time slice
# Validate that detected chords match ground truth
```

### Test Case 3: Real Audio (Amazing Grace)

Use round-trip MIDI → WAV:
- Convert Amazing Grace MIDI to WAV
- Known chord progression
- Run MHT detector
- Compare detected chords vs expected chords

---

## Comparison to Current System

| Aspect | Current (chord_recognizer.py) | MHT-Based Detector |
|--------|------------------------------|-------------------|
| **Input** | Detected fundamentals (post-processing) | Raw spectral data (direct) |
| **Noise handling** | None | Median background + outlier removal |
| **Detection method** | Graph correlation | Matched-filter SNR |
| **Confidence metric** | Correlation score (ad-hoc) | SNR (statistical) |
| **False alarm control** | Threshold tuning (empirical) | P_FA (theoretical) |
| **Harmonic rejection** | Depends on upstream | Built-in (MHTOR) |
| **Multi-chord test** | Sequential scoring | Simultaneous M-ary test |
| **Upstream dependency** | Requires HarmonicAnalyzer | Independent |
| **Theory basis** | Music theory graph | Signal detection theory |

---

## Next Steps

### Immediate Implementation (Phase 1)

1. **Implement BHT detector** (`bht_chord_detector.py`)
   - Single chord template
   - Background calculation (median)
   - SNR calculation
   - Threshold test

2. **Test on synthetic data**
   - Single chord (C major)
   - Measure SNR vs noise level
   - Tune threshold

3. **Validate detection probability**
   - Vary SNR (0-20 dB)
   - Plot ROC curve (detection rate vs false alarm rate)
   - Compare to theoretical P_FA

### Medium-Term (Phase 2-3)

4. **Add outlier removal** (MHTOR)
   - Implement 3-sigma rejection
   - Test on harmonics-rich audio
   - Measure improvement in noise estimation

5. **Implement MHT** (`mht_chord_detector.py`)
   - Generate all chord templates
   - M-ary hypothesis test
   - Adjust threshold for multiple hypotheses

6. **Compare with current system**
   - Run both detectors on same audio
   - Measure accuracy, false positives, false negatives
   - Analyze failure cases

### Long-Term (Phase 4)

7. **Integrate with pipeline**
   - Replace `chord_recognizer.py` with MHT detector
   - Run end-to-end tests
   - Measure impact on MIDI transcription quality

8. **Optimize templates**
   - Gaussian weighting
   - Include inversions (e.g., C/E, C/G)
   - Add extended chords (9th, 11th, 13th)
   - Tune template width (σ_spread)

9. **Advanced features**
   - Sub-frame chord detection (analogous to sub-pixel MHT)
   - Chord progression tracking (temporal smoothing)
   - Key-aware template selection (reduce hypothesis space)

---

## Potential Challenges

### 1. Template Sparsity

**Problem:** Musical chords have sparse templates (only 3-7 frequencies active out of 1000+ bins)

**Impact:** Low SNR denominators, high variance in SNR estimates

**Solutions:**
- Use Gaussian-weighted templates (spreads energy)
- Normalize by template energy: `SNR / sqrt(sum(h²))`
- Consider only frequency bands near chord notes

### 2. Harmonic Complexity

**Problem:** Real instruments produce many harmonics, not just fundamentals

**Impact:** Chord templates may not match complex harmonic spectra

**Solutions:**
- Include harmonics in templates: h(f) = h_fundamental(f) + 0.5·h_harmonic1(f) + ...
- Use instrument-specific templates
- Learn templates from training data (NMF, deep learning)

### 3. Polyphonic Interference

**Problem:** Multiple simultaneous chords (e.g., melody + accompaniment)

**Impact:** MHT assumes single chord present, may give ambiguous results

**Solutions:**
- Detect multiple chords (top-N SNR values)
- Separate melody and harmony (source separation)
- Use hierarchical detection (bass notes first, then upper voices)

### 4. Computational Cost

**Problem:** Testing 132 chord templates × 1000 time slices = 132,000 SNR calculations

**Impact:** Slower than current graph-based method

**Solutions:**
- Vectorize SNR calculation (NumPy broadcasting)
- Precompute template norms: `sqrt(sum(h²))`
- Use key-aware pruning (only test chords in detected key)
- Parallel processing (multi-threading)

---

## Conclusion

The MHT-based chord detection approach offers several advantages over the current graph-based system:

1. **Direct spectral detection** bypasses error-prone fundamental detection
2. **Statistical noise modeling** improves robustness
3. **Outlier rejection** handles harmonics and artifacts
4. **Quantifiable confidence** (SNR) replaces ad-hoc scores
5. **Theoretical foundation** (signal detection theory) enables systematic tuning

The mathematical framework from space object detection translates naturally to music:
- Image frame → Time slice
- PSF → Chord template
- Pixel intensity → Spectral amplitude
- SNR threshold → Chord confidence

**Recommendation:** Implement Phase 1 (BHT) first, validate on synthetic data, then proceed to MHT if results are promising.

---

## References

1. Sligar, A.J. (2015). "Measuring Angular Rate of Celestial Objects Using the Space Surveillance Telescope." AFIT Master's Thesis. *(Source: MHT.md)*

2. Current music transcription system:
   - `spectral_analyzer.py` - Fourier-like frequency decomposition
   - `chord_recognizer.py` - Graph-based chord recognition
   - `audio_graph_builder.py` - NetworkX graph construction
   - `harmonic_analyzer.py` - Louvain community detection

3. Kay, S.M. (1998). "Fundamentals of Statistical Signal Processing: Detection Theory." Prentice Hall.

4. Benesty, J., et al. (2008). "Springer Handbook of Speech Processing." Springer.

---

*Document created: 2025-11-17*
*Status: Proposed enhancement to audio-to-MIDI transcription system*
*Next action: Implement Phase 1 (BHT detector) and validate on synthetic chords*
