# User Scenarios

## Audio-to-MIDI Transcription System

### User Personas

#### Persona 1: Professional Musician (Maria)
- **Background**: Classical pianist, music teacher
- **Technical Skill**: Basic computer use, no programming
- **Goal**: Transcribe piano recordings of student performances for analysis
- **Pain Point**: Manual transcription is time-consuming and tedious

#### Persona 2: Music Researcher (Dr. James)
- **Background**: Musicology professor, studies harmonic structure
- **Technical Skill**: Intermediate Python, familiar with data analysis
- **Goal**: Analyze harmonic progressions in jazz recordings
- **Pain Point**: Existing tools don't explain WHY they made transcription decisions

#### Persona 3: Music App Developer (Alex)
- **Background**: Software engineer building music education apps
- **Technical Skill**: Advanced programming, familiar with APIs
- **Goal**: Integrate automated transcription into their application
- **Pain Point**: Black-box ML models don't integrate well with music theory

#### Persona 4: Hobbyist Composer (Sam)
- **Background**: Amateur musician, learns songs by ear
- **Technical Skill**: Basic command line, some Python experience
- **Goal**: Quickly get MIDI files from YouTube audio downloads
- **Pain Point**: Wants simple CLI tool, doesn't care about technical details

---

## Use Cases

### Use Case 1: Single-Instrument Piano Transcription

**Actor**: Maria (Professional Musician)

**Scenario**:
Maria records a student's piano performance as a WAV file. She wants to transcribe it to MIDI to:
1. Identify wrong notes or timing errors
2. Provide visual feedback (MIDI can be imported to notation software)
3. Compare with the original score

**Steps**:
1. Maria runs: `python audio_to_midi_pipeline.py student_performance.wav --output student.mid`
2. System analyzes the WAV file using spectral analysis
3. System builds graph of frequency-time-intensity relationships
4. System identifies fundamental frequencies (separating harmonics)
5. System detects note onsets and durations
6. System generates MIDI file: `student.mid`
7. Maria imports MIDI into MuseScore or Finale for notation

**Success Criteria**:
- 90%+ note accuracy for single-instrument piano
- Correct onset timing (within 50ms)
- Reasonable note durations (quantized to musical values)
- Processing time < 2x audio duration

---

### Use Case 2: Polyphonic Jazz Analysis

**Actor**: Dr. James (Music Researcher)

**Scenario**:
Dr. James has a jazz trio recording (piano, bass, drums). He wants to:
1. Separate the three instruments into separate tracks
2. Analyze the harmonic progression of the piano part
3. Study the voice leading (how chords connect)

**Steps**:
1. Dr. James runs: `python audio_to_midi_pipeline.py jazz_trio.wav --separate-instruments --output-format multi-track`
2. System builds multi-layer graph (one layer per instrument)
3. System uses spectral range clustering to separate bass/harmony/melody
4. System applies community detection to identify harmonic communities
5. System analyzes chord progressions using music theory edges
6. System generates multi-track MIDI with separate channels
7. System produces analysis report: `jazz_trio_analysis.json`
8. Dr. James reviews the graph visualization showing harmonic relationships

**Success Criteria**:
- Successfully separate 3 instruments
- Identify chord progressions with 70%+ accuracy
- Provide human-readable explanation of decisions
- Generate visualization of harmonic graph

---

### Use Case 3: API Integration for Music App

**Actor**: Alex (Music App Developer)

**Scenario**:
Alex is building a "learn to play" app. Users upload recordings and want:
1. Automatic transcription to MIDI
2. Difficulty rating (based on note complexity)
3. Suggested fingerings (requires MIDI)

**Steps**:
1. Alex integrates the transcription library into their Python backend
2. User uploads WAV file via web interface
3. Backend calls: `transcriber.transcribe(wav_file, confidence_threshold=0.8)`
4. System returns MIDI data structure + metadata (confidence scores, detected key, etc.)
5. Alex's app uses MIDI data to generate fingering suggestions
6. Alex queries metadata for note density → difficulty rating

**Success Criteria**:
- Library provides clean Python API
- Returns structured data (not just MIDI file)
- Includes confidence scores for quality filtering
- Processing time suitable for web app (< 30 seconds for 3-minute song)

---

### Use Case 4: Quick CLI Transcription

**Actor**: Sam (Hobbyist Composer)

**Scenario**:
Sam downloaded audio from YouTube and wants MIDI quickly. Doesn't care about perfect accuracy.

**Steps**:
1. Sam runs: `transcribe song.wav`
2. System transcribes using default settings
3. System outputs: `song.mid` in same directory
4. Sam imports to their DAW (Digital Audio Workstation)

**Success Criteria**:
- Single command execution
- Reasonable default parameters
- Outputs standard MIDI format
- Works with common WAV formats (44.1kHz, stereo, 16-bit)

---

## User Journey Maps

### Journey 1: From Audio File to Sheet Music

```
1. User has audio recording (WAV)
   ↓
2. User runs transcription tool
   ↓
3. System analyzes audio (spectral → graph → analysis)
   ↓
4. System outputs MIDI file
   ↓
5. User imports MIDI to notation software (MuseScore, Finale, etc.)
   ↓
6. User reviews and corrects transcription
   ↓
7. User exports to PDF sheet music
```

**Pain Points to Address**:
- Step 6: Make transcription accurate enough to minimize corrections
- Step 3: Provide progress feedback for long files
- Step 4: Include metadata (confidence scores) to highlight uncertain sections

### Journey 2: From Research Question to Insight

```
1. Researcher has hypothesis about musical structure
   ↓
2. Researcher collects audio dataset
   ↓
3. Researcher runs batch transcription
   ↓
4. System outputs MIDI + analysis reports
   ↓
5. Researcher analyzes graph structures (harmonics, progressions, etc.)
   ↓
6. Researcher validates hypothesis
```

**Pain Points to Address**:
- Step 5: Provide visualization tools for graph analysis
- Step 4: Export analysis in research-friendly formats (JSON, CSV)
- Step 3: Support batch processing of multiple files

---

## Non-Functional Requirements (Derived from Scenarios)

1. **Usability**: Simple CLI for non-technical users, Python API for developers
2. **Accuracy**: 80-90% note detection for single instrument, 60-70% for polyphonic
3. **Performance**: Near real-time processing (< 2x audio duration)
4. **Interpretability**: Provide explanations for transcription decisions
5. **Extensibility**: Easy to add new analysis algorithms
6. **Compatibility**: Standard MIDI output, WAV input (common formats)
7. **Robustness**: Handle various audio qualities (recordings, studio, live)
