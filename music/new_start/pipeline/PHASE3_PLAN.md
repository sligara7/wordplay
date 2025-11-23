# Phase 3: Full Audio-to-MIDI Transcription

## Goal

Integrate Phase 1 (Timing & Dynamics) and Phase 2 (Melody Extraction) into a complete audio-to-MIDI transcription pipeline.

## Components Completed

### Phase 1: Timing & Dynamics ✅
- **Onset Detection:** 100% accuracy on real piano
- **Velocity Estimation:** 0.845 correlation with dynamics (pp/mf/ff)
- Methods: Energy-based + Spectral flux with `first_onset_only` mode

### Phase 2: Melody Extraction ✅
- **Pitch Detection:** 82.7% accuracy on Iowa samples (256 notes)
- Method: Hybrid FFT (high notes) + Autocorrelation (low notes)
- Frequency range: 27.5 Hz (A0) to 4186 Hz (C8)

## Phase 3 Architecture

### Input
- Audio file (WAV format, mono or stereo)

### Pipeline Stages

1. **Load & Preprocess**
   - Read WAV file
   - Convert to mono if stereo
   - Normalize to float32 (-1.0 to 1.0)

2. **Onset Detection**
   - Detect note attack times
   - Output: Array of onset times (seconds)

3. **Pitch Detection**
   - For each onset, detect fundamental frequency
   - Output: Array of frequencies (Hz)

4. **Velocity Estimation**
   - For each onset, estimate note intensity
   - Output: Array of velocities (1-127)

5. **MIDI Generation**
   - Convert frequency → MIDI note number
   - Create MIDI file with:
     - Note on/off events
     - Timing (from onsets)
     - Velocity (from estimation)
     - Duration (from next onset or fixed default)

### Output
- MIDI file (.mid)

## Implementation Plan

### Step 1: Create Integrated Transcriber Class

```python
class AudioToMIDITranscriber:
    """
    Complete audio-to-MIDI transcription pipeline.

    Integrates onset detection, pitch detection, and velocity estimation
    to create MIDI files from piano audio.
    """

    def __init__(self, sample_rate=44100):
        self.onset_detector = OnsetDetector(sample_rate)
        self.pitch_detector = PitchDetector(sample_rate)
        self.velocity_estimator = VelocityEstimator(sample_rate)

    def transcribe(self, audio_path, output_midi_path):
        """
        Transcribe audio file to MIDI.

        Args:
            audio_path: Path to input WAV file
            output_midi_path: Path for output MIDI file

        Returns:
            Transcription results dict
        """
        # Load audio
        audio = self.load_audio(audio_path)

        # Detect onsets
        onset_times = self.onset_detector.detect_onsets_combined(audio)

        # For each onset, detect pitch and velocity
        notes = []
        for onset_time in onset_times:
            pitch = self.pitch_detector.detect_pitch(audio, onset_time)
            velocity = self.velocity_estimator.estimate_velocity(audio, onset_time)

            if pitch > 0:  # Valid pitch detected
                midi_note = freq_to_midi(pitch)
                notes.append({
                    'time': onset_time,
                    'note': midi_note,
                    'velocity': velocity
                })

        # Generate MIDI file
        self.create_midi_file(notes, output_midi_path)

        return notes
```

### Step 2: MIDI File Generation

Use `mido` library to create MIDI files:

```python
def create_midi_file(self, notes, output_path, default_duration=0.5):
    """
    Create MIDI file from detected notes.

    Args:
        notes: List of dicts with 'time', 'note', 'velocity'
        output_path: Output MIDI file path
        default_duration: Default note duration in seconds
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Add tempo (default 120 BPM)
    track.append(mido.MetaMessage('set_tempo', tempo=500000))

    # Convert notes to MIDI events
    # Calculate delta times between events
    # Add note_on and note_off messages

    mid.save(output_path)
```

### Step 3: Duration Estimation

**Challenge:** We detect onsets but not note durations.

**Solutions:**
1. **Simple:** Use fixed duration (e.g., 0.5 seconds)
2. **Better:** Duration = time until next onset (or fixed if last note)
3. **Advanced:** Analyze amplitude decay to detect note release

For Phase 3, use **Solution 2** (time until next onset).

### Step 4: Testing Strategy

**Test 1: Single-note transcription**
- Input: Iowa piano samples (1 note each)
- Expected: MIDI with 1 note at correct pitch/velocity
- Success: Correct MIDI note number

**Test 2: Scale transcription**
- Input: Chromatic scale recording
- Expected: MIDI with 12 ascending notes
- Success: All 12 notes detected in sequence

**Test 3: Real music transcription**
- Input: Simple piano piece (e.g., C scale arpeggio)
- Expected: Playable MIDI file
- Success: MIDI sounds recognizable

**Test 4: Round-trip test**
- MIDI → WAV (synthesis) → MIDI (transcription)
- Compare original MIDI to transcribed MIDI
- Measure accuracy

## Success Criteria

### Phase 3 Goals

1. **Generate valid MIDI files** - Files open in MIDI software ✅
2. **Note accuracy > 75%** - For simple monophonic piano pieces
3. **Timing error < 100ms** - Average onset timing error
4. **Playable output** - MIDI sounds like the original (subjectively)

### Stretch Goals

- Handle polyphonic audio (multiple simultaneous notes)
- Improve duration estimation (amplitude decay analysis)
- Add pedal detection
- Add tempo/beat tracking

## File Structure

```
pipeline/
├── onset_detector.py           ✅ Complete
├── pitch_detector.py           ✅ Complete
├── velocity_estimator.py       (part of onset_detector.py) ✅
├── audio_to_midi.py           ⬅️ NEW: Main transcriber
├── test_transcription.py      ⬅️ NEW: Integration tests
└── PHASE3_PLAN.md             ⬅️ This file
```

## Next Steps

1. ✅ Create `audio_to_midi.py` with AudioToMIDITranscriber class
2. ✅ Implement MIDI file generation
3. ✅ Test on Iowa single-note samples
4. ✅ Test on chromatic scale
5. ✅ Test on real piano recording
6. 📊 Measure end-to-end accuracy

## Timeline Estimate

- Implementation: 1-2 hours
- Testing & refinement: 1-2 hours
- Total: **2-4 hours** to complete Phase 3

Then we'll have a **working audio-to-MIDI transcription pipeline**!
