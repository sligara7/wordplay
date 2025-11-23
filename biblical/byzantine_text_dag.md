# Byzantine Majority Text Word-Based DAG

This tool creates a word-based Directed Acyclic Graph (DAG) from the Koine Greek Byzantine Majority Text (Robinson-Pierpont edition).

## Overview

The `byzantine_text_dag.py` script downloads, parses, and analyzes the Greek New Testament text from the [byztxt/byzantine-majority-text](https://github.com/byztxt/byzantine-majority-text) repository, building a directed graph where:

- **Nodes**: Individual Greek words (tokens) with diacritical marks preserved
- **Edges**: Word-to-word transitions (word A followed by word B)
- **Edge weights**: Transition probabilities (normalized from occurrence counts)

## Features

- **Automatic downloading**: Fetches CSV files from the Byzantine text repository
- **Caching**: Downloads are cached locally to avoid repeated fetches
- **Text cleaning**: Removes textual apparatus notation (`{NA ...}`, `{WH ...}`, etc.)
- **Greek tokenization**: Preserves accents, breathing marks, and other diacritics
- **Flexible selection**: Process specific books, all NT, just Gospels, or just Epistles
- **Statistics**: Per-book word counts and unique word statistics
- **Graph analysis**: Identifies dead ends and unreachable words

## Installation

No additional dependencies required beyond Python 3 standard library.

## Usage

### Build DAG from entire New Testament

```bash
python3 src/byzantine_text_dag.py -o data/byzantine_nt_dag.json
```

### Build DAG from the four Gospels only

```bash
python3 src/byzantine_text_dag.py --gospels-only -o data/byzantine_gospels_dag.json
```

### Build DAG from Epistles only

```bash
python3 src/byzantine_text_dag.py --epistles-only -o data/byzantine_epistles_dag.json
```

### Build DAG from specific books

```bash
python3 src/byzantine_text_dag.py -b MAT MAR LUK -o data/synoptic_gospels_dag.json
```

### Command-line Options

```
-o, --output PATH       Output JSON file path (default: data/byzantine_text_dag.json)
-b, --books BOOK...     Specific books to process (e.g., MAT JOH ROM)
--cache-dir DIR         Directory to cache CSV files (default: data/byzantine)
--gospels-only          Process only the four Gospels (MAT, MAR, LUK, JOH)
--epistles-only         Process only the Epistles
```

### Available Book Abbreviations

**Gospels**: MAT, MAR, LUK, JOH
**Acts**: ACT
**Paul's Letters**: ROM, 1CO, 2CO, GAL, EPH, PHP, COL, 1TH, 2TH, 1TI, 2TI, TIT, PHM
**General Epistles**: HEB, JAM, 1PE, 2PE, 1JO, 2JO, 3JO, JUD
**Apocalypse**: REV

## Output Format

The tool generates a JSON file in the system_of_systems_graph.json format with:

### Metadata
```json
{
  "metadata": {
    "generated": "2025-11-15T04:28:11.468423",
    "framework": "Byzantine Text Flow",
    "framework_id": "byzantine_greek_flow",
    "source": "Robinson-Pierpont Byzantine Majority Text",
    "source_repository": "https://github.com/byztxt/byzantine-majority-text",
    "books_included": ["MAT", "MAR", ...],
    "num_nodes": 19753,
    "num_edges": 80906,
    "total_tokens": 142226,
    "unique_words": 19753,
    "book_stats": {
      "MAT": {"word_count": 18849, "unique_words": 4506},
      ...
    }
  }
}
```

### Graph Structure
```json
{
  "graph": {
    "nodes": [
      {
        "id": "greek_Ἰησοῦ",
        "name": "Ἰησοῦ",
        "type": "greek_word",
        "raw": {
          "word": "Ἰησοῦ",
          "frequency": 347,
          "outgoing_transitions": 50
        }
      }
    ],
    "links": [
      {
        "source": "greek_Ἰησοῦ",
        "target": "greek_χριστοῦ",
        "type": "word_transition",
        "weight": 0.406,
        "raw": {
          "transition_count": 141,
          "transition_probability": 0.406
        }
      }
    ]
  }
}
```

## Statistics (Full NT)

When processing the complete New Testament:

- **Total words**: 142,226
- **Unique words**: 19,753
- **Total transitions**: 80,906
- **Books processed**: 27

### Per-Book Statistics

| Book | Words | Unique Words |
|------|-------|--------------|
| Matthew | 18,849 | 4,506 |
| Mark | 11,743 | 3,265 |
| Luke | 20,013 | 5,214 |
| John | 16,008 | 3,064 |
| Acts | 18,927 | 5,134 |
| Romans | 7,240 | 2,208 |
| 1 Corinthians | 6,939 | 2,191 |
| ... | ... | ... |

## Technical Details

### Text Cleaning

The script removes:
- Textual apparatus notation: `{NA ...}`, `{WH ...}`, `{TR ...}`
- Paragraph markers: `¶`
- Non-Greek characters (punctuation, etc.)

### Greek Tokenization

The tokenizer:
- Preserves Unicode Greek letters (U+0370-U+03FF)
- Preserves Greek Extended characters (U+1F00-U+1FFF) for diacritics
- Maintains accents, breathing marks, and iota subscripts
- Splits on whitespace after cleaning

### Graph Properties

- **Directed**: Yes (word A → word B indicates sequential occurrence)
- **Weighted**: Yes (edge weights = transition probabilities)
- **Multigraph**: No (single edge per word pair with aggregated count)

## Use Cases

1. **Linguistic analysis**: Study Koine Greek word patterns and collocations
2. **Textual criticism**: Analyze word usage across different books
3. **Statistical modeling**: Build language models of NT Greek
4. **Visualization**: Create network graphs of Greek vocabulary
5. **Computational theology**: Analyze semantic relationships in original text

## Source Data

This tool uses the **Robinson-Pierpont Byzantine Majority Text** in Unicode CSV format with textual variants included. The source repository is maintained at:

https://github.com/byztxt/byzantine-majority-text

## License

The Byzantine Majority Text data is provided by the byztxt repository. Please refer to their repository for licensing information regarding the Greek text.

This tool (byzantine_text_dag.py) is part of the wordplay project.
