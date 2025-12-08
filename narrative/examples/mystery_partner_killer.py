"""
Test Story: The Partner's Secret

A mystery where a detective discovers her partner is the killer she's been hunting.

This example demonstrates building a complete narrative DAG using the
functional analysis approach and validating it with the analysis tools.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from narrative import (
    NarrativeDAG,
    PlotNode,
    NodeType,
    EdgeType,
    NarrativeAnalyzer,
    NarrativeGapDetector,
    CharacterGelAnalyzer,
    NarrativeFunctionalAnalyzer,
    NarrativeFunctionType,
    export_narrative_to_reflow,
)


def create_partners_secret_story():
    """
    Create "The Partner's Secret" - a mystery with a twist.

    Premise: Detective Sarah Chen has been hunting a serial killer for months.
    The evidence finally leads her to a shocking truth: her trusted partner
    of five years, Detective Mike Torres, is the killer.
    """

    # ========== Phase 1: Functional Requirements ==========
    print("Phase 1: Setting up functional requirements...")

    analyzer = NarrativeFunctionalAnalyzer()

    # Extract genre requirements
    analyzer.extract_requirements_from_genre("mystery")

    # Add story-specific requirements
    analyzer.add_requirement(
        description="Establish Sarah as competent, ethical detective",
        function_type=NarrativeFunctionType.INTRODUCE_CHARACTER,
        priority=1,
        success_criteria=["Show her solving a case", "Demonstrate her moral code"]
    )

    analyzer.add_requirement(
        description="Establish Mike as trustworthy partner",
        function_type=NarrativeFunctionType.INTRODUCE_CHARACTER,
        priority=1,
        success_criteria=["Show genuine partnership moments", "Create reader trust"]
    )

    analyzer.add_requirement(
        description="Plant fair clues pointing to Mike",
        function_type=NarrativeFunctionType.PLANT_CLUE,
        priority=1,
        success_criteria=["At least 5 clues visible in hindsight", "None too obvious"]
    )

    analyzer.add_requirement(
        description="Create devastating emotional impact at reveal",
        function_type=NarrativeFunctionType.DELIVER_TWIST,
        priority=1,
        success_criteria=["Reader feels betrayed alongside Sarah"]
    )

    analyzer.add_requirement(
        description="Explore theme of trust and betrayal",
        function_type=NarrativeFunctionType.DEVELOP_CHARACTER,
        priority=2,
        success_criteria=["Multiple relationship layers examined"]
    )

    print(f"  Created {len(analyzer.requirements)} requirements")

    # ========== Phase 2: Build the DAG ==========
    print("\nPhase 2: Building narrative DAG...")

    dag = NarrativeDAG(
        title="The Partner's Secret",
        author="Test Author"
    )

    # ACT 1: Setup (Chapters 1-6)
    # Establish characters, partnership, introduce case

    dag.add_node(PlotNode(
        id="opening_case",
        node_type=NodeType.SETUP,
        description="Sarah and Mike close a different case together, showing partnership",
        chapter=1,
        character="Sarah",
        subplot="main",
        stakes_level=3
    ))

    dag.add_node(PlotNode(
        id="serial_killer_intro",
        node_type=NodeType.CATALYST,
        description="New victim discovered - third in pattern. Sarah assigned lead",
        chapter=2,
        character="Sarah",
        subplot="main",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="mike_assigned_partner",
        node_type=NodeType.SETUP,
        description="Mike joins as partner on case. Their history established (5 years)",
        chapter=2,
        character="Mike",
        subplot="main",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="clue_1_timing",
        node_type=NodeType.FORESHADOWING,
        description="Mike was 'in the gym' during first murder. Mentioned casually",
        chapter=3,
        character="Mike",
        subplot="main",
        stakes_level=2
    ))

    dag.add_node(PlotNode(
        id="victim_profile",
        node_type=NodeType.REVELATION,
        description="Victims all connected to cold case from 6 years ago",
        chapter=4,
        character="Sarah",
        subplot="main",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="mikes_past",
        node_type=NodeType.SETUP,
        description="Sarah learns Mike's sister died in unsolved case years ago",
        chapter=5,
        character="Mike",
        subplot="Mike_backstory",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="clue_2_knowledge",
        node_type=NodeType.FORESHADOWING,
        description="Mike knows detail about crime scene before it's shared officially",
        chapter=5,
        character="Mike",
        subplot="main",
        stakes_level=3
    ))

    # ACT 2: Investigation (Chapters 7-16)

    dag.add_node(PlotNode(
        id="fourth_victim",
        node_type=NodeType.COMPLICATION,
        description="Fourth victim found. Pattern accelerating",
        chapter=7,
        character="Sarah",
        subplot="main",
        stakes_level=6
    ))

    dag.add_node(PlotNode(
        id="witness_description",
        node_type=NodeType.REVELATION,
        description="Witness describes man matching general description. Could be anyone",
        chapter=8,
        character="Sarah",
        subplot="main",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="red_herring_suspect",
        node_type=NodeType.COMPLICATION,
        description="Evidence points to ex-cop with grudge. Mike pushes this angle hard",
        chapter=9,
        character="Mike",
        subplot="main",
        stakes_level=6
    ))

    dag.add_node(PlotNode(
        id="sarah_mike_bond",
        node_type=NodeType.SETUP,
        description="Personal moment: Mike comforts Sarah after hard day. Deepens trust",
        chapter=10,
        character="Sarah",
        subplot="relationship",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="clue_3_alibi_crack",
        node_type=NodeType.FORESHADOWING,
        description="Small inconsistency in Mike's timeline. Sarah notices but dismisses",
        chapter=11,
        character="Sarah",
        subplot="main",
        stakes_level=4
    ))

    dag.add_node(PlotNode(
        id="red_herring_arrest",
        node_type=NodeType.COMPLICATION,
        description="Ex-cop arrested. Case seems solved",
        chapter=12,
        character="Sarah",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="fifth_victim",
        node_type=NodeType.COMPLICATION,
        description="Fifth victim while ex-cop in custody. Wrong suspect",
        chapter=14,
        character="Sarah",
        subplot="main",
        stakes_level=8,
        is_twist=True
    ))

    dag.add_node(PlotNode(
        id="mikes_motive_seed",
        node_type=NodeType.REVELATION,
        description="Sarah discovers all victims were connected to cover-up of Mike's sister's death",
        chapter=15,
        character="Sarah",
        subplot="main",
        stakes_level=7
    ))

    dag.add_node(PlotNode(
        id="clue_4_physical",
        node_type=NodeType.REVELATION,
        description="DNA under victim's nails. Lab backed up, results pending",
        chapter=16,
        character="Sarah",
        subplot="main",
        stakes_level=8
    ))

    # ACT 3: The Truth (Chapters 17-22)

    dag.add_node(PlotNode(
        id="sarah_suspicion",
        node_type=NodeType.DECISION,
        description="Sarah starts quietly investigating Mike. Guilt and denial",
        chapter=17,
        character="Sarah",
        subplot="main",
        stakes_level=8
    ))

    dag.add_node(PlotNode(
        id="clue_5_alibi_breaks",
        node_type=NodeType.REVELATION,
        description="Gym CCTV shows Mike wasn't there during first murder",
        chapter=18,
        character="Sarah",
        subplot="main",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="mike_knows",
        node_type=NodeType.COMPLICATION,
        description="Mike realizes Sarah suspects him. Tension",
        chapter=19,
        character="Mike",
        subplot="main",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="dna_match",
        node_type=NodeType.REVELATION,
        description="DNA results: match to Mike Torres",
        chapter=20,
        character="Sarah",
        subplot="main",
        stakes_level=10,
        is_twist=True
    ))

    dag.add_node(PlotNode(
        id="confrontation",
        node_type=NodeType.CONFRONTATION,
        description="Sarah confronts Mike. He doesn't deny it. Explains his justice",
        chapter=21,
        character="Sarah",
        subplot="main",
        stakes_level=10
    ))

    dag.add_node(PlotNode(
        id="mikes_choice",
        node_type=NodeType.DECISION,
        description="Mike could kill Sarah to escape. Instead, he surrenders",
        chapter=22,
        character="Mike",
        subplot="main",
        stakes_level=10
    ))

    # ACT 4: Resolution (Chapters 23-24)

    dag.add_node(PlotNode(
        id="arrest",
        node_type=NodeType.CONSEQUENCE,
        description="Sarah arrests her partner. Both devastated",
        chapter=23,
        character="Sarah",
        subplot="main",
        stakes_level=9
    ))

    dag.add_node(PlotNode(
        id="aftermath",
        node_type=NodeType.RESOLUTION,
        description="Sarah grapples with aftermath. Questions her judgment, her career",
        chapter=24,
        character="Sarah",
        subplot="main",
        stakes_level=5
    ))

    dag.add_node(PlotNode(
        id="final_image",
        node_type=NodeType.RESOLUTION,
        description="Sarah visits Mike in prison. Complex ending - justice served but at what cost?",
        chapter=24,
        character="Sarah",
        subplot="relationship",
        stakes_level=6
    ))

    # ========== Build Edges (Causal Relationships) ==========
    print("  Adding causal relationships...")

    # Setup → Catalyst
    dag.add_edge("opening_case", "serial_killer_intro", EdgeType.ENABLES)
    dag.add_edge("serial_killer_intro", "mike_assigned_partner", EdgeType.CAUSES)

    # Early clues foreshadow reveal
    dag.add_edge("mike_assigned_partner", "clue_1_timing", EdgeType.ENABLES)
    dag.add_edge("clue_1_timing", "dna_match", EdgeType.FORESHADOWS)

    # Investigation chain
    dag.add_edge("serial_killer_intro", "victim_profile", EdgeType.ENABLES)
    dag.add_edge("victim_profile", "mikes_past", EdgeType.REVEALS)
    dag.add_edge("mikes_past", "clue_2_knowledge", EdgeType.ENABLES)
    dag.add_edge("clue_2_knowledge", "dna_match", EdgeType.FORESHADOWS)

    # Rising action
    dag.add_edge("victim_profile", "fourth_victim", EdgeType.CAUSES)
    dag.add_edge("fourth_victim", "witness_description", EdgeType.ENABLES)
    dag.add_edge("witness_description", "red_herring_suspect", EdgeType.CAUSES)

    # Red herring subplot
    dag.add_edge("red_herring_suspect", "red_herring_arrest", EdgeType.CAUSES)
    dag.add_edge("red_herring_arrest", "fifth_victim", EdgeType.CONTRASTS)

    # Trust building makes betrayal worse
    dag.add_edge("mike_assigned_partner", "sarah_mike_bond", EdgeType.ENABLES)
    dag.add_edge("sarah_mike_bond", "confrontation", EdgeType.CONTRASTS)

    # More clues
    dag.add_edge("fourth_victim", "clue_3_alibi_crack", EdgeType.ENABLES)
    dag.add_edge("clue_3_alibi_crack", "clue_5_alibi_breaks", EdgeType.FORESHADOWS)

    # Truth emerges
    dag.add_edge("fifth_victim", "mikes_motive_seed", EdgeType.REVEALS)
    dag.add_edge("mikes_motive_seed", "clue_4_physical", EdgeType.ENABLES)
    dag.add_edge("clue_4_physical", "sarah_suspicion", EdgeType.CAUSES)

    # Investigation of partner
    dag.add_edge("sarah_suspicion", "clue_5_alibi_breaks", EdgeType.CAUSES)
    dag.add_edge("clue_5_alibi_breaks", "mike_knows", EdgeType.CAUSES)
    dag.add_edge("sarah_suspicion", "dna_match", EdgeType.ENABLES)

    # Climax
    dag.add_edge("dna_match", "confrontation", EdgeType.CAUSES)
    dag.add_edge("mike_knows", "confrontation", EdgeType.ENABLES)
    dag.add_edge("confrontation", "mikes_choice", EdgeType.CAUSES)
    dag.add_edge("mikes_choice", "arrest", EdgeType.CAUSES)

    # Resolution
    dag.add_edge("arrest", "aftermath", EdgeType.CAUSES)
    dag.add_edge("aftermath", "final_image", EdgeType.ENABLES)
    dag.add_edge("sarah_mike_bond", "final_image", EdgeType.RESOLVES)
    dag.add_edge("serial_killer_intro", "arrest", EdgeType.RESOLVES)

    print(f"  Created DAG with {len(dag._nodes)} nodes and {dag.graph.number_of_edges()} edges")

    return dag, analyzer


def analyze_story(dag, analyzer):
    """Run analysis on the story DAG."""

    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    # ========== Structural Analysis ==========
    print("\n1. Structural Analysis:")
    narrative_analyzer = NarrativeAnalyzer(dag)
    diagnosis = narrative_analyzer.diagnose()
    print(diagnosis.summary())

    # ========== Metrics ==========
    print("\n2. Narrative Metrics:")
    metrics = dag.calculate_metrics()
    print(metrics.summary())

    # ========== Gap Detection ==========
    print("\n3. Gap Detection:")
    gap_detector = NarrativeGapDetector(dag)
    gaps = gap_detector.detect_all_gaps()
    if gaps:
        print(f"  Found {len(gaps)} potential gaps:")
        for gap in gaps[:5]:  # Show first 5
            print(f"    [{gap.gap_type}] {gap.description} (severity: {gap.severity})")
    else:
        print("  No significant gaps detected!")

    # ========== Character Relationships ==========
    print("\n4. Character Relationship Analysis:")
    gel_analyzer = CharacterGelAnalyzer(dag)
    sarah_mike = gel_analyzer.analyze_pair("Sarah", "Mike")
    if sarah_mike:
        print(f"  Sarah & Mike:")
        print(f"    Relationship: {sarah_mike.suggested_relationship}")
        print(f"    Tension: {sarah_mike.thematic_tension}")
        print(f"    Connection strength: {sarah_mike.connection_strength:.2f}")

    # ========== Requirements Coverage ==========
    print("\n5. Requirements Coverage:")
    coverage = analyzer.validate_coverage()
    print(f"  Total requirements: {coverage['total_requirements']}")
    print(f"  Coverage: {coverage['coverage_percentage']:.1f}%")

    # ========== Structural Signature ==========
    print("\n6. Structural Signature (for cross-domain comparison):")
    signature = narrative_analyzer.extract_structural_signature()
    print(f"  Domain: {signature['domain']}")
    print(f"  Scale: {signature['scale']}")
    print(f"  Motifs: hub_ratio={signature['motifs']['hub_ratio']:.2f}, "
          f"chain_ratio={signature['motifs']['chain_ratio']:.2f}")
    print(f"  Flow: causal_depth={signature['flow']['causal_depth']}, "
          f"resolution_rate={signature['flow']['resolution_rate']:.2f}")


def main():
    """Run the complete example."""
    print("="*60)
    print("TEST STORY: The Partner's Secret")
    print("A Mystery with a Twist")
    print("="*60)

    # Create the story
    dag, analyzer = create_partners_secret_story()

    # Run analysis
    analyze_story(dag, analyzer)

    # Export to reflow format
    output_path = Path(__file__).parent / "output" / "partners_secret.json"
    output_path.parent.mkdir(exist_ok=True)
    export_narrative_to_reflow(dag, output_path)
    print(f"\n7. Exported to: {output_path}")

    # Validate DAG
    print(f"\n8. Validation:")
    print(f"  Is valid DAG: {dag.is_valid_dag()}")
    print(f"  Dangling setups: {len(dag.find_dangling_setups())}")
    print(f"  Orphan nodes: {len(dag.find_orphan_nodes())}")

    return dag


if __name__ == "__main__":
    dag = main()
