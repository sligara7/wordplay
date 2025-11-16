# Component Deltas Summary

**System**: Audio-to-MIDI Transcription
**Date**: 2025-11-16
**Total Components**: 3 new components
**Total Estimated Effort**: 26-36 hours

---

## Overview

This document summarizes the exact code-level changes required to complete the audio-to-MIDI transcription pipeline. All 3 missing components have been specified in detail with class/function signatures, logic flows, and integration points.

---

## GAP-001: Onset Detector

**File**: `onset_detector.py`
**Estimated Effort**: 12-16 hours
**Priority**: 1 (CRITICAL)
**Lines of Code**: 300-400

### Key Components
- **Class**: `OnsetDetector`
  - `calculate_intensity_derivatives()` - Temporal intensity analysis
  - `detect_onsets_for_frequency()` - Peak detection in derivatives
  - `estimate_note_duration()` - Follow decay to find offset
  - `detect_onsets()` - Main method coordinating onset detection
  - `intensity_to_velocity()` - Convert to MIDI velocity

- **Function**: `frequency_to_midi_note()` - Hz → MIDI number conversion

### Inputs
- NetworkX MultiDiGraph (from audio_graph_builder)
- List of fundamental notes (from harmonic_analyzer)

### Outputs
- List of note events: `{onset_time_seconds, duration_seconds, velocity, note_name, midi_note}`

### Dependencies
- networkx
- numpy
- typing, collections

### Validation Criteria
- Onset timing accuracy within 50ms
- Detect ≥90% of true onsets
- False positive rate <10%
- Duration estimates within 100ms

---

## GAP-002: MIDI Generator

**File**: `midi_generator.py`
**Estimated Effort**: 8-12 hours
**Priority**: 2 (CRITICAL)
**Lines of Code**: 200-300

### Key Components
- **Class**: `MidiGenerator`
  - `note_name_to_midi_number()` - Parse note names like "C4"
  - `seconds_to_ticks()` - Convert time to MIDI ticks
  - `create_midi_track()` - Build track from note events
  - `add_metadata()` - Set tempo, time sig, key
  - `generate_midi()` - Main method creating MIDI file
  - `validate_note_events()` - Input validation

### Inputs
- List of note events from onset_detector

### Outputs
- MIDI file (.mid) written to disk

### Dependencies
- mido (MIDI library)
- typing, pathlib

### Validation Criteria
- Valid MIDI files (parseable by mido)
- Playable in DAWs (Logic, Ableton, MuseScore)
- Timing accuracy within 1ms
- Correct velocity mapping (0-127)

---

## GAP-003: Pipeline Orchestrator

**File**: `audio_to_midi_pipeline.py`
**Estimated Effort**: 6-8 hours
**Priority**: 3 (CRITICAL)
**Lines of Code**: 150-250

### Key Components
- **Function**: `transcribe()` - Main orchestration logic
  1. Validate input WAV file
  2. Run spectral analysis (SpectralAnalyzer)
  3. Build graph (AudioGraphBuilder)
  4. Detect fundamentals (HarmonicAnalyzer)
  5. Detect onsets (OnsetDetector)
  6. Generate MIDI (MidiGenerator)

- **Function**: `main()` - CLI entry point
  - Argument parsing with argparse
  - Progress feedback
  - Error handling

- **Function**: `validate_wav_file()` - Input validation

### CLI Interface
```bash
python audio_to_midi_pipeline.py INPUT.wav [OPTIONS]

Options:
  --output, -o PATH            Output MIDI file (default: INPUT.mid)
  --intensity-threshold FLOAT  Graph node threshold (default: 0.05)
  --confidence FLOAT           Fundamental confidence (default: 0.3)
  --min-duration INT           Min sustained samples (default: 3)
  --tempo INT                  MIDI tempo in BPM (default: 120)
  --verbose, -v                Verbose output
```

### Inputs
- WAV file from filesystem

### Outputs
- MIDI file to filesystem
- Status messages to console

### Dependencies
- All pipeline components (spectral_analyzer, audio_graph_builder, harmonic_analyzer, onset_detector, midi_generator)
- argparse, scipy, pathlib, sys

### Validation Criteria
- Single command transcribes WAV to MIDI
- Helpful error messages
- Processing time < 3x audio duration
- Memory usage < 500MB for 3-min files

---

## Implementation Order

### Phase 1: Core Analysis (Priority 1)
1. **Onset Detector** (12-16h)
   - No dependencies on other missing components
   - Enables note timing detection
   - Most complex component

### Phase 2: Output Generation (Priority 2)
2. **MIDI Generator** (8-12h)
   - Depends on onset_detector completion
   - Standard MIDI file generation
   - Moderate complexity

### Phase 3: User Interface (Priority 3)
3. **Pipeline Orchestrator** (6-8h)
   - Depends on onset_detector + midi_generator
   - Ties everything together
   - Simplest component (mostly coordination)

---

## Testing Strategy

### Unit Tests
- `tests/test_onset_detector.py` (150-200 lines)
- `tests/test_midi_generator.py` (100-150 lines)
- `tests/test_pipeline.py` (150-200 lines)

### Integration Tests
- End-to-end: WAV → MIDI with sample files
- Validate MIDI output is playable
- Benchmark accuracy against ground truth

### Total Test Code
- Estimated 400-550 lines of test code
- Target coverage: >70%

---

## Total Effort Breakdown

| Component | Effort | Lines | Priority |
|-----------|--------|-------|----------|
| onset_detector | 12-16h | 300-400 | 1 |
| midi_generator | 8-12h | 200-300 | 2 |
| pipeline_orchestrator | 6-8h | 150-250 | 3 |
| **TOTAL** | **26-36h** | **650-950** | - |

**Plus testing**: +8-12 hours for comprehensive test coverage

**Grand total**: 34-48 hours for complete implementation with tests

---

## Next Steps (BU-05)

With component deltas complete, we can now:
1. Design the formal integration architecture
2. Create service_architecture.json files
3. Define interface contracts
4. Generate system graph
5. Validate the architecture

All implementation details are now specified and ready for development.
