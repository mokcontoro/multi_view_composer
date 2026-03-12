"""Tests for camera module."""

import cv2

from multi_view_composer.camera import CameraConfig, create_camera_configs, ROTATION_MAP
from multi_view_composer.config import CameraDefinition, TitleConfig


class TestCameraConfig:
    def test_rotation_map_values(self):
        assert ROTATION_MAP[90] == cv2.ROTATE_90_CLOCKWISE
        assert ROTATION_MAP[180] == cv2.ROTATE_180
        assert ROTATION_MAP[270] == cv2.ROTATE_90_COUNTERCLOCKWISE
        assert ROTATION_MAP[-90] == cv2.ROTATE_90_COUNTERCLOCKWISE

    def test_get_effective_resolution_no_rotation(self):
        config = CameraConfig(
            name="cam1",
            resolution=(480, 640, 3),
            rotate=None,
            centermark=False,
        )
        assert config.get_effective_resolution() == (480, 640, 3)

    def test_get_effective_resolution_90(self):
        config = CameraConfig(
            name="cam1",
            resolution=(480, 640, 3),
            rotate=cv2.ROTATE_90_CLOCKWISE,
            centermark=False,
        )
        # 90 degree rotation swaps height and width
        assert config.get_effective_resolution() == (640, 480, 3)

    def test_get_effective_resolution_180(self):
        config = CameraConfig(
            name="cam1",
            resolution=(480, 640, 3),
            rotate=cv2.ROTATE_180,
            centermark=False,
        )
        # 180 does not swap dimensions
        assert config.get_effective_resolution() == (480, 640, 3)

    def test_get_effective_resolution_270(self):
        config = CameraConfig(
            name="cam1",
            resolution=(480, 640, 3),
            rotate=cv2.ROTATE_90_COUNTERCLOCKWISE,
            centermark=False,
        )
        assert config.get_effective_resolution() == (640, 480, 3)


class TestCreateCameraConfigs:
    def test_creates_configs_from_definitions(self):
        definitions = {
            "cam1": CameraDefinition(name="cam1", resolution=(480, 640)),
            "cam2": CameraDefinition(name="cam2", resolution=(720, 1280)),
        }
        configs = create_camera_configs(definitions, num_layouts=1)

        assert "cam1" in configs
        assert "cam2" in configs
        assert configs["cam1"].resolution == (480, 640, 3)
        assert configs["cam2"].resolution == (720, 1280, 3)

    def test_applies_rotation(self):
        definitions = {
            "cam1": CameraDefinition(name="cam1", resolution=(480, 640), rotate=90),
        }
        configs = create_camera_configs(definitions, num_layouts=1)

        assert configs["cam1"].rotate == cv2.ROTATE_90_CLOCKWISE

    def test_no_rotation(self):
        definitions = {
            "cam1": CameraDefinition(name="cam1", resolution=(480, 640)),
        }
        configs = create_camera_configs(definitions, num_layouts=1)

        assert configs["cam1"].rotate is None

    def test_applies_title_config(self):
        definitions = {
            "cam1": CameraDefinition(
                name="cam1",
                resolution=(480, 640),
                title=TitleConfig(text="My Camera", opacity=0.7),
            ),
        }
        configs = create_camera_configs(definitions, num_layouts=1)

        assert configs["cam1"].title.text == "My Camera"
        assert configs["cam1"].title.opacity == 0.7

    def test_multi_layout_target_sizes(self):
        definitions = {
            "cam1": CameraDefinition(name="cam1", resolution=(480, 640)),
        }
        configs = create_camera_configs(definitions, num_layouts=3)

        assert len(configs["cam1"].target_sizes) == 3
        assert len(configs["cam1"].processed_images) == 3

    def test_centermark_flag(self):
        definitions = {
            "cam1": CameraDefinition(
                name="cam1", resolution=(480, 640), centermark=True
            ),
            "cam2": CameraDefinition(
                name="cam2", resolution=(480, 640), centermark=False
            ),
        }
        configs = create_camera_configs(definitions, num_layouts=1)

        assert configs["cam1"].centermark is True
        assert configs["cam2"].centermark is False
