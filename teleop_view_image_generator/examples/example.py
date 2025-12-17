#!/usr/bin/env python3
"""
Example: Using the teleop_view_image_generator package

This example demonstrates how to use the TeleopImageGenerator
with synthetic images (no external image files required).

Usage:
    python -m teleop_view_image_generator.examples.example
"""

import cv2
import numpy as np
import os
from teleop_view_image_generator import TeleopImageGenerator, load_config, ViewerConfig


def create_synthetic_image(height: int, width: int, color: tuple, label: str) -> np.ndarray:
    """Create a synthetic colored image with a label."""
    img = np.full((height, width, 3), color, dtype=np.uint8)

    # Add label text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(label, font, 1.0, 2)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    cv2.putText(img, label, (text_x, text_y), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

    return img


def main():
    # Try to load config from file, or use a minimal config
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")

    if os.path.exists(config_path):
        print(f"Loading config from: {config_path}")
        generator = TeleopImageGenerator(config_path)
    else:
        print("Config file not found, using default config")
        # Create minimal config programmatically
        from teleop_view_image_generator.config import (
            ViewerConfig, OverlayStyle, TextOverlayConfig,
            CentermarkConfig, BorderConfig, LayoutNodeConfig,
            ColorRule, VariableConfig, VariableCondition
        )

        config = ViewerConfig(
            resolutions={
                "ee_cam": [480, 848, 3],
                "ifm": [800, 1280, 3],
                "monitor_cam": [720, 1280, 3],
            },
            hardware={"old_elbow_cam": True, "camera_mount": "D"},
            text_overlays=[
                TextOverlayConfig(
                    id="status",
                    template="Status: {robot_status}",
                    cameras=["back_monitor_cam", "front_monitor_cam"],
                    color=(255, 128, 0),
                ),
            ],
            layouts={
                "horizontal": LayoutNodeConfig(
                    direction="horizontal",
                    children=[
                        LayoutNodeConfig(camera="ee_cam"),
                        LayoutNodeConfig(camera="ifm_camera1"),
                        LayoutNodeConfig(
                            direction="horizontal",
                            children=[
                                LayoutNodeConfig(camera="front_monitor_cam"),
                                LayoutNodeConfig(camera="back_monitor_cam"),
                            ]
                        ),
                    ]
                ),
            },
            active_layout="horizontal",
        )
        generator = TeleopImageGenerator(config)

    # Define camera colors for visualization
    camera_colors = {
        "ee_cam": (50, 50, 150),              # Dark red
        "ifm_camera1": (50, 150, 50),         # Dark green
        "ifm_camera2": (150, 50, 50),         # Dark blue
        "front_monitor_cam": (50, 150, 150),  # Dark yellow
        "back_monitor_cam": (150, 50, 150),   # Dark magenta
        "boxwall_monitor_cam": (80, 120, 80), # Olive
    }

    # Create and update synthetic images for each camera
    print(f"\nCameras in use: {generator.get_camera_names()}")

    for cam_name in generator.get_camera_names():
        cam_config = generator.get_camera_config(cam_name)
        if cam_config:
            h, w = cam_config.resolution[:2]
            color = camera_colors.get(cam_name, (100, 100, 100))
            img = create_synthetic_image(h, w, color, cam_name)
            generator.update_camera_image(cam_name, img, active=True)

    # Update sensor data
    generator.update_sensor_data(
        laser_distance=25.0,
        laser_active=True,
        pressure_manifold=0.45,
        pressure_base=0.32,
        robot_status="SCANNING",
        is_manual_review=True,
    )

    # Generate the output frame
    frames = generator.generate_frame()

    # Display result
    print(f"Generated {len(frames)} frame(s)")
    print(f"Output size: {frames[0].shape[1]}x{frames[0].shape[0]} pixels")

    # Show the frame (press any key to close)
    cv2.imshow("Teleop View Example", frames[0])
    print("\nPress any key to close the window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Cleanup
    generator.shutdown()


if __name__ == "__main__":
    main()
