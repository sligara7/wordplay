# Hybrid Graphs: Merging Lyrics and Music

## Overview

Songs are inherently multimodal - they combine **words** (lyrics) and **music** (melody) into a unified artistic expression. Wordplay's hybrid graph system allows you to analyze both dimensions together, revealing how language and melody interact.

## Why Hybrid Graphs?

Traditional analysis treats lyrics and music separately:
- **Lyrics-only analysis**: Misses the emotional impact of melody
- **Music-only analysis**: Ignores the meaning conveyed by words

**Hybrid graphs** capture both dimensions simultaneously, enabling:
- **Word-melody associations**: Which notes are sung with emotional words?
- **Cross-modal patterns**: How do lyrical and melodic structures align?
- **Comparative analysis**: How do different songs use similar words with different melodies?
- **Complete artistic expression**: Understand the full song structure

## Three Tokenization Modes

### 1. Hybrid Mode (Recommended)

**Concept**: Combine words and notes into single tokens

**Format**: `word-note` (e.g., `"love-C4"`, `"fly-G4"`)

**Use case**: Analyze complete song structure with both dimensions

```bash
python3 src/hybrid_tokenizer.py songs/song_aligned.txt \
  -o songs/song_hybrid.txt \
  -m hybrid
```

**Example output**:
```
hello-C4 world-C4 how-G4 are-G4 you-A4 today-A4
```

**Graph insights**:
- Centrality: Most important word-note combinations
- Communities: Clusters of related expressions
- Patterns: Recurring lyrical-melodic motifs

### 2. Parallel Mode

**Concept**: Separate but aligned word and note sequences

**Format**: Two files - one with words, one with notes

**Use case**: Compare lyrical vs melodic structure independently

```bash
python3 src/hybrid_tokenizer.py songs/song_aligned.txt \
  -o songs/song_tokens.txt \
  -m parallel
```

**Output files**:
- `song_tokens_words.txt`: `hello world how are you`
- `song_tokens_notes.txt`: `C4 C4 G4 G4 A4`

**Workflow**:
```bash
# Build separate graphs
python3 src/word_graph_builder.py songs/song_tokens_words.txt -o output/lyrics_graph.json
python3 src/midi_graph_builder.py songs/song_tokens_notes.txt -o output/melody_graph.json

# Merge for comparison
python3 src/merge_word_graphs.py output/lyrics_graph.json output/melody_graph.json
```

**Graph insights**:
- Orthogonality: How different are word and note vocabularies? (always 1.0)
- Separate centrality: Important words vs important notes
- Independent community structures

### 3. Layered Mode

**Concept**: All three representations (hybrid, words, notes)

**Format**: Three files for maximum flexibility

**Use case**: Comprehensive analysis from multiple perspectives

```bash
python3 src/hybrid_tokenizer.py songs/song_aligned.txt \
  -o songs/song_tokens.txt \
  -m layered
```

**Output files**:
- `song_tokens_hybrid.txt`: Combined tokens
- `song_tokens_words.txt`: Lyrical sequence
- `song_tokens_notes.txt`: Melodic sequence

## Input Formats

### Simple Format (Recommended for Getting Started)

Plain text file with one word-note pair per line:

```
# songs/my_song_aligned.txt
hello C4
world C4
how G4
are G4
you A4
today A4
```

**Rules**:
- One syllable per line
- Format: `word note` (space-separated)
- Lines starting with `#` are comments
- Blank lines are ignored

### JSON Format (Advanced)

Structured format with timestamps:

```json
{
  "title": "My Song",
  "aligned_tokens": [
    {"word": "hello", "note": "C4", "timestamp": 0.0},
    {"word": "world", "note": "C4", "timestamp": 0.5},
    {"word": "how", "note": "G4", "timestamp": 1.0}
  ]
}
```

**Use case**: When you have precise timing information

```bash
python3 src/hybrid_tokenizer.py songs/song.json \
  -o songs/song_hybrid.txt \
  --format json
```

## Complete Workflow Examples

### Example 1: Analyze a Single Song (Hybrid Mode)

```bash
# 1. Create aligned lyrics+melody file
cat > songs/my_song.txt << 'EOF'
love C4
is D4
all E4
you F4
need G4
EOF

# 2. Tokenize in hybrid mode
python3 src/hybrid_tokenizer.py songs/my_song.txt \
  -o songs/my_song_hybrid.txt \
  -m hybrid

# 3. Build graph
python3 src/midi_graph_builder.py songs/my_song_hybrid.txt \
  -o output/my_song_graph.json \
  -t "My Song"

# 4. Analyze
python3 src/analyze_word_graph.py output/my_song_graph.json
```

### Example 2: Compare Lyrics vs Melody (Parallel Mode)

```bash
# 1. Tokenize in parallel mode
python3 src/hybrid_tokenizer.py songs/song.txt \
  -o songs/song_tokens.txt \
  -m parallel

# 2. Build separate graphs
python3 src/word_graph_builder.py songs/song_tokens_words.txt \
  -o output/lyrics_graph.json \
  -t "Song Lyrics"

python3 src/midi_graph_builder.py songs/song_tokens_notes.txt \
  -o output/melody_graph.json \
  -t "Song Melody"

# 3. Analyze each separately
python3 src/analyze_word_graph.py output/lyrics_graph.json
python3 src/analyze_word_graph.py output/melody_graph.json

# 4. Merge for comparison
python3 src/merge_word_graphs.py \
  output/lyrics_graph.json \
  output/melody_graph.json \
  -o output/merged_graph.json
```

### Example 3: Compare Two Different Songs

```bash
# Create hybrid graphs for both songs
python3 src/hybrid_tokenizer.py songs/song1.txt -o songs/song1_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/song1_hybrid.txt -o output/song1_graph.json

python3 src/hybrid_tokenizer.py songs/song2.txt -o songs/song2_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/song2_hybrid.txt -o output/song2_graph.json

# Compare the songs
python3 src/merge_word_graphs.py \
  output/song1_graph.json \
  output/song2_graph.json \
  -o output/compared_songs.json
```

**Insights**:
- **Touchpoints**: Which word-note combinations appear in both songs?
- **Orthogonality**: How different are the songs? (0.0 = identical, 1.0 = completely different)
- **Unique patterns**: What makes each song distinctive?

## Real-World Analysis Results

### Simple Song (25 tokens)

**Hybrid tokenization statistics**:
```
Unique words: 21
Unique notes: 6
Unique hybrid tokens: 24

Word-note associations:
  "hello" → always sung on C4 (tonic/home note)
  "world" → sung on both C4 and G4 (tonic and dominant)
  "feeling" → sung on both G4 and F4 (different melodic contexts)
  "you" → always on A4 (consistent melodic treatment)
```

**Musical insights**:
- Repeated words often use same notes (consistency)
- Some words paired with multiple notes (variation)
- Opening words typically on tonic (C4) - establishes key
- Emotional words sometimes get higher notes

### Nature Song (33 tokens)

**Hybrid tokenization statistics**:
```
Unique words: 31
Unique notes: 6
Unique hybrid tokens: 33

Word-note associations:
  "the" → sung on C4, E4, and G4 (versatile connector word)
  "trees" → C4 (grounded, low)
  "above" → A4 (highest note for "above" - semantic match!)
  "fly" → F4 (elevated but not highest)
```

**Musical insights**:
- Semantic-melodic alignment: "above" gets highest note
- Common words ("the") more melodically flexible
- Content words get consistent melodic treatment
- Verbs of motion paired with mid-high notes

### Comparison: Simple Song vs Nature Song

```
Orthogonality: 0.982 (98.2% different)
Common tokens: 1 (nearly no overlap)
Shared patterns: Different lyrical and melodic vocabularies
```

**Insights**:
- Different topics → different word choices
- Different melodies → different note patterns
- Minimal hybrid token overlap despite using same pitch range

## Musical and Linguistic Insights

### Word-Melody Associations

Hybrid graphs reveal how specific words pair with specific notes:

**Common patterns observed**:
1. **Tonic grounding**: Opening/closing words often on tonic (C in C major)
2. **Semantic height**: "up", "high", "above" → higher notes
3. **Emotional intensity**: Strong emotions → wider intervals or higher notes
4. **Functional words**: Articles, prepositions → more melodic variation
5. **Content consistency**: Important nouns/verbs → consistent melodic treatment

### Centrality in Hybrid Graphs

**What centrality means for hybrid tokens**:
- **High degree**: Word-note combination connects to many others (versatile transitions)
- **High betweenness**: Critical bridge between song sections
- **High closeness**: Central to the song's overall structure

**Example**:
- `hello-C4` has high centrality → song opener, returns frequently
- `day-F4` has low centrality → appears at song end

### Communities in Hybrid Graphs

Communities reveal **musical phrases** or **thematic sections**:

**Example**:
```
Community 1: [hello-C4, world-C4, my-C4, way-C4]
  → Opening phrase, all on tonic

Community 2: [you-A4, today-A4, singing-A4, songs-A4]
  → High-energy section, all on A4

Community 3: [feeling-G4, are-G4, all-G4, how-G4]
  → Middle section, questioning/connecting
```

### Cycles in Hybrid Graphs

Cycles indicate **recurring patterns**:

**Types of cycles**:
1. **Lyrical repetition on same note**: "la-C4 → la-C4" (like "la la la")
2. **Chorus patterns**: Same word-note sequence repeats
3. **Melodic motifs**: Different words, same melodic contour

## Advanced Use Cases

### 1. Emotional Word-Melody Mapping

**Goal**: Discover which notes are associated with emotional words

```bash
# Create song with emotional markers
cat > songs/emotional_song.txt << 'EOF'
happy G4
sad D4
love E4
joy A4
pain C4
hope F4
EOF

# Build hybrid graph
python3 src/hybrid_tokenizer.py songs/emotional_song.txt -o songs/emotional_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/emotional_hybrid.txt -o output/emotional_graph.json

# Analyze note associations
python3 src/hybrid_tokenizer.py songs/emotional_song.txt --stats-only
```

**Insight**: See which emotions get which melodic treatments

### 2. Genre-Specific Word-Melody Patterns

**Goal**: Compare how different genres pair words with melodies

```bash
# Analyze pop song
python3 src/hybrid_tokenizer.py songs/pop_song.txt -o songs/pop_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/pop_hybrid.txt -o output/pop_graph.json

# Analyze folk song
python3 src/hybrid_tokenizer.py songs/folk_song.txt -o songs/folk_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/folk_hybrid.txt -o output/folk_graph.json

# Compare
python3 src/merge_word_graphs.py output/pop_graph.json output/folk_graph.json
```

**Insight**: Different genres may use same words with different melodic treatments

### 3. Songwriter Style Analysis

**Goal**: Identify unique word-melody signatures of different songwriters

```bash
# Analyze multiple songs by same artist
for song in artist1_*.txt; do
    python3 src/hybrid_tokenizer.py songs/$song -o songs/${song%.txt}_hybrid.txt -m hybrid
    python3 src/midi_graph_builder.py songs/${song%.txt}_hybrid.txt -o output/${song%.txt}_graph.json
done

# Merge all graphs
python3 src/merge_word_graphs.py output/artist1_*.json -o output/artist1_signature.json
```

**Insight**: Artists may have characteristic word-note pairings

### 4. Translation Analysis

**Goal**: Compare original song to translated version

```bash
# Original language
python3 src/hybrid_tokenizer.py songs/original.txt -o songs/original_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/original_hybrid.txt -o output/original_graph.json

# Translation (same melody, different words)
python3 src/hybrid_tokenizer.py songs/translated.txt -o songs/translated_hybrid.txt -m hybrid
python3 src/midi_graph_builder.py songs/translated_hybrid.txt -o output/translated_graph.json

# Compare
python3 src/merge_word_graphs.py output/original_graph.json output/translated_graph.json
```

**Insight**: Melody stays same (shared note patterns), lyrics change (different hybrid tokens)

### 5. Cover Song Analysis

**Goal**: See how different artists interpret the same song

```bash
# Original version
python3 src/hybrid_tokenizer.py songs/original_version.txt -o songs/original_hybrid.txt

# Cover version (might have melodic variations)
python3 src/hybrid_tokenizer.py songs/cover_version.txt -o songs/cover_hybrid.txt

# Build and compare
# ... (same workflow as above)
```

**Insight**: Identify which word-note combinations stay vs change

## Tips for Creating Aligned Files

### 1. Manual Alignment

For short songs, manually write word-note pairs:

```
verse C4
one D4
goes E4
like F4
this G4
```

### 2. MIDI + Lyrics Alignment (Future)

For existing MIDI + lyrics:
1. Load MIDI to get note timing
2. Load lyrics text
3. Manually or algorithmically align syllables to notes
4. Export as aligned format

### 3. Syllable Splitting

Break multi-syllable words:

```
beau-ti-ful C4 D4 E4  → becomes:
beau C4
ti D4
ful E4
```

### 4. Melismas (Multiple Notes per Syllable)

Choose one of:
- **Use first note**: `love-C4` (ignoring the embellishment)
- **Create sequence**: `love-C4 love-D4 love-C4` (shows the run)

## Limitations and Future Work

### Current Limitations

1. **Manual alignment required**: No automatic syllable-to-note matching yet
2. **Monophonic melodies**: Best for single melody line, not full arrangements
3. **No harmony**: Chord progressions not captured
4. **No rhythm detail**: Duration/timing simplified
5. **No rests**: Silence not represented

### Future Enhancements

1. **Automatic alignment**: Use speech-to-MIDI alignment algorithms
2. **Harmony support**: Include chord symbols (e.g., `love-C4-Cmaj7`)
3. **Rhythm encoding**: Include duration in tokens (e.g., `love-C4-quarter`)
4. **Multi-voice**: Analyze harmonies and backing vocals
5. **Prosody analysis**: Map lyrical stress to melodic accents
6. **Phonetic matching**: Analyze vowel sounds with pitch contours

## Research Applications

1. **Music cognition**: How do humans associate words with melodies?
2. **Songwriting AI**: Train models on word-melody patterns
3. **Music education**: Visualize word-melody relationships for students
4. **Cultural analysis**: Compare word-melody conventions across cultures
5. **Emotional mapping**: Study emotion-pitch associations
6. **Linguistic prosody**: Analyze tonal languages through music
7. **Accessibility**: Help non-musicians understand song structure

## Example Questions Hybrid Graphs Can Answer

1. **Does "love" usually get sung on higher notes?**
   - Check word-note associations for emotional words

2. **Which words appear in both the verse and chorus?**
   - Analyze communities and find shared tokens

3. **How similar are two love songs?**
   - Compute orthogonality of hybrid graphs

4. **What makes this artist's style unique?**
   - Compare artist's hybrid patterns to others

5. **Did the cover change the melody?**
   - Compare original vs cover hybrid graphs, check for different note associations

6. **Which section of the song is most repetitive?**
   - Count cycles in hybrid graph

7. **Are there semantic-melodic alignments?** (e.g., "high" sung on high notes)
   - Manually inspect word-note associations

## Conclusion

Hybrid graphs represent a powerful new way to analyze songs as complete artistic works, bridging the gap between linguistic and musical analysis. By treating word-melody combinations as tokens, we can:

- **Unify** text and music analysis
- **Discover** hidden word-melody patterns
- **Compare** different artistic interpretations
- **Understand** how meaning emerges from both dimensions

Whether you're a musician, researcher, or data scientist, hybrid graphs open new possibilities for understanding the art of songwriting.

---

**From words to notes to songs - Wordplay analyzes it all!**
