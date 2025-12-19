"""Tests for layout module."""

import pytest
import numpy as np

from multi_view_composer import (
    vconcat_resize,
    hconcat_resize,
    create_placeholder,
)


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

    def test_preserves_channels(self, image_480x640):
        img1 = image_480x640.copy()
        img2 = image_480x640.copy()

        result = vconcat_resize(img1, img2)

        assert result.shape[2] == 3


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

    def test_preserves_channels(self, image_480x640):
        img1 = image_480x640.copy()
        img2 = image_480x640.copy()

        result = hconcat_resize(img1, img2)

        assert result.shape[2] == 3


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
