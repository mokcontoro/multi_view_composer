"""Tests for layout module."""

import pytest
import numpy as np

from multi_view_composer import (
    vconcat_resize,
    hconcat_resize,
    create_placeholder,
    build_layout_from_config,
    compute_layout_from_config,
    LayoutManager,
    LayoutNode,
    Direction,
)
from multi_view_composer.config import LayoutNodeConfig


@pytest.fixture
def image_480x640():
    """Create a 480x640 image."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def image_720x1280():
    """Create a 720x1280 image."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


class TestVconcatResize:
    def test_same_width(self, image_480x640):
        img1 = image_480x640.copy()
        img2 = image_480x640.copy()

        result = vconcat_resize(img1, img2)

        assert result.shape[0] == 960  # 480 + 480
        assert result.shape[1] == 640

    def test_different_widths(self):
        img1 = np.zeros((480, 640, 3), dtype=np.uint8)
        img2 = np.zeros((720, 1280, 3), dtype=np.uint8)

        result = vconcat_resize(img1, img2)

        # Should resize to match narrower width (640)
        assert result.shape[1] == 640



class TestHconcatResize:
    def test_same_height(self, image_480x640):
        img1 = image_480x640.copy()
        img2 = image_480x640.copy()

        result = hconcat_resize(img1, img2)

        assert result.shape[0] == 480
        assert result.shape[1] == 1280  # 640 + 640

    def test_different_heights(self):
        img1 = np.zeros((480, 640, 3), dtype=np.uint8)
        img2 = np.zeros((720, 640, 3), dtype=np.uint8)

        result = hconcat_resize(img1, img2)

        # Should resize to match shorter height (480)
        assert result.shape[0] == 480



class TestCreatePlaceholder:
    def test_creates_black_image(self):
        result = create_placeholder(480, 640)

        assert result.shape == (480, 640, 3)
        assert np.all(result == 0)

    def test_custom_channels(self):
        result = create_placeholder(480, 640, channels=1)

        assert result.shape == (480, 640, 1)

    def test_dtype(self):
        result = create_placeholder(100, 100)

        assert result.dtype == np.uint8


class TestBuildLayoutFromConfig:
    def test_simple_horizontal(self):
        config = LayoutNodeConfig(
            direction="horizontal",
            children=[
                LayoutNodeConfig(camera="cam1"),
                LayoutNodeConfig(camera="cam2"),
            ],
        )
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}
        target_sizes = {}

        root = build_layout_from_config(config, camera_sizes, target_sizes)

        assert root.direction == Direction.HORIZONTAL
        assert root.left.camera == "cam1"
        assert root.right.camera == "cam2"
        assert "cam1" in target_sizes
        assert "cam2" in target_sizes

    def test_nested_vertical_in_horizontal(self):
        config = LayoutNodeConfig(
            direction="horizontal",
            children=[
                LayoutNodeConfig(
                    direction="vertical",
                    children=[
                        LayoutNodeConfig(camera="cam1"),
                        LayoutNodeConfig(camera="cam2"),
                    ],
                ),
                LayoutNodeConfig(camera="cam3"),
            ],
        )
        camera_sizes = {
            "cam1": (240, 320),
            "cam2": (240, 320),
            "cam3": (480, 320),
        }
        target_sizes = {}

        root = build_layout_from_config(config, camera_sizes, target_sizes)

        assert root.direction == Direction.HORIZONTAL
        assert root.left.direction == Direction.VERTICAL
        assert root.right.camera == "cam3"

    def test_weighted_children(self):
        config = LayoutNodeConfig(
            direction="horizontal",
            children=[
                LayoutNodeConfig(camera="cam1", weight=0.4),
                LayoutNodeConfig(camera="cam2", weight=0.6),
            ],
        )
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}
        target_sizes = {}

        root = build_layout_from_config(config, camera_sizes, target_sizes)

        # cam2 should be wider than cam1 due to 60/40 weight split
        cam1_w = target_sizes["cam1"][1]
        cam2_w = target_sizes["cam2"][1]
        assert cam2_w > cam1_w

    def test_unknown_camera_gets_default_size(self):
        config = LayoutNodeConfig(
            direction="horizontal",
            children=[
                LayoutNodeConfig(camera="unknown1"),
                LayoutNodeConfig(camera="unknown2"),
            ],
        )
        target_sizes = {}
        root = build_layout_from_config(config, {}, target_sizes)

        assert target_sizes["unknown1"] == (480, 640)


class TestLayoutManager:
    def test_initialization(self):
        layout_configs = {
            "main": LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
        }
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}

        manager = LayoutManager(camera_sizes, layout_configs, active_layout="main")

        assert manager.num_layouts == 1
        assert manager.active_layout_index == 0

    def test_get_target_size(self):
        layout_configs = {
            "main": LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
        }
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}
        manager = LayoutManager(camera_sizes, layout_configs)

        size = manager.get_target_size("cam1", tree_index=0)
        assert size == (480, 640)

    def test_get_target_size_unknown_camera(self):
        layout_configs = {
            "main": LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
        }
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}
        manager = LayoutManager(camera_sizes, layout_configs)

        size = manager.get_target_size("unknown", tree_index=0)
        assert size == (480, 640)  # default

    def test_multi_layout(self):
        layout_configs = {
            "main": LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
            "alt": LayoutNodeConfig(
                direction="vertical",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
        }
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}

        manager = LayoutManager(camera_sizes, layout_configs, active_layout="alt")

        assert manager.num_layouts == 2

    def test_concatenate(self):
        layout_configs = {
            "main": LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="cam1"),
                    LayoutNodeConfig(camera="cam2"),
                ],
            ),
        }
        camera_sizes = {"cam1": (480, 640), "cam2": (480, 640)}
        manager = LayoutManager(camera_sizes, layout_configs)

        def get_image(name):
            return np.zeros((480, 640, 3), dtype=np.uint8)

        result = manager.concatenate(get_image, tree_index=0)
        assert result.shape == (480, 1280, 3)
