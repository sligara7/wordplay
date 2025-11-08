# Temporal Analysis: Rhythm, Cadence, and Timing

## The Critical Missing Dimension

You're absolutely right - the basic graph representation was missing **temporal structure**:

**What was lost:**
- ❌ **Rhythm**: Which notes are quarter vs half notes?
- ❌ **Tempo**: How fast is the piece? (BPM)
- ❌ **Cadence**: Timing patterns that create emotion
- ❌ **Syllable duration**: In speech/poetry
- ❌ **Pauses**: Rests and silence
- ❌ **Timing relationships**: Inter-onset intervals

**What we had:**
- ✅ Pitch sequences (which notes)
- ✅ Transitions (which note follows which)
- ✅ Chords (simultaneous notes)

## Solution: Temporal-Aware Tokenization

### Music: Rhythm and Duration

Instead of just `C4`, we now capture:

```
Temporal token: C4_quarter
            ↓         ↓
         pitch    duration

Full example:
  Basic:    C4 D4 E4 F4 G4
  Temporal: C4_quarter D4_eighth E4_eighth F4_half G4_quarter

The graph now shows BOTH melodic and rhythmic patterns!
```

### Real Analysis Example

**Twinkle Twinkle Little Star:**
```bash
python3 src/temporal_midi_tokenizer.py music/twinkle.mid

Results:
{
  "tempo_bpm": 120.0,
  "rhythm_pattern_frequency": [
    ["quarter", 36],    # Mostly quarter notes
    ["half", 6]         # Some half notes (phrase endings)
  ],
  "timing_statistics": {
    "shortest_duration": 480 ticks (quarter note),
    "longest_duration": 960 ticks (half note),
    "average_duration": 548 ticks
  }
}

Tokens generated:
  C4_quarter C4_quarter G4_quarter G4_quarter A4_quarter A4_quarter G4_half
  ↑ Repetitive quarter notes           ↑ Half note emphasizes "star"
```

**Musical insight**: Simple, repetitive rhythm perfect for children's song.

### Text: Syllables and Cadence

For speech/poetry, we need similar temporal awareness:

```
Text without timing:  "twinkle twinkle little star"
Text with syllables:  "twin-kle twin-kle lit-tle star"
Text with stress:     "TWIN-kle TWIN-kle LIT-tle STAR"
Text with duration:   "twin_long kle_short twin_long kle_short"

This captures the CADENCE - how we speak/sing the words.
```

## Temporal Tokenization Modes

### 1. `pitch_duration` Mode

**What it captures**: Note + how long it lasts

```bash
python3 src/temporal_midi_tokenizer.py music/song.mid -m pitch_duration

Output: C4_quarter D4_eighth E4_eighth F4_half
```

**Use case**: Analyze rhythmic patterns
**Graph shows**: Which rhythmic patterns follow which

### 2. `pitch_ioi` Mode (Inter-Onset Interval)

**What it captures**: Note + time since previous note

```bash
python3 src/temporal_midi_tokenizer.py music/song.mid -m pitch_ioi

Output: C4_ioi0 D4_ioi480 E4_ioi240 F4_ioi240
                    ↑ 480 ticks after C
                             ↑ 240 ticks after D
```

**Use case**: Analyze timing relationships and tempo variations
**Graph shows**: Timing patterns between notes

### 3. `full_temporal` Mode

**What it captures**: Complete temporal information

```bash
python3 src/temporal_midi_tokenizer.py music/song.mid -m full_temporal

Output: C4_durquarter_ioi0 D4_dureighth_ioi480
```

**Use case**: Maximum temporal awareness
**Graph shows**: Both duration and timing patterns

### 4. Rhythm-Only Extraction

**What it captures**: Pure rhythm pattern (no pitch)

```bash
python3 src/temporal_midi_tokenizer.py music/song.mid --rhythm-only

Output: quarter quarter eighth eighth half
```

**Use case**: Analyze rhythmic structure independently
**Graph shows**: Rhythmic patterns used in piece

## Does This Properly Represent Sheet Music?

### Sheet Music Components vs Graph Representation

| Sheet Music Element | Graph Representation |
|---------------------|----------------------|
| **Pitch** (notes on staff) | ✅ Node names (C4, D#5) |
| **Duration** (note shape) | ✅ Temporal tokens (quarter, half) |
| **Rhythm** (timing pattern) | ✅ IOI and duration patterns |
| **Tempo** (BPM marking) | ✅ Captured in metadata |
| **Dynamics** (p, f, ff) | ✅ Velocity tokenization |
| **Articulation** (staccato, legato) | ⚠️ Partially (from duration) |
| **Time signature** (4/4, 3/4) | ⚠️ Can infer from pattern |
| **Key signature** | ⚠️ Can infer from pitch set |
| **Rests** (silence) | ⚠️ Captured in IOI gaps |
| **Expression marks** | ❌ Not in MIDI |

**Conclusion**: Temporal tokenization captures **most** musical information from sheet music/MIDI:
- ✅ Pitch sequences
- ✅ Rhythmic patterns
- ✅ Harmonic structure (chords)
- ✅ Tempo and timing
- ⚠️ Some interpretive elements
- ❌ Text annotations

## Batch Processing: Multiple Graphs

### The Power of Batch Analysis

Instead of analyzing one song at a time, find patterns across **multiple pieces**:

```bash
# Analyze 10 different songs
python3 src/batch_graph_merger.py output/song*.json --report-only
```

**Results show:**
- Elements common across ALL songs
- Most frequent melodic patterns
- Most frequent chord progressions
- Average complexity metrics
- Representative graph of the corpus

### Real Example: Analyzing Song Collection

```bash
# Create graphs for multiple songs
for file in music/*.mid; do
    python3 src/temporal_midi_tokenizer.py $file -o tokens/$(basename $file .mid).txt
    python3 src/midi_graph_builder.py tokens/$(basename $file .mid).txt \
        -o output/$(basename $file .mid)_graph.json
done

# Find common patterns
python3 src/batch_graph_merger.py output/*_graph.json --report-only

=== RESULTS ===
Graphs Analyzed: 3

Most frequent elements:
  G4: appears in 2/3 graphs
  C4: appears in 2/3 graphs
  F4: appears in 2/3 graphs

Most frequent transitions:
  G4 → A4: appears in 2 graphs
  D4 → C4: appears in 2 graphs

Average density: 0.253
```

**Insights**:
- **Common notes**: G4, C4, F4 (C major scale tones)
- **Common transitions**: Stepwise motion (G→A, D→C)
- **Graph density**: ~0.25 (moderate connectivity)

## Merging Word Graphs with Music Graphs

### Cross-Domain Analysis

Your goal: Merge multiple word graphs with multiple music graphs to find universal patterns.

**Workflow:**

```bash
# 1. Create word graphs from poems/text
python3 src/word_graph_builder.py books/poem1.txt -o output/poem1_graph.json
python3 src/word_graph_builder.py books/poem2.txt -o output/poem2_graph.json
python3 src/word_graph_builder.py books/poem3.txt -o output/poem3_graph.json

# 2. Create music graphs with temporal info
python3 src/temporal_midi_tokenizer.py music/song1.mid -o tokens/song1.txt
python3 src/midi_graph_builder.py tokens/song1.txt -o output/song1_graph.json

python3 src/temporal_midi_tokenizer.py music/song2.mid -o tokens/song2.txt
python3 src/midi_graph_builder.py tokens/song2.txt -o output/song2_graph.json

# 3. Batch merge to find cross-domain patterns
python3 src/batch_graph_merger.py output/poem*.json output/song*.json -o output/cross_domain.json

# This will show:
# - Common structural patterns (if any)
# - Average complexity across both domains
# - Representative graph of text + music
```

### What Cross-Domain Merging Reveals

**Orthogonality Analysis:**
```
Text vocabulary:     {love, heart, soul, dream}
Music vocabulary:    {C4_quarter, G4_half, D4_eighth}
Orthogonality:       ~1.0 (completely different vocabularies)

BUT the STRUCTURE might be similar:
  Both have ~20 nodes
  Both have density ~0.15
  Both show cyclical patterns (repetition)
```

**Structural Similarity Despite Different Content:**

```
Poem graph:
  Nodes: 25 words
  Edges: 30 transitions
  Cycles: 5 (repeated phrases)
  Density: 0.16

Song graph:
  Nodes: 24 notes
  Edges: 28 transitions
  Cycles: 6 (repeated musical phrases)
  Density: 0.15

Conclusion: Similar STRUCTURAL complexity!
```

## Cadence and Emotion

### Music: Tempo Creates Feeling

```python
Fast tempo (140 BPM) + short durations (eighth notes) = Energetic, exciting
Slow tempo (60 BPM) + long durations (half notes) = Calm, contemplative

Temporal analysis reveals:
- "Twinkle Twinkle": 120 BPM, mostly quarters = Moderate, comfortable
- "Funeral March": 60 BPM, mostly halves = Slow, solemn
- "Dance Track": 140 BPM, mostly sixteenths = Fast, energetic
```

### Text: Syllables and Stress

**Poetic meter** is the temporal structure of language:

```
Iambic pentameter (Shakespeare):
  Shall I / com-PARE / thee TO / a SUM / mer's DAY
  ˘ ¯    ˘  ¯      ˘  ¯    ˘  ¯    ˘    ¯

Temporal pattern: short-LONG short-LONG short-LONG
Just like eighth-quarter eighth-quarter in music!
```

**Future enhancement**: Syllable-aware text tokenization:
```bash
# Instead of: "compare thee to a summer's day"
# Use:        "com_short pare_LONG thee_short to_short a_short sum_short mer's_LONG day_LONG"

This captures the CADENCE of speech.
```

## Complete Workflow: Representative Graph from Multiple Sources

### Goal: Find Universal Patterns

**Input**:
- 10 poems (word graphs)
- 10 songs (music graphs with temporal info)

**Process**:

```bash
# Step 1: Generate all word graphs
for poem in books/poems/*.txt; do
    python3 src/word_graph_builder.py $poem -o output/words/$(basename $poem .txt)_graph.json
done

# Step 2: Generate all music graphs (with rhythm)
for song in music/*.mid; do
    python3 src/temporal_midi_tokenizer.py $song -m pitch_duration -o tokens/$(basename $song .mid).txt
    python3 src/midi_graph_builder.py tokens/$(basename $song .mid).txt \
        -o output/music/$(basename $song .mid)_graph.json
done

# Step 3: Find patterns within each domain
python3 src/batch_graph_merger.py output/words/*_graph.json -o output/poetry_representative.json
python3 src/batch_graph_merger.py output/music/*_graph.json -o output/music_representative.json

# Step 4: Cross-domain analysis
python3 src/batch_graph_merger.py output/poetry_representative.json output/music_representative.json \
    --report-only

# This shows:
# - Average complexity: poetry vs music
# - Structural patterns common to both
# - Density comparison
# - Cyclical vs linear structures
```

### Expected Insights

**Poetic corpus might show:**
```
Average nodes: 150 words
Average density: 0.08 (sparse - many unique expressions)
Most common transitions: "the" → "of", "and" → "the"
Cycles: Frequent (repeated refrains, choruses)
```

**Musical corpus might show:**
```
Average nodes: 30 notes
Average density: 0.20 (denser - limited pitch vocabulary)
Most common transitions: C → G, G → C (tonic-dominant)
Cycles: Frequent (verse-chorus structure)
```

**Cross-domain comparison:**
```
Structural similarity:
  - Both show cyclical patterns (repetition)
  - Poetry more sparse (more unique vocabulary)
  - Music denser (limited note vocabulary)
  - Both have clear transitional structures
```

## Advanced: Hybrid Tempo-Aware Songs

Combine lyrics + melody + rhythm:

```bash
# 1. Create aligned song with syllables + temporal notes
cat > songs/love_song_temporal.txt << 'EOF'
# word syllable_duration note note_duration
I short C4 eighth
love long E4 quarter
you long G4 half
EOF

# 2. Tokenize with temporal awareness
python3 src/hybrid_tokenizer.py songs/love_song_temporal.txt -o songs/love_hybrid_temporal.txt

# Tokens: I_short-C4_eighth love_long-E4_quarter you_long-G4_half

# 3. Build and analyze
python3 src/midi_graph_builder.py songs/love_hybrid_temporal.txt -o output/hybrid_temporal_graph.json
python3 src/analyze_word_graph.py output/hybrid_temporal_graph.json
```

**This captures**:
- ✅ What words are sung
- ✅ What notes they're sung on
- ✅ How long each syllable lasts
- ✅ How long each note lasts
- ✅ Complete temporal structure

## Summary: Proper Musical Representation

**Question**: Does the graph properly represent sheet music/MIDI?

**Answer**: With temporal tokenization, YES!

| Musical Aspect | Captured? | How? |
|---------------|-----------|------|
| Pitch | ✅ Yes | Node names (C4, D#5) |
| Duration | ✅ Yes | Temporal tokens (_quarter, _half) |
| Rhythm | ✅ Yes | Duration + IOI patterns |
| Tempo | ✅ Yes | BPM in metadata |
| Chords | ✅ Yes | Polyphonic analyzer |
| Harmony | ✅ Yes | Chord progression graphs |
| Dynamics | ✅ Yes | Velocity tokenization |
| Timing | ✅ Yes | Inter-onset intervals |
| Rests | ⚠️ Partial | Gaps in IOI |
| Cadence | ✅ Yes | Rhythm pattern analysis |

**The graph now represents** the complete temporal structure of music and can be compared across multiple pieces to find common patterns.

## Tools Reference

### Temporal MIDI Tokenizer
```bash
python3 src/temporal_midi_tokenizer.py music/song.mid -m pitch_duration
```

### Batch Graph Merger
```bash
python3 src/batch_graph_merger.py output/*.json -o output/merged.json
```

### Complete Pipeline
```bash
# 1. Tokenize with rhythm
python3 src/temporal_midi_tokenizer.py music/song.mid -o tokens/song.txt

# 2. Build graph
python3 src/midi_graph_builder.py tokens/song.txt -o output/song_graph.json

# 3. Analyze
python3 src/analyze_word_graph.py output/song_graph.json

# 4. Merge with other songs
python3 src/batch_graph_merger.py output/*_graph.json -o output/collection.json
```

---

**From sequences to temporal structures - now we capture the RHYTHM that creates emotion!** 🎵⏱️
