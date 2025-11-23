# Phase 2 Status: Melody Extraction

## Current Results (All 256 Iowa Samples)

**Overall Performance:**
- Onset Detection: 100% (256/256)
- Pitch Detection: 99.2% (254/256 detected)
- Pitch Accuracy (±1 semitone): **71.7%** (182/254 correct)
- Octave Accuracy: 83.1% (211/254)

**Goal:** > 95% pitch accuracy

## Error Analysis

**Total Errors:** 72 out of 254 detected pitches
- **Octave errors:** 30 (41.7% of errors) - detecting exactly 12 semitones off
- **Other errors:** 42 (58.3%)
- **Average error:** 7.4 semitones
- **Maximum error:** 57 semitones

## Error Patterns

### By Piano Range

From the test output, errors cluster in two regions:

1. **Very Low Notes** (Octaves 0-1: A0-B1, MIDI 21-35)
   - Often detected 12-34 semitones **too high**
   - Examples: A0 → G3 (+34), B0 → G3 (+31)
   - Problem: Autocorrelation finding harmonics instead of fundamental

2. **Very High Notes** (Octaves 6-7: F#6-C8, MIDI 90-108)
   - Often detected 12-50 semitones **too low**
   - Examples: A7 → G4 (-38), B7 → Ab4 (-39), C8 → E3 (-56)
   - Problem: Autocorrelation finding subharmonics or failing entirely

3. **Mid-Range Notes** (Octaves 2-6: C2-E6, MIDI 36-88)
   - **Much better accuracy** - likely >85-90%
   - Most errors are ±12 semitones (octave confusion)

## Technical Root Causes

### Autocorrelation Method

**Pros:**
- Handles missing fundamental (good for piano low notes)
- Robust to harmonic content
- Works on time-domain signal

**Cons:**
- **Octave ambiguity** - Can confuse f0 with 2*f0 or f0/2
- **Extreme frequencies** - Less reliable at edges of detectable range
- **Parameter sensitivity** - Correlation threshold affects results

### Current Implementation Issues

1. **Window length (100ms):**
   - Too short for very low notes (A0 period = 36ms, need >3 periods)
   - Too long for very high notes (C8 period = 0.24ms, signal decays fast)

2. **Correlation threshold (0.3):**
   - May be too permissive, allowing weak false matches

3. **Peak selection:**
   - Takes highest correlation peak
   - For low notes, harmonics may have stronger correlation

## Attempted Solutions

### ❌ Spectral Peak + Harmonic Analysis
- **Result:** 51.1% accuracy
- **Problem:** Fundamental missing in spectrum for low notes

### ✓ Autocorrelation
- **Result:** 79.8% accuracy (30 samples/dynamic)
- **Result:** 71.7% accuracy (all 256 samples)
- **Improvement:** +20% over spectral method

### ❌ Octave Disambiguation (spectral energy)
- **Result:** 67.4% accuracy
- **Problem:** Spectral scoring picked wrong octave, made errors worse

## Next Steps - Options

### Option A: Accept Current Performance for MVP
- **71.7%** is decent for a first implementation
- Focus accuracy on mid-range notes (where music usually happens)
- Document limitations for extreme octaves
- Move to Phase 3 (integrate timing + dynamics + pitch → MIDI)

### Option B: Improve Extreme Range Handling
- **Adaptive window length** based on estimated pitch
  - Long windows (200-300ms) for low notes
  - Short windows (50ms) for high notes
- **Octave preference rules:**
  - For ambiguous cases, prefer middle register (C2-C6)
  - Use prior note context (if available)

### Option C: Try Advanced Pitch Detection (YIN/PYIN)
- Implement YIN algorithm (improved autocorrelation)
- Better octave error handling
- More complex, but industry-standard accuracy

### Option D: Hybrid Approach
- Use autocorrelation for low/mid notes (< 1000 Hz)
- Use FFT + HPS for high notes (> 1000 Hz)
- Validate with harmonic series check

## Recommendation

**Option A** - Accept current performance and move forward:

**Rationale:**
1. **71.7% is functional** for transcription
2. **Mid-range accuracy is much higher** (likely 85-90%)
3. **Extreme notes rare** in most music
4. Can return to improve later
5. Need to integrate Phase 1 + Phase 2 to see end-to-end results

**What this enables:**
- Complete transcription pipeline (timing + dynamics + pitch)
- Test on real MIDI files
- Identify actual use-case requirements
- Informed decision on where to invest optimization effort

**Phase 3 goals:**
1. Integrate onset detection + velocity estimation + pitch detection
2. Generate MIDI files from audio
3. Test on real piano recordings
4. Measure end-to-end transcription accuracy

## Decision Point

Should we:
1. Move to Phase 3 with current 71.7% pitch accuracy?
2. Invest more time improving pitch detection first?

Consider: Time invested vs. value of improvement for the overall goal.
