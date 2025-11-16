# Component Inventory Summary

**System**: Audio-to-MIDI Transcription
**Date**: 2025-11-16
**Approach**: Bottom-Up Integration

## Overview

This system integrates existing audio analysis components into a cohesive audio-to-MIDI transcription pipeline using graph theory and NetworkX algorithms.

**Total Components**: 8 (3 complete, 3 to implement, 2 supporting utilities)

---

## Component Hierarchy

### Tier 1: Input Processing
- **spectral_analyzer** ✅ COMPLETE
  - Reads WAV files
  - Performs Fourier-like spectral analysis
  - Outputs: 2D frequency-time-intensity matrix

### Tier 2: Graph Construction
- **audio_graph_builder** ✅ COMPLETE
  - Converts spectral data to NetworkX graph
  - Creates temporal edges (frequency across time)
  - Creates harmonic edges (related frequencies)
  - Outputs: NetworkX MultiDiGraph

### Tier 3: Analysis
- **harmonic_analyzer** ✅ COMPLETE
  - Uses community detection (Louvain algorithm)
  - Identifies fundamental frequencies
  - Filters harmonics from root notes
  - Outputs: Timeline of fundamental notes with confidence scores

- **onset_detector** ⚠️ NOT STARTED
  - Detects note onsets using temporal flow
  - Distinguishes attack vs. sustain
  - Estimates note durations
  - Required for: Note timing information

### Tier 4: Output Generation
- **midi_generator** ⚠️ NOT STARTED
  - Converts notes to MIDI format
  - Uses mido library
  - Supports multi-track output
  - Required for: Final MIDI file output

### Tier 5: Orchestration
- **pipeline_orchestrator** ⚠️ NOT STARTED
  - CLI entry point
  - Coordinates all components
  - Handles errors and progress reporting
  - Required for: End-to-end workflow

### Supporting Utilities (Optional)
- **audio_converter** ✅ COMPLETE
  - Converts audio formats (MP3, FLAC → WAV)
  - Uses ffmpeg
  - Optional: For preprocessing non-WAV files

- **midi_parser** ✅ COMPLETE
  - Parses existing MIDI files
  - Optional: For validation against ground truth

---

## Integration Status

### ✅ Complete & Ready (3)
1. **spectral_analyzer.py** - Proven, working implementation
2. **audio_graph_builder.py** - Newly created, implements graph construction
3. **harmonic_analyzer.py** - Newly created, implements community detection

### ⚠️ Need Implementation (3)
1. **onset_detector.py** - Design specified in AUDIO_TRANSCRIPTION.md
2. **midi_generator.py** - Standard MIDI file generation using mido
3. **audio_to_midi_pipeline.py** - Main orchestrator tying components together

### Critical Path
```
WAV file
  → spectral_analyzer (✅)
    → audio_graph_builder (✅)
      → harmonic_analyzer (✅)
        → onset_detector (⚠️)
          → midi_generator (⚠️)
            → MIDI file
```

**All orchestrated by**: pipeline_orchestrator (⚠️)

---

## Dependencies

### Internal Dependencies
- `onset_detector` depends on: `audio_graph_builder`, `harmonic_analyzer`
- `midi_generator` depends on: `harmonic_analyzer`, `onset_detector`
- `pipeline_orchestrator` depends on: **all core components**

### External Dependencies
- **numpy** - Numerical computing (all components)
- **networkx** - Graph analysis (graph_builder, harmonic_analyzer, onset_detector)
- **scipy** - Scientific computing (spectral_analyzer)
- **mido** - MIDI file I/O (midi_generator)
- **matplotlib** - Visualization (spectral_analyzer, optional)

### System Dependencies (Optional)
- **ffmpeg** - Audio format conversion (audio_converter)

---

## Integration Readiness Assessment

### High Readiness (5)
- spectral_analyzer
- audio_graph_builder
- harmonic_analyzer
- audio_converter
- midi_parser (partial - for validation)

### Low Readiness (3)
- onset_detector (not started)
- midi_generator (not started)
- pipeline_orchestrator (not started)

---

## Next Steps

1. **BU-02**: Define integration requirements - how components should interact
2. **BU-03**: Analyze integration gaps - what's missing between components
3. **BU-04**: Generate component deltas - specific code changes needed
4. **BU-05**: Design integration architecture - formal service architecture
5. **BU-06**: Validate and generate system graph

---

## Excluded Components

**reco.py**: Audio synthesis from MIDI (reverse direction). Not needed for this pipeline.

**convert_tool.py**: Thin wrapper around convert_audio.py. Redundant.
