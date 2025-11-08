# Wordplay Quick Start Guide

## Installation

No installation needed! Just Python 3.8+ with NetworkX:

```bash
pip install networkx
```

## 5-Minute Quick Start

### 1. Create a text file

Create `books/mybook.txt`:
```
The cat sat on the mat. The dog ran fast. The bird flew high.
```

### 2. Generate word graph

```bash
cd /home/ajs7/project/wordplay
python3 src/word_graph_builder.py books/mybook.txt -t "My Book" -o output/mybook_graph.json
```

### 3. Analyze the graph

```bash
python3 src/analyze_word_graph.py output/mybook_graph.json
```

You'll see:
- Most connected words (centrality)
- Word communities (clusters)
- Cycles in language flow
- Structural analysis

## Common Use Cases

### Use Case 1: Compare Two Books

```bash
# Generate graphs for both books
python3 src/word_graph_builder.py books/book1.txt -o output/book1_graph.json
python3 src/word_graph_builder.py books/book2.txt -o output/book2_graph.json

# Merge and compare
python3 src/merge_word_graphs.py \
  output/book1_graph.json \
  output/book2_graph.json \
  -o output/merged.json
```

**Output includes:**
- Orthogonality score (how different the vocabularies are)
- Common words (touchpoints)
- Unique words per book

### Use Case 2: Batch Process Multiple Books

```bash
# Put all .txt files in books/ directory
python3 src/batch_process_books.py books/ -o output/graphs --pattern "*.txt"

# Creates graphs for all books at once
# Summary saved in output/graphs/batch_summary.json
```

### Use Case 3: Remove Common Words

```bash
# Filter out stopwords (the, is, was, etc.)
python3 src/word_graph_builder.py books/mybook.txt \
  --remove-stopwords \
  -o output/mybook_filtered_graph.json
```

**Result**: Focus on content words (nouns, verbs, adjectives)

### Use Case 4: Analyze Only Common Words

```bash
# Merge with intersection strategy (only common words)
python3 src/merge_word_graphs.py \
  output/book1_graph.json \
  output/book2_graph.json \
  -s intersection \
  -o output/common_only.json
```

**Use for**: Finding shared vocabulary between different texts

## Understanding the Output

### Graph Statistics
```
Words (nodes): 83              # Unique words in text
Transitions (edges): 86        # Word-to-word transitions
Density: 0.0127                # How interconnected (0-1)
Avg transitions per word: 1.04 # Branching factor
```

### Centrality Scores
```
Most Connected Words (by degree):
  - forest: 0.061    # Connects to 6.1% of all words
  - through: 0.049   # Bridge word
  - water: 0.037     # Important concept
```

- **High degree**: Versatile words used in many contexts
- **High betweenness**: Bridge words connecting different topics
- **High closeness**: Central words close to all others

### DAG Status
```
DAG Status: ✗ Contains 12 cycles
```

- **Perfect DAG (no cycles)**: Linear narrative flow
- **Many cycles**: Repetitive language, circular references

### Structural Issues
```
Dead ends: 1              # Sentence-final words
Unreachable: 0            # Sentence-initial words
Orphaned words: 0         # Isolated words
Bottlenecks: [...]        # Critical connection points
```

## Advanced Options

### Word Graph Builder Options

```bash
python3 src/word_graph_builder.py INPUT [OPTIONS]

Options:
  -t, --title TITLE           Book title for metadata
  -o, --output FILE           Output JSON file
  -m, --min-length N          Minimum word length (default: 2)
  --keep-case                 Preserve capitalization
  --remove-stopwords          Filter common words
```

### Merge Options

```bash
python3 src/merge_word_graphs.py GRAPHS... [OPTIONS]

Options:
  -o, --output FILE           Output merged graph
  -s, --strategy STRATEGY     union (all) or intersection (common only)
  --analyze-only              Show touchpoints without merging
```

## Example Results

### Nature Book (83 words)
```
Most Connected: forest, through, water
Communities: 5 clusters
  - Cluster 1: forest, trees, birds, branches (nature)
  - Cluster 2: river, fish, water, creek (aquatic)
  - Cluster 3: deer, squirrels, animals (fauna)
DAG: ✗ 12 cycles (e.g., "the forest" → "forest floor" → "the forest")
```

### Technology Book (80 words)
```
Most Connected: system, data, software
Communities: 6 clusters
  - Cluster 1: computer, processor, memory (hardware)
  - Cluster 2: code, software, applications (software)
  - Cluster 3: network, server, cloud (infrastructure)
DAG: ✗ 15 cycles
```

### Merged (Nature + Technology)
```
Orthogonality: 0.988 (98.8% different vocabularies)
Common Words: 2 (touchpoints: "the", "each")
Total Words: 161
Communities: 12 clusters (nature and tech separate)
```

## Interpreting Results

### High Orthogonality (>0.8)
**Meaning**: Books use very different vocabularies
**Example**: Nature book + Technology book = 0.988
**Insight**: Different domains, minimal overlap

### Low Orthogonality (<0.3)
**Meaning**: Books share most vocabulary
**Example**: Two chapters from same book
**Insight**: Similar topics or same author

### Many Cycles
**Meaning**: Repetitive language patterns
**Could indicate**:
- Formal/legal writing (repeated phrases)
- Poetry (refrains, repetition)
- Conversational text (circular topics)

### Few Cycles (Near-DAG)
**Meaning**: Linear progression
**Could indicate**:
- Narrative storytelling
- Technical documentation
- Sequential instructions

### High Centrality Words
**Common high-centrality words**:
- Articles: the, a, an
- Prepositions: in, on, at, through
- Conjunctions: and, but, or

**Content high-centrality words** (with --remove-stopwords):
- Main topics/themes
- Key concepts
- Central characters/objects

## Troubleshooting

### "No words found"
**Cause**: All words filtered out (too short or stopwords)
**Solution**: Lower `--min-length` or don't use `--remove-stopwords`

### "Graph is empty"
**Cause**: Text file is empty or unreadable
**Solution**: Check file encoding (should be UTF-8)

### "Too many nodes"
**Cause**: Very large book (>10k unique words)
**Solution**: Use `--remove-stopwords` to reduce size

### Analysis takes too long
**Cause**: Large merged graphs (>1000 nodes)
**Solution**: Use `--analyze-only` to skip full merge, or process smaller samples

## Next Steps

1. **Try your own texts**: Books, articles, code documentation
2. **Compare genres**: Fiction vs non-fiction, technical vs literary
3. **Track evolution**: Compare different editions or versions
4. **Cross-language**: Compare translations

## Resources

- **Full documentation**: See README.md
- **Graph format**: system_of_systems_graph.json from reflow
- **Analysis methods**: NetworkX documentation
- **Related tools**: reflow and chain_reflow projects
