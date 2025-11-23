# Pipeline2: Integration with Existing MHT System

## What We Built

Pipeline2 **integrates** the existing, proven MHT components with the original design flow:

```
MIDI Input → Synthesis → Spectral Analysis → MHT Detection → Validation
```

## Key Insight

**We didn't need to rebuild MHT detection!** You already had:

1. ✅ **UltraFastChordDetector** (`ultra_fast_detector.py`)
   - Vectorized matrix multiplication
   - `PSF_matrix @ spectral_data = correlations` (all at once!)
   - MHTOR outlier removal
   - SNR-based matched-filter detection

2. ✅ **Multi-Octave PSF Templates** (`multi_octave_psf_templates.pkl`)
   - 660 templates (12 roots × 11 types × 5 octaves)
   - Pre-built via `build_multi_octave_psf.py`
   - Generated from actual synthesized chords

3. ✅ **Spectral Analyzer** (`spectral_analyzer.py`)
   - Your custom Fourier-like analysis
   - Musical frequency optimization
   - 4 cycles of A0 analysis window

## What Pipeline2 Adds

### New Components Created

1. **`midi_synthesizer.py`** - NEW ✨
   - Synthesizes MIDI to WAV using `synthesize_instruments/`
   - Pure synthesis (no external samples needed)
   - Extracts ground truth chords from MIDI
   - Supports percussion, brass, strings, piano

2. **`pipeline_v2.py`** - NEW ✨
   - Integrates MIDI synthesis + existing MHT detection
   - Automatic ground truth validation
   - Precision/Recall/F1 metrics
   - Handles octave-agnostic chord matching

3. **Test MIDI Files** - NEW ✨
   - `examples/simple_c_major.mid`
   - `examples/chord_progression.mid` (I-IV-V-I)
   - `examples/c_scale.mid`

### Files NOT Used (Replaced by Existing)

1. ❌ **`mht_pipeline.py`** - REPLACED by `ultra_fast_detector.py`
   - My version was essentially recreating what you already had
   - Your version is more mature and tested

2. ❌ **`pipeline.py`** - REPLACED by `pipeline_v2.py`
   - pipeline.py used my new mht_pipeline.py
   - pipeline_v2.py uses your existing ultra_fast_detector.py

## Architecture Comparison

### What You Were Already Using (test_roundtrip_hard_mode.py)

```python
# 1. MIDI → WAV
from reco_enhanced import midi_to_wav

# 2. Spectral Analysis
from spectral_analyzer import SpectralAnalyzer
spectral_data = analyzer.dotop(audio)

# 3. MHT Detection
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs

templates, frequencies, metadata = load_multi_octave_psfs("multi_octave_psf_templates.pkl")
detector = UltraFastChordDetector(templates, threshold=6.5)
results = detector.detect_all_time_slices(spectral_data)

# 4. Theory Filtering (HARD/MEDIUM/SOFT)
from aggressive_theory_filter import AggressiveTheoryFilter
filter_results = filter.detect_with_aggressive_filtering(snr_matrix, ...)
```

### What Pipeline2 V2 Does

```python
# 1. MIDI → WAV (NEW synthesis approach)
from midi_synthesizer import MIDISynthesizer  # NEW
synth = MIDISynthesizer(sample_rate=44100)
audio, midi_data = synth.synthesize_from_file(midi_path)  # Extracts ground truth

# 2. Spectral Analysis (SAME)
from spectral_analyzer import SpectralAnalyzer
spectral_data = analyzer.dotop(audio)

# 3. MHT Detection (SAME - using your existing code)
from ultra_fast_detector import UltraFastChordDetector
from build_multi_octave_psf import load_multi_octave_psfs

detector = UltraFastChordDetector(templates, threshold=6.5)
results = detector.detect_all_time_slices(spectral_data)

# 4. Validation (NEW)
validation = validate_against_ground_truth(
    detected_chords,
    midi_data['chords']  # Ground truth from MIDI
)
```

## Key Differences

| Aspect | test_roundtrip_hard_mode.py | pipeline2_v2.py |
|--------|---------------------------|-----------------|
| **Input** | MIDI file | MIDI file |
| **Synthesis** | reco_enhanced (external samples?) | midi_synthesizer (pure synthesis) |
| **Spectral** | spectral_analyzer.py | spectral_analyzer.py ✅ |
| **MHT** | UltraFastChordDetector | UltraFastChordDetector ✅ |
| **PSF Templates** | multi_octave_psf_templates.pkl | multi_octave_psf_templates.pkl ✅ |
| **Filtering** | AggressiveTheoryFilter (HARD/MEDIUM/SOFT) | Direct SNR threshold |
| **Output** | Chord counts, statistics | Ground truth validation metrics |
| **Validation** | Manual inspection | Automatic Precision/Recall/F1 |
| **Ground Truth** | Not extracted automatically | Extracted from MIDI |

## What We Can Do Now

### 1. Test on Simple MIDI Files

```bash
cd pipeline2
python pipeline_v2.py examples/simple_c_major.mid
```

Expected:
- Synthesize C major chord
- Detect via MHT
- Validate: 100% precision/recall (if working correctly)

### 2. Compare Synthesis Methods

Test same MIDI file with:
- **A**: reco_enhanced.py (your existing)
- **B**: midi_synthesizer.py (new pure synthesis)

Compare chord detection results.

### 3. Ground Truth Validation

For any MIDI file:
1. Extract ground truth chords automatically
2. Synthesize and detect
3. Get objective metrics (not just "looks good")

### 4. Tune Parameters

With automatic validation, we can:
- Sweep MHT threshold (5.0 → 8.0)
- Try different sigma values for noise estimation
- Compare MHTOR on/off
- Optimize F1 score

## Missing Pieces (Optional)

1. **AggressiveTheoryFilter** ❓
   - You referenced it in test_roundtrip_hard_mode.py
   - File doesn't exist in the codebase (yet)
   - Could be integrated into pipeline_v2.py

2. **reco_enhanced.py** ❓
   - Used in test_roundtrip_hard_mode.py
   - File doesn't exist (yet)
   - Might be in a different location?

3. **Theory Filtering Modes** ⬜
   - HARD, MEDIUM, SOFT, BASELINE
   - Could add to pipeline_v2.py as optional parameter

## Next Steps

### Immediate (1-2 hours)

1. ✅ Created pipeline2 structure
2. ✅ Created midi_synthesizer.py
3. ✅ Created pipeline_v2.py (integrating existing MHT)
4. ✅ Created test MIDI files
5. ⬜ **Run pipeline_v2.py on test MIDI files**
6. ⬜ Debug any issues
7. ⬜ Verify ground truth validation works

### Short-term (1 day)

8. ⬜ Compare synthesis: reco_enhanced vs midi_synthesizer
9. ⬜ Find/integrate AggressiveTheoryFilter
10. ⬜ Add filtering modes to pipeline_v2
11. ⬜ Parameter sweep (threshold, sigma, etc.)

### Long-term (1 week)

12. ⬜ Process real MIDI files (Amazing Grace, etc.)
13. ⬜ Build ROC curves (threshold vs precision/recall)
14. ⬜ Compare with pipeline/ results
15. ⬜ Publication-quality results

## File Structure

```
pipeline2/
├── README.md                          ✅ Original design documentation
├── STATUS.md                          ✅ Development status
├── INTEGRATION_SUMMARY.md             ✅ This file
├── midi_synthesizer.py                ✅ NEW: MIDI → WAV with ground truth
├── pipeline_v2.py                     ✅ NEW: Integrated pipeline
├── create_test_midi.py                ✅ NEW: Test file generator
├── examples/
│   ├── simple_c_major.mid            ✅ Test case
│   ├── chord_progression.mid         ✅ Test case
│   └── c_scale.mid                   ✅ Test case
├── mht_pipeline.py                    ⚠️ Not used (replaced by ultra_fast_detector)
└── pipeline.py                        ⚠️ Not used (replaced by pipeline_v2)
```

**Files Used from Parent Directory:**

```
../
├── spectral_analyzer.py               ✅ Your custom Fourier analysis
├── ultra_fast_detector.py            ✅ Vectorized MHT (THE KEY COMPONENT)
├── build_multi_octave_psf.py         ✅ PSF generation
├── multi_octave_psf_templates.pkl    ✅ Pre-built templates (660 chords)
├── bht_chord_detector.py             ⚠️ Original BHT (not used, ultra_fast is better)
└── synthesize_instruments/            ✅ Instrument synthesizers
    ├── __init__.py
    ├── synthesize_common_percussion.py
    ├── synthesize_brass.py
    └── synthesize_string_instruments.py
```

## Conclusion

**Pipeline2 successfully integrates your proven MHT detection system with MIDI-based ground truth validation.**

The key insight was that you already had all the hard parts:
- ✅ Vectorized MHT detection
- ✅ Multi-octave PSF templates
- ✅ Spectral analysis

What we added:
- ✨ MIDI synthesis with ground truth extraction
- ✨ Automatic validation metrics
- ✨ Test framework

**This is the original design you wanted:** MIDI → Spectral → MHT, using the matrix-based rapid approach!

---

**Ready to test:**

```bash
cd /home/ajs7/project/wordplay/music/new_start/pipeline2
python pipeline_v2.py examples/simple_c_major.mid test_output.wav
```

If this works, we'll have:
- ✅ MIDI ground truth extraction
- ✅ Synthesis to WAV
- ✅ Spectral analysis
- ✅ Vectorized MHT detection
- ✅ Automatic validation
- ✅ Precision/Recall/F1 metrics

All using your existing, proven MHT system! 🎉
