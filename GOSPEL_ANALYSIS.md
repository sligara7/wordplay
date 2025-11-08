# Gospel Analysis: Four Gospels Word Graph Comparison

## Overview

Analysis of the four gospels (Matthew, Mark, Luke, John) from the King James Version, using graph-based tokenization to identify common themes, vocabulary, and narrative patterns.

## Individual Gospel Statistics

| Gospel | Unique Words | Edges (Transitions) | Total Tokens | Vocabulary Richness |
|--------|--------------|---------------------|--------------|---------------------|
| **Matthew** | 1,988 | 8,257 | 10,629 | Most comprehensive |
| **Luke** | 2,258 | 9,175 | 11,038 | **Richest vocabulary** |
| **Mark** | 1,552 | 5,389 | 6,406 | Shortest, most direct |
| **John** | 1,271 | 6,050 | 8,146 | **Most concise** |

### Key Observations:

- **Luke** has the richest vocabulary (2,258 unique words) - aligns with scholarly consensus that Luke was writing for a Greek audience
- **John** has the most concise vocabulary (1,271 words) but still 8,146 tokens - heavy repetition of key theological terms
- **Mark** is the shortest gospel (6,406 tokens) - consistent with tradition as the earliest, most action-focused gospel
- Average graph density: 0.0025 (very sparse) - indicates rich, varied language with minimal repetition

## Common Elements Across All 4 Gospels

### Core Shared Vocabulary: 623 Words

Words appearing in ALL four gospels represent the **essential gospel narrative**:

**Sample of common words:**
- Theological: world, kingdom, eternal, life, death, glory, spirit, truth, father, son
- Actions: departed, seeking, healed, troubled, maketh, committeth
- Descriptive: known, called, lying, loud, darkness, wilderness, desert
- Relational: before, against, every, certain

### Common Narrative Transitions: 256 Patterns

**Most significant transitions** (appear in all 4 gospels):

1. **eternal → life** (central theological theme)
2. **christ → son** (christological identity)
3. **put → death** (passion narrative)
4. **jesus → cried** / **jesus → took** (narrative actions)
5. **chief → priests** (antagonists)
6. **certain → man** (parable/story pattern)
7. **life → shall** (promises about eternal life)
8. **unto → drink** / **unto → thy** (direct discourse patterns)
9. **bringeth → forth** (agricultural/spiritual metaphors)
10. **shall → find** / **shall → man** (prophetic statements)

## Themes Emerging from Common Patterns

### 1. **Eternal Life Theme**
- Transition: "eternal → life" appears in all 4 gospels
- Central promise and theological focus
- John particularly emphasizes this (most concise vocabulary but repeats key terms)

### 2. **Christ's Identity**
- Transition: "christ → son"
- All four gospels establish Jesus as the Christ/Son
- Consistent across synoptics (Matthew, Mark, Luke) and John

### 3. **Passion Narrative**
- Transition: "put → death"
- All four gospels culminate in crucifixion
- "chief → priests" as consistent antagonists

### 4. **Healing Ministry**
- Word: "healed" in all 4
- Transition patterns around healing narratives
- Signs of kingdom power

### 5. **Kingdom/Wilderness Motifs**
- Words: "kingdom", "wilderness", "desert"
- John the Baptist connection
- Temptation narratives
- Eschatological themes

### 6. **Light/Darkness Dualism**
- Word: "darkness" common to all
- Particularly prominent in John's prologue
- Theological/cosmological framework

### 7. **Direct Discourse Patterns**
- "unto → thy", "wilt → thou", "why → ye"
- Teaching style: direct address
- Parable introduction: "certain → man"

## Unique Characteristics by Gospel

### Matthew (1,988 words, 8,257 transitions)
- Most comprehensive vocabulary
- Likely includes genealogies, Sermon on the Mount
- Teaching-focused content

### Mark (1,552 words, 5,389 transitions)
- Shortest, most action-oriented
- Direct narrative style
- Fewer unique words but still complete gospel

### Luke (2,258 words, 9,175 transitions)
- **Richest vocabulary** - educated Greek audience
- Includes unique parables (Good Samaritan, Prodigal Son)
- Most literary gospel
- Detailed birth narrative

### John (1,271 words, 6,050 transitions)
- **Most concise vocabulary**
- High repetition of theological terms
- Different structure: "I AM" statements
- Prologue about "the Word"
- More abstract/theological vs. narrative

## Translation Implications (For Future Analysis)

Your excellent idea about comparing translations:

**Proposed comparisons:**
1. **English translations:**
   - KJV (analyzed here) - 1611, formal/archaic
   - NIV - modern, dynamic equivalence
   - ESV - modern, formal equivalence
   - Expected: Similar graph structure, different vocabulary density

2. **Original Greek (Koine):**
   - Would show:
     - Word order differences (Greek more flexible)
     - Case endings (not present in English)
     - Particle usage (untranslatable nuances)
   - Tokenization challenge: Greek uses different word boundaries
   - Would need Greek-aware stopword removal

3. **Other ancient languages:**
   - Latin Vulgate (Jerome's translation)
   - Aramaic (Peshitta) - closer to Jesus' spoken language
   - Coptic, Syriac versions

**Research question:** Do different translations preserve the same graph **structure** even if vocabulary changes?

## Key Findings

1. **High agreement on core vocabulary** (623/~2000 words = ~31% overlap)
   - Indicates strong consistency in gospel narratives
   - Core theological vocabulary shared

2. **Consistent narrative transitions** (256 common patterns)
   - Gospel writers follow similar story arcs
   - Common teaching/discourse style

3. **Vocabulary richness varies significantly**
   - Luke: 2,258 words (Greek literary style)
   - John: 1,271 words (focused theological repetition)
   - Ratio: 1.78:1 (Luke 78% more vocab than John)

4. **Sparse graph density** (0.0025 average)
   - Rich, varied language
   - Minimal repetitive patterns
   - Indicates literary sophistication

5. **Core theological themes evident in transitions:**
   - Eternal life
   - Christ's identity
   - Death and resurrection
   - Healing and kingdom
   - Light vs. darkness

## Comparative Historical Context (Future Analysis)

Your proposed expansion to contemporary sources:

**Jewish sources of the period:**
- Josephus (37-100 CE) - Jewish Antiquities, Jewish War
- Dead Sea Scrolls (Qumran, ~150 BCE - 70 CE)
- Mishnah (compiled ~200 CE, oral traditions from Jesus' time)

**Roman sources mentioning Christ/Christians:**
- Tacitus, Annals 15.44 (~116 CE) - mentions Christ, Pontius Pilate
- Suetonius, Lives of Caesars (~121 CE) - mentions "Chrestus"
- Pliny the Younger, Letters 10.96 (~112 CE) - asks Trajan about Christians

**Expected findings from cross-corpus analysis:**
- Gospel vocabulary vs. Josephus: Overlapping historical/geographical terms, different theological vocabulary
- Gospels vs. Dead Sea Scrolls: Shared apocalyptic themes, sectarian differences
- Gospels vs. Roman sources: Minimal vocabulary overlap, different perspectives on same events

## Technical Notes

- All graphs generated with stopwords removed
- Analysis using Wordplay batch graph merger
- Transition probabilities normalized per gospel
- Graph format: system_of_systems_graph.json (compatible with reflow)

## Next Steps

1. ✅ Complete 4 gospels analysis
2. ⏳ Compare different English translations (KJV vs. NIV vs. ESV)
3. ⏳ Analyze Greek New Testament (Koine Greek tokenization)
4. ⏳ Compare with contemporary historical sources (Josephus, Tacitus, etc.)
5. ⏳ Expand to full New Testament corpus
6. ⏳ Cross-reference with Dead Sea Scrolls, Mishnah

---

**Files Generated:**
- `books/gospels/matthew.txt` - Matthew gospel text
- `books/gospels/mark.txt` - Mark gospel text
- `books/gospels/luke.txt` - Luke gospel text
- `books/gospels/john.txt` - John gospel text
- `output/gospels/matthew_graph.json` - Matthew word graph
- `output/gospels/mark_graph.json` - Mark word graph
- `output/gospels/luke_graph.json` - Luke word graph
- `output/gospels/john_graph.json` - John word graph
- `output/gospels/four_gospels_common.json` - Representative graph (common elements)

**Analysis Date:** 2025-11-08
**Translation:** King James Version (KJV)
**Methodology:** Graph-based tokenization with stopword removal
