"""Tests for overlays module."""

import pytest
import numpy as np

from multi_view_composer import SensorData, draw_centermark, draw_border
from multi_view_composer.config import CentermarkConfig, BorderConfig


@pytest.fixture
def sample_image():
    """Create a sample 480x640 BGR image."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sensor_data():
    """Create sample sensor data."""
    data = SensorData()
    data.set("temperature", 25.0)
    data.set("level", 75)
    data.set("active", True)
    return data


class TestSensorData:
    def test_default_values(self):
        data = SensorData()
        d = data.to_dict()

        # Default predefined values
        assert d["laser_distance"] == 35.0
        assert d["laser_active"] is True

    def test_set_custom_value(self):
        data = SensorData()
        data.set("temperature", 30.0)
        data.set("mode", "auto")

        d = data.to_dict()
        assert d["temperature"] == 30.0
        assert d["mode"] == "auto"

    def test_cache_key_includes_custom(self):
        data1 = SensorData()
        data2 = SensorData()

        data1.set("temp", 25.0)
        data2.set("temp", 30.0)

        assert data1.cache_key() != data2.cache_key()


class TestDrawCentermark:
    def test_draws_crosshair(self, sample_image):
        config = CentermarkConfig(enabled=True)
        img = sample_image.copy()
        draw_centermark(img, config)

        # Check that some pixels are non-zero (crosshair was drawn)
        assert np.any(img > 0)

    def test_disabled_does_nothing(self, sample_image):
        config = CentermarkConfig(enabled=False)
        img = sample_image.copy()
        draw_centermark(img, config)

        assert not np.any(img > 0)

    def test_center_position(self, sample_image):
        config = CentermarkConfig(enabled=True, color=(255, 0, 255))
        img = sample_image.copy()
        draw_centermark(img, config)

        h, w = img.shape[:2]
        cx, cy = w // 2, h // 2

        # Check center pixel has the crosshair color
        assert img[cy, cx, 0] == 255  # Blue channel
        assert img[cy, cx, 2] == 255  # Red channel


class TestDrawBorder:
    def test_draws_border(self, sample_image):
        config = BorderConfig(enabled=True, color=(255, 255, 255))
        img = sample_image.copy()
        draw_border(img, config)

        h, w = img.shape[:2]
        # Check corners have border color
        assert np.all(img[0, 0] == 255)
        assert np.all(img[0, w - 1] == 255)
        assert np.all(img[h - 1, 0] == 255)

    def test_disabled_does_nothing(self, sample_image):
        config = BorderConfig(enabled=False)
        img = sample_image.copy()
        draw_border(img, config)

        assert not np.any(img > 0)
