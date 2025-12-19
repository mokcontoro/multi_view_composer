#!/usr/bin/env python3
"""Benchmark script for multi_view_composer.

Uses synthetic images in memory - no disk I/O required.
"""

import time
import argparse
import os
import random
import numpy as np

from multi_view_composer import MultiViewComposer, load_config

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "example_config.yaml")


def create_test_image(height: int, width: int, label: str) -> np.ndarray:
    """Create a test image with a label."""
    # Generate unique color based on label hash
    h = hash(label)
    color = ((h & 0xFF) // 3 + 40, ((h >> 8) & 0xFF) // 3 + 40, ((h >> 16) & 0xFF) // 3 + 40)
    img = np.full((height, width, 3), color, dtype=np.uint8)
    return img


def run_benchmark(num_frames: int = 50, config_path: str = None):
    if config_path is None:
        config_path = DEFAULT_CONFIG
    print("=" * 60)
    print("MULTI-VIEW COMPOSER BENCHMARK")
    print("=" * 60)

    config = load_config(config_path)
    composer = MultiViewComposer(config)

    # Create test images for each camera
    camera_names = composer.get_camera_names()
    print(f"\nCameras: {camera_names}")

    for name in camera_names:
        cfg = composer.get_camera_config(name)
        h, w = cfg.resolution[:2]
        img = create_test_image(h, w, name)
        composer.update_camera_image(name, img, active=True)

    # Warm up with sample data
    composer.update_dynamic_data(
        temperature=25.0,
        speed_ms=5.0,
        mode="auto",
        level=50,
        show_warning=False,
        warning_msg="",
        battery_v=12.0,
    )
    _ = composer.generate_frame()

    # Benchmark
    print(f"\nRunning {num_frames} frames...")
    print("-" * 40)

    start = time.perf_counter()
    for _ in range(num_frames):
        composer.update_dynamic_data(
            temperature=random.uniform(20, 35),
            speed_ms=random.uniform(0, 15),
            mode=random.choice(["auto", "manual", "standby"]),
            level=random.randint(0, 100),
            show_warning=random.random() < 0.1,
            warning_msg="Test",
            battery_v=random.uniform(9, 12.6),
        )
        _ = composer.generate_frame()
    elapsed = time.perf_counter() - start

    fps = num_frames / elapsed
    ms_per_frame = (elapsed / num_frames) * 1000

    print(f"  Frames: {num_frames}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  FPS: {fps:.1f}")
    print(f"  ms/frame: {ms_per_frame:.2f}")
    print(f"  Overlays: {len(config.text_overlays)}")
    print(f"  Cameras: {len(camera_names)}")

    composer.shutdown()

    print("\n" + "=" * 60)
    print(f"RESULT: {fps:.1f} FPS ({ms_per_frame:.2f} ms/frame)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark multi_view_composer")
    parser.add_argument("-n", "--frames", type=int, default=50, help="Number of frames")
    parser.add_argument("-c", "--config", default=None, help="Config file (default: example_config.yaml)")
    args = parser.parse_args()

    run_benchmark(args.frames, args.config)
