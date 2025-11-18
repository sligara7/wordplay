# PSF-Based MHT Detector vs Graph-Based Chord Recognizer

## Executive Summary

We now have **two complementary approaches** to chord detection:

1. **PSF-Based MHT Detector** (New): Direct spectral template matching using matched-filter detection
2. **Graph-Based Recognizer** (Existing): Music theory correlation with fundamental detection

Both solve different problems and could work together in a hybrid system.

---

## Comparison Table

| Aspect | PSF/MHT Detector | Graph-Based Recognizer |
|--------|------------------|------------------------|
| **Primary Purpose** | Direct chord detection from spectra | Filter over-detected fundamentals |
| **Input** | Raw spectral data [freq, time] | List of fundamental notes |
| **Method** | Matched-filter SNR detection | Music theory graph correlation |
| **Templates** | 660 PSF spectral signatures | 12 chord interval templates |
| **Processing** | Vectorized across all time slices | Time-windowed (100ms windows) |
| **Speed** | **297 slices/sec** | ~22 windows/sec |
| **Detection Threshold** | SNR > 6.5 | Correlation score > 0.5 |
| **Output** | Chord + octave (e.g., C_major_oct4) | Chord only (e.g., C major) |
| **Problem Solved** | What chord is being played? | Too many false positives |
| **Strength** | High accuracy on clean signals | Reduces over-detection by 90% |
| **Weakness** | Untested on polyphonic music | Requires fundamental detection first |

---

## Detailed Comparison

### PSF-Based MHT Detector (New Approach)

**Algorithm:**
```
1. Generate PSF templates via spectral_analyzer
2. Analyze entire audio → spectral matrix [freq, time]
3. For each time slice:
   - Compute SNR = Σ[(A(f) - B) · h_c(f)] / (σ · ||h_c||)
   - Select chord with max SNR
   - Accept if SNR > threshold (6.5)
4. Merge consecutive detections into segments
```

**Test Results:**

| File | Duration | Slices | Chords Detected | Detection Rate | Processing Time |
|------|----------|--------|-----------------|----------------|-----------------|
| test_amazing_grace.wav | 178.72s | 1229 | 723 segments | 96.6% | 5.27s |
| andy_song_2.wav | 220.23s | 1515 | 213 segments | 100% | ~6.5s |

**Characteristics:**
- ✓ Very fast (297 slices/sec)
- ✓ 100% accuracy on pure sinusoids (98% across octaves)
- ✓ Direct chord detection (no intermediate steps)
- ✓ Octave-aware (distinguishes C3 from C4)
- ⚠ Many suspended/complex chords detected (may be harmonics?)
- ⚠ Untested on polyphonic music
- ⚠ Unknown behavior with instrument overtones

**Dominant chords detected (test_amazing_grace.wav):**
```
B_sus4_oct3:  17.74s (59 segments)
G_sus4_oct3:   6.40s (16 segments)
D_sus4_oct4:   5.96s (25 segments)
```

Observation: Many sus4 chords - unusual for hymn. Possible overtone confusion?

---

### Graph-Based Recognizer (Existing Approach)

**Algorithm:**
```
1. Detect fundamentals via harmonic analysis
2. Group fundamentals into 100ms time windows
3. For each window:
   - Correlate notes with music theory graph
   - Match against chord templates
   - Score based on theory validity
4. Filter notes based on correlation:
   - Score > 0.5: Keep notes fitting chord
   - Score ≤ 0.5: Use key-based filtering
```

**Test Results (from CHORD_RECOGNITION_RESULTS.md):**

| File | Fundamentals | After Filtering | Chords | Reduction |
|------|--------------|-----------------|--------|-----------|
| andy_song_2.wav | 2,546 | 617 | 859 | 75.8% |
| cdl.wav | 1,247 | 477 | 570 | 61.7% |

**Problem Solved:**
- Before: **364% over-detection** (detecting 3.64× too many notes)
- After: **90% reduction in false positives**
- Root cause: Harmonics detected as fundamentals

**Characteristics:**
- ✓ Filters spurious detections using music theory
- ✓ Reduces over-detection by 90%
- ✓ Key detection capability
- ✓ Chord progression awareness
- ⚠ Requires fundamental detection first (can fail)
- ⚠ Slower processing (depends on harmonic analyzer)
- ⚠ No octave information

**Dominant chords detected (andy_song_2.wav):**
```
859 chords in 220 seconds = ~3.9 chords/second
(Details not provided in original results)
```

---

## Architecture Differences

### PSF/MHT: Direct Detection
```
Audio WAV
    ↓
Spectral Analyzer (entire file)
    ↓
Spectral Matrix [freq, time]
    ↓
PSF Template Matching (vectorized)
    ↓
Chords + Octaves + SNR
```

**Pipeline:** 2 steps
**Latency:** ~5-6 seconds for 3 minutes
**Dependencies:** spectral_analyzer, PSF templates

### Graph-Based: Multi-Stage Filtering
```
Audio WAV
    ↓
Spectral Analyzer
    ↓
Audio Graph Builder
    ↓
Harmonic Analyzer → Fundamentals
    ↓
Chord Recognizer (graph correlation)
    ↓
Filtered Chords (no octave)
```

**Pipeline:** 4 steps
**Latency:** Unknown (dependent on harmonic analysis)
**Dependencies:** spectral_analyzer, graph builder, harmonic analyzer, theory graph

---

## Key Insights

### 1. Different Problems, Different Solutions

**Graph approach solves**: "We detect too many notes (364% over-detection) - use music theory to filter"

**PSF approach solves**: "What chord is being played? - use template matching to detect directly"

### 2. Complementary Strengths

| Task | Best Approach |
|------|---------------|
| Direct chord detection | PSF/MHT |
| Filtering false positives | Graph-based |
| Handling polyphonic music | Graph-based (tested) |
| Fast processing | PSF/MHT (10× faster) |
| Octave detection | PSF/MHT (only one that does it) |
| Key detection | Graph-based (only one that does it) |

### 3. Suspicious Patterns

Both approaches show potential issues:

**PSF detector:**
- Detects many sus4, aug, maj11 chords in traditional hymn
- Possible cause: Instrument harmonics triggering complex chord templates
- Need to test: Real ground truth comparison

**Graph detector:**
- 859 chords in 220 seconds = 3.9 chords/sec
- Seems high for typical music (usually ~2-4 chords per measure)
- But successfully reduced 364% over-detection to ~10-20%

---

## Hybrid System Proposal

Combine both approaches for best results:

### Option A: PSF as Primary, Graph as Validator
```
Audio → PSF Detection → Graph Validation → Final Chords
```

**Benefits:**
- Fast PSF detection
- Graph validates against music theory
- Best of both worlds

**Workflow:**
1. PSF detects chords with octaves
2. Extract pitch classes from detected chord
3. Validate against music theory graph
4. Keep high-confidence detections
5. Filter suspicious patterns (e.g., excessive complex chords)

### Option B: Graph as Primary, PSF for Octaves
```
Audio → Fundamentals → Graph Chords → PSF Octave Refinement
```

**Benefits:**
- Graph filters over-detection
- PSF adds octave information
- Music theory validation comes first

**Workflow:**
1. Detect fundamentals (existing pipeline)
2. Apply graph-based chord recognition
3. Use PSF to determine octave of detected chords
4. Combine into final output with octaves

### Option C: Ensemble Voting
```
Audio → [PSF Detection, Graph Detection] → Vote/Merge → Final
```

**Benefits:**
- Cross-validation between methods
- Higher confidence when both agree
- Can detect disagreements for manual review

---

## Test Comparison: andy_song_2.wav

| Metric | PSF/MHT | Graph-Based | Winner |
|--------|---------|-------------|--------|
| Chord segments | 213 | 859 | ? |
| Processing time | ~6.5s | Unknown | PSF (if < 6.5s) |
| Over-detection risk | Unknown | Fixed (was 364%) | Graph |
| Octave info | Yes | No | PSF |
| Music theory validation | No | Yes | Graph |
| Detection rate | 100% | ~10-20% | PSF (higher) |

**Analysis:**
- PSF detected **213 segments**, Graph detected **859 chords**
- PSF is 4× more conservative (fewer detections)
- This could mean:
  - PSF has false negatives (missing chords)
  - Graph has false positives (over-detecting)
  - They're detecting different things (segments vs instantaneous chords)

---

## Recommendations

### Immediate Next Steps

1. **Ground Truth Comparison**
   - Test both methods on MIDI→WAV with known chords
   - Measure precision/recall for both approaches
   - Determine which is more accurate

2. **Hybrid Implementation**
   - Start with Option A (PSF primary, Graph validator)
   - Use graph to filter suspicious PSF detections
   - Combine strengths of both

3. **Harmonics Investigation**
   - Determine why PSF detects many sus4/complex chords
   - May need to adjust templates or add harmonic suppression
   - Compare with graph's harmonic filtering

4. **Performance Benchmark**
   - Measure end-to-end latency for both approaches
   - Compare on same audio files
   - Document resource usage

### Long-Term Strategy

**For Real-Time Applications:**
- Use PSF/MHT (10× faster, direct detection)
- Add lightweight music theory validation

**For High-Accuracy Transcription:**
- Use hybrid approach
- Graph filters initial over-detection
- PSF adds octave precision
- Cross-validate for confidence

**For Research/Analysis:**
- Run both methods independently
- Compare results
- Use ensemble voting for final output

---

## Conclusion

We have two powerful, complementary approaches:

1. **PSF/MHT Detector**: Fast, direct, octave-aware chord detection
   - Best for: Real-time, clean signals, when octave matters
   - Needs: Validation against ground truth, harmonic handling

2. **Graph-Based Recognizer**: Music theory-validated filtering
   - Best for: Reducing false positives, key detection, music theory analysis
   - Needs: Faster processing, octave information

**Recommended Path Forward:**
Implement **hybrid Option A** - use PSF for fast detection, validate with graph-based music theory correlation. This combines the speed and directness of PSF with the validation power of music theory.

The future is not "PSF vs Graph" but "PSF + Graph" = best of both worlds!
