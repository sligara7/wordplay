# System Mission Statement

## Audio-to-MIDI Transcription System

### Purpose

This system implements a novel graph-based approach to transcribing audio recordings (WAV files) into MIDI format and sheet music. Unlike traditional signal processing methods, this approach treats frequency-time-intensity data as a network of relationships that can be analyzed using graph theory.

### Primary Objectives

1. **Fundamental Frequency Detection**: Separate root notes from their harmonics using community detection algorithms
2. **Note Onset Detection**: Identify when notes actually start vs. when they are sustained using temporal flow analysis
3. **Multi-Instrument Separation**: Distinguish and separate multiple simultaneous instruments into distinct voices
4. **Music Theory Integration**: Apply musical constraints (scales, chords, progressions) to improve transcription accuracy
5. **MIDI Generation**: Convert detected notes and timings into standard MIDI format

### Key Stakeholders

**Primary Users**:
- Musicians and composers who want to transcribe recordings to sheet music
- Music researchers studying audio signal processing
- Developers building music transcription applications

**Technical Users**:
- Data scientists applying graph theory to audio analysis
- Systems engineers working on multi-modal analysis pipelines

### Success Criteria (High Level)

1. **Accuracy**: Successfully identify fundamental frequencies with >80% accuracy for single-instrument recordings
2. **Robustness**: Handle polyphonic music with multiple simultaneous instruments
3. **Interpretability**: Provide human-readable explanations for transcription decisions using graph analysis
4. **Extensibility**: Easy to add new analysis methods or edge types to the graph
5. **Performance**: Process audio files in reasonable time (near real-time for live applications)

### System Boundaries

**In Scope**:
- WAV audio file input
- Spectral analysis (Fourier-like transform)
- Graph construction and analysis
- MIDI file output
- Harmonic, temporal, and music theory analysis

**Out of Scope** (for initial version):
- Real-time processing
- Direct sheet music notation output (MIDI can be converted by other tools)
- Lyrics/vocal analysis
- Audio synthesis or playback
- GUI interface (command-line tool initially)

### Technical Approach

The system treats audio analysis as a graph problem:
- **Nodes**: Frequency-time-intensity points
- **Edges**: Temporal, harmonic, and music theory relationships
- **Analysis**: NetworkX algorithms for community detection, centrality, flow, etc.
- **Output**: MIDI file with detected notes, timings, and velocities
