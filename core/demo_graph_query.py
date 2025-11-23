#!/usr/bin/env python3
"""
Demo script for graph querying system.

Shows how to query word graphs with natural language questions.
"""

from graph_query import GraphQueryEngine
from pathlib import Path


def run_demo_queries():
    """Run a series of demo queries on gospel texts."""

    print("\n" + "="*80)
    print("GRAPH QUERY SYSTEM DEMONSTRATION")
    print("="*80)
    print("\nThis system extracts relevant subgraphs by finding shortest paths")
    print("between query terms, revealing narrative connections.\n")

    # KJV English queries
    print("\n" + "="*80)
    print("ENGLISH (KJV) QUERIES")
    print("="*80 + "\n")

    kjv_engine = GraphQueryEngine("data/kjv_gospels_dag.json")

    english_questions = [
        "Did Jesus walk on water?",
        "Jesus healing sick people",
        "disciples boat storm",
        "kingdom of heaven",
        "bread fish miracle"
    ]

    for question in english_questions:
        result = kjv_engine.query(question, max_path_length=8)

        if result['subgraph'] is not None:
            context = kjv_engine.analyze_query_context(result)

            print(f"\n📊 Top narrative fragment: {context['narrative_fragments'][0]}")

            # Show highest probability connection
            if context['edge_weights']:
                top_edge = context['edge_weights'][0]
                print(f"🔗 Strongest connection: '{top_edge['from']}' → '{top_edge['to']}' ({top_edge['probability']:.1%})")

        print("\n" + "-"*80)

    # Greek queries
    print("\n" + "="*80)
    print("GREEK (BYZANTINE) QUERIES")
    print("="*80 + "\n")

    greek_engine = GraphQueryEngine("data/byzantine_gospels_dag.json")

    # Greek questions (Jesus, disciples, kingdom, heaven, bread, fish)
    greek_questions = [
        "Ἰησοῦς μαθηταὶ",  # Jesus disciples
        "βασιλεία οὐρανῶν",  # kingdom of heaven
        "ἄρτος ὀψάριον",  # bread fish
        "θάλασσα πλοῖον",  # sea boat
        "Πέτρος Ἰωάννης Ἰάκωβος"  # Peter John James
    ]

    for question in greek_questions:
        result = greek_engine.query(question, max_path_length=8)

        if result['subgraph'] is not None:
            context = greek_engine.analyze_query_context(result)

            print(f"\n📊 Top narrative fragment: {context['narrative_fragments'][0]}")

            # Show highest probability connection
            if context['edge_weights']:
                top_edge = context['edge_weights'][0]
                print(f"🔗 Strongest connection: '{top_edge['from']}' → '{top_edge['to']}' ({top_edge['probability']:.1%})")

        print("\n" + "-"*80)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
The query system successfully:
✓ Extracts meaningful words from natural language questions
✓ Finds matching nodes in the word graph
✓ Computes shortest paths between query terms
✓ Identifies "bridge words" that connect concepts
✓ Reveals narrative fragments and high-probability phrases
✓ Works with both English and Greek text

This demonstrates graph-based question answering where the structure
of word transitions encodes semantic relationships.
    """)


def interactive_mode():
    """Run interactive query mode."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python demo_graph_query.py <graph_path> [--demo]")
        print("\nOptions:")
        print("  --demo    Run demonstration queries")
        print("\nInteractive mode:")
        print("  python demo_graph_query.py data/kjv_gospels_dag.json")
        print("  (then type questions interactively)")
        sys.exit(1)

    if '--demo' in sys.argv:
        run_demo_queries()
        return

    graph_path = sys.argv[1]
    engine = GraphQueryEngine(graph_path)

    print(f"\n{'='*80}")
    print("INTERACTIVE GRAPH QUERY MODE")
    print(f"{'='*80}")
    print(f"\nGraph: {graph_path}")
    print(f"Nodes: {engine.G.number_of_nodes()}")
    print(f"Edges: {engine.G.number_of_edges()}")
    print("\nType your questions (or 'quit' to exit):\n")

    while True:
        try:
            question = input("Query> ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not question:
                continue

            result = engine.query(question, max_path_length=10)

            if result['subgraph'] is not None:
                context = engine.analyze_query_context(result)

                print("\n📊 INSIGHTS:")
                if context['narrative_fragments']:
                    print(f"  Top fragment: {context['narrative_fragments'][0]}")

                if context['edge_weights']:
                    top_edge = context['edge_weights'][0]
                    print(f"  Strongest link: {top_edge['from']} → {top_edge['to']} ({top_edge['probability']:.1%})")

                print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    interactive_mode()
