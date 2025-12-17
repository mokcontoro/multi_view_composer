"""Tests for generator module."""

import pytest
import numpy as np

from multi_view_composer import (
    MultiViewComposer,
    CameraConfig,
    ViewerConfig,
    LayoutNodeConfig,
)


def create_test_config(num_layouts: int = 1) -> ViewerConfig:
    """Create a test configuration with layouts."""
    # Create a simple horizontal layout
    horizontal_layout = LayoutNodeConfig(
        direction="horizontal",
        children=[
            LayoutNodeConfig(camera="ee_cam"),
            LayoutNodeConfig(camera="ifm_camera1"),
            LayoutNodeConfig(camera="ifm_camera2"),
            LayoutNodeConfig(
                direction="horizontal",
                children=[
                    LayoutNodeConfig(camera="front_monitor_cam"),
                    LayoutNodeConfig(camera="back_monitor_cam"),
                ]
            ),
        ]
    )

    layouts = {"horizontal": horizontal_layout}

    # Add vertical layout if requested
    if num_layouts > 1:
        vertical_layout = LayoutNodeConfig(
            direction="vertical",
            children=[
                LayoutNodeConfig(camera="ee_cam"),
                LayoutNodeConfig(camera="ifm_camera2"),
            ]
        )
        layouts["vertical"] = vertical_layout

    return ViewerConfig(
        resolutions={
            "ee_cam": [480, 848, 3],
            "ifm": [800, 1280, 3],
            "monitor_cam": [720, 1280, 3],
            "recovery_cam": [530, 848, 3],
        },
        hardware={
            "old_elbow_cam": True,
            "camera_mount": "D",
        },
        layouts=layouts,
        active_layout="horizontal",
    )


@pytest.fixture
def default_config():
    """Create default configuration."""
    return create_test_config(num_layouts=1)


@pytest.fixture
def composer(default_config):
    """Create a composer instance."""
    comp = MultiViewComposer(default_config)
    yield comp
    comp.shutdown()


@pytest.fixture
def sample_image():
    """Create a sample camera image."""
    return np.random.randint(0, 255, (480, 848, 3), dtype=np.uint8)


class TestMultiViewComposerInit:
    def test_initializes_with_config(self):
        config = create_test_config(num_layouts=1)
        comp = MultiViewComposer(config)

        assert comp is not None
        assert comp.num_layouts == 1
        comp.shutdown()

    def test_multi_layout_mode(self):
        config = create_test_config(num_layouts=2)
        comp = MultiViewComposer(config)

        assert comp.num_layouts == 2
        comp.shutdown()

    def test_initializes_only_used_cameras(self, composer):
        """Only cameras referenced in layout should be initialized."""
        cameras = composer.get_camera_names()

        # These are in the layout
        assert "ee_cam" in cameras
        assert "ifm_camera1" in cameras
        assert "ifm_camera2" in cameras
        assert "front_monitor_cam" in cameras
        assert "back_monitor_cam" in cameras

        # These are NOT in the layout (should be filtered out)
        assert "A1_cam1" not in cameras
        assert "A1_cam2" not in cameras
        assert "boxwall_monitor_cam" not in cameras

    def test_raises_error_without_layouts(self):
        """Should raise error if no layouts defined."""
        config = ViewerConfig(
            resolutions={"ee_cam": [480, 848, 3]},
            hardware={},
            layouts={},  # Empty layouts
        )
        with pytest.raises(ValueError, match="No layouts defined"):
            MultiViewComposer(config)


class TestUpdateCameraImage:
    def test_updates_existing_camera(self, composer, sample_image):
        result = composer.update_camera_image("ee_cam", sample_image, active=True)

        assert result is True
        cam = composer.get_camera_config("ee_cam")
        assert cam.active is True
        assert cam.raw_image is not None

    def test_rejects_unknown_camera(self, composer, sample_image):
        result = composer.update_camera_image("unknown_camera", sample_image)

        assert result is False

    def test_sets_inactive(self, composer, sample_image):
        composer.update_camera_image("ee_cam", sample_image, active=False)

        cam = composer.get_camera_config("ee_cam")
        assert cam.active is False


class TestUpdateDynamicData:
    def test_updates_laser_distance(self, composer):
        composer.update_dynamic_data(laser_distance=42.0)

        assert composer.sensor_data.laser_distance == 42.0

    def test_updates_robot_status(self, composer):
        composer.update_dynamic_data(robot_status="NAVIGATING")

        assert composer.sensor_data.robot_status == "NAVIGATING"

    def test_updates_multiple_values(self, composer):
        composer.update_dynamic_data(
            laser_distance=35.0,
            laser_active=False,
            pressure_manifold=0.8,
            robot_status="SCANNING"
        )

        assert composer.sensor_data.laser_distance == 35.0
        assert composer.sensor_data.laser_active is False
        assert composer.sensor_data.pressure_manifold == 0.8
        assert composer.sensor_data.robot_status == "SCANNING"


class TestGenerateFrame:
    def test_generates_single_frame(self, composer, sample_image):
        # Set up some camera images
        composer.update_camera_image("ee_cam", sample_image, active=True)

        frames = composer.generate_frame()

        assert len(frames) == 1
        assert frames[0] is not None
        assert len(frames[0].shape) == 3

    def test_generates_two_frames_multi_layout(self, sample_image):
        config = create_test_config(num_layouts=2)
        comp = MultiViewComposer(config)

        comp.update_camera_image("ee_cam", sample_image, active=True)
        frames = comp.generate_frame()

        assert len(frames) == 2
        comp.shutdown()

    def test_handles_no_active_cameras(self, composer):
        # Don't set any camera images
        frames = composer.generate_frame()

        # Should still return frames (with placeholders)
        assert len(frames) == 1
        assert frames[0] is not None


class TestGetCameraConfig:
    def test_returns_config_for_existing_camera(self, composer):
        config = composer.get_camera_config("ee_cam")

        assert config is not None
        assert isinstance(config, CameraConfig)
        assert config.name == "ee_cam"

    def test_returns_none_for_unknown_camera(self, composer):
        config = composer.get_camera_config("unknown_camera")

        assert config is None


class TestShutdown:
    def test_shutdown_completes(self):
        config = create_test_config()
        comp = MultiViewComposer(config)
        comp.shutdown()

        # Should not raise any exceptions
        assert True
