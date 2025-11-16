#!/usr/bin/env python3
"""
Create a simple test image for testing the image region graph builder

This creates a synthetic image with distinct colored regions to demonstrate
how the region DAG builder works.
"""

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path


def create_simple_test_image(output_path: str, size=(400, 300)):
    """
    Create a simple test image with distinct regions

    Creates an image with:
    - Blue sky region (top)
    - Green grass region (bottom)
    - Red circle (sun/ball)
    - Brown rectangle (house/object)
    - Yellow triangle (roof)

    Args:
        output_path: Where to save the image
        size: Image dimensions (width, height)
    """
    width, height = size

    # Create blank white image
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    # Sky (top half) - Blue
    draw.rectangle(
        [(0, 0), (width, height // 2)],
        fill=(135, 206, 235)  # Sky blue
    )

    # Grass (bottom half) - Green
    draw.rectangle(
        [(0, height // 2), (width, height)],
        fill=(34, 139, 34)  # Forest green
    )

    # Sun/ball - Red circle
    sun_center = (width - 80, 60)
    sun_radius = 40
    draw.ellipse(
        [
            (sun_center[0] - sun_radius, sun_center[1] - sun_radius),
            (sun_center[0] + sun_radius, sun_center[1] + sun_radius)
        ],
        fill=(255, 69, 0)  # Red-orange
    )

    # House body - Brown rectangle
    house_left = width // 3
    house_top = height // 2 - 80
    house_width = 120
    house_height = 100
    draw.rectangle(
        [(house_left, house_top), (house_left + house_width, house_top + house_height)],
        fill=(139, 69, 19)  # Saddle brown
    )

    # Roof - Yellow triangle
    roof_points = [
        (house_left - 20, house_top),  # Left point
        (house_left + house_width + 20, house_top),  # Right point
        (house_left + house_width // 2, house_top - 60)  # Top point
    ]
    draw.polygon(roof_points, fill=(255, 215, 0))  # Gold

    # Save image
    img.save(output_path)
    print(f"Test image created: {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  Regions: sky (blue), grass (green), sun (red), house (brown), roof (yellow)")

    return img


def create_dog_like_test_image(output_path: str, size=(400, 400)):
    """
    Create a more complex test image resembling a simple dog silhouette

    This demonstrates how the region DAG would work with a more
    complex shape that has multiple parts.

    Args:
        output_path: Where to save the image
        size: Image dimensions (width, height)
    """
    width, height = size

    # Create blank white background
    img = Image.new('RGB', size, color=(240, 240, 240))  # Light gray background
    draw = ImageDraw.Draw(img)

    # Dog color (brown)
    dog_color = (139, 90, 43)  # Brown
    ear_color = (101, 67, 33)  # Darker brown

    # Body - ellipse
    body_bbox = [
        (width // 2 - 80, height // 2),
        (width // 2 + 80, height // 2 + 120)
    ]
    draw.ellipse(body_bbox, fill=dog_color)

    # Head - circle
    head_center = (width // 2, height // 2 - 40)
    head_radius = 50
    draw.ellipse(
        [
            (head_center[0] - head_radius, head_center[1] - head_radius),
            (head_center[0] + head_radius, head_center[1] + head_radius)
        ],
        fill=dog_color
    )

    # Left ear
    left_ear = [
        (head_center[0] - 45, head_center[1] - 40),
        (head_center[0] - 30, head_center[1] - 70),
        (head_center[0] - 20, head_center[1] - 35)
    ]
    draw.polygon(left_ear, fill=ear_color)

    # Right ear
    right_ear = [
        (head_center[0] + 20, head_center[1] - 35),
        (head_center[0] + 30, head_center[1] - 70),
        (head_center[0] + 45, head_center[1] - 40)
    ]
    draw.polygon(right_ear, fill=ear_color)

    # Legs (4 rectangles)
    leg_width = 20
    leg_height = 60

    # Front left leg
    draw.rectangle(
        [
            (width // 2 - 50, height // 2 + 100),
            (width // 2 - 50 + leg_width, height // 2 + 100 + leg_height)
        ],
        fill=dog_color
    )

    # Front right leg
    draw.rectangle(
        [
            (width // 2 + 30, height // 2 + 100),
            (width // 2 + 30 + leg_width, height // 2 + 100 + leg_height)
        ],
        fill=dog_color
    )

    # Back left leg
    draw.rectangle(
        [
            (width // 2 - 70, height // 2 + 90),
            (width // 2 - 70 + leg_width, height // 2 + 90 + leg_height)
        ],
        fill=dog_color
    )

    # Back right leg
    draw.rectangle(
        [
            (width // 2 + 50, height // 2 + 90),
            (width // 2 + 50 + leg_width, height // 2 + 90 + leg_height)
        ],
        fill=dog_color
    )

    # Tail - curved polygon
    tail_points = [
        (width // 2 + 75, height // 2 + 40),
        (width // 2 + 90, height // 2 + 20),
        (width // 2 + 100, height // 2 + 30),
        (width // 2 + 80, height // 2 + 50)
    ]
    draw.polygon(tail_points, fill=dog_color)

    # Eyes (two small black circles)
    eye_radius = 5
    left_eye = (head_center[0] - 15, head_center[1] - 10)
    right_eye = (head_center[0] + 15, head_center[1] - 10)

    draw.ellipse(
        [
            (left_eye[0] - eye_radius, left_eye[1] - eye_radius),
            (left_eye[0] + eye_radius, left_eye[1] + eye_radius)
        ],
        fill=(0, 0, 0)
    )
    draw.ellipse(
        [
            (right_eye[0] - eye_radius, right_eye[1] - eye_radius),
            (right_eye[0] + eye_radius, right_eye[1] + eye_radius)
        ],
        fill=(0, 0, 0)
    )

    # Nose (small black triangle)
    nose_points = [
        (head_center[0] - 8, head_center[1] + 15),
        (head_center[0] + 8, head_center[1] + 15),
        (head_center[0], head_center[1] + 25)
    ]
    draw.polygon(nose_points, fill=(0, 0, 0))

    # Save image
    img.save(output_path)
    print(f"Dog test image created: {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  Parts: body, head, ears, legs, tail, eyes, nose")

    return img


def main():
    """Create test images"""
    output_dir = Path(__file__).parent.parent / 'data'
    output_dir.mkdir(exist_ok=True)

    # Create simple scene
    simple_path = output_dir / 'test_simple_scene.png'
    create_simple_test_image(str(simple_path))

    # Create dog-like shape
    dog_path = output_dir / 'test_dog_shape.png'
    create_dog_like_test_image(str(dog_path))

    print("\nTest images created successfully!")
    print(f"  {simple_path}")
    print(f"  {dog_path}")
    print("\nYou can now test the image graph builder:")
    print(f"  python src/image_graph_builder.py {simple_path} --preview")
    print(f"  python src/image_graph_builder.py {dog_path} --preview")


if __name__ == '__main__':
    main()
