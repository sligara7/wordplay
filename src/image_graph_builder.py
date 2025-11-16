#!/usr/bin/env python3
"""
Image Region Graph Builder - Creates directed graphs from image regions

Segments images into uniform regions and builds a graph where:
- Nodes: Image regions (superpixels with similar color/texture)
- Edges: Spatial adjacency between regions
- Edge weights: Strength of adjacency (shared boundary length, normalized)

This creates a structural "fingerprint" of the image that is:
- Scale invariant (relative relationships preserved)
- Partially rotation invariant (can be normalized)
- Frequency-based (common patterns emerge across multiple images)

Output format compatible with the existing graph analysis tools.

Future Variants:
- Intensity mode: Use grayscale instead of RGB for color-invariant matching
- Emotion detection: Specialized features for facial expression regions
"""

import json
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise ImportError("PIL/Pillow required: pip install Pillow")

try:
    from skimage import segmentation, color, measure, graph as skimage_graph
except ImportError:
    raise ImportError("scikit-image required: pip install scikit-image")


class ImageGraphBuilder:
    """Builds a spatial adjacency graph from image regions"""

    def __init__(self,
                 image_path: str,
                 image_name: str = "Untitled",
                 n_segments: int = 100,
                 compactness: float = 10.0,
                 mode: str = "rgb",
                 min_region_size: int = 10):
        """
        Initialize the image graph builder

        Args:
            image_path: Path to the image file
            image_name: Name/identifier for this image
            n_segments: Approximate number of superpixel segments (SLIC algorithm)
            compactness: Balance between color similarity and spatial proximity (higher = more compact)
            mode: Feature extraction mode - "rgb" for color, "intensity" for grayscale
            min_region_size: Minimum region size in pixels (smaller regions ignored)
        """
        self.image_path = Path(image_path)
        self.image_name = image_name
        self.n_segments = n_segments
        self.compactness = compactness
        self.mode = mode.lower()
        self.min_region_size = min_region_size

        if self.mode not in ["rgb", "intensity"]:
            raise ValueError(f"Mode must be 'rgb' or 'intensity', got '{self.mode}'")

        # Load image
        self.image = None
        self.image_array = None
        self.load_image()

        # Segmentation results
        self.segments = None
        self.num_regions = 0

        # Graph data structures
        self.region_features = {}  # region_id -> feature dict
        self.region_adjacencies = defaultdict(Counter)  # region_id -> {neighbor_id: boundary_length}
        self.unique_regions = set()

    def load_image(self):
        """Load and convert image to numpy array"""
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        self.image = Image.open(self.image_path)

        # Convert to RGB if necessary
        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')

        self.image_array = np.array(self.image)

        print(f"Loaded image: {self.image_path}")
        print(f"  Size: {self.image.size[0]}x{self.image.size[1]}")
        print(f"  Mode: {self.mode}")

    def segment_image(self):
        """
        Segment image into regions using SLIC superpixels

        SLIC (Simple Linear Iterative Clustering) groups similar pixels
        into perceptually meaningful regions based on color similarity
        and spatial proximity.
        """
        print(f"Segmenting image into ~{self.n_segments} regions...")

        # Apply SLIC segmentation
        self.segments = segmentation.slic(
            self.image_array,
            n_segments=self.n_segments,
            compactness=self.compactness,
            start_label=0
        )

        # Get actual number of segments
        self.num_regions = len(np.unique(self.segments))

        print(f"  Created {self.num_regions} regions")

    def extract_region_features(self):
        """
        Extract features for each region

        Features include:
        - Color (RGB average or intensity average)
        - Size (area in pixels)
        - Position (centroid)
        - Shape (bounding box, aspect ratio)
        """
        print("Extracting region features...")

        for region_id in range(self.num_regions):
            # Get mask for this region
            mask = (self.segments == region_id)
            area = np.sum(mask)

            # Skip very small regions
            if area < self.min_region_size:
                continue

            self.unique_regions.add(region_id)

            # Extract pixel values for this region
            region_pixels = self.image_array[mask]

            # Calculate features based on mode
            if self.mode == "rgb":
                # RGB color features
                color_avg = region_pixels.mean(axis=0).astype(int)
                color_std = region_pixels.std(axis=0).astype(int)
                color_feature = f"rgb_{color_avg[0]}_{color_avg[1]}_{color_avg[2]}"
            else:  # intensity mode
                # Convert to grayscale intensity
                intensity = (0.299 * region_pixels[:, 0] +
                           0.587 * region_pixels[:, 1] +
                           0.114 * region_pixels[:, 2])
                intensity_avg = int(intensity.mean())
                intensity_std = int(intensity.std())
                color_feature = f"intensity_{intensity_avg}"

            # Calculate position (centroid)
            coords = np.argwhere(mask)
            centroid_y, centroid_x = coords.mean(axis=0).astype(int)

            # Calculate bounding box
            min_y, min_x = coords.min(axis=0)
            max_y, max_x = coords.max(axis=0)
            width = max_x - min_x + 1
            height = max_y - min_y + 1

            # Store features (convert numpy types to native Python types for JSON serialization)
            if self.mode == "rgb":
                self.region_features[region_id] = {
                    "region_id": int(region_id),
                    "color_avg_rgb": [int(c) for c in color_avg],
                    "color_std_rgb": [int(c) for c in color_std],
                    "color_feature": color_feature,
                    "area": int(area),
                    "centroid": [int(centroid_x), int(centroid_y)],
                    "bbox": [int(min_x), int(min_y), int(width), int(height)],
                    "aspect_ratio": float(width / height) if height > 0 else 0.0,
                    "mode": "rgb"
                }
            else:  # intensity
                self.region_features[region_id] = {
                    "region_id": int(region_id),
                    "intensity_avg": int(intensity_avg),
                    "intensity_std": int(intensity_std),
                    "color_feature": color_feature,
                    "area": int(area),
                    "centroid": [int(centroid_x), int(centroid_y)],
                    "bbox": [int(min_x), int(min_y), int(width), int(height)],
                    "aspect_ratio": float(width / height) if height > 0 else 0.0,
                    "mode": "intensity"
                }

        print(f"  Extracted features for {len(self.unique_regions)} regions")

    def detect_adjacencies(self):
        """
        Detect spatial adjacencies between regions

        Two regions are adjacent if they share a boundary.
        Edge weight = length of shared boundary (number of adjacent pixels)
        """
        print("Detecting region adjacencies...")

        # Manual adjacency detection by scanning boundaries
        # Check each pixel's neighbors (4-connectivity: up, down, left, right)
        height, width = self.segments.shape
        adjacency_pairs = defaultdict(int)

        for y in range(height):
            for x in range(width):
                current_region = self.segments[y, x]

                # Skip filtered regions
                if current_region not in self.unique_regions:
                    continue

                # Check right neighbor
                if x < width - 1:
                    right_region = self.segments[y, x + 1]
                    if right_region != current_region and right_region in self.unique_regions:
                        pair = tuple(sorted([current_region, right_region]))
                        adjacency_pairs[pair] += 1

                # Check bottom neighbor
                if y < height - 1:
                    bottom_region = self.segments[y + 1, x]
                    if bottom_region != current_region and bottom_region in self.unique_regions:
                        pair = tuple(sorted([current_region, bottom_region]))
                        adjacency_pairs[pair] += 1

        # Convert to bidirectional adjacencies (ensure Python native ints)
        adjacency_count = 0
        for (region1, region2), boundary_length in adjacency_pairs.items():
            self.region_adjacencies[int(region1)][int(region2)] = int(boundary_length)
            self.region_adjacencies[int(region2)][int(region1)] = int(boundary_length)
            adjacency_count += 2  # Counting both directions

        print(f"  Found {adjacency_count} adjacency relationships ({len(adjacency_pairs)} unique pairs)")

    def build_graph(self):
        """Build the complete region adjacency graph"""
        self.segment_image()
        self.extract_region_features()
        self.detect_adjacencies()

    def normalize_weights(self) -> Dict[int, Dict[int, float]]:
        """
        Normalize adjacency weights to probabilities

        For each region, normalize its adjacency weights so they sum to 1.0
        This makes edge weights comparable across different regions.

        Returns:
            Dictionary of region_id -> {neighbor_id: probability}
        """
        normalized = {}

        for region_id, adjacencies in self.region_adjacencies.items():
            total_boundary = sum(adjacencies.values())
            if total_boundary > 0:
                normalized[region_id] = {
                    neighbor_id: weight / total_boundary
                    for neighbor_id, weight in adjacencies.items()
                }
            else:
                normalized[region_id] = {}

        return normalized

    def to_system_graph_json(self) -> dict:
        """
        Convert region graph to system_of_systems_graph.json format

        Compatible with existing analysis tools (analyze_word_graph.py, etc.)

        Returns:
            Dictionary in standard graph format
        """
        normalized_weights = self.normalize_weights()

        # Build nodes list
        nodes = []
        for region_id in sorted(self.unique_regions):
            region_id = int(region_id)  # Ensure native Python int
            features = self.region_features[region_id]

            node = {
                "id": f"region_{region_id}",
                "name": f"region_{region_id}",
                "type": "region",
                "raw": {
                    "region_id": region_id,
                    "features": features,
                    "num_neighbors": len(self.region_adjacencies.get(region_id, {})),
                    "framework": "image_region_flow"
                },
                "functions": [
                    {
                        "function_id": f"F-REGION-{region_id:04d}",
                        "function_name": f"Region {region_id}: {features['color_feature']}",
                        "description": f"Image region with area={features['area']} at {features['centroid']}"
                    }
                ]
            }
            nodes.append(node)

        # Build edges list
        edges = []
        processed_pairs = set()  # Avoid duplicate bidirectional edges

        for source_id, adjacencies in self.region_adjacencies.items():
            source_id = int(source_id)  # Ensure native Python int
            for target_id, boundary_length in adjacencies.items():
                target_id = int(target_id)  # Ensure native Python int
                # Create unique pair identifier (sorted to avoid duplicates)
                pair = tuple(sorted([source_id, target_id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                # Get normalized weights for both directions
                weight_forward = normalized_weights.get(source_id, {}).get(target_id, 0)
                weight_backward = normalized_weights.get(target_id, {}).get(source_id, 0)

                # Average weight for undirected adjacency
                avg_weight = (weight_forward + weight_backward) / 2.0

                edge = {
                    "source": f"region_{source_id}",
                    "target": f"region_{target_id}",
                    "type": "region_adjacency",
                    "interaction_type": "adjacent_to",
                    "weight": float(avg_weight),
                    "raw": {
                        "boundary_length": int(boundary_length),
                        "weight_forward": float(weight_forward),
                        "weight_backward": float(weight_backward),
                        "source_region": source_id,
                        "target_region": target_id
                    }
                }
                edges.append(edge)

        # Calculate statistics
        total_adjacencies = sum(
            len(adjacencies) for adjacencies in self.region_adjacencies.values()
        ) // 2  # Divide by 2 because each adjacency is counted twice

        # Build the complete graph structure
        graph = {
            "metadata": {
                "generated": datetime.utcnow().isoformat(),
                "framework": "Image Region Flow",
                "framework_id": "image_region_flow",
                "component_term": "region",
                "connection_term": "adjacency",
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "tool_version": "1.0.0",
                "image_name": self.image_name,
                "image_path": str(self.image_path),
                "image_size": list(self.image.size),
                "total_regions": len(self.unique_regions),
                "total_adjacencies": total_adjacencies,
                "segmentation_params": {
                    "n_segments": self.n_segments,
                    "compactness": self.compactness,
                    "mode": self.mode,
                    "min_region_size": self.min_region_size
                }
            },
            "graph": {
                "directed": False,  # Region adjacency is inherently undirected
                "multigraph": False,
                "graph": {},
                "nodes": nodes,
                "links": edges
            },
            "architectural_issues": {
                "circular_dependencies": [],
                "orphaned_nodes": [],  # Regions with no neighbors
                "dead_ends": [],
                "unreachable_regions": []
            },
            "architectural_issues_summary": {
                "total_issues": 0,
                "by_type": {}
            }
        }

        # Analyze for orphaned regions (no neighbors)
        regions_with_adjacencies = set(self.region_adjacencies.keys())
        orphaned = self.unique_regions - regions_with_adjacencies

        graph["architectural_issues"]["orphaned_nodes"] = sorted(orphaned)

        issue_count = len(orphaned)
        graph["architectural_issues_summary"]["total_issues"] = issue_count
        graph["architectural_issues_summary"]["by_type"] = {
            "orphaned_nodes": len(orphaned)
        }

        return graph

    def save_graph(self, output_path: str):
        """
        Save the graph to a JSON file

        Args:
            output_path: Path to save the JSON file
        """
        graph = self.to_system_graph_json()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)

        print(f"\nGraph saved to: {output_path}")
        print(f"  Nodes: {graph['metadata']['num_nodes']}")
        print(f"  Edges: {graph['metadata']['num_edges']}")
        print(f"  Total regions: {graph['metadata']['total_regions']}")
        print(f"  Orphaned regions: {len(graph['architectural_issues']['orphaned_nodes'])}")

    def save_segmentation_preview(self, output_path: str):
        """
        Save a visual preview of the segmentation

        Args:
            output_path: Path to save the preview image
        """
        if self.segments is None:
            raise ValueError("Must call build_graph() first")

        # Create segmentation visualization
        segmented_image = segmentation.mark_boundaries(
            self.image_array,
            self.segments,
            color=(1, 0, 0),  # Red boundaries
            mode='thick'
        )

        # Convert to PIL Image and save
        preview = Image.fromarray((segmented_image * 255).astype(np.uint8))
        preview.save(output_path)

        print(f"Segmentation preview saved to: {output_path}")


def main():
    """Command-line interface for image graph builder"""
    parser = argparse.ArgumentParser(
        description='Build a region adjacency graph from an image'
    )
    parser.add_argument('input_file', help='Path to image file')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-n', '--name', help='Image name', default='Untitled')
    parser.add_argument('-s', '--segments', type=int, default=100,
                        help='Number of segments (default: 100)')
    parser.add_argument('-c', '--compactness', type=float, default=10.0,
                        help='Compactness parameter (default: 10.0)')
    parser.add_argument('-m', '--mode', choices=['rgb', 'intensity'], default='rgb',
                        help='Feature mode: rgb (color) or intensity (grayscale)')
    parser.add_argument('--min-size', type=int, default=10,
                        help='Minimum region size in pixels (default: 10)')
    parser.add_argument('--preview', action='store_true',
                        help='Save segmentation preview image')

    args = parser.parse_args()

    # Check input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}")
        return 1

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = input_path.parent / f"{input_path.stem}_region_graph.json"

    # Build graph
    print(f"Building region graph from: {input_path}")
    print(f"Image name: {args.name}")

    builder = ImageGraphBuilder(
        image_path=str(input_path),
        image_name=args.name,
        n_segments=args.segments,
        compactness=args.compactness,
        mode=args.mode,
        min_region_size=args.min_size
    )

    builder.build_graph()
    builder.save_graph(str(output_path))

    # Optionally save preview
    if args.preview:
        preview_path = input_path.parent / f"{input_path.stem}_segmentation_preview.png"
        builder.save_segmentation_preview(str(preview_path))

    return 0


if __name__ == '__main__':
    exit(main())
