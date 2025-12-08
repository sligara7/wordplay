"""
Test Story: The Reluctant Heir

An epic fantasy where a farmhand discovers they're heir to a fallen kingdom,
and must choose between the simple life they love and their destiny.

This example demonstrates building a multi-subplot epic fantasy DAG
with parallel character arcs and convergent threads.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from narrative import (
    NarrativeDAG,
    PlotNode,
    NodeType,
    EdgeType,
    NarrativeAnalyzer,
    NarrativeGapDetector,
    SpinoffGenerator,
    export_narrative_to_reflow,
)


def create_reluctant_heir_story():
    """
    Create "The Reluctant Heir" - an epic fantasy.

    Premise: Kira, a farmhand in a remote village, discovers she bears
    the birthmark of the lost royal line. With the Dark Lord rising,
    she must claim her heritage or watch the world burn.
    """

    dag = NarrativeDAG(
        title="The Reluctant Heir",
        author="Test Author"
    )

    # ========== ACT 1: THE ORDINARY WORLD (Ch 1-8) ==========

    # Main Plot - Kira's journey
    dag.add_node(PlotNode(
        id="village_life",
        node_type=NodeType.SETUP,
        description="Kira's happy life on the farm. Her dreams of staying forever",
        chapter=1,
        character="Kira",
        subplot="main",
        stakes_level=1,
        emotional_valence=0.7
    ))

    dag.add_node(PlotNode(
        id="strange_dreams",
        node_type=NodeType.FORESHADOWING,
        description="Kira has recurring dreams of a burning castle, a woman's voice",
        chapter=2,
        character="Kira",
        subplot="main",
        stakes_level=2
    ))

    dag.add_node(PlotNode(
        id="stranger_arrives",
        node_type=NodeType.CATALYST,
        description="Wounded stranger (Aldric, former knight) collapses at farm",
        chapter=3,
        character="Aldric",
        subplot="main",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="dark_lord_mentioned",
        node_type=NodeType.SETUP,
        description="Aldric speaks of Dark Lord's armies marching. War coming",
        chapter=4,
        character="Aldric",
        subplot="villain",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="birthmark_revealed",
        node_type=NodeType.REVELATION,
        description="Aldric sees Kira's birthmark - the Royal Seal. She's the heir",
        chapter=5,
        character="Kira",
        subplot="main",
        stakes_level=6,
        is_twist=True
    ))

    dag.add_node(PlotNode(
        id="kira_refuses",
        node_type=NodeType.DECISION,
        description="Kira refuses to believe. She's just a farmhand. Wants normal life",
        chapter=6,
        character="Kira",
        subplot="main",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="village_attacked",
        node_type=NodeType.COMPLICATION,
        description="Dark Lord's scouts attack village looking for 'the heir'",
        chapter=7,
        character="Kira",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="family_killed",
        node_type=NodeType.CONSEQUENCE,
        description="Kira's adoptive family killed in attack. She couldn't save them",
        chapter=8,
        character="Kira",
        subplot="main",
        stakes_level=8,
        emotional_valence=-0.9
    ))

    # ========== ACT 2A: THE JOURNEY (Ch 9-16) ==========

    dag.add_node(PlotNode(
        id="reluctant_departure",
        node_type=NodeType.DECISION,
        description="Kira flees with Aldric. Not to claim throne, just to survive",
        chapter=9,
        character="Kira",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="mentor_teaching",
        node_type=NodeType.SETUP,
        description="Aldric begins teaching Kira swordplay and royal history",
        chapter=10,
        character="Aldric",
        subplot="main",
        stakes_level=5
    ))

    # Subplot: Resistance
    dag.add_node(PlotNode(
        id="resistance_intro",
        node_type=NodeType.SETUP,
        description="They meet the Resistance - ragtag fighters against Dark Lord",
        chapter=11,
        character="Kira",
        subplot="resistance",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="lyra_intro",
        node_type=NodeType.SETUP,
        description="Lyra, Resistance leader, doesn't trust Kira. Rival dynamic",
        chapter=11,
        character="Lyra",
        subplot="resistance",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="first_battle",
        node_type=NodeType.COMPLICATION,
        description="Kira's first real battle. Freezes. Aldric saves her",
        chapter=13,
        character="Kira",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="kira_saves_lyra",
        node_type=NodeType.DECISION,
        description="Despite rivalry, Kira saves Lyra. Begins earning respect",
        chapter=14,
        character="Kira",
        subplot="resistance",
        stakes_level=7
    ))

    # Subplot: Dark Lord's perspective
    dag.add_node(PlotNode(
        id="dark_lord_plans",
        node_type=NodeType.SETUP,
        description="Dark Lord learns heir lives. Sends his champion to hunt her",
        chapter=12,
        character="Dark Lord",
        subplot="villain",
        stakes_level=6
    ))

    dag.add_node(PlotNode(
        id="champion_hunt",
        node_type=NodeType.COMPLICATION,
        description="Champion nearly catches them. Narrow escape costs lives",
        chapter=15,
        character="Kira",
        subplot="main",
        stakes_level=8
    ))

    dag.add_node(PlotNode(
        id="ancient_magic_hint",
        node_type=NodeType.REVELATION,
        description="Aldric reveals: Royal bloodline can wield ancient magic",
        chapter=16,
        character="Aldric",
        subplot="main",
        stakes_level=6
    ))

    # ========== ACT 2B: MIDPOINT AND TRIALS (Ch 17-24) ==========

    dag.add_node(PlotNode(
        id="reach_ancient_temple",
        node_type=NodeType.SETUP,
        description="Journey to ancient temple where Kira must prove her blood",
        chapter=17,
        character="Kira",
        subplot="main",
        stakes_level=6
    ))

    dag.add_node(PlotNode(
        id="temple_trial",
        node_type=NodeType.CONFRONTATION,
        description="Kira faces magical trial. Sees vision of mother's sacrifice",
        chapter=18,
        character="Kira",
        subplot="main",
        stakes_level=8
    ))

    dag.add_node(PlotNode(
        id="magic_awakens",
        node_type=NodeType.REVELATION,
        description="Kira's magic awakens. She accepts part of her heritage",
        chapter=19,
        character="Kira",
        subplot="main",
        stakes_level=8,
        is_twist=True,
        emotional_valence=0.6
    ))

    dag.add_node(PlotNode(
        id="aldric_secret",
        node_type=NodeType.REVELATION,
        description="Aldric confesses: He failed to save Kira's mother. His guilt",
        chapter=20,
        character="Aldric",
        subplot="main",
        stakes_level=7,
        is_twist=True
    ))

    dag.add_node(PlotNode(
        id="resistance_betrayal",
        node_type=NodeType.COMPLICATION,
        description="Spy in Resistance. Their base is attacked. Many die",
        chapter=21,
        character="Lyra",
        subplot="resistance",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="lyra_captured",
        node_type=NodeType.COMPLICATION,
        description="Lyra captured by Dark Lord's forces",
        chapter=22,
        character="Lyra",
        subplot="resistance",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="kira_dark_moment",
        node_type=NodeType.CONSEQUENCE,
        description="Kira at lowest point. Everything she touches dies. Wants to quit",
        chapter=23,
        character="Kira",
        subplot="main",
        stakes_level=9,
        emotional_valence=-0.8
    ))

    dag.add_node(PlotNode(
        id="aldric_sacrifice_setup",
        node_type=NodeType.DECISION,
        description="Aldric plans to trade himself for Lyra. Redemption",
        chapter=24,
        character="Aldric",
        subplot="main",
        stakes_level=9
    ))

    # ========== ACT 3: THE CLIMAX (Ch 25-30) ==========

    dag.add_node(PlotNode(
        id="rescue_mission",
        node_type=NodeType.DECISION,
        description="Kira chooses to lead rescue. First time she leads willingly",
        chapter=25,
        character="Kira",
        subplot="main",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="fortress_infiltration",
        node_type=NodeType.CONFRONTATION,
        description="Team infiltrates Dark Lord's fortress",
        chapter=26,
        character="Kira",
        subplot="main",
        stakes_level=10
    ))

    dag.add_node(PlotNode(
        id="aldric_falls",
        node_type=NodeType.CONSEQUENCE,
        description="Aldric dies saving Kira from champion. His redemption",
        chapter=27,
        character="Aldric",
        subplot="main",
        stakes_level=10,
        emotional_valence=-0.7
    ))

    dag.add_node(PlotNode(
        id="face_dark_lord",
        node_type=NodeType.CONFRONTATION,
        description="Kira faces Dark Lord alone. Magic vs. magic",
        chapter=28,
        character="Kira",
        subplot="main",
        stakes_level=10
    ))

    dag.add_node(PlotNode(
        id="final_choice",
        node_type=NodeType.DECISION,
        description="Dark Lord offers deal: power together. Kira refuses, embraces light",
        chapter=29,
        character="Kira",
        subplot="main",
        stakes_level=10
    ))

    dag.add_node(PlotNode(
        id="dark_lord_defeated",
        node_type=NodeType.CONSEQUENCE,
        description="Kira defeats Dark Lord using inherited magic and her farm-girl grit",
        chapter=29,
        character="Kira",
        subplot="villain",
        stakes_level=10,
        is_twist=True
    ))

    # ========== ACT 4: RESOLUTION (Ch 30-32) ==========

    dag.add_node(PlotNode(
        id="offered_crown",
        node_type=NodeType.SETUP,
        description="Kira offered the crown. The kingdom needs a ruler",
        chapter=30,
        character="Kira",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="kira_final_choice",
        node_type=NodeType.DECISION,
        description="Kira accepts, but plans to build a different kind of kingdom",
        chapter=31,
        character="Kira",
        subplot="main",
        stakes_level=6
    ))

    dag.add_node(PlotNode(
        id="lyra_partnership",
        node_type=NodeType.RESOLUTION,
        description="Lyra becomes Kira's champion. Former rivals now sisters",
        chapter=31,
        character="Lyra",
        subplot="resistance",
        stakes_level=4,
        emotional_valence=0.7
    ))

    dag.add_node(PlotNode(
        id="memorial",
        node_type=NodeType.RESOLUTION,
        description="Kira honors Aldric and all who fell. Plants a garden on farm ruins",
        chapter=32,
        character="Kira",
        subplot="main",
        stakes_level=3,
        emotional_valence=0.5
    ))

    dag.add_node(PlotNode(
        id="new_beginning",
        node_type=NodeType.RESOLUTION,
        description="Queen Kira looks to the future. The farm girl made good",
        chapter=32,
        character="Kira",
        subplot="main",
        stakes_level=4,
        emotional_valence=0.8
    ))

    # ========== Build Causal Edges ==========

    # Act 1: Setup to Catalyst
    dag.add_edge("village_life", "strange_dreams", EdgeType.ENABLES)
    dag.add_edge("strange_dreams", "temple_trial", EdgeType.FORESHADOWS)
    dag.add_edge("village_life", "stranger_arrives", EdgeType.ENABLES)
    dag.add_edge("stranger_arrives", "dark_lord_mentioned", EdgeType.REVEALS)
    dag.add_edge("stranger_arrives", "birthmark_revealed", EdgeType.CAUSES)
    dag.add_edge("birthmark_revealed", "kira_refuses", EdgeType.CAUSES)
    dag.add_edge("dark_lord_mentioned", "village_attacked", EdgeType.CAUSES)
    dag.add_edge("kira_refuses", "village_attacked", EdgeType.PARALLELS)
    dag.add_edge("village_attacked", "family_killed", EdgeType.CAUSES)

    # Act 2A: Journey begins
    dag.add_edge("family_killed", "reluctant_departure", EdgeType.CAUSES)
    dag.add_edge("reluctant_departure", "mentor_teaching", EdgeType.ENABLES)
    dag.add_edge("mentor_teaching", "resistance_intro", EdgeType.ENABLES)
    dag.add_edge("resistance_intro", "lyra_intro", EdgeType.ENABLES)
    dag.add_edge("mentor_teaching", "first_battle", EdgeType.ENABLES)
    dag.add_edge("lyra_intro", "kira_saves_lyra", EdgeType.CONTRASTS)
    dag.add_edge("first_battle", "kira_saves_lyra", EdgeType.CAUSES)

    # Villain subplot
    dag.add_edge("dark_lord_mentioned", "dark_lord_plans", EdgeType.ENABLES)
    dag.add_edge("birthmark_revealed", "dark_lord_plans", EdgeType.CAUSES)
    dag.add_edge("dark_lord_plans", "champion_hunt", EdgeType.CAUSES)

    dag.add_edge("champion_hunt", "ancient_magic_hint", EdgeType.ENABLES)

    # Act 2B: Trials
    dag.add_edge("ancient_magic_hint", "reach_ancient_temple", EdgeType.CAUSES)
    dag.add_edge("reach_ancient_temple", "temple_trial", EdgeType.ENABLES)
    dag.add_edge("temple_trial", "magic_awakens", EdgeType.CAUSES)
    dag.add_edge("magic_awakens", "aldric_secret", EdgeType.ENABLES)

    dag.add_edge("kira_saves_lyra", "resistance_betrayal", EdgeType.ENABLES)
    dag.add_edge("resistance_betrayal", "lyra_captured", EdgeType.CAUSES)
    dag.add_edge("lyra_captured", "kira_dark_moment", EdgeType.CAUSES)
    dag.add_edge("aldric_secret", "kira_dark_moment", EdgeType.CAUSES)
    dag.add_edge("kira_dark_moment", "aldric_sacrifice_setup", EdgeType.CAUSES)

    # Act 3: Climax
    dag.add_edge("aldric_sacrifice_setup", "rescue_mission", EdgeType.ENABLES)
    dag.add_edge("kira_dark_moment", "rescue_mission", EdgeType.CONTRASTS)
    dag.add_edge("rescue_mission", "fortress_infiltration", EdgeType.CAUSES)
    dag.add_edge("fortress_infiltration", "aldric_falls", EdgeType.CAUSES)
    dag.add_edge("aldric_secret", "aldric_falls", EdgeType.RESOLVES)
    dag.add_edge("aldric_falls", "face_dark_lord", EdgeType.ENABLES)
    dag.add_edge("magic_awakens", "face_dark_lord", EdgeType.ENABLES)
    dag.add_edge("face_dark_lord", "final_choice", EdgeType.CAUSES)
    dag.add_edge("final_choice", "dark_lord_defeated", EdgeType.CAUSES)

    # Resolution
    dag.add_edge("dark_lord_defeated", "offered_crown", EdgeType.CAUSES)
    dag.add_edge("fortress_infiltration", "lyra_partnership", EdgeType.ENABLES)
    dag.add_edge("offered_crown", "kira_final_choice", EdgeType.CAUSES)
    dag.add_edge("kira_final_choice", "lyra_partnership", EdgeType.ENABLES)
    dag.add_edge("aldric_falls", "memorial", EdgeType.ENABLES)
    dag.add_edge("family_killed", "memorial", EdgeType.RESOLVES)
    dag.add_edge("lyra_partnership", "new_beginning", EdgeType.ENABLES)
    dag.add_edge("memorial", "new_beginning", EdgeType.ENABLES)
    dag.add_edge("village_life", "new_beginning", EdgeType.CONTRASTS)

    return dag


def analyze_fantasy_story(dag):
    """Run analysis on the epic fantasy DAG."""

    print("\n" + "="*60)
    print("ANALYSIS: The Reluctant Heir")
    print("="*60)

    # Structural Analysis
    print("\n1. Structural Analysis:")
    analyzer = NarrativeAnalyzer(dag)
    diagnosis = analyzer.diagnose()
    if diagnosis.has_issues:
        print(diagnosis.summary())
    else:
        print("  No structural issues detected!")

    # Metrics
    print("\n2. Narrative Metrics:")
    metrics = dag.calculate_metrics()
    print(f"  Chapters: {dag._chapter_count}")
    print(f"  Total nodes: {len(dag._nodes)}")
    print(f"  Total edges: {dag.graph.number_of_edges()}")
    print(f"  Twist count: {metrics.twist_count}")
    print(f"  Subplot count: {metrics.subplot_count}")
    print(f"  Causal depth: {metrics.causal_depth}")

    # Gap Detection
    print("\n3. Gap Detection:")
    detector = NarrativeGapDetector(dag)
    gaps = detector.detect_all_gaps()
    print(f"  Found {len(gaps)} potential gaps")

    # Character Arcs
    print("\n4. Character Arcs:")
    for char in ["Kira", "Aldric", "Lyra"]:
        arc = dag.get_character_arc(char)
        print(f"  {char}: {len(arc)} scenes across chapters "
              f"{min(n.chapter for n in arc if n.chapter)}-{max(n.chapter for n in arc if n.chapter)}")

    # Spinoff Potential
    print("\n5. Spinoff Seeds:")
    spinoff_gen = SpinoffGenerator(dag)
    seeds = spinoff_gen.find_spinoff_seeds()
    print(f"  Found {len(seeds)} potential spinoffs:")
    for seed in seeds[:3]:
        print(f"    - {seed.spinoff_theme} ({seed.potential_length})")

    # Structural Signature
    print("\n6. Structural Signature:")
    sig = analyzer.extract_structural_signature()
    print(f"  Hub ratio: {sig['motifs']['hub_ratio']:.2f}")
    print(f"  Chain ratio: {sig['motifs']['chain_ratio']:.2f}")
    print(f"  Funnel nodes: {sig['motifs']['funnel_nodes']}")

    return dag


def main():
    """Run the epic fantasy example."""
    print("="*60)
    print("TEST STORY: The Reluctant Heir")
    print("An Epic Fantasy")
    print("="*60)

    dag = create_reluctant_heir_story()
    print(f"\nCreated DAG with {len(dag._nodes)} nodes, {dag.graph.number_of_edges()} edges")

    analyze_fantasy_story(dag)

    # Export
    output_path = Path(__file__).parent / "output" / "reluctant_heir.json"
    output_path.parent.mkdir(exist_ok=True)
    export_narrative_to_reflow(dag, output_path)
    print(f"\n7. Exported to: {output_path}")

    return dag


if __name__ == "__main__":
    dag = main()
