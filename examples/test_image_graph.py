#!/usr/bin/env python3
"""
Example script demonstrating image region graph building

This script shows how to:
1. Build a region adjacency graph from an image
2. Analyze the graph structure
3. Compare graphs from multiple images
4. Use both RGB and intensity modes

Usage:
    python examples/test_image_graph.py path/to/image.jpg

Requirements:
    pip install Pillow scikit-image numpy
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_graph_builder import ImageGraphBuilder
import json


def analyze_image_basic(image_path: str):
    """
    Basic example: Build and analyze a single image graph

    Args:
        image_path: Path to image file
    """
    print("=" * 70)
    print("BASIC IMAGE GRAPH ANALYSIS")
    print("=" * 70)

    # Build graph with default settings (RGB mode, ~100 regions)
    builder = ImageGraphBuilder(
        image_path=image_path,
        image_name=Path(image_path).stem,
        n_segments=100,
        compactness=10.0,
        mode="rgb"
    )

    builder.build_graph()

    # Save outputs
    output_dir = Path(image_path).parent
    json_path = output_dir / f"{Path(image_path).stem}_region_graph.json"
    preview_path = output_dir / f"{Path(image_path).stem}_segmentation_preview.png"

    builder.save_graph(str(json_path))
    builder.save_segmentation_preview(str(preview_path))

    # Load and display some graph statistics
    with open(json_path, 'r') as f:
        graph_data = json.load(f)

    metadata = graph_data['metadata']
    print("\n" + "=" * 70)
    print("GRAPH STATISTICS")
    print("=" * 70)
    print(f"Total regions: {metadata['total_regions']}")
    print(f"Total adjacencies: {metadata['total_adjacencies']}")
    print(f"Avg neighbors per region: {metadata['total_adjacencies'] * 2 / metadata['total_regions']:.2f}")

    # Show some example regions
    print("\n" + "=" * 70)
    print("SAMPLE REGIONS (first 5)")
    print("=" * 70)
    for i, node in enumerate(graph_data['graph']['nodes'][:5]):
        features = node['raw']['features']
        print(f"\nRegion {features['region_id']}:")
        if features['mode'] == 'rgb':
            print(f"  Color (RGB): {features['color_avg_rgb']}")
        else:
            print(f"  Intensity: {features['intensity_avg']}")
        print(f"  Area: {features['area']} pixels")
        print(f"  Position: {features['centroid']}")
        print(f"  Neighbors: {node['raw']['num_neighbors']}")

    # Show some example adjacencies
    print("\n" + "=" * 70)
    print("SAMPLE ADJACENCIES (first 5)")
    print("=" * 70)
    for i, edge in enumerate(graph_data['graph']['links'][:5]):
        print(f"\n{edge['source']} <-> {edge['target']}")
        print(f"  Boundary length: {edge['raw']['boundary_length']} pixels")
        print(f"  Weight: {edge['weight']:.4f}")

    return graph_data


def compare_rgb_vs_intensity(image_path: str):
    """
    Compare RGB mode vs Intensity mode

    RGB mode: Distinguishes colors (red dog vs brown dog different)
    Intensity mode: Color-invariant (red dog vs brown dog similar)

    Args:
        image_path: Path to image file
    """
    print("\n" + "=" * 70)
    print("RGB MODE vs INTENSITY MODE COMPARISON")
    print("=" * 70)

    output_dir = Path(image_path).parent
    image_stem = Path(image_path).stem

    # Build RGB graph
    print("\nBuilding RGB graph...")
    rgb_builder = ImageGraphBuilder(
        image_path=image_path,
        image_name=f"{image_stem}_rgb",
        n_segments=100,
        mode="rgb"
    )
    rgb_builder.build_graph()
    rgb_path = output_dir / f"{image_stem}_rgb_graph.json"
    rgb_builder.save_graph(str(rgb_path))

    # Build Intensity graph
    print("\nBuilding Intensity graph...")
    intensity_builder = ImageGraphBuilder(
        image_path=image_path,
        image_name=f"{image_stem}_intensity",
        n_segments=100,
        mode="intensity"
    )
    intensity_builder.build_graph()
    intensity_path = output_dir / f"{image_stem}_intensity_graph.json"
    intensity_builder.save_graph(str(intensity_path))

    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"RGB graph regions: {len(rgb_builder.unique_regions)}")
    print(f"Intensity graph regions: {len(intensity_builder.unique_regions)}")
    print("\nNote: When comparing multiple images of the same object type,")
    print("intensity mode will produce more similar graphs across different")
    print("colored instances (e.g., black dog vs brown dog).")


def demonstrate_scale_invariance(image_path: str):
    """
    Demonstrate that region graphs are approximately scale-invariant

    The relative structure of the graph should be similar even if
    we use different numbers of segments.

    Args:
        image_path: Path to image file
    """
    print("\n" + "=" * 70)
    print("SCALE INVARIANCE DEMONSTRATION")
    print("=" * 70)

    output_dir = Path(image_path).parent
    image_stem = Path(image_path).stem

    # Build graphs with different granularities
    segment_counts = [50, 100, 200]

    for n_seg in segment_counts:
        print(f"\nBuilding graph with {n_seg} segments...")
        builder = ImageGraphBuilder(
            image_path=image_path,
            image_name=f"{image_stem}_{n_seg}seg",
            n_segments=n_seg,
            mode="rgb"
        )
        builder.build_graph()

        output_path = output_dir / f"{image_stem}_{n_seg}seg_graph.json"
        builder.save_graph(str(output_path))

        # Calculate average neighbors
        avg_neighbors = sum(
            len(adjs) for adjs in builder.region_adjacencies.values()
        ) / len(builder.unique_regions) if builder.unique_regions else 0

        print(f"  Regions: {len(builder.unique_regions)}")
        print(f"  Avg neighbors: {avg_neighbors:.2f}")

    print("\nNote: The graph structure (connectivity pattern) should be similar")
    print("across different segment counts, even though absolute numbers differ.")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python test_image_graph.py <image_path>")
        print("\nExample:")
        print("  python examples/test_image_graph.py data/sample_dog.jpg")
        return 1

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        return 1

    # Run demonstrations
    try:
        # 1. Basic analysis
        graph_data = analyze_image_basic(image_path)

        # 2. RGB vs Intensity comparison
        compare_rgb_vs_intensity(image_path)

        # 3. Scale invariance
        demonstrate_scale_invariance(image_path)

        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("\n1. Analyze the generated graph with existing tools:")
        print(f"   python src/analyze_word_graph.py {Path(image_path).parent}/{Path(image_path).stem}_region_graph.json")
        print("\n2. Build graphs from multiple images and merge them to find common patterns")
        print("\n3. Use graph_query.py to search for specific region patterns")
        print("\n4. Visualize the segmentation preview to see how regions were identified")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
