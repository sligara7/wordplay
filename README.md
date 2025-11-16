# Wordplay - Language Structure Analysis

Analyze language structure as directed graphs using systems engineering tools from [reflow](https://github.com/sligara7/reflow) and [chain_reflow](https://github.com/sligara7/chain_reflow).

## Overview

Wordplay treats language as a system of interconnected components:
- **Nodes**: Individual words (tokens)
- **Edges**: Word transitions (one word following another)
- **Edge Weights**: Transition probabilities (normalized frequencies)

By representing text as graphs, we can apply powerful systems analysis tools to understand:
- **Language structure**: Which words are central vs peripheral
- **Word communities**: Clusters of related words
- **Information flow**: Bottlenecks and pathways through vocabulary
- **Efficiency**: Are there more optimal language structures?

## NEW: Music Analysis Support

**Wordplay now extends to music!** Analyze everything from simple melodies to complex multi-track compositions:
- **Monophonic**: Single melody lines (notes as tokens)
- **Polyphonic**: Multi-track music with chords, bass, drums
- **Hybrid graphs**: Combine lyrics and melodies
- **Harmonic analysis**: Chord progressions using music theory
- **Multi-layer graphs**: Each instrument as a separate graph layer
- **Temporal analysis**: Rhythm, tempo, duration (NEW!)
- **Batch processing**: Merge multiple graphs to find patterns (NEW!)

**Documentation:**
- [MIDI_SUPPORT.md](MIDI_SUPPORT.md) - Basic music analysis
- [HYBRID_GRAPHS.md](HYBRID_GRAPHS.md) - Lyrics + melody integration
- [POLYPHONIC_MUSIC.md](POLYPHONIC_MUSIC.md) - Multi-track polyphonic analysis
- [TEMPORAL_ANALYSIS.md](TEMPORAL_ANALYSIS.md) - Rhythm, cadence, and batch processing
- [AUDIO_TRANSCRIPTION.md](AUDIO_TRANSCRIPTION.md) - **Audio-to-MIDI transcription using graph theory (NEW!)**

**Quick example:**
```bash
# Create a sample MIDI file
python3 src/create_sample_midi.py twinkle

# Tokenize → Build Graph → Analyze
python3 src/midi_tokenizer.py music/twinkle.mid -o music/twinkle_tokens.txt
python3 src/midi_graph_builder.py music/twinkle_tokens.txt -o output/twinkle_graph.json
python3 src/analyze_word_graph.py output/twinkle_graph.json
```

## NEW: Audio-to-MIDI Transcription (Experimental)

**Graph-based approach to converting audio files (.wav) to MIDI using network analysis!**

Traditional audio transcription relies on signal processing alone. This experimental feature uses **graph theory** to model the relationships between frequencies, harmonics, and temporal patterns - leveraging NetworkX algorithms to separate root notes from harmonics and detect note onsets.

### Key Innovation: Musical Networks

Instead of processing frequencies in isolation, we model audio as a **multi-layer network**:

- **Nodes**: Each (frequency, time, intensity) point from a specialized Fourier transform
- **Temporal Edges**: Connect same frequency across time (sustain detection)
- **Harmonic Edges**: Connect frequencies with harmonic ratios (2f, 3f, 4f...)
- **Music Theory Edges**: Connect notes in the same scale/chord

### Graph Analysis Methods

1. **Harmonic Filtering** → Community Detection (Louvain algorithm)
   - Group harmonically-related frequencies into communities
   - Lowest frequency in each community = fundamental note

2. **Onset Detection** → Temporal Flow Analysis
   - Model intensity changes as flow through the network
   - High flow delta = note attack

3. **Music Theory Constraints** → Path Analysis
   - Detect key signature from note histogram
   - Filter implausible notes using scale membership

4. **Instrument Separation** → Structural Holes
   - Use betweenness centrality to identify instrument boundaries
   - Cluster by spectral range and timbre similarity

### Example Usage

```python
from audio_graph_analyzer import AudioGraphAnalyzer, specialized_fourier_transform

# Step 1: Apply specialized Fourier transform (user-provided)
frequency_time_matrix, frequencies, time_samples = specialized_fourier_transform(
    "song.wav",
    num_sub_notes=4,          # Sub-note divisions (quarter-note increments)
    sample_duration_cycles=5   # Time sampling (5 cycles of 27.5 Hz ≈ 182ms)
)

# Step 2: Create graph analyzer
analyzer = AudioGraphAnalyzer(
    frequency_time_matrix=frequency_time_matrix,
    sample_rate_hz=22050,
    frequencies=frequencies,
    time_samples=time_samples
)

# Step 3: Run analysis
result = analyzer.analyze()

# Step 4: Export MIDI
analyzer.export_midi("output.mid", result.notes)

# Step 5: Export graph for further analysis
analyzer.export_graph_json("audio_graph.json")
```

### Status: Design Phase

This feature is currently in the **design/documentation phase**. The skeleton implementation is complete with:
- ✅ Graph construction algorithms
- ✅ Harmonic filtering via community detection
- ✅ Onset detection via temporal flow
- ✅ Music theory integration
- ✅ MIDI output generation
- ⏳ **Awaiting**: Specialized Fourier transform implementation

**Placeholder for Fourier Transform**: Users can provide their own specialized Fourier transform that generates the 2D frequency-time-intensity array. See `src/audio_graph_analyzer.py` for the required format.

**Try it:**
```bash
# Run example with synthetic test data
python3 examples/example_audio_transcription.py
```

See [AUDIO_TRANSCRIPTION.md](AUDIO_TRANSCRIPTION.md) for complete methodology and theoretical background.

## Key Features

### 1. Word Graph Generation
Convert any text into a directed graph compatible with reflow's `system_of_systems_graph.json` format.

```bash
python3 src/word_graph_builder.py books/mybook.txt -t "My Book" -o output/mybook_graph.json
```

**Options:**
- `--min-length N`: Minimum word length (default: 2)
- `--keep-case`: Preserve original capitalization
- `--remove-stopwords`: Filter common words (the, is, was, etc.)

### 2. Graph Analysis
Apply NetworkX-based analysis to discover:
- **Centrality**: Most connected/important words
- **Communities**: Clusters of related words
- **DAG properties**: Cycles in language flow
- **Structural issues**: Orphaned words, dead ends, bottlenecks

```bash
python3 src/analyze_word_graph.py output/mybook_graph.json
```

### 3. Batch Processing
Process multiple books at once:

```bash
python3 src/batch_process_books.py books/ -o output/graphs --pattern "*.txt"
```

### 4. Graph Merging
Merge word networks from different books to find commonality:

```bash
python3 src/merge_word_graphs.py \
  output/graphs/book1_graph.json \
  output/graphs/book2_graph.json \
  -o output/merged_graph.json
```

**Orthogonality Analysis**: Measures how different two vocabularies are
- 0.0 = identical vocabulary
- 1.0 = completely different vocabulary

## Example Workflow

### Example 1: Single Book Analysis

```bash
# 1. Generate word graph
python3 src/word_graph_builder.py books/nature_book.txt \
  -t "Nature Book" \
  -o output/nature_graph.json \
  --remove-stopwords

# 2. Analyze the graph
python3 src/analyze_word_graph.py output/nature_graph.json
```

**Output:**
```
======================================================================
WORD NETWORK ANALYSIS: Nature Book
======================================================================

Basic Statistics:
  Words (nodes): 83
  Transitions (edges): 86
  Density: 0.0127
  Avg transitions per word: 1.04

Most Connected Words (by degree):
  - forest: 0.061
  - through: 0.049
  - water: 0.037

Word Communities: 5 clusters found
  Largest community: 18 words

DAG Status: ✗ Contains 12 cycles

Structural Analysis:
  Dead ends (sentence-final words): 1
  Unreachable (sentence-initial words): 0
  Orphaned words: 0
```

### Example 2: Comparing Orthogonal Books

Two books with completely different topics (Nature vs Technology):

```bash
# 1. Generate graphs for both books
python3 src/batch_process_books.py books/ \
  -o output/graphs \
  --remove-stopwords

# 2. Merge the graphs
python3 src/merge_word_graphs.py \
  output/graphs/nature_book_graph.json \
  output/graphs/technology_book_graph.json \
  -o output/merged_nature_tech.json
```

**Orthogonality Analysis:**
```
Touchpoint Analysis:
  Words common to all books: 2
  Pairwise common words:
    nature_book ∩ technology_book: 2 words

  Unique words per book:
    nature_book: 81 unique words
    technology_book: 78 unique words

Orthogonality Analysis:
  Orthogonality score: 0.988
  (0.0 = identical vocabulary, 1.0 = completely different)
```

**Interpretation**: Despite being 98.8% orthogonal (completely different topics), the books share 2 common words that provide linguistic bridges.

```bash
# 3. Analyze the merged graph
python3 src/analyze_word_graph.py output/merged_nature_tech.json
```

## Graph Format

Word graphs use the `system_of_systems_graph.json` format from reflow:

```json
{
  "metadata": {
    "framework": "Language Flow",
    "framework_id": "language_flow",
    "num_nodes": 83,
    "num_edges": 86,
    "book_title": "Nature Book"
  },
  "graph": {
    "directed": true,
    "nodes": [
      {
        "id": "word_forest",
        "name": "forest",
        "type": "word",
        "raw": {
          "word": "forest",
          "frequency": 5,
          "outgoing_transitions": 4
        }
      }
    ],
    "links": [
      {
        "source": "word_forest",
        "target": "word_grew",
        "type": "word_transition",
        "weight": 0.25,
        "raw": {
          "transition_count": 1,
          "transition_probability": 0.25
        }
      }
    ]
  }
}
```

## Analysis Capabilities

### Centrality Metrics
- **Degree Centrality**: Words with most direct connections (most versatile)
- **Betweenness Centrality**: Bridge words connecting different parts of text
- **Closeness Centrality**: Words closest to all other words (central to vocabulary)

### Community Detection
Uses greedy modularity to identify clusters of words that frequently occur together. Useful for:
- Topic modeling
- Semantic clustering
- Identifying thematic sections

### DAG Analysis
Detects cycles in word transitions:
- **Perfect DAG**: No cycles, linear flow
- **Cycles**: Words that loop back (e.g., "the forest, the trees, the forest")

### Structural Issues
- **Dead Ends**: Sentence-final words (no words follow)
- **Unreachable**: Sentence-initial words (no words lead to them)
- **Orphaned**: Isolated words with no connections
- **Bottlenecks**: Words that must be traversed to connect different regions

## Integration with Reflow/Chain_reflow

Word graphs are fully compatible with reflow's system engineering tools:

### Using system_of_systems_graph_v2.py
While the tool expects to BUILD graphs from component architectures, you can use the analysis functions directly:

```python
import networkx as nx
import json

# Load word graph
with open('output/mybook_graph.json', 'r') as f:
    data = json.load(f)

# Convert to NetworkX DiGraph
G = nx.DiGraph()
for node in data['graph']['nodes']:
    G.add_node(node['id'], **node)
for edge in data['graph']['links']:
    G.add_edge(edge['source'], edge['target'], **edge)

# Now use reflow's analysis functions
# (see analyze_word_graph.py for examples)
```

### Using chain_reflow for Multi-Book Merging
The merge tool (`merge_word_graphs.py`) uses techniques inspired by chain_reflow:
- **Touchpoint identification**: Common words between books
- **Orthogonality assessment**: How different vocabularies are
- **Graph merging**: Combine networks using union or intersection strategies

## Research Questions

This project enables exploration of fascinating questions:

### 1. Language Efficiency
Can we identify more efficient language structures?
- Are there bottleneck words that create unnecessary complexity?
- Do certain authors use more direct vs circuitous paths?

### 2. Genre Differences
How do different genres structure language?
- Scientific writing vs literary fiction
- Technical documentation vs marketing copy

### 3. Cross-Domain Bridges
When merging orthogonal texts, what common words emerge?
- Are bridge words more abstract or concrete?
- Do they represent universal concepts?

### 4. Evolution of Language
Compare texts across time periods:
- How has vocabulary structure changed?
- Are modern texts more/less interconnected?

## Files and Directories

```
wordplay/
├── src/
│   ├── word_graph_builder.py    # Generate word graphs from text
│   ├── analyze_word_graph.py    # Analyze graph structure
│   ├── batch_process_books.py   # Process multiple books
│   └── merge_word_graphs.py     # Merge graphs from different books
├── books/                        # Input text files
│   ├── sample_text.txt
│   ├── nature_book.txt
│   └── technology_book.txt
├── output/
│   ├── graphs/                   # Individual book graphs
│   └── merged_*.json             # Merged graphs
├── specs/
│   └── machine/
│       └── graphs/               # Graph schemas
└── README.md                     # This file
```

## Dependencies

- **Python 3.8+**
- **NetworkX**: `pip install networkx`
- **Standard library**: json, argparse, collections, pathlib, datetime

Optional:
- **reflow tools**: For advanced analysis ([reflow](https://github.com/sligara7/reflow))
- **chain_reflow tools**: For multi-graph linking ([chain_reflow](https://github.com/sligara7/chain_reflow))

## Future Enhancements

### Advanced Analysis
- **Semantic enrichment**: Add word embeddings for similarity
- **Part-of-speech tagging**: Analyze syntactic patterns
- **N-gram graphs**: Extend to multi-word sequences

### Visualization
- **Interactive graphs**: D3.js/Cytoscape.js visualizations
- **Heatmaps**: Transition probability matrices
- **Flow diagrams**: Sankey diagrams for word flows

### Integration
- **Full chain_reflow workflows**: Use creative linking for cross-genre analysis
- **Matryoshka analysis**: Detect hierarchical levels (word → phrase → sentence → paragraph)
- **Causality analysis**: Distinguish correlation from causation in word relationships

## Citation

If you use this project in research, please cite:

```
Wordplay: Language Structure Analysis using Systems Engineering Tools
Built with reflow (https://github.com/sligara7/reflow) and
chain_reflow (https://github.com/sligara7/chain_reflow)
```

## License

MIT License (or match reflow/chain_reflow license)

## Contributing

Contributions welcome! Areas of interest:
- More sophisticated tokenization (handle punctuation, contractions better)
- Additional analysis metrics (entropy, complexity measures)
- Visualization tools
- Integration with NLP libraries (spaCy, NLTK)

## Acknowledgments

This project builds on:
- [reflow](https://github.com/sligara7/reflow): Systems engineering workflows
- [chain_reflow](https://github.com/sligara7/chain_reflow): Multi-architecture linking
- [NetworkX](https://networkx.org/): Graph analysis library
