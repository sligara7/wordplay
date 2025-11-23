```markdown
# Polyphonic Music Analysis

## Overview

Real music is **polyphonic** - multiple instruments playing simultaneously, creating complex harmonic and rhythmic structures. This module extends Wordplay to handle the full complexity of multi-track music.

## Key Concepts

### Multi-Dimensional Musical Structure

Unlike simple monophonic melodies, real music has multiple dimensions:

```
VERTICAL (Harmonic) - Notes played simultaneously → Chords
     |
     ├─ C4, E4, G4 played together = C major chord
     ├─ Multiple instruments creating harmony
     └─ Chords are "mini-graphs" or structural units

HORIZONTAL (Melodic) - Notes/chords in sequence → Progressions
     |
     ├─ Cmaj → Fmaj → Gmaj = Chord progression
     ├─ Bass line: C2 → F2 → G2
     └─ Melody: C4 → D4 → E4

MULTI-TRACK (Layered) - Different instruments = Different graph layers
     |
     ├─ Track 1: Melody (Piano)
     ├─ Track 2: Chords (Strings)
     ├─ Track 3: Bass (Electric Bass)
     └─ Track 4: Drums (Percussion patterns)
```

### Why This Matters

**Simple monophonic analysis misses:**
- Harmonic progressions (I → IV → V → I)
- Voice leading (how notes move between chords)
- Rhythmic independence (polyrhythms, syncopation)
- Instrumental interactions
- Texture and orchestration

**Polyphonic analysis captures:**
- **Chord progressions** as high-level structures
- **Multi-layer graphs** (one per instrument)
- **Harmonic relationships** using music theory
- **Track interactions** through cross-layer analysis

## Tokenization Strategies

### 1. Chord-Based Tokenization

**Concept**: Treat chords as atomic units

**Modes:**

#### `chord_name` (Recommended)
Uses music theory to identify chords:
- `Cmaj` - C major triad
- `Gmin7` - G minor 7th
- `Ddim` - D diminished
- `F#aug` - F# augmented

**Example:**
```
Input: C4, E4, G4 played simultaneously
Output: "Cmaj"
```

#### `pitch_set`
Lists all notes in the chord:
- `C4_E4_G4` - C major chord
- `D4_F4_A4` - D minor chord

**Example:**
```
Input: F3, A3, C4 played together
Output: "F3_A3_C4"
```

#### `intervals`
Interval structure (music theory):
- `4_3` - Major triad (major 3rd + minor 3rd)
- `3_4` - Minor triad (minor 3rd + major 3rd)
- `4_3_4` - Major 7th chord

**Example:**
```
Input: C4 (root), E4 (+4 semitones), G4 (+3 more)
Output: "4_3"
```

### 2. Multi-Track Analysis

**Concept**: Each instrument gets its own graph layer

**Benefits:**
- Analyze melody independently from harmony
- Study bass line patterns separately
- Understand drum/percussion rhythms
- Compare instrumental roles

**Example:**
```python
# Parse polyphonic MIDI
python3 src/polyphonic_midi_analyzer.py music/song.mid -o music/tracks/

# Creates separate token files:
#   music/tracks/Melody_ch0.txt
#   music/tracks/Chords_ch1.txt
#   music/tracks/Bass_ch2.txt
#   music/tracks/Drums_ch9.txt
```

## Complete Workflow

### Step 1: Create or Use Polyphonic MIDI

```bash
# Create a sample polyphonic song
python3 src/create_sample_midi.py polyphonic

# This creates:
#   - Melody track (Piano): C D E F G F E D C
#   - Chord track (Strings): Cmaj, Fmaj, Gmaj, Cmaj
#   - Bass track (Electric Bass): C2, F2, G2, C2
```

### Step 2: Extract Multi-Track Structure

```bash
# Analyze with chord names (music theory)
python3 src/polyphonic_midi_analyzer.py music/polyphonic_song.mid \
  -o music/tracks/ \
  -m chord_name

# Output:
#   Found 3 tracks/channels
#   Melody: 9 single notes
#   Chords: 4 chord symbols (Cmaj, Fmaj, Gmaj, Cmaj)
#   Bass: 4 bass notes (C2, F2, G2, C2)
```

### Step 3: Build Graphs for Each Layer

```bash
# Build melody graph
python3 src/midi_graph_builder.py music/tracks/Melody_ch0.txt \
  -o output/melody_graph.json \
  -t "Melody Line"

# Build chord progression graph
python3 src/midi_graph_builder.py music/tracks/Chords_ch1.txt \
  -o output/chords_graph.json \
  -t "Chord Progression"

# Build bass line graph
python3 src/midi_graph_builder.py music/tracks/Bass_ch2.txt \
  -o output/bass_graph.json \
  -t "Bass Line"
```

### Step 4: Analyze Each Layer

```bash
# Analyze chord progression
python3 src/analyze_word_graph.py output/chords_graph.json
```

**Output insights:**
```
======================================================================
GRAPH ANALYSIS: Chord Progression
======================================================================

Basic Statistics:
  Nodes: 3 (Cmaj, Fmaj, Gmaj)
  Edges: 3
  Density: 0.50

Most Connected Chords:
  - Fmaj: Central chord (high betweenness)
  - Cmaj: Tonic (start/end)
  - Gmaj: Dominant (transitional)

DAG Status: ✓ Perfect DAG (linear progression, no cycles)

Structure: I → IV → V → I (classic cadence)
```

### Step 5: Compare Layers

```bash
# Compare melody vs harmony
python3 src/merge_word_graphs.py \
  output/melody_graph.json \
  output/chords_graph.json \
  -o output/melody_harmony_comparison.json
```

**Insights:**
- **Orthogonality**: How different are melody and harmony vocabularies?
- **Touchpoints**: Do any elements overlap?
- **Structural independence**: Different patterns in each layer

## Real-World Analysis Example

### Input: Polyphonic Song
- **Melody**: C4 D4 E4 F4 G4 F4 E4 D4 C4
- **Chords**: Cmaj, Fmaj, Gmaj, Cmaj
- **Bass**: C2, F2, G2, C2 (repeated)

### Analysis Results

#### Chord Progression Graph
```json
{
  "nodes": ["Cmaj", "Fmaj", "Gmaj"],
  "transitions": [
    "Cmaj → Fmaj (50% probability)",
    "Fmaj → Gmaj (100%)",
    "Gmaj → Cmaj (100%)"
  ],
  "structure": "I-IV-V-I (Perfect authentic cadence)"
}
```

**Musical insight**: Classic Western harmony pattern (tonic → subdominant → dominant → tonic)

#### Melody Graph
```json
{
  "nodes": ["C4", "D4", "E4", "F4", "G4"],
  "pattern": "Ascending then descending scale",
  "communities": 2,
  "cycles": 4
}
```

**Musical insight**: Stepwise motion, balanced structure

#### Bass Graph
```json
{
  "nodes": ["C2", "F2", "G2"],
  "pattern": "Follows chord roots",
  "role": "Harmonic foundation"
}
```

**Musical insight**: Bass reinforces harmonic progression

## Advanced Features

### 1. Harmonic Function Analysis

Chords have **functional roles** in music theory:

```python
Tonic (I): Cmaj - Home, stable
Subdominant (IV): Fmaj - Moving away from home
Dominant (V): Gmaj - Tension, wants to resolve to I
```

**Graph analysis reveals:**
- Centrality → Functional importance
- Betweenness → Transitional chords (II, VI)
- Cycles → Repeated progressions (verse/chorus)

### 2. Voice Leading Analysis

**How notes move between chords:**

```
Cmaj (C-E-G) → Fmaj (F-A-C)
  C → C (common tone)
  E → F (+1 semitone - stepwise)
  G → A (+2 semitones - stepwise)
```

**Smooth voice leading** = low semitone movement = good counterpoint

### 3. Rhythmic Pattern Extraction

**For percussion/drums (channel 9):**

```bash
python3 src/polyphonic_midi_analyzer.py music/song_with_drums.mid -o tracks/

# Drums track shows:
#   - Kick drum patterns
#   - Snare patterns
#   - Hi-hat patterns
#   - Polyrhythms (if present)
```

### 4. Multi-Track Correlation

**Question**: Do melody and bass move together or independently?

```bash
# Build both graphs
# Compare transition patterns
# High orthogonality = independent movement (counterpoint)
# Low orthogonality = parallel movement (doubling)
```

## Music Theory Integration

### Chord Identification Algorithm

The system identifies chords using **interval patterns**:

```python
Major triad: Root + Major 3rd (4 semitones) + minor 3rd (3 semitones)
  Example: C + E (4) + G (3) = Cmaj

Minor triad: Root + minor 3rd (3) + Major 3rd (4)
  Example: A + C (3) + E (4) = Amin

Dominant 7th: Major triad + minor 7th (10 semitones from root)
  Example: G + B (4) + D (3) + F (10) = G7
```

**Supported chord types:**
- Major, minor, diminished, augmented triads
- Major 7th, dominant 7th, minor 7th, diminished 7th
- Suspended chords (sus2, sus4)
- Extended chords (9th, 11th, 13th) - future

### Common Chord Progressions

**Graph patterns reveal standard progressions:**

```
I-IV-V-I: Cmaj → Fmaj → Gmaj → Cmaj (Classical cadence)
I-V-vi-IV: C → G → Am → F (Pop progression)
ii-V-I: Dm → G7 → Cmaj (Jazz turnaround)
I-vi-IV-V: C → Am → F → G (50s progression)
```

**Cycle detection** identifies repeated progressions (verse/chorus structure)

## Use Cases

### 1. Music Composition Analysis

**Goal**: Understand how a composer structures harmony

```bash
# Analyze a Bach chorale
python3 src/polyphonic_midi_analyzer.py bach_chorale.mid -o output/bach/

# Results might show:
#   - Heavy use of ii-V-I progressions
#   - Smooth voice leading (low transition jumps)
#   - Complex harmonic rhythm
```

### 2. Genre Classification

**Goal**: Identify musical genres by harmonic patterns

```bash
# Compare jazz vs classical vs pop
python3 src/polyphonic_midi_analyzer.py jazz_song.mid -o jazz_tracks/
python3 src/polyphonic_midi_analyzer.py classical.mid -o classical_tracks/
python3 src/polyphonic_midi_analyzer.py pop_song.mid -o pop_tracks/

# Build and compare chord progression graphs
# Jazz: Complex chords (7ths, 9ths, altered), frequent changes
# Classical: Functional harmony, clear cadences
# Pop: Simple chords (triads), repetitive progressions
```

### 3. Cover Song Comparison

**Goal**: How does a cover differ from the original?

```bash
# Analyze original
python3 src/polyphonic_midi_analyzer.py original.mid -o orig/

# Analyze cover
python3 src/polyphonic_midi_analyzer.py cover.mid -o cover/

# Compare chord progressions
python3 src/merge_word_graphs.py orig/Chords*.json cover/Chords*.json

# Results:
#   - Same progression? → Faithful cover
#   - Different chords? → Reharmonization
#   - Different tempo/rhythm? → Stylistic interpretation
```

### 4. Orchestration Analysis

**Goal**: Understand how instruments interact

```bash
# Analyze full orchestra MIDI
python3 src/polyphonic_midi_analyzer.py symphony.mid -o orchestra/

# Results:
#   - 20+ tracks (strings, brass, woodwinds, percussion)
#   - Melody track analysis: Main theme
#   - Harmony tracks: Supporting chords
#   - Bass track: Harmonic foundation
#   - Percussion: Rhythmic drive
```

### 5. AI Music Generation Evaluation

**Goal**: Evaluate AI-generated music quality

```bash
# Analyze AI-generated piece
python3 src/polyphonic_midi_analyzer.py ai_composition.mid -o ai_analysis/

# Check for:
#   - Repetitive chord progressions (mode collapse)
#   - Unnatural voice leading (large jumps)
#   - Lack of harmonic variety
#   - Structural coherence (DAG vs cyclic)
```

## Limitations and Future Work

### Current Limitations

1. **Time quantization**: Notes must be quantized to discrete time slices
2. **Microtonal music**: Only supports 12-tone equal temperament
3. **Extended chords**: Limited support for 9ths, 11ths, 13ths
4. **Polyrhythms**: Complex rhythmic relationships not fully captured
5. **Non-Western music**: Music theory assumes Western tonal harmony

### Future Enhancements

1. **Voice leading graph**: Show how individual notes move between chords
2. **Rhythmic pattern recognition**: Identify drum patterns, grooves
3. **Tension/resolution analysis**: Quantify harmonic tension
4. **Key modulation detection**: Identify key changes
5. **Form analysis**: Detect verse/chorus/bridge structure
6. **Orchestration patterns**: Common instrument combinations
7. **Jazz harmony**: Extended and altered chords
8. **Non-Western scales**: Modes, ragas, maqams

## Technical Details

### Chord Merging Threshold

Notes within `merge_threshold` ticks are considered simultaneous:

```python
# Default: 10 ticks
# At 480 ticks per quarter note:
#   - 10 ticks ≈ 1/48th note
#   - Notes within this window → Same chord
```

### Time Quantization

Events are quantized to `time_quantization` resolution:

```python
# Default: 120 ticks (1/16th note at 480 ppq)
# Benefits:
#   - Aligns notes to rhythmic grid
#   - Reduces noise from timing variations
#   - Enables pattern matching
```

### Percussion Handling

**Channel 9 (MIDI channel 10)** is percussion:
- Pitch numbers represent different drums (not notes)
- Example: 36=Kick, 38=Snare, 42=Hi-hat closed
- Tokenized as drum names instead of pitches

## Command Reference

### Polyphonic Analyzer

```bash
python3 src/polyphonic_midi_analyzer.py <midi_file> [options]

Options:
  -o, --output DIR          Output directory for track tokens
  -m, --mode MODE           Chord mode: chord_name, pitch_set, intervals
  --quantize TICKS          Time quantization (default: 120)
  --merge-threshold TICKS   Simultaneous note threshold (default: 10)
  --stats-only              Print statistics without exporting
```

### Create Polyphonic MIDI

```bash
python3 src/create_sample_midi.py polyphonic

Creates:
  music/polyphonic_song.mid - Multi-track example with melody, chords, bass
```

## Research Applications

1. **Music cognition**: How do humans perceive harmonic progressions?
2. **Historical musicology**: Evolution of harmonic language over time
3. **Cultural analysis**: Compare harmonic conventions across cultures
4. **Music education**: Visualize chord progressions for students
5. **Composer attribution**: Identify composers by harmonic fingerprints
6. **Performance analysis**: Compare different interpretations
7. **Music therapy**: Analyze emotional impact of harmony

## Conclusion

Polyphonic analysis extends Wordplay from simple melodies to **complete musical structures**, capturing the full complexity of real music:

- ✅ **Vertical**: Chords as structural units
- ✅ **Horizontal**: Harmonic progressions
- ✅ **Layered**: Multi-track analysis
- ✅ **Music theory**: Chord identification and functional harmony

From **monophonic melodies** → **polyphonic compositions** → **multi-dimensional musical analysis**!

---

**The same graph analysis principles apply across all layers of musical structure.**
```
