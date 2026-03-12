"""Tests for overlays module."""

import pytest
import numpy as np

from multi_view_composer import draw_centermark, draw_border, draw_camera_title
from multi_view_composer.overlays import draw_text_overlay
from multi_view_composer.config import (
    CentermarkConfig,
    BorderConfig,
    TitleConfig,
    OverlayStyle,
    TextOverlayConfig,
    ColorRule,
)


@pytest.fixture
def sample_image():
    """Create a sample 480x640 BGR image."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


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


class TestDrawCameraTitle:
    def test_renders_title_text(self, sample_image):
        title = TitleConfig(text="Test Camera")
        style = OverlayStyle()
        img = sample_image.copy()

        draw_camera_title(img, title, style)

        # Some pixels should be non-zero (text + background drawn)
        assert np.any(img > 0)

    def test_respects_opacity(self, sample_image):
        style = OverlayStyle()

        # High opacity => darker background blend
        img_high = sample_image.copy()
        img_high[:] = 128  # mid-gray base
        draw_camera_title(img_high, TitleConfig(text="Hi", opacity=0.9), style)

        # Low opacity => lighter background blend
        img_low = sample_image.copy()
        img_low[:] = 128
        draw_camera_title(img_low, TitleConfig(text="Hi", opacity=0.1), style)

        # The images should differ due to different opacity blending
        assert not np.array_equal(img_high, img_low)

    def test_no_title_does_nothing(self, sample_image):
        style = OverlayStyle()
        img = sample_image.copy()

        draw_camera_title(img, None, style)

        assert not np.any(img > 0)

    def test_empty_text_does_nothing(self, sample_image):
        style = OverlayStyle()
        img = sample_image.copy()

        draw_camera_title(img, TitleConfig(text=""), style)

        assert not np.any(img > 0)


class TestDrawTextOverlay:
    def test_renders_text_with_variables(self, sample_image):
        overlay = TextOverlayConfig(
            id="temp",
            template="Temp: {temperature}C",
            cameras=["cam1"],
            color=(255, 255, 255),
        )
        img = sample_image.copy()

        draw_text_overlay(img, overlay, {"temperature": 25.0}, OverlayStyle())

        assert np.any(img > 0)

    def test_applies_color_rules(self, sample_image):
        overlay = TextOverlayConfig(
            id="level",
            template="Level: {level}%",
            cameras=["cam1"],
            color_rules=[
                ColorRule(color=(0, 255, 0), when="{level} >= 70"),
                ColorRule(color=(0, 0, 255), when=None),
            ],
        )
        img = sample_image.copy()

        draw_text_overlay(img, overlay, {"level": 80}, OverlayStyle())

        # Green text should be drawn (level=80 >= 70)
        assert np.any(img[:, :, 1] > 0)  # green channel

    def test_respects_visible_when_false(self, sample_image):
        overlay = TextOverlayConfig(
            id="warn",
            template="WARNING",
            cameras=["cam1"],
            color=(255, 255, 255),
            visible_when="{show} == true",
        )
        img = sample_image.copy()

        draw_text_overlay(img, overlay, {"show": False}, OverlayStyle())

        assert not np.any(img > 0)

    def test_respects_visible_when_true(self, sample_image):
        overlay = TextOverlayConfig(
            id="warn",
            template="WARNING",
            cameras=["cam1"],
            color=(255, 255, 255),
            visible_when="{show} == true",
        )
        img = sample_image.copy()

        draw_text_overlay(img, overlay, {"show": True}, OverlayStyle())

        assert np.any(img > 0)
