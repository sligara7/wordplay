# MIDI Support for Wordplay

## Overview

Wordplay now extends beyond text analysis to music! MIDI files can be treated as "musical sentences" where notes are "words" and melodies are "phrases". This allows you to apply the same graph-based analysis techniques to music.

**NEW: Hybrid Graphs!** Combine lyrics and melodies into unified graphs. See [HYBRID_GRAPHS.md](HYBRID_GRAPHS.md) for complete documentation on analyzing songs with both words and music together.

## Conceptual Mapping

| Text Domain | MIDI Domain | Example |
|-------------|-------------|---------|
| **Words** | **Notes** | C4, D#5, A3 |
| **Sentences** | **Melodies/Tracks** | A sequence of notes |
| **Word transitions** | **Note sequences** | Which note follows which |
| **Word frequency** | **Note frequency** | How often each note appears |
| **Vocabulary** | **Pitch vocabulary** | Set of unique notes used |

## Quick Start

### 1. Create a Sample MIDI File

```bash
# Create test MIDI files
python3 src/create_sample_midi.py all

# This creates:
#   music/scale.mid     - C major scale
#   music/twinkle.mid   - Twinkle Twinkle Little Star
#   music/chords.mid    - C-G-Am-F chord progression
```

### 2. Tokenize the MIDI File

```bash
# Basic tokenization (pitch only)
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt

# With rhythm information
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt -m pitch_duration

# With dynamics (velocity)
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt -m pitch_velocity

# Full tokenization (pitch + rhythm + dynamics)
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt -m full
```

### 3. Build the Graph

```bash
python3 src/midi_graph_builder.py music/twinkle_tokens.txt \
  -o output/twinkle_graph.json \
  -t "Twinkle Twinkle Little Star"
```

### 4. Analyze the Graph

```bash
python3 src/analyze_word_graph.py output/twinkle_graph.json
```

## Complete Workflow Example

```bash
# Step 1: Create sample MIDI
python3 src/create_sample_midi.py twinkle

# Step 2: Tokenize
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt

# Step 3: Build graph
python3 src/midi_graph_builder.py music/twinkle_tokens.txt \
  -o output/twinkle_graph.json \
  -t "Twinkle Twinkle Little Star"

# Step 4: Analyze
python3 src/analyze_word_graph.py output/twinkle_graph.json
```

## Tokenization Modes

### `pitch` (default)
- **Tokens**: Just note names (C4, D#5, A3)
- **Use case**: Melodic analysis, pitch patterns
- **Example**: `C4 D4 E4 F4 G4`

### `pitch_duration`
- **Tokens**: Note + rhythm bucket (C4_quarter, D4_eighth)
- **Use case**: Rhythmic patterns, timing analysis
- **Example**: `C4_quarter D4_eighth E4_quarter`

### `pitch_velocity`
- **Tokens**: Note + dynamic level (C4_mf, D4_ff)
- **Use case**: Expression analysis, dynamic patterns
- **Example**: `C4_mf D4_f E4_ff`

### `full`
- **Tokens**: All attributes (C4_quarter_mf)
- **Use case**: Complete musical analysis
- **Example**: `C4_quarter_mf D4_eighth_f E4_quarter_ff`

## Musical Insights from Analysis

### 1. Centrality Analysis

**What it tells you about music:**

- **Degree Centrality**: Most versatile notes (connect to many other notes)
- **Betweenness Centrality**: Bridge notes that connect different musical sections
- **Closeness Centrality**: Central notes in the melody (tonal center, home notes)

**Example from "Twinkle Twinkle":**
```
Most Connected Notes:
  - G4: 1.400 (dominant note - very central)
  - D4: 1.000 (connects different sections)
  - C4: 0.800 (tonic - home note)
```

### 2. Community Detection

**What it tells you about music:**
- Groups of notes that frequently appear together
- Musical phrases or motifs
- Harmonic relationships

**Example from "Twinkle Twinkle":**
```
3 communities found:
  Community 0: [C4, D4]  - Lower register movement
  Community 1: [E4, F4]  - Middle register
  Community 2: [A4, G4]  - Upper register leap
```

### 3. DAG Analysis (Cycles)

**What it tells you about music:**
- Cycles indicate repetitive patterns
- Musical loops and recurring motifs
- Verse/chorus structure in songs

**Example from "Twinkle Twinkle":**
```
Contains 9 cycles - highly repetitive melody
Self-loops: [A4, C4, D4, E4, F4] - notes that repeat consecutively
```

### 4. Structural Analysis

**What it tells you about music:**
- **Dead ends**: Final notes of phrases
- **Unreachable**: Opening notes
- **Bottlenecks**: Critical transition notes

### 5. Connectivity

**What it tells you about music:**
- **Strongly connected**: Can reach any note from any other (explores full range)
- **Weakly connected**: Fragmented sections or isolated phrases

## Comparing Musical Pieces

```bash
# Compare two songs
python3 src/merge_word_graphs.py \
  output/twinkle_graph.json \
  output/scale_graph.json \
  -o output/merged_music.json

# This shows:
# - Common notes (touchpoints)
# - Orthogonality (how different the melodies are)
# - Unique melodic patterns
```

## Real-World Analysis Results

### "Twinkle Twinkle Little Star"
```
Nodes: 6 unique notes (C4, D4, E4, F4, G4, A4)
Edges: 14 transitions
Density: 0.467 (moderately connected)
Communities: 3 (clear phrase structure)
Cycles: 9 (very repetitive - children's song)
Strongly connected: Yes (explores all notes)
```

**Musical interpretation:**
- Simple melody with limited pitch range
- Highly repetitive (pedagogical structure)
- G4 is the dominant note (highest centrality)
- Three distinct musical phrases

### "C Major Scale"
```
Nodes: 8 unique notes (C4-C5)
Edges: 14 transitions
Density: 0.250 (linear progression)
Communities: 2 (ascending vs descending)
Cycles: 7 (up-down pattern)
Strongly connected: Yes
```

**Musical interpretation:**
- Linear melodic movement
- Two communities = ascending and descending motion
- Even note distribution
- Lower density = more predictable sequence

## Advanced Use Cases

### 1. Genre Classification
Compare transition patterns across different musical genres:
```bash
python3 src/batch_process_books.py midi_tokens/ -o output/genres/
python3 src/merge_word_graphs.py output/genres/*.json
```

### 2. Composer Identification
Analyze unique melodic signatures:
- Bach might have more complex transition patterns
- Mozart might show different centrality distributions

### 3. Music Generation Quality
Use LLM analyzer to detect:
- Mode collapse (limited note vocabulary)
- Unnatural transitions
- Lack of musical structure

```bash
python3 src/llm_analyzer.py generated_melody_graph.json \
  --reference human_composed_graph.json
```

### 4. Musical Translation
Compare original melodies to variations/covers:
```bash
python3 src/merge_word_graphs.py original.json cover.json
# Check orthogonality to see how different the versions are
```

### 5. Harmonic Analysis
Use chord tokenization mode:
```bash
# Create chord progression MIDI
python3 src/create_sample_midi.py chords

# Tokenize as chords (requires custom chord detection)
# Analyze harmonic movement patterns
```

## Musical Insights You Can Discover

1. **Tonal Centers**: Which notes are most central (likely tonic/dominant)
2. **Melodic Patterns**: Recurring note sequences (motifs)
3. **Phrase Structure**: Communities reveal how melody is organized
4. **Repetition**: Cycle count indicates song complexity
5. **Range Exploration**: Connectivity shows if all notes are utilized
6. **Transition Smoothness**: Edge weights reveal stepwise vs leap motion
7. **Compositional Style**: Graph density indicates melodic complexity

## Limitations

### Current Implementation
- **Monophonic focus**: Best for single melody lines
- **Chord representation**: Chords are tokenized as simultaneous notes
- **No timing context**: Tempo and absolute timing are lost
- **No rests**: Silence gaps are not represented

### Future Enhancements
- Polyphonic analysis (multiple voices)
- Rest tokens for silence
- Time signature awareness
- Key detection and transposition
- Chord detection and labeling

## Research Applications

1. **Musicology**: Analyze historical composition patterns
2. **Music Education**: Visualize melodic structure for students
3. **Music Generation**: Evaluate AI-composed music quality
4. **Cultural Analysis**: Compare musical traditions across cultures
5. **Plagiarism Detection**: Find similar melodic patterns
6. **Music Therapy**: Analyze complexity for therapeutic purposes

## Technical Details

### MIDI Note Representation
- **Pitch**: MIDI number 0-127 (C4 = 60, A4 = 69)
- **Velocity**: 0-127 (0 = silent, 127 = maximum)
- **Duration**: Measured in ticks (typically 480 per quarter note)

### Duration Buckets
```
≥1920 ticks  → whole
≥960 ticks   → half
≥480 ticks   → quarter
≥240 ticks   → eighth
≥120 ticks   → sixteenth
<120 ticks   → short
```

### Velocity Levels (Dynamics)
```
112-127  → fff (fortississimo)
96-111   → ff  (fortissimo)
80-95    → f   (forte)
64-79    → mf  (mezzo-forte)
48-63    → mp  (mezzo-piano)
32-47    → p   (piano)
0-31     → pp  (pianissimo)
```

## Dependencies

```bash
pip install -r requirements.txt

# Requirements:
# - networkx (graph analysis)
# - mido (MIDI file parsing)
```

## File Structure

```
wordplay/
├── src/
│   ├── midi_tokenizer.py         # MIDI → tokens
│   ├── midi_graph_builder.py     # Tokens → graph
│   ├── create_sample_midi.py     # Generate test files
│   ├── analyze_word_graph.py     # Analyze graphs (works for music too!)
│   └── merge_word_graphs.py      # Compare melodies
├── music/                         # MIDI files
│   ├── *.mid                      # Original MIDI files
│   └── *_tokens.txt               # Tokenized versions
└── output/                        # Generated graphs
    ├── *_graph.json               # Graph files
    └── *_analysis.json            # Analysis results
```

## Examples

See `music/` directory for sample MIDI files and `output/` for their analyses.

## Contributing

Have ideas for musical analysis features? Open an issue or submit a PR!

Possible extensions:
- Chord detection and tokenization
- Polyphonic voice separation
- Time signature and rhythm analysis
- Scale and mode detection
- Musical interval analysis
- Harmonic progression analysis

---

**From words to notes, from language to music - the same principles of structure and flow apply!**
