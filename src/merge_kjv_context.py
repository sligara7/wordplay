"""
Quick merge of KJV Gospels + Historical Context

Simplified merger for faster processing.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def extract_clean_word(node_id):
    """Extract clean word from node ID."""
    if '_' in node_id:
        return node_id.split('_', 1)[1].lower()
    return node_id.lower()


def merge_kjv_context():
    """Merge KJV Gospels with historical context."""
    print("="*80)
    print("MERGING KJV GOSPELS + HISTORICAL CONTEXT")
    print("="*80)

    # Load graphs
    print("\nLoading graphs...")
    with open('data/kjv_gospels_dag.json', 'r') as f:
        kjv_data = json.load(f)
    print(f"✓ Loaded KJV Gospels: {len(kjv_data['graph']['nodes'])} nodes")

    with open('data/historical_context_dag.json', 'r') as f:
        context_data = json.load(f)
    print(f"✓ Loaded Historical Context: {len(context_data['graph']['nodes'])} nodes")

    # Build word -> nodes mapping
    word_to_nodes = defaultdict(list)

    for node in kjv_data['graph']['nodes']:
        clean = extract_clean_word(node['id'])
        word_to_nodes[clean].append(('kjv', node))

    for node in context_data['graph']['nodes']:
        clean = extract_clean_word(node['id'])
        word_to_nodes[clean].append(('context', node))

    # Find touchpoints
    touchpoints = {w for w, nodes in word_to_nodes.items() if len(nodes) > 1}
    print(f"\n✓ Found {len(touchpoints)} touchpoint words")

    # Create merged nodes
    merged_nodes = []
    for word, node_list in word_to_nodes.items():
        sources = [src for src, _ in node_list]
        total_freq = sum(n.get('raw', {}).get('frequency', 0) for _, n in node_list)

        merged_node = {
            'id': f'merged_{word}',
            'name': word,
            'type': 'merged_word',
            'raw': {
                'word': word,
                'total_frequency': total_freq,
                'sources': sources,
                'is_touchpoint': word in touchpoints
            }
        }
        merged_nodes.append(merged_node)

    print(f"✓ Created {len(merged_nodes)} merged nodes")

    # Merge edges
    print("\nMerging edges...")
    edge_map = {}  # (source_word, target_word) -> edge data

    # Process KJV edges
    for edge in kjv_data['graph']['links']:
        src = extract_clean_word(edge['source'])
        tgt = extract_clean_word(edge['target'])
        key = (src, tgt)

        if key not in edge_map:
            edge_map[key] = {
                'source': f'merged_{src}',
                'target': f'merged_{tgt}',
                'type': 'word_transition',
                'interaction_type': 'follows',
                'weight': edge.get('weight', 0),
                'raw': {
                    'sources': [{'name': 'kjv', 'weight': edge.get('weight', 0)}]
                }
            }
        else:
            edge_map[key]['raw']['sources'].append(
                {'name': 'kjv', 'weight': edge.get('weight', 0)}
            )

    # Process context edges
    for edge in context_data['graph']['links']:
        src = extract_clean_word(edge['source'])
        tgt = extract_clean_word(edge['target'])
        key = (src, tgt)

        if key not in edge_map:
            edge_map[key] = {
                'source': f'merged_{src}',
                'target': f'merged_{tgt}',
                'type': 'word_transition',
                'interaction_type': 'follows',
                'weight': edge.get('weight', 0),
                'raw': {
                    'sources': [{'name': 'context', 'weight': edge.get('weight', 0)}]
                }
            }
        else:
            edge_map[key]['raw']['sources'].append(
                {'name': 'context', 'weight': edge.get('weight', 0)}
            )
            # Average the weights
            weights = [s['weight'] for s in edge_map[key]['raw']['sources']]
            edge_map[key]['weight'] = sum(weights) / len(weights)

    merged_edges = list(edge_map.values())
    print(f"✓ Created {len(merged_edges)} merged edges")

    # Build output
    output = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'framework': 'KJV + Historical Context Merged',
            'framework_id': 'kjv_context_merged',
            'component_term': 'merged_word',
            'connection_term': 'transition',
            'num_nodes': len(merged_nodes),
            'num_edges': len(merged_edges),
            'tool_version': '1.0.0',
            'source_graphs': ['kjv_gospels', 'historical_context'],
            'touchpoint_count': len(touchpoints)
        },
        'graph': {
            'directed': True,
            'multigraph': False,
            'nodes': merged_nodes,
            'links': merged_edges
        }
    }

    # Save
    output_path = 'data/kjv_context_merged.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to: {output_path}")

    # Print sample touchpoints
    print("\nSample touchpoint words (in both KJV and historical sources):")
    for word in sorted(list(touchpoints))[:20]:
        print(f"  {word}")

    print("\n" + "="*80)
    print("MERGE COMPLETE!")
    print("="*80)


if __name__ == '__main__':
    merge_kjv_context()
