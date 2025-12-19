#!/usr/bin/env python3
"""
Minimal example demonstrating all text overlay features.

Features shown:
  1. Simple overlay with static color
  2. Formula variable (computed value)
  3. Conditional variable (text based on conditions)
  4. Conditional colors (color based on thresholds)
  5. Visibility condition (show/hide overlay)
  6. Combined features (formula + conditional display + conditional color)

Usage:
    python example.py
    python example.py --debug  # Enable debug logging
"""

import cv2
import logging
import numpy as np
import os
import random
import sys
import time
from multi_view_composer import MultiViewComposer, setup_logging

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_test_image(height: int, width: int, color: tuple, label: str) -> np.ndarray:
    """Create a colored test image with a centered label."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(label, font, 0.6, 1)[0]
    x = (width - text_size[0]) // 2
    y = (height + text_size[1]) // 2
    cv2.putText(img, label, (x, y), font, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    return img


def main():
    # Setup logging (use --debug for verbose output)
    log_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
    setup_logging(level=log_level)

    config_path = os.path.join(SCRIPT_DIR, "example_config.yaml")
    composer = MultiViewComposer(config_path)

    # Create test images for each camera
    colors = {
        "cam_top_left": (80, 60, 60),
        "cam_bottom_left": (60, 80, 60),
        "cam_right": (60, 60, 80),
    }
    for name in composer.get_camera_names():
        cfg = composer.get_camera_config(name)
        h, w = cfg.resolution[:2]
        img = create_test_image(h, w, colors.get(name, (50, 50, 50)), name)
        composer.update_camera_image(name, img, active=True)

    print("Running example... Press 'q' or ESC to quit\n")
    print("Overlay features demonstrated:")
    print("  1. Temperature - static color")
    print("  2. Speed - formula (m/s -> km/h)")
    print("  3. Mode - conditional text")
    print("  4. Level - conditional colors")
    print("  5. Warning - visibility condition")
    print("  6. Battery - combined features\n")

    frame_count = 0
    start_time = time.time()

    while True:
        # Random sensor values
        composer.update_dynamic_data(
            temperature=random.uniform(20, 35),
            speed_ms=random.uniform(0, 15),
            mode=random.choice(["auto", "manual", "standby"]),
            level=random.randint(0, 100),
            show_warning=random.random() < 0.15,
            warning_msg=random.choice(["Overheating", "Low signal", "Check sensor"]),
            battery_v=random.uniform(9, 12.6),
        )

        frames = composer.generate_frame()
        cv2.imshow("Multi-View Composer Example", frames[0])

        frame_count += 1
        if frame_count % 50 == 0:
            fps = frame_count / (time.time() - start_time)
            print(f"Frame {frame_count} | FPS: {fps:.1f}")

        if cv2.waitKey(100) & 0xFF in (ord('q'), 27):
            break

    cv2.destroyAllWindows()
    composer.shutdown()
    print(f"\nDone. {frame_count} frames rendered.")


if __name__ == "__main__":
    main()
