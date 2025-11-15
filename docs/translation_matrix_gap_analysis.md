# Translation Matrix Gap Analysis

## Overview

This project uses gap closure analysis from the [reflow](https://github.com/sligara7/reflow) framework to discover the transformation matrix **B** that translates between Koine Greek and King James English gospels.

## The Three-System Model

Using the gap analysis equation: **B = C × A^(-1)**

- **System A** (Source): Byzantine Majority Text Koine Greek Gospels DAG
- **System B** (Gap/Translation): The unknown transformation matrix we're discovering
- **System C** (Target): King James Version English Gospels DAG

## Results

### System Statistics

| System | Words | Effective Rank | Density | Description |
|--------|-------|----------------|---------|-------------|
| **A** (Greek) | 9,674 | 3,684 | 0.0004 | Byzantine Greek gospels word flow |
| **B** (Translation) | 3,447 × 9,674 | - | - | Transformation matrix (Greek → English) |
| **C** (English) | 3,447 | 1,235 | 0.0023 | KJV English gospels word flow |

### Key Insights

#### 1. Compression Ratio: 2.81x
Greek uses **2.81 times more unique words** than the English translation:
- Greek: 9,674 unique words
- English: 3,447 unique words

This reflects:
- Greek's rich inflectional morphology (case, number, gender)
- English's use of word order and helper words
- Translation choices that consolidate Greek variants

#### 2. Structural Complexity

**English has 5.8x higher transition density:**
- Greek density: 0.0004 (more sparse transitions)
- English density: 0.0023 (more interconnected word patterns)

This indicates:
- English relies more heavily on common function words
- Greek distributes meaning across more diverse vocabulary
- English word order is more flexible (more transition paths)

#### 3. Dimensionality Reduction

**Effective rank comparison:**
- Greek: 3,684 dimensions (38% of vocabulary)
- English: 1,235 dimensions (36% of vocabulary)

Both languages show similar **intrinsic dimensionality** relative to their vocabulary size, suggesting the underlying semantic structure is preserved across translation.

### Top Words by Weighted Degree

#### Greek (Top 10)
1. **καὶ** (kai - "and") - 871.38 weighted degree
2. **δὲ** (de - "but/and") - 273.56
3. **Καὶ** (Kai - capitalized "And") - 241.76
4. **ἐν** (en - "in") - 196.70
5. **εἰς** (eis - "into/to") - 188.68
6. **τοῦ** (tou - genitive article) - 188.59
7. **αὐτοῦ** (autou - "his/of him") - 175.85
8. **τὸν** (ton - accusative article) - 165.02
9. **ὁ** (ho - nominative article) - 145.49
10. **αὐτῷ** (auto - "to him") - 127.87

#### English (Top 10)
1. **and** - 552.21 weighted degree
2. **of** - 214.73
3. **the** - 129.96
4. **him** - 91.85
5. **which** - 90.83
6. **to** - 89.77
7. **in** - 82.69
8. **but** - 75.32
9. **for** - 74.67
10. **that** - 67.51

### Translation Patterns

#### Direct Correspondences
- **καὶ** (kai) → **and**: The most central word in both languages
- **ἐν** (en) → **in**: Prepositions maintain high centrality
- **ὁ/τοῦ/τὸν** (articles) → **the**: Greek articles collapse to single English article

#### Structural Transformations
1. **Article System**: Greek has 24 article forms (gender/case/number) → English has 1 ("the")
2. **Pronouns**: Greek pronouns encode case → English uses word position
3. **Conjunctions**: Greek distinguishes **καὶ** (and) vs **δὲ** (but) more strictly than English

## Technical Approach

### Matrix Representation

1. **Build Adjacency Matrices**: Convert word DAGs to matrices
   - Rows/columns = words (sorted alphabetically)
   - Cells = transition probabilities between words

2. **Singular Value Decomposition (SVD)**: Decompose both matrices
   ```
   A = U_a × S_a × V_a^T  (Greek)
   C = U_c × S_c × V_c^T  (English)
   ```

3. **Translation Matrix**: Compute transformation in reduced space
   ```
   B = U_c × S_c × V_c × V_a^(-1) × S_a^(-1) × U_a^T
   ```

### Why SVD?

- **Handles different dimensions**: Greek and English have different vocabulary sizes
- **Reduces noise**: Focuses on the most significant transformation patterns
- **Reveals structure**: Singular values show the "importance" of each transformation dimension

## Files

### Data Files
- `data/byzantine_gospels_dag.json` - System A (Greek)
- `data/kjv_gospels_dag.json` - System C (English)
- `data/translation_matrix_analysis.json` - System B analysis results

### Source Code
- `src/byzantine_text_dag.py` - Builds Greek gospel DAG
- `src/kjv_gospels_dag.py` - Builds English gospel DAG
- `src/translation_matrix_finder.py` - Discovers translation matrix B

### Tools
- `tools/matrix_gap_detection.py` - Matrix-based gap detection (from reflow)
- `tools/reflow_gap_closure.py` - Gap closure framework (from reflow)

## Usage

### Build System A (Greek Gospels)
```bash
python3 src/byzantine_text_dag.py --gospels-only -o data/byzantine_gospels_dag.json
```

### Build System C (English Gospels)
```bash
python3 src/kjv_gospels_dag.py -o data/kjv_gospels_dag.json
```

### Discover System B (Translation Matrix)
```bash
python3 src/translation_matrix_finder.py \
  --greek data/byzantine_gospels_dag.json \
  --english data/kjv_gospels_dag.json \
  --output data/translation_matrix_analysis.json
```

## Applications

### 1. Translation Studies
- Quantify translation choices and patterns
- Identify semantic shifts across languages
- Measure information preservation/loss

### 2. Computational Linguistics
- Cross-lingual word embeddings
- Translation model training data
- Language complexity metrics

### 3. Biblical Scholarship
- Compare Greek source with English translations
- Identify translation biases or choices
- Analyze semantic evolution of terms

### 4. Machine Learning
- **System B** can be used as a translation model
- Features for neural translation systems
- Cross-lingual transfer learning

## Theoretical Foundation

This approach is inspired by:

1. **Homography matrices** in computer vision (transforming image perspectives)
2. **Scientific reflow** framework (discovering unknown systems in experimental chains)
3. **Gap closure analysis** (mathematical inference of missing transformations)

Just as a homography matrix transforms one image view to another, **System B** transforms Greek word space into English word space.

## Future Work

- [ ] Compare multiple English translations (ESV, NIV, NASB)
- [ ] Analyze translation matrix for individual books
- [ ] Build neural translation model using System B as initialization
- [ ] Extend to full New Testament (beyond gospels)
- [ ] Incorporate morphological analysis for Greek
- [ ] Add semantic similarity metrics to transformation

## References

- [Byzantine Majority Text Repository](https://github.com/byztxt/byzantine-majority-text)
- [KJV Bible JSON](https://github.com/aruljohn/Bible-kjv)
- [Reflow Framework](https://github.com/sligara7/reflow)
- [Scientific Reflow](https://github.com/sligara7/reflow/tree/main/scientific-reflow)

## Citation

If you use this translation matrix analysis in your research, please cite:

```
Translation Matrix Gap Analysis for Biblical Text
Uses Byzantine Majority Text (Robinson-Pierpont) and King James Version
Framework: Scientific Reflow Gap Closure Analysis
Generated: 2025-11-15
```
