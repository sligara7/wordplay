# Success Criteria

## Audio-to-MIDI Transcription System

### Measurable Success Criteria

#### 1. Functional Requirements

##### FR-1: Audio Input Processing
- **Criterion**: System accepts WAV files in standard formats
- **Measurement**: Successfully parse 44.1kHz, 48kHz sample rates; 16-bit, 24-bit depth; mono and stereo
- **Target**: 100% success rate for standard formats
- **Test**: Process 50 WAV files with varying formats

##### FR-2: Fundamental Frequency Detection
- **Criterion**: Correctly identify root notes vs. harmonics
- **Measurement**: Accuracy compared to ground-truth MIDI
- **Target**:
  - Single instrument: ≥ 80% accuracy
  - Polyphonic (2-3 instruments): ≥ 60% accuracy
- **Test**: Benchmark dataset with known MIDI ground truth

##### FR-3: Note Onset Detection
- **Criterion**: Identify when notes start (attack phase)
- **Measurement**: Timing accuracy vs. ground truth
- **Target**:
  - Onset detection within 50ms of ground truth
  - 75% of onsets detected correctly
- **Test**: Piano recordings with known note timings

##### FR-4: Note Duration Estimation
- **Criterion**: Estimate how long notes are held
- **Measurement**: Duration accuracy vs. ground truth
- **Target**:
  - Duration within 100ms for sustained notes
  - 60% accuracy for complex passages
- **Test**: Held note recordings with measured durations

##### FR-5: Multi-Instrument Separation
- **Criterion**: Separate polyphonic recordings into instrument tracks
- **Measurement**: Instrument assignment accuracy
- **Target**:
  - Bass/melody separation: ≥ 70% accuracy
  - 3-instrument separation: ≥ 50% accuracy
- **Test**: Multi-track recordings with isolated instrument tracks

##### FR-6: MIDI File Generation
- **Criterion**: Output valid MIDI format
- **Measurement**: MIDI validation + playback test
- **Target**:
  - 100% valid MIDI files (parseable by mido library)
  - Playback preserves musical intent
- **Test**: Import to DAW (Logic, Ableton, etc.) and verify playback

##### FR-7: Music Theory Constraints
- **Criterion**: Apply scale/chord/progression constraints
- **Measurement**: Detected key signature accuracy
- **Target**:
  - Key detection: ≥ 80% accuracy for tonal music
  - Chord detection: ≥ 60% accuracy
- **Test**: Benchmark with known harmonic analyses

---

#### 2. Performance Requirements

##### PR-1: Processing Speed
- **Criterion**: Process audio in reasonable time
- **Measurement**: Processing time / audio duration
- **Target**:
  - Simple (single instrument): < 1.5x audio duration
  - Complex (polyphonic): < 3x audio duration
- **Test**: Time 100 audio files of varying complexity
- **Example**: 3-minute song should process in < 4.5 minutes (simple) or < 9 minutes (complex)

##### PR-2: Memory Usage
- **Criterion**: Reasonable memory footprint
- **Measurement**: Peak memory usage during processing
- **Target**:
  - < 500MB for 3-minute audio file
  - Linear scaling with audio duration
- **Test**: Monitor memory usage with `memory_profiler`

##### PR-3: Scalability
- **Criterion**: Handle long audio files
- **Measurement**: Max audio duration before failure
- **Target**:
  - Support files up to 30 minutes
  - Graceful degradation for longer files (sliding window)
- **Test**: Process 15-minute, 30-minute, 60-minute files

---

#### 3. Non-Functional Requirements

##### NFR-1: Interpretability
- **Criterion**: Provide explanations for transcription decisions
- **Measurement**: Qualitative assessment + metadata output
- **Target**:
  - Include confidence scores for each note
  - Export graph analysis (community structure, centrality)
  - Human-readable analysis report
- **Test**: Expert review of explanation quality

##### NFR-2: Extensibility
- **Criterion**: Easy to add new analysis methods
- **Measurement**: Lines of code to add new edge type or analysis
- **Target**:
  - Add new edge type: < 50 lines of code
  - Add new analysis algorithm: < 100 lines
- **Test**: Add a "rhythm analysis" module and measure effort

##### NFR-3: Robustness to Noise
- **Criterion**: Handle real-world audio with background noise
- **Measurement**: Accuracy degradation with added noise
- **Target**:
  - SNR > 20dB: < 10% accuracy loss
  - SNR > 10dB: < 25% accuracy loss
- **Test**: Add Gaussian noise to clean recordings

##### NFR-4: Usability (CLI)
- **Criterion**: Simple command-line interface
- **Measurement**: User testing with non-technical users
- **Target**:
  - Single command for basic transcription
  - Helpful error messages
  - Progress indicators for long files
- **Test**: 5 non-technical users can transcribe a file in < 5 minutes

##### NFR-5: API Quality (for developers)
- **Criterion**: Clean Python API for integration
- **Measurement**: API design review
- **Target**:
  - Documented classes and methods (docstrings)
  - Type hints for all public APIs
  - Simple usage examples in README
- **Test**: Code review + external developer feedback

---

### System-Level Success Metrics

#### Metric 1: Overall Transcription Quality
**Formula**: `(correct_notes / total_notes) × (correct_onsets / total_onsets)`

**Targets**:
- Single instrument (piano): ≥ 0.64 (80% × 80%)
- Polyphonic (3 instruments): ≥ 0.36 (60% × 60%)

#### Metric 2: User Satisfaction
**Measurement**: Qualitative feedback from 10 beta testers

**Target**:
- 7/10 users rate quality as "good" or "excellent"
- 8/10 users successfully transcribe a file on first attempt
- 9/10 users understand basic command usage

#### Metric 3: Comparative Performance
**Benchmark**: Compare against existing tools (aubio, librosa + onset detection)

**Target**:
- Match or exceed accuracy of traditional signal processing methods
- Provide better explanations (graph analysis vs. black box)
- Competitive performance (within 2x processing time of fastest tools)

---

### Acceptance Criteria for MVP

**Minimum Viable Product includes**:

1. ✅ WAV input processing (44.1kHz, stereo/mono, 16-bit)
2. ✅ Spectral analysis (using existing spectral_analyzer.py)
3. ✅ Graph construction (temporal + harmonic edges)
4. ✅ Harmonic filtering (community detection)
5. ✅ Onset detection (temporal flow analysis)
6. ✅ MIDI output (valid, playable files)
7. ✅ CLI interface (`python transcribe.py input.wav --output output.mid`)
8. ✅ Basic documentation (README with usage examples)

**Out of scope for MVP** (future enhancements):
- Real-time processing
- Multi-track MIDI with instrument separation
- Advanced music theory (voice leading, modulation detection)
- GUI interface
- Batch processing of multiple files
- Web API

---

### Testing Strategy

#### Unit Tests
- Test each graph builder component independently
- Test harmonic analyzer with synthetic signals (known frequencies)
- Test onset detector with generated attack patterns
- **Target**: 80% code coverage

#### Integration Tests
- End-to-end: WAV input → MIDI output
- Validate MIDI structure and playability
- **Target**: 5 test cases (simple, polyphonic, noisy, edge cases)

#### Benchmarking
- Compare against ground-truth MIDI files
- Measure accuracy, precision, recall
- **Dataset**: 20 recordings with known MIDI transcriptions

#### Performance Testing
- Measure processing time for various audio lengths
- Memory profiling
- **Target**: Meet performance requirements (PR-1, PR-2, PR-3)

---

### Success Review Criteria

**System is considered successful if**:

1. ✅ MVP acceptance criteria met (8/8 items)
2. ✅ Functional requirements targets met (6/7 passing, 80%+ overall)
3. ✅ Performance requirements met (3/3 passing)
4. ✅ User satisfaction ≥ 70% positive feedback
5. ✅ Benchmark comparison: competitive with existing tools

**Decision Point**: After MVP, assess whether to:
- **Continue**: Add multi-instrument separation, real-time processing
- **Iterate**: Improve accuracy before adding features
- **Pivot**: Focus on specific use case (e.g., piano-only tool)
