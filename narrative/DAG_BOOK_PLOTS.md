# DAG-Based Narrative Structures for Books and Novels

## Vision

Using Directed Acyclic Graphs to model, analyze, and generate compelling plot structures for novels and screenplays. Unlike word-level text analysis, this approach operates at the **structural outline level** - mapping plot points, character arcs, revelations, and narrative dependencies.

> "Every story is a journey through a graph of possibilities, where each node is a moment of change and each edge is the causality that binds them."

---

## The Core Insight

**Plots are inherently DAGs.** Events depend on prior events. Revelations require setup. Character growth demands catalysts. By modeling these dependencies explicitly, we can:

1. **Analyze** - Understand why certain plot structures feel satisfying
2. **Generate** - Create novel plot outlines with structural integrity
3. **Compare** - Find resonances between stories across genres
4. **Diagnose** - Identify structural weaknesses (dangling threads, rushed arcs)

---

## Fundamental Building Blocks

### Node Types (Plot Elements)

```
SETUP          - Establishing information (world, character, stakes)
CATALYST       - Inciting incident that starts the journey
COMPLICATION   - Obstacle or twist that raises stakes
REVELATION     - Information that changes understanding
DECISION       - Character choice that affects trajectory
CONSEQUENCE    - Result of prior actions
CONFRONTATION  - Direct conflict or challenge
RESOLUTION     - Closure of a thread
CLIFFHANGER    - Unresolved tension (chapter/act boundaries)
```

### Edge Types (Narrative Dependencies)

```
CAUSES         - A directly causes B
ENABLES        - A makes B possible (but doesn't guarantee it)
REVEALS        - A provides context that reframes B
FORESHADOWS    - A hints at future B (reader may not notice)
CONTRASTS      - A and B are thematically opposed
PARALLELS      - A and B mirror each other structurally
REQUIRES       - B cannot happen without A
```

---

## Genre-Specific DAG Structures

### 1. Mystery / Detective (The Revelation Tree)

**Signature Pattern:** Convergent structure where scattered clues funnel toward a single revelation.

```
                    [Crime Occurs]
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    [Clue A]        [Clue B]        [Clue C]
         │               │               │
    [Red Herring]   [Witness]      [Physical Evidence]
         │               │               │
    [Eliminated]    [Testimony]    [Lab Results]
         │               │               │
         └───────────────┼───────────────┘
                         │
                  [Detective Synthesis]
                         │
                  [Revelation: Killer Identity]
                         │
                  [Confrontation]
                         │
                  [Resolution]
```

**M. Night Shyamalan Structure:** Modified mystery with a late-stage "inversion node" that recontextualizes earlier events.

```
    [Setup A] ──────────────────────────────────┐
         │                                      │
    [Setup B] ─────────────────────────┐        │
         │                             │        │
    [Rising Action]                    │        │
         │                             │        │
    [Climax Approach]                  │        │
         │                             ▼        ▼
    ╔════════════════════════════════════════════════╗
    ║          TWIST REVELATION NODE                 ║
    ║   (Recontextualizes A and B retroactively)     ║
    ╚════════════════════════════════════════════════╝
         │
    [Reframed Understanding]
         │
    [New Emotional Resolution]
```

**Key Metrics:**
- **Clue Distribution Index** - How evenly clues are spread across chapters
- **Red Herring Ratio** - False leads vs. true clues
- **Revelation Depth** - How many prior nodes are recontextualized

---

### 2. Epic Fantasy (The Convergent Threads)

**Signature Pattern:** Multiple parallel storylines that gradually merge toward climax.

```
    [World Setup]
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
[Hero Arc] [Mentor] [Villain] [Side Quest]
    │         │        │        │
    │     [Training]   │        │
    │         │        │        │
    ├─────────┤        │        │
    │         │   [Villain Grows]│
[Quest Pt 1] │        │        │
    │         │        │        │
    │    [Mentor Dies]─┘        │
    │         │                 │
    │         ▼                 │
    │   [Hero Crisis]           │
    │         │        ┌────────┘
    │         │        │
    └─────────┴────────┘
              │
        [Final Battle]
              │
        [New World State]
```

**Key Metrics:**
- **Thread Count** - Number of parallel storylines
- **Convergence Rate** - How quickly threads merge
- **Thread Isolation** - Chapters before threads interact

---

### 3. Romance (The Intertwining Helix)

**Signature Pattern:** Two character arcs that repeatedly approach, diverge, and finally merge.

```
    [Meet Cute]
         │
    ┌────┴────┐
    │         │
[Char A]  [Char B]
    │         │
    ├────X────┤  ← First Conflict
    │         │
[A Growth] [B Growth]
    │         │
    └────┬────┘  ← Reconnection
         │
    ┌────┴────┐
    │         │
[A Setback] [B Setback]
    │         │
    ├────X────┤  ← Misunderstanding
    │         │
    └────┬────┘
         │
   [Grand Gesture]
         │
   [Union/Resolution]
```

**Key Metrics:**
- **Oscillation Frequency** - How often characters connect/separate
- **Growth Symmetry** - Balance between character arcs
- **Tension Gradient** - Stakes increase per separation

---

### 4. Thriller (The Escalating Cascade)

**Signature Pattern:** Each node raises stakes, creating a relentless forward momentum with ticking clock pressure.

```
    [Ordinary World]
         │
    [Inciting Threat]
         │
    ┌────┴────┐
    │         │
[Escape 1] [Clock Starts]
    │         │
    │    [Stakes Rise]
    │         │
[Caught]──────┤
    │         │
[Escape 2]    │
    │         │
    │    [Stakes Rise Again]
    │         │
    │    [Time Running Out]
    │         │
[Final Gambit]────┐
    │             │
    │        [Sacrifice]
    │             │
    └──────┬──────┘
           │
    [Resolution Under Wire]
```

**Key Metrics:**
- **Escalation Index** - Rate of stakes increase per chapter
- **Clock Pressure** - Presence of time constraints
- **Escape/Capture Ratio** - Protagonist agency measure

---

### 5. Literary Fiction (The Character Web)

**Signature Pattern:** Dense interconnections between character internal states and external events, often non-linear.

```
         [Present: Character at Crossroads]
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
[Memory A]     [Present Decision]  [Memory B]
    │                 │                 │
[Past Trauma]    [External Event] [Past Joy]
    │                 │                 │
    └─────────────────┼─────────────────┘
                      │
              [Internal Shift]
                      │
              [New Understanding]
                      │
              [Ambiguous Resolution]
```

**Key Metrics:**
- **Temporal Fragmentation** - Non-linearity measure
- **Internal/External Ratio** - Balance of thought vs. action
- **Resolution Ambiguity** - Openness of ending

---

### 6. Alternating POV / Ensemble (The Braided River)

**Signature Pattern:** Multiple protagonists with chapters alternating between viewpoints, occasional intersections.

```
Chapter: 1    2    3    4    5    6    7    8    9    10

Char A:  [A1]─────[A2]─────[A3]─────────[A4]──────[A5]
              \        \         \          \       │
               \        \         ═══════════\══════╪═══ Intersection
                \        \                    \     │
Char B:      [B1]────[B2]─────[B3]─────[B4]────────[B5]
                          \              │          │
                           \             │          │
Char C:               [C1]─────[C2]─────[C3]───────[C5]

                                    Final Convergence ──▶
```

**Key Metrics:**
- **POV Balance** - Chapter distribution across characters
- **Intersection Density** - How often storylines cross
- **Convergence Point** - When all threads meet

---

## Structural Motifs (Extending the Existing Framework)

Mapping to the Structural Rorschach motif vocabulary:

| Narrative Pattern | Structural Motif | Description |
|------------------|------------------|-------------|
| Central Protagonist | `hub_spoke` | One character connects all others |
| Sequential Quest | `chain` | Linear progression through challenges |
| Ensemble Cast | `cluster` | Tightly connected character group |
| Plot Twist | `bridge` | Single node connecting two isolated subgraphs |
| Recurring Theme | `cycle` | Pattern that returns with variation |
| Branching Choice | `fork` | Decision point leading to different paths |
| Convergent Climax | `funnel` | Multiple threads merging to one point |
| Love Triangle | `triangle` | Three-way interconnected relationship |
| Mentor/Student | `star_3` | Central figure with orbiting dependents |

---

## DAG Analysis Metrics for Narrative

### Structural Health Indicators

```python
# Proposed metrics for plot analysis

class NarrativeDAGMetrics:
    """Metrics for analyzing plot structure quality."""

    # PACING
    chapter_density: float      # Nodes per chapter (too sparse = slow, too dense = rushed)
    revelation_spacing: float   # Average chapters between major revelations

    # COHERENCE
    dangling_threads: int       # Setup nodes without resolution
    orphan_nodes: int          # Events without causal connection
    causal_depth: int          # Longest dependency chain

    # TENSION
    complication_gradient: float  # Rate of obstacle introduction
    stakes_escalation: float      # How quickly stakes increase

    # CHARACTER
    arc_completeness: float    # Percentage of character arcs resolved
    agency_ratio: float        # Character decisions vs. external events

    # GENRE FIT
    genre_signature_match: float  # Similarity to genre prototype DAG
```

### Diagnostic Queries

```
find_dangling_setups()     → Setup nodes with no ENABLES/REQUIRES edges pointing forward
find_deus_ex_machina()     → Resolution nodes with no prior CAUSES edges
find_rushed_arcs()         → Character arcs with < 3 intermediate nodes
find_sagging_middle()      → Chapters with low node density between act breaks
find_unfired_guns()        → FORESHADOWS edges that never connect to payoff
```

---

## Generation: Creating Plot Outlines

### Approach 1: Template-Based Generation

Start with genre-specific DAG templates, then populate with specific elements.

```
1. Select genre template (Mystery, Romance, Thriller, etc.)
2. Define character roster and their arc types
3. Instantiate template nodes with specific plot points
4. Add genre-specific complications
5. Verify structural integrity (no dangling threads)
6. Optimize pacing (node distribution across chapters)
```

### Approach 2: Constraint-Based Generation

Define desired metrics, generate DAGs that satisfy constraints.

```
Constraints:
- 3 POV characters with balanced chapter distribution
- Convergence by chapter 20
- At least 2 twist revelations
- Escalating stakes with 3 major complications
- All character arcs complete

Generate → Validate → Refine
```

### Approach 3: Structural Resonance

Find existing successful novels with desired "feel," extract their DAG structure, use as template for new content.

```
1. Analyze "Gone Girl" → Extract structural signature
2. Identify key patterns: dual unreliable POV, mid-point revelation, inversion
3. Generate new plot with same structural bones, different content
4. Novel maintains satisfying structure while being original
```

---

## Chapter Distribution Strategies

### Linear Distribution
```
Ch 1: [Setup] [Setup] [Catalyst]
Ch 2: [Complication] [Decision]
Ch 3: [Consequence] [Complication]
...
```

### Cliffhanger Distribution
```
Ch 1: [Setup] [Setup] [Catalyst]
Ch 2: [Complication] [Decision] [CLIFFHANGER]
Ch 3: [Resolution of 2] [Complication] [CLIFFHANGER]
...
```

### Braided Distribution (Multiple POV)
```
Ch 1 (A): [A-Setup] [A-Catalyst]
Ch 2 (B): [B-Setup] [B-Catalyst]
Ch 3 (A): [A-Complication] [A-Decision]
Ch 4 (B): [B-Complication] [Intersection with A]
...
```

---

## Connection to Structural Rorschach

This narrative DAG framework naturally extends the existing cross-domain analysis:

### Signature Extraction
```python
# Extract structural signature from a novel's plot DAG
signature = SignatureExtractor.extract(novel_dag)

# Compare to genre prototypes
mystery_similarity = compare_signatures(signature, MYSTERY_PROTOTYPE)
thriller_similarity = compare_signatures(signature, THRILLER_PROTOTYPE)
```

### Cross-Domain Resonance
```
"This novel's structure resonates with Beethoven's 5th Symphony"
- Both have: hub_spoke (central motif/character), escalating chains,
  dramatic bridge before finale, triumphant resolution pattern

"This mystery's revelation structure mirrors a fractal image"
- Both have: self-similar patterns at different scales,
  convergent funneling, information density gradients
```

### Applications
1. **Genre Classification** - Automatically identify genre from structure alone
2. **Adaptation Planning** - Match novel structure to screenplay templates
3. **Series Consistency** - Ensure multi-book series maintain structural voice
4. **Originality Analysis** - How structurally novel is this plot?

---

## Example: Analyzing a Mystery Novel

### "The Da Vinci Code" - Simplified DAG

```
[Louvre Murder]
      │
      ├──CAUSES──▶ [Langdon Summoned]
      │                  │
      │            ENABLES
      │                  ▼
      │           [First Clue: Fibonacci]
      │                  │
      ├──REVEALS──┐      │
      │           │      │
[Victim's Secret]─┼──────┤
      │           │      │
      │           │  CAUSES
      │           │      ▼
      │           └▶[Sophie Introduction]
      │                  │
      │            PARALLELS
      │                  │
[Church Conspiracy]──────┤
      │                  │
      │            COMPLICATES
      │                  ▼
      │           [Silas Pursuit]
      │                  │
      │            ┌─────┴─────┐
      │            │           │
      │      [Chase 1]    [Clue 2: Cryptex]
      │            │           │
      │            └─────┬─────┘
      │                  │
      │            ESCALATES
      │                  ▼
      │           [Bank Heist/Escape]
      │                  │
[Teabing Introduction]───┤
      │                  │
      │            REVEALS
      │                  ▼
      │           [Grail Legend Context]
      │                  │
      │            ┌─────┴─────┐
      │            │           │
      │     [Westminster]  [Betrayal Setup]
      │            │           │
      │            └─────┬─────┘
      │                  │
╔═════════════════════════════════════╗
║     TWIST: Teabing is Villain       ║
║  (Recontextualizes all his help)    ║
╚═════════════════════════════════════╝
                  │
            RESOLVES
                  ▼
           [Final Revelation: Bloodline]
                  │
            CLOSES
                  ▼
           [Emotional Resolution]
```

**Extracted Metrics:**
- Clue Distribution: 7 major clues across 105 chapters (1 per 15 chapters)
- Red Herring Ratio: 3:7 (Silas, Bishop, initial Louvre theories)
- Revelation Depth: The Teabing twist recontextualizes ~40% of prior nodes
- Chase Sequences: 4 major pursuits (escalating intensity)
- Structural Pattern: Mystery + Thriller hybrid (chase escalation + revelation tree)

---

## Gap Discovery and Resolution

Inspired by [chain_reflow](https://github.com/sligara7/chain_reflow)'s gap detection workflows, the narrative module includes powerful tools for identifying and filling structural gaps in plots.

### The Problem: Incomplete Narratives

Writers often have:
- **Compelling scenes** but not the full end-to-end plot
- **Interesting characters** but unclear how they interact
- **A chapter or two** but not the connective tissue
- **An ending in mind** but no clear path from the beginning

### Gap Detection: Finding What's Missing

Like chain_reflow's matrix-based gap detection (treating missing systems as "transformation matrices" between known states), we detect narrative gaps:

```python
from narrative import NarrativeGapDetector, get_template

# Start with a partial narrative
dag = get_template('mystery').create_skeleton()

# Detect gaps
detector = NarrativeGapDetector(dag)
gaps = detector.detect_all_gaps()

for gap in gaps:
    print(f"[{gap.gap_type.upper()}] {gap.description}")
    print(f"  Severity: {gap.severity}/5")
    print(f"  Suggested bridges: {gap.suggested_bridges}")
```

**Gap Types Detected:**
- **Causal Gaps** - Events that need intermediary steps (stakes jump too large)
- **Character Gaps** - Characters appearing without introduction or vanishing without resolution
- **Temporal Gaps** - Chapters with no plot advancement (sagging middle)
- **Thematic Gaps** - Foreshadowing that never pays off

### Character Gel Analysis: How Do They Interact?

When you have characters but don't know how they should relate:

```python
from narrative import CharacterGelAnalyzer, NarrativeDAG, PlotNode, NodeType

dag = NarrativeDAG("My Novel")
# Add character appearances...

analyzer = CharacterGelAnalyzer(dag)
gel = analyzer.analyze_pair("Alice", "Bob")

print(f"Suggested relationship: {gel.suggested_relationship}")
print(f"Thematic tension: {gel.thematic_tension}")
print(f"Suggested scenes to establish relationship:")
for scene in gel.suggested_scenes:
    print(f"  - {scene}")
```

**Relationship Types Detected:**
- `protagonist-antagonist` - Opposing goals, opposite emotional valences
- `allies` - Shared high stakes, overlapping arcs
- `rivals` - Similar goals, competitive dynamics
- `parallel-protagonists` - Different journeys, eventual convergence
- `frenemies` - Shifting allegiances, complex dynamics

### Spinoff Generation: Tangential Stories

Find natural divergence points for spinoff narratives:

```python
from narrative import SpinoffGenerator, get_template

dag = get_template('epic_fantasy').create_skeleton()
generator = SpinoffGenerator(dag)

for seed in generator.find_spinoff_seeds():
    print(f"Spinoff from: {seed.origin_node.description}")
    print(f"  Theme: {seed.spinoff_theme}")
    print(f"  Length: {seed.potential_length}")
    print(f"  Key elements: {seed.key_elements}")
```

**Natural Spinoff Points:**
- High-stakes decision nodes ("What if they chose differently?")
- Interesting secondary characters (origin stories)
- Major revelations (deeper exploration)
- Unresolved subplots (completing loose threads)

### Merging Narrative Fragments

Combine partial plots into coherent wholes, using strategy selection inspired by chain_reflow:

```python
from narrative import NarrativeMerger, NarrativeDAG

merger = NarrativeMerger()
merger.add_fragment(scene_collection_1)
merger.add_fragment(character_backstory)
merger.add_fragment(climax_sequence)

# Automatic strategy selection
strategy = merger.determine_strategy()
print(f"Using linking strategy: {strategy.name}")

# Merge with automatic bridge creation
complete_story = merger.merge("My Complete Novel")
```

**Linking Strategies (from chain_reflow):**
- `HIERARCHICAL` - Main plot → Subplots (clear parent-child)
- `PAIRWISE` - Direct connections between 2-3 threads
- `NETWORK` - Multiple peer storylines with mesh connections
- `PHASED` - Large stories: cluster first, then cross-link
- `WITH_INTERMEDIARIES` - High orthogonality requiring bridge scenes

### Gap Closure: Suggested Bridges

Automatically suggest nodes to close detected gaps:

```python
from narrative import suggest_gap_closure

for gap in detector.detect_all_gaps():
    bridge_node = suggest_gap_closure(gap)
    print(f"To close gap: {gap.description}")
    print(f"  Add: [{bridge_node.node_type.name}] {bridge_node.description}")
    print(f"  Chapter: {bridge_node.chapter}")
```

### Integration with chain_reflow Concepts

| chain_reflow Concept | Narrative Application |
|---------------------|----------------------|
| Homography matrix transformation | Finding missing plot elements between known scenes |
| SVD-based gap detection | Identifying transformational story elements |
| Strategy determination | Choosing how to merge orthogonal storylines |
| Intermediary systems | Bridge scenes connecting disparate plot threads |
| Touchpoint catalogs | Character intersection points |
| Graph orthogonality | Measuring how different two storylines are |

---

## Reflow Integration

The narrative module exports to [reflow](https://github.com/sligara7/reflow)'s `system_of_systems_graph.json` format, enabling use of all reflow analysis tools on narrative structures.

### Export to Reflow Format

```python
from narrative import get_template, export_narrative_to_reflow

# Create a narrative DAG
dag = get_template('mystery').create_skeleton('Murder at Midnight')

# Export for reflow analysis
export_narrative_to_reflow(dag, 'output/mystery_graph.json')
```

### Mapping Narrative → Systems Engineering

| Narrative Concept | Reflow Concept | Example |
|------------------|----------------|---------|
| Plot Event | System/Component | "Discover Body" → `discovery_system` |
| Chapter | Tier/Layer | Chapter 5 → `tier: 5` |
| Character | Interface | "Detective Smith" → `interfaces: ["Smith"]` |
| Subplot | Framework | "Romance subplot" → `framework_id: "romance"` |
| Causal Link | Dependency | CAUSES → `dependency` edge |

### Using Reflow Tools on Narratives

```bash
# Analyze narrative for integration gaps (plot holes)
python3 reflow/tools/analyze_integration_gaps.py output/mystery_graph.json

# Link multiple storylines
python3 reflow/tools/link_architectures.py story1.json story2.json -o combined.json

# Detect missing scenes using matrix analysis
python3 reflow/tools/matrix_gap_detection.py beginning.json ending.json
```

### Round-Trip Editing

```python
from narrative import export_narrative_to_reflow, import_narrative_from_reflow

# Export → Edit with reflow tools → Import back
export_narrative_to_reflow(dag, 'temp.json')
# ... run reflow analysis/modification tools ...
modified_dag = import_narrative_from_reflow('temp.json')
```

---

## Functional Analysis: Systems Engineering Approach

Inspired by reflow's functional analysis workflows (FA-01 through FA-07), the narrative module supports a full systems engineering approach to plot design.

### The Systems Engineering Analogy

| Systems Engineering | Narrative Writing |
|--------------------|-------------------|
| Functional Requirement | "The story must make readers care about the hero" |
| Atomic Function | "Reveal hero's vulnerability in scene 3" |
| Service/Component | Chapter (allocation unit) |
| Workflow | Character arc |
| Domain | Subplot |

### Requirements-Driven Plot Development

```python
from narrative import NarrativeFunctionalAnalyzer, NarrativeFunctionType

analyzer = NarrativeFunctionalAnalyzer()

# Step 1: Extract requirements from genre
analyzer.extract_requirements_from_genre('mystery')

# Step 2: Add premise-specific requirements
analyzer.add_requirement(
    description="Reader must be able to solve mystery before detective",
    function_type=NarrativeFunctionType.PLANT_CLUE,
    priority=1,
    success_criteria=["At least 5 fair clues planted", "No essential info withheld"]
)

# Step 3: Decompose requirements into atomic functions
for req_id in analyzer.requirements:
    analyzer.decompose_requirement(req_id)

# Step 4: Create chapters and allocate functions
for i in range(1, 25):
    analyzer.add_chapter(i)
analyzer.auto_allocate()

# Step 5: Validate coverage
coverage = analyzer.validate_coverage()
print(f"Coverage: {coverage['coverage_percentage']:.1f}%")
print(f"Uncovered requirements: {len(coverage['uncovered'])}")
```

### Atomic Functions

Following reflow's principle: "Smallest reusable unit of functionality that performs ONE specific task."

```python
# Each function has inputs, outputs, and satisfies requirements
analyzer.add_function(
    name="Reveal Victim's Secret",
    description="Detective discovers victim was blackmailing someone",
    function_type=NarrativeFunctionType.PLANT_CLUE,
    inputs=["victim_identity", "detective_investigating"],
    outputs=["blackmail_motive_established", "suspect_pool_expanded"],
    characters=["Detective", "Witness"],
    satisfies=["NR-003"]  # Links to requirement
)
```

### Chapter Allocation Strategies

Like reflow's service organization strategies:

```python
from narrative import AllocationStrategy

# Chronological: Events in time order
analyzer.auto_allocate(AllocationStrategy.CHRONOLOGICAL)

# POV-based: Group by point-of-view character
analyzer.auto_allocate(AllocationStrategy.POV_BASED)

# Subplot-based: Group by storyline
analyzer.auto_allocate(AllocationStrategy.SUBPLOT_BASED)

# Emotional arc: Group by emotional beats
analyzer.auto_allocate(AllocationStrategy.EMOTIONAL_ARC)
```

### Quick Start: From Premise to Plot

```python
from narrative import create_narrative_from_premise

# One-liner to generate a plot structure
analyzer, dag = create_narrative_from_premise(
    premise="A detective discovers her partner is the killer",
    genre="mystery",
    num_chapters=24
)

# Check what was generated
print(f"Requirements: {len(analyzer.requirements)}")
print(f"Functions: {len(analyzer.functions)}")
print(f"Chapters: {len(analyzer.chapters)}")

# Validate and export
print(analyzer.validate_coverage())
analyzer.save('my_mystery_analysis.json')
```

### Flow Analysis

Track how functions connect to form narrative flows:

```python
# Create a character arc flow
arc = analyzer.create_character_arc_flow("Detective Smith")
print(f"Arc contains {len(arc.functions)} functions")
print(f"Entry: {arc.entry_point}, Exit: {arc.exit_points}")

# Create a mystery revelation flow
analyzer.add_flow(
    name="Mystery Unraveling",
    flow_type="process",
    functions=["F-012", "F-015", "F-018", "F-023"],
    decision_points=[
        {"at": "F-015", "condition": "clue_found", "branches": ["F-016", "F-017"]}
    ]
)
```

---

## Implementation Roadmap

### Phase 1: Data Model
- Define node types and edge types as Python classes
- Create NarrativeDAG class extending NetworkX DiGraph
- Implement chapter distribution metadata

### Phase 2: Analysis Tools
- Port existing SignatureExtractor to narrative domain
- Implement genre-specific metric calculations
- Build diagnostic query system

### Phase 3: Visualization
- Chapter-based timeline view
- Character thread braiding view
- Dependency graph view

### Phase 4: Generation
- Template library for major genres
- Constraint-based generation engine
- Structural resonance matching

### Phase 5: Integration
- Connect to existing Structural Rorschach pipeline
- Enable cross-domain comparisons (novel ↔ symphony ↔ film)
- Build corpus of analyzed bestsellers for reference

---

## Philosophical Note

Stories are humanity's way of encoding causal understanding. By making plot structure explicit as DAGs, we don't reduce creativity - we illuminate the deep patterns that make narratives resonate across cultures and centuries.

The goal isn't to mechanize storytelling, but to give storytellers a new lens for understanding why certain structures satisfy, why plot holes frustrate, and how the skeleton of a story supports its flesh of prose.

> "Structure is the bones. Prose is the skin. Character is the soul. The DAG reveals the skeleton so writers can ensure it will bear the weight of their vision."

---

## References & Inspiration

- **Save the Cat!** - Blake Snyder's beat sheet as a linear DAG template
- **The Hero's Journey** - Campbell's monomyth as a circular DAG pattern
- **Story** - Robert McKee's structural principles
- **Into the Woods** - John Yorke's five-act structure analysis
- **The Seven Basic Plots** - Christopher Booker's archetypal patterns

---

## Future Extensions

1. **Interactive Plot Builder** - Visual DAG editor for writers
2. **Structural Beta Reader** - Automated plot hole detection
3. **Genre Hybridization** - Merge DAG patterns from multiple genres
4. **Adaptation Analyzer** - Compare book DAG to film DAG for same story
5. **Cultural Pattern Analysis** - How do plot structures vary by culture/era?
6. **Collaborative Worldbuilding** - Multi-author DAG merging for shared universes
