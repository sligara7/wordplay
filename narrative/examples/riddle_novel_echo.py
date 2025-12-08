"""
Example Riddle-Novel: "ECHO"

A psychological thriller where the entire plot functions as a riddle.
The reader should be able to solve the mystery before the reveal,
but only if they pay close attention to what's hidden in plain sight.

THE RIDDLE: Who is the killer?
THE FRAME: Detective Sarah Chen investigates a serial killer who leaves
           cryptic messages predicting each victim.
THE ANSWER: Sarah herself has DID (Dissociative Identity Disorder).
            Her alter "Echo" is the killer. She's been hunting herself.

This example demonstrates:
- How to plant the answer early (Sarah's "blackouts", her intimate knowledge)
- How to create compelling decoys (the obvious suspects)
- How to build the paradox (evidence that can't fit the frame)
- How to execute the perspective shift (the reframe cascade)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from narrative import (
    NarrativeDAG,
    PlotNode,
    NodeType,
    EdgeType,
    NarrativeAnalyzer,
    get_template,
)


def create_echo_riddle_novel() -> NarrativeDAG:
    """
    Create the complete DAG for 'ECHO' - a riddle-novel thriller.

    Structure follows the riddle-novel template:
    - Act 1: The Frame (establish false reality)
    - Act 2A: Deepening (plant answers, build decoys)
    - Act 2B: The Paradox (things stop making sense)
    - Act 3: The Shift (everything recontextualizes)
    """
    dag = NarrativeDAG(
        title="ECHO",
        genre="riddle_novel",
        target_chapters=24,
    )

    # ==========================================================
    # ACT 1: THE FRAME (Chapters 1-6)
    # Establish Sarah as competent detective hunting a serial killer
    # ==========================================================

    # Chapter 1: Opening - The Question Is Posed
    dag.add_node(PlotNode(
        id="opening_crime_scene",
        node_type=NodeType.SETUP,
        description="""
        Detective Sarah Chen arrives at crime scene. Victim has message carved:
        'ECHO KNOWS'. Sarah feels strange familiarity with the scene.

        HIDDEN ANSWER #1: Sarah touches evidence without gloves instinctively,
        as if she's been here before. She catches herself, plays it off as fatigue.
        """,
        chapter=1,
        character="Sarah Chen",
        stakes_level=5,
        emotional_valence=-0.4,
    ))

    dag.add_node(PlotNode(
        id="sarah_background",
        node_type=NodeType.SETUP,
        description="""
        Sarah's background established: brilliant but troubled. History of 'blackouts'
        she attributes to overwork. Lives alone. Colleagues respect but don't know her.

        HIDDEN ANSWER #2: Her apartment has a locked room she 'never uses'.
        Mentioned casually, never explored in Act 1.
        """,
        chapter=1,
        character="Sarah Chen",
        stakes_level=3,
    ))

    # Chapter 2: The Investigation Begins
    dag.add_node(PlotNode(
        id="evidence_analysis",
        node_type=NodeType.SETUP,
        description="""
        Evidence points to someone with intimate knowledge of police procedures.
        Sarah recognizes patterns in the killer's methodology - 'someone trained'.

        HIDDEN ANSWER #3: Sarah's insights are TOO good. She explains them as
        'intuition' but she's actually accessing Echo's memories.
        """,
        chapter=2,
        character="Sarah Chen",
        stakes_level=4,
    ))

    dag.add_node(PlotNode(
        id="introduce_suspects",
        node_type=NodeType.SETUP,
        description="""
        Three suspects introduced:
        1. Marcus Webb - ex-cop, fired for brutality, fits profile
        2. Dr. Helena Vance - psychiatrist, had access to victims
        3. James Chen - Sarah's estranged brother, history of violence

        DECOY SETUP: Each has compelling motive and opportunity.
        """,
        chapter=2,
        character="Ensemble",
        stakes_level=4,
    ))

    # Chapter 3: First Decoy Thread
    dag.add_node(PlotNode(
        id="marcus_confrontation",
        node_type=NodeType.COMPLICATION,
        description="""
        Sarah confronts Marcus Webb. He's evasive, hostile, fits profile perfectly.
        Has alibi for one murder - but alibis can be faked.

        DECOY STRENGTHENING: Marcus warns Sarah she's 'looking in wrong places'.
        Reader interprets this as threat; it's actually compassion.
        """,
        chapter=3,
        character="Marcus Webb",
        stakes_level=5,
    ))

    # Chapter 4: Sarah's First Blackout (on page)
    dag.add_node(PlotNode(
        id="first_blackout",
        node_type=NodeType.COMPLICATION,
        description="""
        Sarah has blackout while reviewing case files. Wakes hours later.
        Case files are reorganized - in her handwriting, but she doesn't remember.

        PARADOX SEED: The new organization reveals connections only the killer
        could know. Sarah dismisses it as her 'subconscious working'.
        """,
        chapter=4,
        character="Sarah Chen",
        stakes_level=6,
        emotional_valence=-0.6,
    ))

    # Chapter 5: Second Murder
    dag.add_node(PlotNode(
        id="second_murder",
        node_type=NodeType.CATALYST,
        description="""
        Second victim found. Message: 'ECHO REMEMBERS'.
        Sarah has no alibi - was blacked out. Doesn't realize significance.

        HIDDEN ANSWER #4: The victim is someone Sarah interviewed yesterday.
        Someone who 'saw something' in Sarah's eyes that scared them.
        """,
        chapter=5,
        character="Sarah Chen",
        stakes_level=7,
        emotional_valence=-0.7,
    ))

    # Chapter 6: The Frame Solidifies
    dag.add_node(PlotNode(
        id="frame_complete",
        node_type=NodeType.DECISION,
        description="""
        Sarah is fully committed to hunting the killer. Gets pressure from above
        to solve case. She PROMISES she'll find Echo.

        IRONY: The promise is to herself. She will keep it.
        """,
        chapter=6,
        character="Sarah Chen",
        stakes_level=7,
    ))

    # ==========================================================
    # ACT 2A: THE DEEPENING (Chapters 7-12)
    # Plant more answers, strengthen decoys, build reader investment
    # ==========================================================

    # Chapter 7: Dr. Vance Sessions
    dag.add_node(PlotNode(
        id="therapy_sessions",
        node_type=NodeType.REVELATION,
        description="""
        Sarah sees Dr. Vance (suspect #2) for mandated therapy. Vance notices
        'gaps' in Sarah's narrative. Suggests she explore her blackouts.

        HIDDEN ANSWER #5: Vance's notes (shown briefly) include:
        'Possible dissociative disorder. Fragmented identity. Dangerous?'
        """,
        chapter=7,
        character="Dr. Helena Vance",
        stakes_level=5,
    ))

    # Chapter 8: James Chen Returns
    dag.add_node(PlotNode(
        id="brother_reunion",
        node_type=NodeType.COMPLICATION,
        description="""
        Sarah's brother James appears. He's been watching her, concerned.
        They haven't spoken in years. He knows something about their childhood
        that Sarah has 'forgotten'.

        DECOY: James looks guilty, acts suspicious. Reader suspects him.
        TRUTH: He's trying to protect her from herself.
        """,
        chapter=8,
        character="James Chen",
        stakes_level=6,
        emotional_valence=-0.3,
    ))

    # Chapter 9: Third Murder - Escalation
    dag.add_node(PlotNode(
        id="third_murder",
        node_type=NodeType.CATALYST,
        description="""
        Third victim. Message: 'ECHO IS CLOSER'. This victim was investigating Sarah.
        Internal affairs had received anonymous tip about her behavior.

        HIDDEN ANSWER #6: The 'anonymous tip' was from Echo - Sarah's alter
        was trying to get caught, trying to stop herself.
        """,
        chapter=9,
        character="Sarah Chen",
        stakes_level=8,
        emotional_valence=-0.8,
        is_twist=True,
    ))

    # Chapter 10: Evidence Points to Marcus
    dag.add_node(PlotNode(
        id="false_climax_setup",
        node_type=NodeType.REVELATION,
        description="""
        Definitive evidence links Marcus Webb to murders. His DNA, his fingerprints.
        Sarah arrests him. Case appears solved.

        FALSE ANSWER: The reader who stopped here would be satisfied.
        But something feels off to careful readers...
        """,
        chapter=10,
        character="Marcus Webb",
        stakes_level=7,
    ))

    # Chapter 11: Celebration and Doubt
    dag.add_node(PlotNode(
        id="false_resolution",
        node_type=NodeType.RESOLUTION,
        description="""
        Marcus is in custody. Department celebrates. Sarah should feel relieved.
        Instead, her blackouts intensify. She finds herself at crime scenes
        at night, not remembering how she got there.

        PARADOX EMERGING: If Marcus is guilty, why is Sarah still blacking out?
        """,
        chapter=11,
        character="Sarah Chen",
        stakes_level=6,
        emotional_valence=0.2,
    ))

    # Chapter 12: Fourth Murder - Impossible
    dag.add_node(PlotNode(
        id="paradox_murder",
        node_type=NodeType.CATALYST,
        description="""
        Fourth victim found while Marcus is in custody. Message: 'ECHO WAS NEVER HIM'.
        This is impossible in the current frame. Either Marcus has an accomplice,
        or... he was never the killer.

        THE FRAME CRACKS: Everything the reader believed is now in question.
        """,
        chapter=12,
        character="Sarah Chen",
        stakes_level=9,
        emotional_valence=-0.9,
        is_twist=True,
    ))

    # ==========================================================
    # ACT 2B: THE PARADOX (Chapters 13-18)
    # The false frame breaks down, Sarah (and reader) must find new frame
    # ==========================================================

    # Chapter 13: Re-investigation
    dag.add_node(PlotNode(
        id="reinvestigation",
        node_type=NodeType.DECISION,
        description="""
        Sarah reopens investigation. Reviews all evidence with fresh eyes.
        Notices anomalies she dismissed before: her own fingerprints at scenes,
        her handwriting on the reorganized files.

        DENIAL: She finds explanations for each one. The reader sees through them.
        """,
        chapter=13,
        character="Sarah Chen",
        stakes_level=8,
    ))

    # Chapter 14: The Locked Room
    dag.add_node(PlotNode(
        id="locked_room_discovery",
        node_type=NodeType.REVELATION,
        description="""
        Sarah finally opens her locked room. Inside: a shrine. Photos of victims
        BEFORE they were killed. Detailed plans. A journal in two handwritings.

        HIDDEN ANSWER REVEALED: The second handwriting is hers.
        Sarah doesn't recognize it. Echo does.
        """,
        chapter=14,
        character="Sarah Chen",
        stakes_level=9,
        emotional_valence=-0.95,
        is_twist=True,
    ))

    # Chapter 15: The Journal
    dag.add_node(PlotNode(
        id="echo_journal",
        node_type=NodeType.FLASHBACK,
        description="""
        The journal reveals Echo's perspective. Born from childhood trauma
        (James knows about this). Echo protected Sarah by 'handling' threats.
        Over time, Echo's definition of 'threat' expanded.

        RECONTEXTUALIZATION BEGINS: Every scene gains new meaning.
        """,
        chapter=15,
        character="Echo/Sarah",
        stakes_level=8,
        emotional_valence=-0.7,
    ))

    # Chapter 16: James Explains
    dag.add_node(PlotNode(
        id="james_revelation",
        node_type=NodeType.REVELATION,
        description="""
        James confronts Sarah with the truth he's always known. Their father
        was abusive. Sarah 'disappeared' during episodes. Echo took over.
        James watched it happen. That's why he left - he was afraid of Echo.

        NOW JAMES HAS RETURNED: Because the killings match Echo's old pattern.
        """,
        chapter=16,
        character="James Chen",
        stakes_level=9,
    ))

    # Chapter 17: Dr. Vance's Betrayal/Help
    dag.add_node(PlotNode(
        id="vance_truth",
        node_type=NodeType.REVELATION,
        description="""
        Dr. Vance admits she suspected from session one. She's been documenting
        Sarah's disorder, trying to help. The 'suspicion' around her was misdirection.

        She explains DID, integration, treatment. There's hope - if Sarah accepts it.

        DECOY RESOLVED: Vance was helper, not villain.
        """,
        chapter=17,
        character="Dr. Helena Vance",
        stakes_level=8,
    ))

    # Chapter 18: Confronting Echo
    dag.add_node(PlotNode(
        id="internal_confrontation",
        node_type=NodeType.CONFRONTATION,
        description="""
        Sarah must confront Echo internally. Through therapy, she accesses
        Echo's perspective. Understands why Echo kills: protection, twisted love.
        Echo believes the victims were threats to Sarah.

        THE PARADOX RESOLVED: Sarah is both hunter and hunted, hero and villain.
        """,
        chapter=18,
        character="Sarah Chen / Echo",
        stakes_level=10,
        emotional_valence=-0.5,
    ))

    # ==========================================================
    # ACT 3: THE SHIFT (Chapters 19-24)
    # The perspective shift and new understanding
    # ==========================================================

    # Chapter 19: The Choice
    dag.add_node(PlotNode(
        id="the_choice",
        node_type=NodeType.DECISION,
        description="""
        Sarah faces impossible choice: turn herself in and destroy her life,
        or try to control Echo and risk more deaths. Neither option is clean.

        PERSPECTIVE SHIFT COMPLETE: The 'who did it' question transforms into
        'what will Sarah do now that she knows?'
        """,
        chapter=19,
        character="Sarah Chen",
        stakes_level=10,
        emotional_valence=-0.4,
    ))

    # Chapter 20: Final Message
    dag.add_node(PlotNode(
        id="final_message",
        node_type=NodeType.REVELATION,
        description="""
        Sarah finds one more message, hidden in her own apartment. Written by Echo,
        to Sarah: 'I DID IT FOR YOU. I'M SORRY. MAKE IT STOP.'

        Echo was never a monster - just a broken protector. She wants to stop too.
        """,
        chapter=20,
        character="Echo",
        stakes_level=9,
        emotional_valence=-0.6,
    ))

    # Chapter 21: Reframe Cascade
    dag.add_node(PlotNode(
        id="reframe_cascade",
        node_type=NodeType.REVELATION,
        description="""
        Montage chapter showing key scenes from earlier, now with full context:
        - Opening: Sarah's familiarity = she was there as Echo
        - Her 'intuition' = Echo's memories bleeding through
        - Marcus's warning = he knew Sarah, was trying to help
        - The anonymous tip = Echo crying for help

        Every piece clicks into place. The answer was always there.
        """,
        chapter=21,
        character="Sarah Chen",
        stakes_level=8,
        is_twist=True,
    ))

    # Chapter 22: Integration
    dag.add_node(PlotNode(
        id="integration_attempt",
        node_type=NodeType.CONFRONTATION,
        description="""
        Sarah begins integration therapy. Not to destroy Echo, but to merge.
        To become whole. It's painful, terrifying, but necessary.

        The real confrontation was never with a killer outside - it was within.
        """,
        chapter=22,
        character="Sarah Chen",
        stakes_level=9,
        emotional_valence=0.1,
    ))

    # Chapter 23: Resolution
    dag.add_node(PlotNode(
        id="resolution",
        node_type=NodeType.RESOLUTION,
        description="""
        Sarah confesses. Not to murder - she's not legally responsible - but to
        the families. She explains, apologizes, accepts their hatred.

        Marcus is released. James stays. Dr. Vance continues treatment.
        """,
        chapter=23,
        character="Sarah Chen",
        stakes_level=8,
        emotional_valence=0.3,
    ))

    # Chapter 24: Retrospective Clarity
    dag.add_node(PlotNode(
        id="epilogue",
        node_type=NodeType.RESOLUTION,
        description="""
        One year later. Sarah works in victim advocacy. Echo is integrated -
        not gone, but no longer separate. Sarah is whole for the first time.

        Final line: Sarah looks in mirror and says 'We're okay now.'

        RETROSPECTIVE CLARITY: On re-read, every clue is visible. The riddle
        was fair. The answer was always 'Echo is the detective'.
        """,
        chapter=24,
        character="Sarah Chen",
        stakes_level=5,
        emotional_valence=0.7,
    ))

    # ==========================================================
    # EDGES: The connections that make the riddle work
    # ==========================================================

    # Frame establishment
    dag.add_edge("opening_crime_scene", "sarah_background", EdgeType.ENABLES)
    dag.add_edge("sarah_background", "evidence_analysis", EdgeType.ENABLES)
    dag.add_edge("evidence_analysis", "introduce_suspects", EdgeType.CAUSES)

    # Decoy threads
    dag.add_edge("introduce_suspects", "marcus_confrontation", EdgeType.CAUSES)
    dag.add_edge("marcus_confrontation", "false_climax_setup", EdgeType.FORESHADOWS)
    dag.add_edge("introduce_suspects", "therapy_sessions", EdgeType.ENABLES)
    dag.add_edge("introduce_suspects", "brother_reunion", EdgeType.ENABLES)

    # Hidden answer thread (subtle connections)
    dag.add_edge("opening_crime_scene", "first_blackout", EdgeType.FORESHADOWS)
    dag.add_edge("first_blackout", "second_murder", EdgeType.FORESHADOWS)
    dag.add_edge("second_murder", "third_murder", EdgeType.CAUSES)
    dag.add_edge("first_blackout", "locked_room_discovery", EdgeType.FORESHADOWS)

    # Investigation flow
    dag.add_edge("second_murder", "frame_complete", EdgeType.CAUSES)
    dag.add_edge("frame_complete", "therapy_sessions", EdgeType.ENABLES)
    dag.add_edge("therapy_sessions", "vance_truth", EdgeType.FORESHADOWS)
    dag.add_edge("brother_reunion", "james_revelation", EdgeType.FORESHADOWS)

    # False climax
    dag.add_edge("third_murder", "false_climax_setup", EdgeType.CAUSES)
    dag.add_edge("false_climax_setup", "false_resolution", EdgeType.CAUSES)

    # Paradox emergence
    dag.add_edge("false_resolution", "paradox_murder", EdgeType.CONTRASTS)
    dag.add_edge("paradox_murder", "reinvestigation", EdgeType.CAUSES)

    # Revelation cascade
    dag.add_edge("reinvestigation", "locked_room_discovery", EdgeType.CAUSES)
    dag.add_edge("locked_room_discovery", "echo_journal", EdgeType.REVEALS)
    dag.add_edge("echo_journal", "james_revelation", EdgeType.ENABLES)
    dag.add_edge("james_revelation", "vance_truth", EdgeType.ENABLES)
    dag.add_edge("vance_truth", "internal_confrontation", EdgeType.ENABLES)

    # The shift
    dag.add_edge("internal_confrontation", "the_choice", EdgeType.CAUSES)
    dag.add_edge("the_choice", "final_message", EdgeType.REVEALS)
    dag.add_edge("final_message", "reframe_cascade", EdgeType.CAUSES)

    # Reframe connects back to all planted answers
    dag.add_edge("reframe_cascade", "opening_crime_scene", EdgeType.REVEALS)
    dag.add_edge("reframe_cascade", "first_blackout", EdgeType.REVEALS)
    dag.add_edge("reframe_cascade", "evidence_analysis", EdgeType.REVEALS)

    # Resolution
    dag.add_edge("reframe_cascade", "integration_attempt", EdgeType.ENABLES)
    dag.add_edge("integration_attempt", "resolution", EdgeType.CAUSES)
    dag.add_edge("resolution", "epilogue", EdgeType.CAUSES)

    return dag


def analyze_echo_riddle() -> None:
    """Analyze the riddle-novel structure."""
    dag = create_echo_riddle_novel()
    analyzer = NarrativeAnalyzer(dag)
    diagnosis = analyzer.diagnose()

    print("=" * 70)
    print("RIDDLE-NOVEL ANALYSIS: 'ECHO'")
    print("=" * 70)

    print(f"\nTitle: {dag.title}")
    print(f"Genre: {dag.genre}")
    print(f"Chapters: {dag.target_chapters}")
    print(f"Total Nodes: {len(dag.nodes)}")
    print(f"Total Edges: {len(dag.edges)}")

    # Show riddle-specific metrics
    print("\n" + "-" * 40)
    print("RIDDLE STRUCTURE ANALYSIS")
    print("-" * 40)

    # Count hidden answers (nodes with "HIDDEN ANSWER" in description)
    hidden_answers = [n for n in dag.nodes.values()
                     if "HIDDEN ANSWER" in n.description]
    print(f"\nHidden Answers Planted: {len(hidden_answers)}")
    for i, node in enumerate(hidden_answers, 1):
        print(f"  {i}. Chapter {node.chapter}: {node.id}")

    # Count decoys
    decoys = [n for n in dag.nodes.values()
              if "DECOY" in n.description]
    print(f"\nDecoy Elements: {len(decoys)}")

    # Identify twist nodes
    twists = [n for n in dag.nodes.values() if n.is_twist]
    print(f"\nTwist/Revelation Points: {len(twists)}")
    for node in twists:
        print(f"  - Chapter {node.chapter}: {node.id}")

    # Check fair play: all hidden answers before major revelation
    major_reveal = dag.nodes.get("locked_room_discovery")
    if major_reveal:
        early_answers = [n for n in hidden_answers if n.chapter < major_reveal.chapter]
        print(f"\nFair Play Check: {len(early_answers)}/{len(hidden_answers)} answers planted before reveal")

    print("\n" + "-" * 40)
    print("STRUCTURAL DIAGNOSIS")
    print("-" * 40)

    if diagnosis.issues:
        print("\nIssues Found:")
        for issue in diagnosis.issues:
            print(f"  ! {issue}")
    else:
        print("\nNo structural issues detected.")

    if diagnosis.suggestions:
        print("\nSuggestions:")
        for suggestion in diagnosis.suggestions:
            print(f"  → {suggestion}")

    print("\n" + "-" * 40)
    print("CHAPTER-BY-CHAPTER BREAKDOWN")
    print("-" * 40)

    # Group nodes by chapter
    chapters: dict[int, list[PlotNode]] = {}
    for node in dag.nodes.values():
        if node.chapter not in chapters:
            chapters[node.chapter] = []
        chapters[node.chapter].append(node)

    for chapter_num in sorted(chapters.keys()):
        nodes = chapters[chapter_num]
        print(f"\nChapter {chapter_num}:")
        for node in nodes:
            twist_marker = " [TWIST]" if node.is_twist else ""
            print(f"  - {node.id} ({node.node_type.value}){twist_marker}")


def demonstrate_riddle_structure() -> None:
    """Show how the riddle structure works."""
    print("\n" + "=" * 70)
    print("THE RIDDLE STRUCTURE OF 'ECHO'")
    print("=" * 70)

    print("""
THE RIDDLE:
    "A detective hunts a killer named Echo who leaves messages.
     Each victim knew something about Sarah. Who is Echo?"

THE FRAME (False Context):
    Reader assumes: Sarah vs. External Killer
    Sarah is the detective/hero
    Echo is a separate person to catch

THE MISDIRECTION (Decoys):
    1. Marcus Webb - ex-cop, obvious suspect
    2. Dr. Helena Vance - psychiatrist with access
    3. James Chen - estranged brother with violent history

THE HIDDEN ANSWER (In Plain Sight):
    Chapter 1: Sarah's strange familiarity with crime scene
    Chapter 1: The locked room she 'never uses'
    Chapter 2: Her TOO-good intuition
    Chapter 4: Blackouts + reorganized files in her handwriting
    Chapter 5: No alibi during murders (she was there!)
    Chapter 7: Dr. Vance's notes about dissociation

THE PARADOX (The Lock):
    Chapter 12: Murder happens while Marcus is in custody
    Frame breaks: "This is impossible unless..."

THE SHIFT (The Key):
    Chapter 14: The locked room reveals everything
    Reader (and Sarah) must abandon original frame
    New frame: Sarah IS Echo. She's been hunting herself.

THE RETROSPECTIVE CLARITY:
    On re-read, every clue was fair:
    - "Echo" = an echo of Sarah, her other self
    - Messages were self-addressed
    - Victims threatened Sarah specifically
    - Her "intuition" was memory

This is what makes a riddle-novel work: the answer is always visible,
but the frame prevents you from seeing it until the shift.
""")


if __name__ == "__main__":
    # Create and analyze the riddle novel
    analyze_echo_riddle()

    # Demonstrate the structure
    demonstrate_riddle_structure()

    # Export DAG
    dag = create_echo_riddle_novel()
    output_path = Path(__file__).parent / "echo_riddle_dag.json"
    dag.to_json(output_path)
    print(f"\nDAG exported to: {output_path}")
