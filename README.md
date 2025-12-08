# Wordplay - Multi-Domain Graph Analysis

A collection of projects that analyze structured data as directed graphs using systems engineering tools from [reflow](https://github.com/sligara7/reflow) and [chain_reflow](https://github.com/sligara7/chain_reflow).

## Vision

Represent any structured data as graphs to reveal hidden patterns:
- **Nodes**: Elements (words, notes, pixels, concepts)
- **Edges**: Relationships (transitions, harmonics, adjacencies)
- **Analysis**: Centrality, communities, flow patterns, structural issues

## Projects

This repository contains several related but distinct projects:

### 1. Core Language Graphs (`core/`)
The foundation - convert text to directed graphs and analyze.

```bash
# Generate word graph from text
python3 core/word_graph_builder.py books/mybook.txt -o output/graph.json

# Analyze the graph
python3 core/analyze_word_graph.py output/graph.json

# Merge multiple graphs
python3 core/merge_word_graphs.py graph1.json graph2.json -o merged.json
```

**Files:**
- `word_graph_builder.py` - Text to graph conversion
- `analyze_word_graph.py` - NetworkX-based analysis
- `merge_word_graphs.py` - Graph merging with orthogonality analysis
- `batch_process_books.py` - Process multiple texts
- `graph_query.py` - Query word paths and relationships

### 2. Biblical Text Analysis (`biblical/`)
Specialized analysis of KJV Gospels and Byzantine Greek texts.

```bash
# Download and analyze KJV gospels
python3 biblical/kjv_gospels_dag.py

# Analyze Byzantine Greek New Testament
python3 biblical/byzantine_text_dag.py
```

**Files:**
- `kjv_gospels_dag.py` - KJV gospel analysis
- `byzantine_text_dag.py` - Greek text analysis
- `graph_sentence_generator.py` - Generate sentences from graphs

**Docs:** `GOSPEL_ANALYSIS.md`, `byzantine_text_dag.md`

### 3. Music Analysis (`music/`)
Analyze music as graphs - from MIDI tokenization to audio transcription.

#### Subdirectories:
- **`tokenizers/`** - Convert MIDI to tokens (pitch, duration, hybrid)
- **`audio_to_midi/`** - Graph-based audio transcription
- **`synthesis/`** - Generate MIDI files
- **`chord_detection/`** - Chord recognition
- **`midi_synth/`** - MIDI synthesizer modules
- **`new_start/`** - Latest audio-to-MIDI pipeline

```bash
# Tokenize MIDI
python3 music/tokenizers/midi_tokenizer.py music/twinkle.mid -o tokens.txt

# Build music graph
python3 music/audio_to_midi/midi_graph_builder.py tokens.txt -o graph.json
```

**Docs:** `MIDI_SUPPORT.md`, `HYBRID_GRAPHS.md`, `AUDIO_TRANSCRIPTION.md`, `TEMPORAL_ANALYSIS.md`, `POLYPHONIC_MUSIC.md`

### 4. Image Analysis (`image/`)
Create structural fingerprints from images via spatial adjacency graphs.

```bash
# Build image region graph
python3 image/image_graph_builder.py photo.jpg -o image_graph.json
```

**Files:**
- `image_graph_builder.py` - Superpixel segmentation to graphs
- `create_test_image.py` - Generate test images
- `test_image_graph.py` - Demo and testing

**Docs:** `FUTURE_IDEAS.md`

### 5. LLM Evaluation (`llm/`)
Detect LLM output issues (mode collapse, repetition) using graph analysis.

```bash
python3 llm/llm_analyzer.py --reference corpus.txt --test llm_output.txt
```

**Files:**
- `llm_analyzer.py` - Graph-based LLM quality detection
- `good_llm_output.txt`, `bad_llm_output.txt` - Example outputs

**Docs:** `LLM_ANALYZER_GUIDE.md`, `LLM_CONNECTIONS.md`

### 6. Cross-Domain Analysis (`cross_domain/`)
Find structural resonances across domains (Structural Rorschach / Synesthesia).

> "Show me an image, and I'll tell you what it sounds like - not by meaning, but by *shape*."

**Files:** `structural_rorschach/` module with signature extraction, motif detection, spectral analysis

**Docs:** `CROSS_DOMAIN_DAG_FOUNDATION.md`, `FUNCTIONAL_REQUIREMENTS.md`, `FUTURE_EXPLORATIONS.md`

**Note:** This project is also available as a standalone repo at [synesthesia](https://github.com/sligara7/synesthesia).

### 7. Narrative Plot Structures (`narrative/`)
Model, analyze, and generate book/novel plot structures using DAGs.

> "Structure is the bones. Prose is the skin. Character is the soul. The DAG reveals the skeleton."

```bash
# Create a mystery novel skeleton
python3 -c "
from narrative import get_template
dag = get_template('mystery').create_skeleton('My Mystery', 'Author Name')
print(dag)
print(dag.calculate_metrics().summary())
"

# Analyze a narrative structure
python3 -c "
from narrative import NarrativeAnalyzer
from narrative.genre_templates import get_template
dag = get_template('thriller').create_skeleton()
analyzer = NarrativeAnalyzer(dag)
diagnosis = analyzer.diagnose()
print(diagnosis.summary())
"
```

**Features:**
- Genre templates (Mystery, Thriller, Romance, Epic Fantasy, Literary Fiction)
- Plot node types (Setup, Catalyst, Revelation, Complication, etc.)
- Edge types (Causes, Enables, Foreshadows, Reveals, etc.)
- Structural diagnostics (dangling threads, pacing issues, deus ex machina detection)
- Cross-domain signature extraction for Structural Rorschach integration
- **Reflow integration**: Export to `system_of_systems_graph.json` for analysis with reflow tools
- **Functional analysis**: Systems engineering approach with requirements, atomic functions, and chapter allocation

**Docs:** [DAG_BOOK_PLOTS.md](narrative/DAG_BOOK_PLOTS.md)

### 8. Tools & Utilities (`tools/`)
Translation matrices, gap detection, batch merging.

**Files:**
- `translation_matrix_finder.py` - Find transformation matrices between domains
- `matrix_gap_detection.py` - SVD-based gap analysis
- `batch_graph_merger.py` - Batch merge operations
- `reflow_gap_closure.py` - Integration with Reflow workflows

**Docs:** `translation_matrix_gap_analysis.md`, `minimal_anchor_translation.md`

## Directory Structure

```
wordplay/
├── core/                    # Language graph fundamentals
├── biblical/                # KJV & Byzantine text analysis
├── music/                   # Music analysis & synthesis
│   ├── tokenizers/         # MIDI tokenization
│   ├── audio_to_midi/      # Audio transcription
│   ├── synthesis/          # MIDI generation
│   ├── chord_detection/    # Chord recognition
│   ├── midi_synth/         # Synthesizer modules
│   └── new_start/          # Latest pipeline
├── image/                   # Image region graphs
├── llm/                     # LLM evaluation tools
├── cross_domain/            # Structural Rorschach
│   └── structural_rorschach/
├── narrative/               # Book/novel plot structures
├── tools/                   # Translation & gap analysis
├── books/                   # Input text files
├── data/                    # Cached downloads (KJV, Byzantine)
├── output/                  # Generated graphs
├── songs/                   # Song files for hybrid analysis
└── specs/                   # Graph schemas
```

## Installation

```bash
pip install networkx numpy scipy
# For image analysis:
pip install scikit-image pillow
# For music:
pip install mido
```

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a 5-minute introduction.

## Key Concepts

### Graph Format
All projects use the `system_of_systems_graph.json` format from reflow:
- Compatible with systems engineering analysis
- Supports metadata, typed nodes, weighted edges

### Orthogonality Analysis
When merging graphs from different domains:
- **0.0** = identical structure
- **1.0** = completely different

### Centrality Metrics
- **Degree**: Most connected elements
- **Betweenness**: Bridge elements between clusters
- **Closeness**: Central to the whole network

## Documentation

| Project | Docs |
|---------|------|
| Core | [QUICKSTART.md](QUICKSTART.md), [EXAMPLES.md](EXAMPLES.md) |
| Biblical | [GOSPEL_ANALYSIS.md](biblical/GOSPEL_ANALYSIS.md) |
| Music | [MIDI_SUPPORT.md](music/MIDI_SUPPORT.md), [AUDIO_TRANSCRIPTION.md](music/AUDIO_TRANSCRIPTION.md) |
| Image | [FUTURE_IDEAS.md](image/FUTURE_IDEAS.md) |
| LLM | [LLM_ANALYZER_GUIDE.md](llm/LLM_ANALYZER_GUIDE.md) |
| Cross-Domain | [CROSS_DOMAIN_DAG_FOUNDATION.md](cross_domain/CROSS_DOMAIN_DAG_FOUNDATION.md) |
| Narrative | [DAG_BOOK_PLOTS.md](narrative/DAG_BOOK_PLOTS.md) |
| Tools | [translation_matrix_gap_analysis.md](tools/translation_matrix_gap_analysis.md) |

## Integration

Built to work with:
- [reflow](https://github.com/sligara7/reflow) - Systems engineering workflows
- [chain_reflow](https://github.com/sligara7/chain_reflow) - Multi-architecture linking
- [synesthesia](https://github.com/sligara7/synesthesia) - Cross-domain analysis (standalone)

## License

MIT
