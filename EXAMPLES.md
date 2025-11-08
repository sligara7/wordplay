# Wordplay Examples - Research Use Cases

## Example 1: Identifying Language Bottlenecks

**Research Question**: Are there "bottleneck" words that create unnecessary complexity in technical writing?

### Method
1. Generate word graph from technical documentation
2. Analyze betweenness centrality (bridge words)
3. Identify high-betweenness words that could be simplified

### Example
```bash
# Generate graph
python3 src/word_graph_builder.py technical_doc.txt \
  --remove-stopwords \
  -o output/tech_doc_graph.json

# Analyze
python3 src/analyze_word_graph.py output/tech_doc_graph.json
```

### Interpretation
High betweenness words like "utilize", "implement", "facilitate" could be simplified to "use", "do", "help" for better readability.

---

## Example 2: Comparing Author Styles

**Research Question**: Do different authors have distinct language structure signatures?

### Method
1. Generate graphs for books by different authors
2. Compare centrality distributions
3. Analyze community structures

### Example
```bash
# Process books by two authors
python3 src/batch_process_books.py author1_books/ -o output/author1/
python3 src/batch_process_books.py author2_books/ -o output/author2/

# Merge all books by each author
python3 src/merge_word_graphs.py output/author1/*.json -o output/author1_style.json
python3 src/merge_word_graphs.py output/author2/*.json -o output/author2_style.json

# Compare
python3 src/analyze_word_graph.py output/author1_style.json
python3 src/analyze_word_graph.py output/author2_style.json
```

### What to Look For
- **Degree distribution**: Some authors use more varied vocabulary
- **Community count**: More communities = more topic diversity
- **Cycle count**: More cycles = more repetitive/circular language

---

## Example 3: Genre Classification

**Research Question**: Can we distinguish genres by graph structure?

### Method
1. Generate graphs for multiple books in each genre
2. Compute structural metrics (density, centrality, cycles)
3. Look for genre signatures

### Example
```bash
# Process different genres
python3 src/batch_process_books.py fiction_books/ -o output/fiction/
python3 src/batch_process_books.py scientific_papers/ -o output/science/
python3 src/batch_process_books.py news_articles/ -o output/news/

# Analyze each
for genre in fiction science news; do
  python3 src/merge_word_graphs.py output/$genre/*.json -o output/${genre}_merged.json
  python3 src/analyze_word_graph.py output/${genre}_merged.json > output/${genre}_analysis.txt
done
```

### Expected Results

| Genre | Density | Avg Degree | Communities | Cycles |
|-------|---------|------------|-------------|--------|
| Fiction | Low | 1.2 | Many (20+) | Few |
| Science | Medium | 2.5 | Few (5-10) | Many |
| News | High | 3.0 | Medium (10-15) | Some |

**Interpretation**:
- **Fiction**: Linear narrative → low density, few cycles
- **Science**: Technical terms interconnected → higher density, more cycles (repeated terminology)
- **News**: Formulaic structure → high density, medium cycles

---

## Example 4: Translation Quality Assessment

**Research Question**: Do translations preserve the original text's structure?

### Method
1. Generate graphs for original and translated texts
2. Compare structural metrics
3. Identify what changes in translation

### Example
```bash
# Process original and translation
python3 src/word_graph_builder.py original_english.txt -o output/original.json
python3 src/word_graph_builder.py translated_from_french.txt -o output/translation.json

# Merge to find differences
python3 src/merge_word_graphs.py \
  output/original.json \
  output/translation.json \
  -o output/comparison.json
```

### What to Compare
- **Orthogonality**: Should be low (<0.3) for good translation
- **Community structure**: Should be similar
- **Central words**: Key concepts should remain central
- **Cycle patterns**: Narrative structure should be preserved

---

## Example 5: Language Evolution Over Time

**Research Question**: How has English language structure changed over centuries?

### Method
1. Process texts from different time periods
2. Compare vocabulary and structure
3. Track changes in centrality and connectivity

### Example
```bash
# Process texts by century
python3 src/batch_process_books.py 1800s_texts/ -o output/1800s/
python3 src/batch_process_books.py 1900s_texts/ -o output/1900s/
python3 src/batch_process_books.py 2000s_texts/ -o output/2000s/

# Merge by period
for period in 1800s 1900s 2000s; do
  python3 src/merge_word_graphs.py output/$period/*.json -o output/${period}_merged.json
  python3 src/analyze_word_graph.py output/${period}_merged.json > output/${period}_analysis.txt
done

# Compare evolution
python3 src/merge_word_graphs.py \
  output/1800s_merged.json \
  output/2000s_merged.json \
  --analyze-only
```

### Expected Findings
- **Decreasing vocabulary size**: Modern texts may use simpler language
- **Changing centrality**: Different words become central over time
- **New communities**: New topics emerge (technology, social media)

---

## Example 6: Code Documentation Analysis

**Research Question**: Is code documentation more efficient than natural language?

### Method
1. Process API documentation, comments, README files
2. Compare with equivalent natural language descriptions
3. Analyze structural efficiency

### Example
```bash
# Process code docs and natural language docs
python3 src/word_graph_builder.py api_reference.txt -o output/api_docs.json
python3 src/word_graph_builder.py tutorial.txt -o output/tutorial.json

# Analyze
python3 src/analyze_word_graph.py output/api_docs.json
python3 src/analyze_word_graph.py output/tutorial.json
```

### Metrics to Compare
- **Density**: Code docs should be denser (more interconnected)
- **Centrality concentration**: Code docs should have fewer high-centrality words
- **Path length**: Code docs should have shorter paths (more direct)

---

## Example 7: Political Speech Analysis

**Research Question**: Do different political ideologies use different language structures?

### Method
1. Process speeches from different political figures
2. Compare vocabulary overlap (orthogonality)
3. Analyze word communities

### Example
```bash
# Process speeches
python3 src/batch_process_books.py progressive_speeches/ -o output/progressive/
python3 src/batch_process_books.py conservative_speeches/ -o output/conservative/

# Merge by ideology
python3 src/merge_word_graphs.py output/progressive/*.json -o output/progressive_merged.json
python3 src/merge_word_graphs.py output/conservative/*.json -o output/conservative_merged.json

# Compare
python3 src/merge_word_graphs.py \
  output/progressive_merged.json \
  output/conservative_merged.json \
  -o output/political_comparison.json
```

### What to Look For
- **Orthogonality**: How different are the vocabularies?
- **Shared touchpoints**: What common words do they use?
- **Unique communities**: What topics are unique to each?
- **Centrality differences**: What words are most important to each?

---

## Example 8: Detecting Circular Reasoning

**Research Question**: Can we detect circular reasoning in arguments?

### Method
1. Generate graph from argumentative text
2. Analyze cycles
3. Identify logical loops

### Example
```bash
# Process argumentative essay
python3 src/word_graph_builder.py argument.txt -o output/argument.json

# Analyze with focus on cycles
python3 src/analyze_word_graph.py output/argument.json
```

### Interpretation
- **Many short cycles** (2-3 words): May indicate circular definitions
- **Long cycles** (10+ words): May indicate circular arguments
- **No cycles** (DAG): Linear logical flow

**Example circular reasoning**:
```
"A is good because B"
"B is good because C"
"C is good because A"
```
Creates cycle: A → B → C → A

---

## Example 9: Finding Bridge Concepts

**Research Question**: What concepts bridge different domains?

### Method
1. Merge graphs from different domains
2. Find high-betweenness words in merged graph
3. These are bridge concepts

### Example
```bash
# Merge orthogonal domains
python3 src/merge_word_graphs.py \
  output/graphs/biology_book_graph.json \
  output/graphs/computer_science_book_graph.json \
  -o output/bio_cs_merged.json

# Analyze
python3 src/analyze_word_graph.py output/bio_cs_merged.json
```

### Expected Bridge Words
- Abstract concepts: "system", "network", "process", "information"
- Action verbs: "connect", "transmit", "process", "store"
- Structural words: "hierarchy", "organization", "structure"

**Research insight**: Bridge words tend to be more abstract and domain-independent.

---

## Example 10: Optimizing Communication

**Research Question**: Can we identify and eliminate unnecessary complexity?

### Method
1. Generate graph of current documentation
2. Identify bottlenecks and long paths
3. Suggest simpler alternatives

### Example
```bash
# Analyze current documentation
python3 src/word_graph_builder.py current_docs.txt -o output/current.json
python3 src/analyze_word_graph.py output/current.json > output/analysis.txt

# Look for:
# - High betweenness words (bottlenecks)
# - Words with many synonyms
# - Unnecessary jargon
```

### Optimization Strategy
1. **Replace bottleneck words** with simpler alternatives
2. **Reduce cycles** by eliminating repetitive phrases
3. **Increase density** by using more direct connections
4. **Test**: Generate graph of revised docs and compare metrics

---

## Combining Multiple Analyses

### Comprehensive Book Analysis Workflow

```bash
#!/bin/bash
# Comprehensive analysis of a book

BOOK="mybook.txt"
TITLE="My Book"
OUT="output/comprehensive_analysis"

mkdir -p $OUT

# 1. Generate word graph
echo "Generating word graph..."
python3 src/word_graph_builder.py books/$BOOK -t "$TITLE" -o $OUT/graph.json

# 2. Generate filtered graph (no stopwords)
echo "Generating filtered graph..."
python3 src/word_graph_builder.py books/$BOOK -t "$TITLE" \
  --remove-stopwords -o $OUT/graph_filtered.json

# 3. Analyze both
echo "Analyzing graphs..."
python3 src/analyze_word_graph.py $OUT/graph.json -o $OUT/analysis_full.json
python3 src/analyze_word_graph.py $OUT/graph_filtered.json -o $OUT/analysis_filtered.json

# 4. Extract insights
echo "Key insights:"
echo "Full vocabulary:"
jq '.basic_statistics' $OUT/analysis_full.json

echo ""
echo "Content words only:"
jq '.basic_statistics' $OUT/analysis_filtered.json

echo ""
echo "Most central words (full):"
jq '.analyses.centrality.top_by_degree[:5]' $OUT/analysis_full.json

echo ""
echo "Most central content words:"
jq '.analyses.centrality.top_by_degree[:5]' $OUT/analysis_filtered.json
```

---

## Tips for Research

### 1. Preprocessing
- **Remove stopwords** for content analysis
- **Keep stopwords** for style analysis
- **Lowercase** for vocabulary analysis
- **Keep case** for proper noun analysis

### 2. Choosing Metrics
- **Centrality**: Find key concepts
- **Communities**: Identify topics
- **Cycles**: Detect repetition/circular logic
- **Density**: Measure interconnectedness

### 3. Interpretation
- **High density**: Interconnected concepts
- **Low density**: Linear narrative
- **Many communities**: Diverse topics
- **Few communities**: Focused theme
- **Many cycles**: Repetitive language
- **Few cycles**: Progressive flow

### 4. Comparison
- Use **orthogonality** for vocabulary similarity
- Use **structural metrics** for style similarity
- Use **touchpoints** to find shared concepts
- Use **merge analysis** to understand relationships

---

## Further Reading

- **Network Science**: Albert-László Barabási's work on scale-free networks
- **Natural Language Processing**: NLTK, spaCy for advanced text analysis
- **Graph Theory**: NetworkX documentation for more analysis methods
- **Systems Engineering**: Reflow documentation for methodology
