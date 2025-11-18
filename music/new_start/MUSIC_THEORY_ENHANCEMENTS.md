# Music Theory Enhancements for Audio-to-MIDI Transcription

Based on music theory concepts from [Puget Sound Music Theory](https://musictheory.pugetsound.edu/mt21c/).

---

## Current System: "Apply Music Theory" Step

**Current Implementation:** `HarmonicAnalyzer`
- Uses Louvain community detection on graph
- Identifies fundamental frequencies based on harmonic relationships
- Filters noise by confidence and duration

**Current Results:**
- ✓ Detects fundamentals successfully
- ✗ Over-detects (3.6x more notes than original)
- ✗ Pitch accuracy 77.5%
- ✗ No musical context or constraints

---

## Enhancement Opportunities

### 1. Key Signature Detection 🎵

**Concept:** Identify the key(s) of the music to constrain pitch detection.

**From Music Theory:**
- 15 major key signatures (C + 7 sharps + 7 flats)
- Circle of fifths pattern (each key differs by one accidental)
- Sharp keys: F-C-G-D-A-E-B order
- Flat keys: B-E-A-D-G-C-F order

**Implementation Strategy:**

```python
class KeyDetector:
    """Detect musical key from pitch histogram."""

    def __init__(self):
        # Define scale patterns (semitone intervals from root)
        self.major_scale = [0, 2, 4, 5, 7, 9, 11]  # W-W-H-W-W-W-H
        self.minor_scale = [0, 2, 3, 5, 7, 8, 10]  # Natural minor

        # All 24 major and minor keys
        self.all_keys = self._generate_all_keys()

    def detect_key(self, pitch_histogram):
        """
        Find most likely key by comparing pitch distribution to scale templates.

        Uses Krumhansl-Schmuckler algorithm:
        1. Create pitch class histogram (12 bins, C to B)
        2. Correlate with each key profile
        3. Return key with highest correlation
        """
        best_key = None
        best_score = -1

        for key_name, key_profile in self.all_keys.items():
            score = self._correlate(pitch_histogram, key_profile)
            if score > best_score:
                best_score = score
                best_key = key_name

        return best_key, best_score

    def filter_by_key(self, detected_notes, key):
        """
        Filter detected notes based on key membership.

        Keep notes that are in the detected key's scale.
        Boost confidence for scale tones, reduce for chromatic notes.
        """
        scale_notes = self._get_scale_notes(key)

        filtered = []
        for note in detected_notes:
            pitch_class = note['midi_note'] % 12

            if pitch_class in scale_notes:
                # In scale - keep with boosted confidence
                note['confidence'] *= 1.2
                filtered.append(note)
            elif note['confidence'] > 0.5:
                # Strong signal but chromatic - might be real (passing tone, etc.)
                note['confidence'] *= 0.8
                filtered.append(note)
            # Weak chromatic notes filtered out

        return filtered
```

**Expected Benefits:**
- Reduce false positives by 30-40%
- Improved pitch accuracy by filtering non-scale tones
- Better handling of modal music

**Integration Point:** After `HarmonicAnalyzer.filter_noise()`

---

### 2. Chord Recognition & Progression Analysis 🎹

**Concept:** Use chord templates and common progressions to improve detection.

**From Music Theory:**
- Triads: Major (M3+P5), Minor (m3+P5), Diminished (m3+d5), Augmented (M3+A5)
- Seventh chords: Maj7, Min7, Dom7, etc.
- Roman numeral analysis: I, ii, iii, IV, V, vi, vii° in major
- Common progressions: I-IV-V, I-V-vi-IV, ii-V-I

**Implementation Strategy:**

```python
class ChordRecognizer:
    """Recognize chords from simultaneous notes."""

    def __init__(self, chord_templates):
        # Load from your chords.py
        self.templates = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'diminished': [0, 3, 6],
            'augmented': [0, 4, 8],
            'maj7': [0, 4, 7, 11],
            'min7': [0, 3, 7, 10],
            'dom7': [0, 4, 7, 10],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            # ... from your chords.py
        }

        # Common progressions by degree
        self.common_progressions = [
            ['I', 'IV', 'V', 'I'],      # Authentic cadence
            ['I', 'V', 'vi', 'IV'],     # Pop progression
            ['ii', 'V', 'I'],           # Jazz turnaround
            ['I', 'vi', 'IV', 'V'],     # 50s progression
            ['I', 'IV', 'I', 'V'],      # Folk/country
        ]

    def detect_chords_at_time(self, notes_at_time):
        """
        Find chord in simultaneous notes.

        Returns: (root_note, chord_type, quality_score)
        """
        if len(notes_at_time) < 2:
            return None

        # Get pitch classes
        pitch_classes = sorted(set(n['midi_note'] % 12 for n in notes_at_time))

        best_match = None
        best_score = 0

        # Try each note as potential root
        for root in pitch_classes:
            # Transpose to root = 0
            intervals = [(pc - root) % 12 for pc in pitch_classes]

            # Match against templates
            for chord_type, template in self.templates.items():
                score = self._match_quality(intervals, template)
                if score > best_score:
                    best_score = score
                    best_match = (root, chord_type, score)

        return best_match

    def filter_using_chords(self, fundamentals):
        """
        Use chord context to filter spurious notes.

        Groups notes by time windows, detects chords, keeps only
        notes that fit the chord structure.
        """
        # Group by time (e.g., 100ms windows)
        time_windows = self._group_by_time(fundamentals, window_ms=100)

        filtered = []
        for time_window in time_windows:
            chord = self.detect_chords_at_time(time_window)

            if chord:
                root, chord_type, quality = chord
                template = self.templates[chord_type]

                # Keep only notes that fit the chord
                for note in time_window:
                    interval = (note['midi_note'] % 12 - root) % 12
                    if interval in template:
                        filtered.append(note)
                    elif note['confidence'] > 0.8:
                        # Very confident - might be valid (sus, extension, etc.)
                        filtered.append(note)
            else:
                # No clear chord - keep high-confidence notes
                filtered.extend([n for n in time_window if n['confidence'] > 0.6])

        return filtered

    def validate_progression(self, chord_sequence, key):
        """
        Check if chord sequence follows common patterns.

        Could be used to:
        - Boost confidence for notes in expected chords
        - Flag unusual progressions for review
        - Predict next chord in sequence
        """
        # Convert chords to Roman numerals
        roman_numerals = self._to_roman_numerals(chord_sequence, key)

        # Check against common progressions
        for common in self.common_progressions:
            if self._matches_pattern(roman_numerals, common):
                return True, common

        return False, None
```

**Expected Benefits:**
- Reduce over-detection by grouping notes into chords
- Improve pitch accuracy by validating chord memberships
- Handle polyphonic music (piano, guitar) better
- **Estimated improvement:** Detection rate 364% → 150%, Pitch accuracy 77.5% → 85%

**Integration Point:** After key detection, before onset detection

---

### 3. Scale Degrees & Functional Harmony 🎼

**Concept:** Use scale degree functions to validate harmonic progressions.

**From Music Theory:**
- Scale degrees: 1̂ (tonic), 2̂ (supertonic), 3̂ (mediant), 4̂ (subdominant),
                5̂ (dominant), 6̂ (submediant), 7̂ (leading tone)
- Tendency tones: 7̂→1̂, 4̂→3̂
- Harmonic functions: Tonic (I, vi), Subdominant (IV, ii), Dominant (V, vii°)

**Implementation Strategy:**

```python
class FunctionalAnalyzer:
    """Analyze harmonic function and validate progressions."""

    def __init__(self, key):
        self.key = key
        self.tonic_chords = ['I', 'vi', 'iii']
        self.subdominant_chords = ['IV', 'ii']
        self.dominant_chords = ['V', 'vii°', 'V7']

    def get_function(self, chord_numeral):
        """Classify chord by harmonic function."""
        if chord_numeral in self.tonic_chords:
            return 'tonic'
        elif chord_numeral in self.subdominant_chords:
            return 'subdominant'
        elif chord_numeral in self.dominant_chords:
            return 'dominant'
        return 'unknown'

    def validate_progression(self, chord_sequence):
        """
        Check if progression follows harmonic logic.

        Valid progressions generally follow:
        T → S → D → T (Tonic → Subdominant → Dominant → Tonic)
        or
        T → D → T
        """
        functions = [self.get_function(c) for c in chord_sequence]

        # Check for common functional patterns
        valid_patterns = [
            ['tonic', 'subdominant', 'dominant', 'tonic'],
            ['tonic', 'dominant', 'tonic'],
            ['tonic', 'subdominant', 'tonic'],
        ]

        return any(self._contains_pattern(functions, p) for p in valid_patterns)
```

**Expected Benefits:**
- Predict next chord in progression
- Validate detected chord sequences
- Improve temporal coherence

---

### 4. Cadence Detection 🎵

**Concept:** Identify cadences (phrase endings) to structure the analysis.

**From Music Theory:**
- Authentic cadence: V → I (strong conclusion)
- Plagal cadence: IV → I ("Amen" cadence)
- Half cadence: → V (temporary pause)
- Deceptive cadence: V → vi (surprise resolution)

**Implementation Strategy:**

```python
class CadenceDetector:
    """Detect cadences to identify phrase boundaries."""

    def detect_cadences(self, chord_sequence):
        """Find cadence points in chord progression."""
        cadences = []

        for i in range(len(chord_sequence) - 1):
            current = chord_sequence[i]
            next_chord = chord_sequence[i + 1]

            if current == 'V' and next_chord == 'I':
                cadences.append(('authentic', i + 1))
            elif current == 'IV' and next_chord == 'I':
                cadences.append(('plagal', i + 1))
            elif next_chord == 'V':
                cadences.append(('half', i + 1))
            elif current == 'V' and next_chord == 'vi':
                cadences.append(('deceptive', i + 1))

        return cadences

    def use_for_segmentation(self, fundamentals, cadences):
        """
        Use cadences to segment music into phrases.

        Could help with:
        - Onset detection (cadences = phrase boundaries = stronger onsets)
        - Filtering (reset context at phrase boundaries)
        - Structural analysis
        """
        pass
```

**Expected Benefits:**
- Better phrase segmentation
- Improved onset detection at phrase boundaries
- Structural understanding of the piece

---

### 5. Non-Chord Tones & Embellishments 🎶

**Concept:** Distinguish structural notes from ornamental ones.

**From Music Theory:**
- Passing tones: Stepwise motion between chord tones
- Neighbor tones: Stepwise out and back
- Suspensions: Held note resolving down
- Appoggiaturas: Leap to dissonance, step to resolution

**Implementation Strategy:**

```python
class NonChordToneAnalyzer:
    """Identify and handle non-chord tones."""

    def classify_note(self, note, prev_note, next_note, current_chord):
        """
        Determine if note is chord tone or embellishment.
        """
        if self._is_in_chord(note, current_chord):
            return 'chord_tone'

        # Check melodic motion
        if self._is_stepwise(prev_note, note) and self._is_stepwise(note, next_note):
            if prev_note != next_note:
                return 'passing_tone'
            else:
                return 'neighbor_tone'

        if self._is_suspension(note, next_note, current_chord):
            return 'suspension'

        return 'other_embellishment'

    def filter_embellishments(self, melody_notes, chord_progression):
        """
        Keep structural notes, optionally filter embellishments.

        This could reduce over-detection by removing ornamental notes.
        """
        structural_notes = []

        for note in melody_notes:
            classification = self.classify_note(note, ...)

            if classification == 'chord_tone':
                structural_notes.append(note)
            elif classification in ['passing_tone', 'neighbor_tone']:
                # Embellishment - could skip or reduce confidence
                note['confidence'] *= 0.5
                structural_notes.append(note)

        return structural_notes
```

**Expected Benefits:**
- Reduce over-detection by filtering ornamental notes
- Better melodic analysis
- More musically intelligent transcription

---

### 6. Interval Analysis & Voice Leading 🎻

**Concept:** Use interval relationships to validate pitch detection.

**From Music Theory:**
- Perfect intervals: Unison, P4, P5, P8
- Major/minor intervals: M2, m2, M3, m3, M6, m6, M7, m7
- Augmented/diminished intervals
- Voice leading rules (e.g., avoid parallel fifths)

**Implementation Strategy:**

```python
class IntervalAnalyzer:
    """Analyze intervals between notes."""

    def __init__(self):
        self.interval_names = {
            0: 'unison', 1: 'm2', 2: 'M2', 3: 'm3', 4: 'M3',
            5: 'P4', 6: 'tritone', 7: 'P5', 8: 'm6', 9: 'M6',
            10: 'm7', 11: 'M7', 12: 'P8'
        }

    def get_interval(self, note1, note2):
        """Calculate interval between two MIDI notes."""
        semitones = abs(note2 - note1) % 12
        return self.interval_names[semitones]

    def validate_melody(self, note_sequence):
        """
        Check if melodic intervals make musical sense.

        Could flag:
        - Unusual large leaps (> octave)
        - Awkward intervals (augmented 2nd in non-chromatic context)
        - Out-of-range notes for instrument
        """
        suspicious = []

        for i in range(len(note_sequence) - 1):
            interval = abs(note_sequence[i+1]['midi_note'] -
                          note_sequence[i]['midi_note'])

            if interval > 12:  # Leap larger than octave
                suspicious.append((i, 'large_leap', interval))
            elif interval == 6:  # Tritone in melody
                suspicious.append((i, 'tritone_leap', interval))

        return suspicious

    def check_voice_leading(self, chord1_notes, chord2_notes):
        """
        Validate voice leading between chords.

        Good voice leading:
        - Smooth motion (stepwise or common tones)
        - No parallel fifths or octaves
        - Proper resolution of tendency tones
        """
        pass
```

**Expected Benefits:**
- Catch octave errors (note detected in wrong octave)
- Validate melodic coherence
- Improved accuracy for multi-voice music

---

## Integration Roadmap

### Phase 1: Key Detection (High Priority)
1. Implement `KeyDetector` class
2. Add to `HarmonicAnalyzer` after fundamental detection
3. Filter detected notes by key membership
4. **Expected improvement:** 30% reduction in false positives

### Phase 2: Chord Recognition (High Priority)
1. Integrate `chords.py` templates
2. Implement `ChordRecognizer` class
3. Add time-windowed chord detection
4. Filter fundamentals using chord context
5. **Expected improvement:** Detection rate 364% → 150%, Pitch accuracy 77.5% → 85%

### Phase 3: Functional Harmony (Medium Priority)
1. Implement `FunctionalAnalyzer`
2. Add progression validation
3. Use to boost/reduce confidence based on harmonic logic
4. **Expected improvement:** Better temporal coherence

### Phase 4: Advanced Features (Low Priority)
1. Cadence detection for segmentation
2. Non-chord tone classification
3. Interval and voice leading validation
4. **Expected improvement:** More musically sophisticated transcription

---

## Code Structure

```
harmonic_analyzer.py (ENHANCED)
├── HarmonicAnalyzer (existing)
│   ├── detect_fundamentals_in_community()
│   └── filter_noise()
│
├── KeyDetector (NEW)
│   ├── detect_key()
│   ├── filter_by_key()
│   └── get_scale_notes()
│
├── ChordRecognizer (NEW)
│   ├── detect_chords_at_time()
│   ├── filter_using_chords()
│   └── validate_progression()
│
├── FunctionalAnalyzer (NEW)
│   ├── get_function()
│   └── validate_progression()
│
└── MusicTheoryFilter (NEW) - Orchestrator
    ├── apply_all_filters()
    └── combine_confidences()
```

---

## Testing Strategy

### Unit Tests
- Test key detection on known pieces
- Test chord recognition on chord progressions
- Test filtering with ground truth MIDI

### Integration Tests
- Round-trip tests with various musical styles
- Compare against baseline (current system)
- Measure improvements in detection rate and pitch accuracy

### Test Corpus
Categorize by:
- **Solo vs Ensemble**
- **Tonal vs Chromatic**
- **Simple vs Complex harmony**
- **Genre** (classical, jazz, pop, etc.)

---

## Expected Overall Improvements

| Metric | Current | With Key Detection | With Chords | With Full Theory |
|--------|---------|-------------------|-------------|------------------|
| Detection Rate | 364% | ~250% | ~150% | ~110% |
| Pitch Accuracy | 77.5% | ~82% | ~85% | ~92% |
| False Positives | High | Medium | Low | Very Low |
| Musical Intelligence | None | Basic | Good | Excellent |

---

## References

- [Puget Sound Music Theory - Key Signatures](https://musictheory.pugetsound.edu/mt21c/MajorKeySignatures.html)
- [Puget Sound Music Theory - Complete Textbook](https://musictheory.pugetsound.edu/mt21c/MusicTheory.html)
- Krumhansl, C. L. (1990). *Cognitive Foundations of Musical Pitch*
- Temperley, D. (2007). *Music and Probability*
- Harte, C. (2010). *Towards Automatic Extraction of Harmony Information from Music Signals* (PhD thesis)

---

## Conclusion

Adding music theory constraints to the "Apply Music Theory" step can **dramatically improve** the system's accuracy and musical intelligence. The roadmap prioritizes high-impact changes (key detection, chord recognition) that can be implemented relatively quickly and will have the most significant effect on reducing over-detection and improving pitch accuracy.

The complete loop already **works** - these enhancements will make it work **musically**.

---

*Last updated: 2025-11-16*
