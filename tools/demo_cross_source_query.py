#!/usr/bin/env python3
"""
Demo: Cross-Source Historical Queries

Demonstrates querying the merged Gospel + Historical Context graph to find
connections between religious texts and secular historical sources.
"""

from graph_query import GraphQueryEngine


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*80)
    print(title)
    print("="*80 + "\n")


def main():
    """Run cross-source query demonstrations."""

    print_section("CROSS-SOURCE HISTORICAL QUERY DEMONSTRATION")
    print("This demo shows how Gospel narratives connect with Roman and Jewish")
    print("historical sources through word transition graphs.\n")

    # Initialize engine with merged graph
    engine = GraphQueryEngine("data/kjv_context_merged.json")

    print(f"Loaded merged graph:")
    print(f"  Nodes: {engine.G.number_of_nodes()}")
    print(f"  Edges: {engine.G.number_of_edges()}")
    print(f"  Sources: KJV Gospels + Historical Context (Tacitus, Josephus, Talmud, etc.)")

    # Define cross-source queries
    queries = [
        {
            'question': 'Pontius Pilate crucifixion Jesus',
            'context': 'Pilate is mentioned in Gospels, Tacitus, and archaeological evidence (Pilate Stone)'
        },
        {
            'question': 'Jesus brother James stoned',
            'context': 'James is mentioned in Gospels and Josephus (Antiquities XX.9.1)'
        },
        {
            'question': 'Christians Christus Tiberius Rome',
            'context': 'Tacitus\'s Annals mentions Christians, Christ, and execution under Tiberius'
        },
        {
            'question': 'John Baptist baptism Herod',
            'context': 'John the Baptist appears in Gospels and Josephus (Antiquities XVIII.5.2)'
        },
        {
            'question': 'Pharisees Sadducees doctrine law',
            'context': 'Jewish sects described in both Gospels and Josephus\'s historical accounts'
        },
        {
            'question': 'Passover execution hanged',
            'context': 'Babylonian Talmud mentions Yeshu hanged on eve of Passover'
        }
    ]

    # Run queries
    for i, query_info in enumerate(queries, 1):
        print_section(f"QUERY {i}: {query_info['question']}")
        print(f"Context: {query_info['context']}\n")

        result = engine.query(query_info['question'], max_path_length=8)

        if result['subgraph'] is not None:
            context = engine.analyze_query_context(result)

            print("\n📊 KEY FINDINGS:")

            # Show which sources are involved
            query_nodes = result['path_info']['query_nodes']
            sources_involved = set()
            for node in query_nodes:
                node_data = engine.G.nodes.get(node, {})
                node_sources = node_data.get('sources', [])
                sources_involved.update(node_sources)

            if sources_involved:
                print(f"  Sources involved: {', '.join(sources_involved)}")

            # Show top narrative fragment
            if context['narrative_fragments']:
                print(f"  Top connection: {context['narrative_fragments'][0]}")

            # Show strongest edge
            if context['edge_weights']:
                top_edge = context['edge_weights'][0]
                print(f"  Strongest link: {top_edge['from']} → {top_edge['to']} ({top_edge['probability']:.1%})")

            # Show bridge words
            bridge_words = result['path_info'].get('bridge_nodes', [])
            if bridge_words:
                clean_bridges = [engine._clean_node_name(n) for n in bridge_words[:5]]
                print(f"  Bridge words: {', '.join(clean_bridges)}")

        print("\n" + "-"*80)

    # Summary
    print_section("SUMMARY")
    print("""
This demonstration shows how merging Gospel and historical source DAGs enables:

✓ Cross-validation: Find where religious and secular sources agree
✓ Context enrichment: See Gospel events through Roman/Jewish historian perspectives
✓ Historical grounding: Connect theological claims to archaeological evidence
✓ Semantic relationships: Discover how different sources describe same people/events

The graph structure reveals connections like:
  - Pontius Pilate (Gospels + Tacitus + Pilate Stone inscription)
  - James the brother of Jesus (Gospels + Josephus)
  - John the Baptist (Gospels + Josephus)
  - Crucifixion/execution terminology across sources
  - Jewish sects (Gospels + Josephus on Pharisees/Sadducees)

This demonstrates graph-based historical analysis using word transition patterns
to bridge religious and secular historical sources.
    """)


if __name__ == '__main__':
    main()
