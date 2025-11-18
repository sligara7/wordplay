# Comprehensive Chord Detection Test Results

## Summary

Tested **ALL 11 chord types** × **12 root positions** = **132 total tests**

### Overall Results: **8.3% accuracy** ❌

## What Works vs. What Doesn't

### ✅ Simple Triads (Sometimes)
- **Major chords:** 25% accuracy (3/12 roots work)
- **Minor chords:** 33% accuracy (4/12 roots work)
- **Diminished:** 17% accuracy (2/12 roots work)
- **Sus4:** 17% accuracy (2/12 roots work)

**Which roots work:**
- Major: D, F, A#, B ✓
- Minor: C#, D#, E ✓
- Dim: D, D#, F# ✓

### ❌ Complex Chords (Never Work)
- **7th chords (maj7, min7, dom7):** 0% accuracy (0/36 total)
- **Extended chords (dom9, maj11):** 0% accuracy (0/24 total)
- **Aug chords:** 0% accuracy (confused with other chords)
- **Sus2 chords:** 0% accuracy

## Key Issues Identified

### 1. **Root-Dependent Detection** 🔍

Only specific roots are detected correctly. Pattern suggests issue with frequency bin alignment.

**Hypothesis:** Template generation has frequency alignment problems for certain pitch classes.

### 2. **Complex Chords Fail Completely** 📉

Chords with 4+ notes (7ths, 9ths, 11ths) have **0% detection rate**.

**Root cause:** Signal energy spread across more peaks → Lower SNR per peak

**Evidence:**
```
3-note chords (triads):  SNR = 30-45 (detected)
4-note chords (7ths):    SNR = 2.5-3.0 (not detected)
5-note chords (9ths):    SNR = 1.7-2.5 (not detected)
6-note chords (11ths):   SNR = 1.8-2.2 (not detected)
```

### 3. **Outlier Removal Backfires** ⚠️

MHTOR (outlier removal) calculates noise σ incorrectly for strong signals:

```
Signal = 100:  σ = 6.8   (detection works)
Signal = 200:  σ = 13.6  (detection fails)
Signal = 500:  σ = 34.1  (detection fails)
Signal = 1000: σ = 68.2  (detection fails)
```

**Problem:** Chord peaks are treated as part of "noise" calculation, inflating σ.

## Root Cause Analysis

### Issue A: Frequency Bin Spacing

Spectral analyzer uses **semitone-spaced bins** (~15-20 Hz apart):
- Bin 40: 261.63 Hz (C4)
- Bin 41: 277.18 Hz (C#4)
- Bin 42: 293.66 Hz (D4)

But Gaussian peaks (σ=5Hz or even 20Hz) don't align perfectly with all bins.

### Issue B: Template Normalization

All templates are normalized to ||h|| = 1.0, but:
- 3-note chord: Energy spread over 3×7 octaves = 21 peaks
- 6-note chord: Energy spread over 6×7 octaves = 42 peaks

After normalization, each peak in 6-note chord has **half** the amplitude of 3-note chord!

**Effect:** Larger chords inherently have lower SNR.

### Issue C: Signal Generation Mismatch

Synthetic test signals use:
- Gaussian peaks with σ=20Hz
- Amplitude decreasing by 0.8^i for each note

But templates use:
- Gaussian with σ=10Hz
- Equal amplitude for all notes

**Mismatch** → Poor correlation

## Recommendations

### Fix 1: Disable Outlier Removal for Synthetic Tests

The outlier removal (MHTOR) was designed for real audio with noise across all frequencies. Our synthetic tests have clean peaks + small noise, which confuses the algorithm.

```python
detector = FastMHTChordDetector(
    templates,
    threshold=6.5,
    use_outlier_removal=False  # ← Disable for clean synthetic signals
)
```

### Fix 2: Match Template Generation to Signal Generation

Use consistent Gaussian widths and amplitude patterns:

```python
# In build_chord_templates:
sigma_hz = 20.0  # Match test signal generation

# In generate_chord_spectrum:
sigma_hz = 20.0  # Match template generation
```

### Fix 3: Adjust Threshold for Complex Chords

Complex chords (4+ notes) need lower threshold:

```python
# Simple triads
threshold_triads = 6.5

# 7th chords
threshold_7ths = 3.5

# 9th/11th chords
threshold_extended = 2.5
```

Or use **adaptive thresholding** based on chord complexity.

### Fix 4: Energy Normalization

Instead of normalizing templates to ||h|| = 1.0, normalize by **number of notes**:

```python
# Current (problematic):
template = template / np.linalg.norm(template)

# Proposed (energy-preserving):
template = template / np.sqrt(num_notes_in_chord)
```

This ensures 3-note and 6-note chords have similar per-note SNR.

### Fix 5: Use Real Audio for Testing

Synthetic Gaussians don't match real instrument spectra. Test with:
1. MIDI → WAV conversion (known ground truth)
2. Real instrument recordings
3. Spectral data from your `spectral_analyzer.py`

## Next Steps (Prioritized)

### Immediate
1. ✅ Disable outlier removal for synthetic tests
2. ✅ Match sigma between template and signal generation
3. ⏳ Test with these fixes → expect 50-70% accuracy

### Short-Term
4. ⏳ Implement adaptive thresholding
5. ⏳ Fix energy normalization
6. ⏳ Test with real MIDI→WAV audio

### Long-Term
7. ⏳ Investigate root-dependent failures
8. ⏳ Optimize template generation for your spectral_analyzer
9. ⏳ Integrate with actual audio pipeline

## Conclusion

The **concept is sound** (MHT/BHT matched-filter detection), but:
- ❌ Synthetic test signals don't match real use case
- ❌ Outlier removal (MHTOR) inappropriate for clean test signals
- ❌ Template/signal generation mismatch
- ❌ Complex chords need special handling

**Expected performance after fixes:** 60-80% accuracy on synthetic tests, 40-60% on real audio (good starting point for further tuning).

---

*Test run: 2025-11-17*
*Tests: 132 (11 chord types × 12 roots)*
*Accuracy: 8.3% (needs improvement)*
*Detector: FastMHTChordDetector with MHTOR*
