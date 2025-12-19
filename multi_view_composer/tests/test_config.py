"""Tests for config module validation."""

import pytest
import tempfile
import os

from multi_view_composer import load_config, ConfigError


class TestLoadConfigValidation:
    def test_file_not_found(self):
        with pytest.raises(ConfigError, match="Configuration file not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_empty_file(self, tmp_path):
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ConfigError, match="Configuration file is empty"):
            load_config(str(config_file))

    def test_invalid_yaml(self, tmp_path):
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(str(config_file))

    def test_not_a_mapping(self, tmp_path):
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- item1\n- item2")

        with pytest.raises(ConfigError, match="must be a YAML mapping"):
            load_config(str(config_file))

    def test_missing_layouts(self, tmp_path):
        config_file = tmp_path / "no_layouts.yaml"
        config_file.write_text("cameras:\n  cam1:\n    resolution: [480, 640]")

        with pytest.raises(ConfigError, match="must define at least one layout"):
            load_config(str(config_file))

    def test_empty_layouts(self, tmp_path):
        config_file = tmp_path / "empty_layouts.yaml"
        config_file.write_text("layouts: {}")

        with pytest.raises(ConfigError, match="must define at least one layout"):
            load_config(str(config_file))

    def test_invalid_active_layout(self, tmp_path):
        config_file = tmp_path / "bad_active.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
active_layout: nonexistent
""")
        with pytest.raises(ConfigError, match="active_layout 'nonexistent' not found"):
            load_config(str(config_file))


class TestLayoutNodeValidation:
    def test_missing_direction(self, tmp_path):
        config_file = tmp_path / "no_direction.yaml"
        config_file.write_text("""
layouts:
  main:
    children:
      - camera: cam1
      - camera: cam2
""")
        with pytest.raises(ConfigError, match="must have 'direction'"):
            load_config(str(config_file))

    def test_invalid_direction(self, tmp_path):
        config_file = tmp_path / "bad_direction.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: diagonal
    children:
      - camera: cam1
      - camera: cam2
""")
        with pytest.raises(ConfigError, match="must be 'horizontal' or 'vertical'"):
            load_config(str(config_file))

    def test_missing_children(self, tmp_path):
        config_file = tmp_path / "no_children.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
""")
        with pytest.raises(ConfigError, match="must have 'children' list"):
            load_config(str(config_file))

    def test_too_few_children(self, tmp_path):
        config_file = tmp_path / "one_child.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
""")
        with pytest.raises(ConfigError, match="must have at least 2 children"):
            load_config(str(config_file))

    def test_nested_validation(self, tmp_path):
        config_file = tmp_path / "nested_invalid.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - direction: vertical
        children:
          - camera: cam1
      - camera: cam2
""")
        with pytest.raises(ConfigError, match="must have at least 2 children"):
            load_config(str(config_file))


class TestTextOverlayValidation:
    def test_missing_id(self, tmp_path):
        config_file = tmp_path / "no_id.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
text_overlays:
  - template: "Hello"
""")
        with pytest.raises(ConfigError, match="must have 'id'"):
            load_config(str(config_file))

    def test_missing_template(self, tmp_path):
        config_file = tmp_path / "no_template.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
text_overlays:
  - id: overlay1
""")
        with pytest.raises(ConfigError, match="must have 'template'"):
            load_config(str(config_file))


class TestValidConfigLoading:
    def test_minimal_valid_config(self, tmp_path):
        config_file = tmp_path / "valid.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
""")
        config = load_config(str(config_file))
        assert "main" in config.layouts

    def test_full_valid_config(self, tmp_path):
        config_file = tmp_path / "full.yaml"
        config_file.write_text("""
cameras:
  cam1:
    resolution: [480, 640]
  cam2:
    resolution: [480, 640]

layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
  vertical:
    direction: vertical
    children:
      - camera: cam1
      - camera: cam2

active_layout: main

text_overlays:
  - id: status
    template: "Status: {status}"
    cameras: [cam1]

centermark:
  enabled: true
  color: [255, 0, 0]
""")
        config = load_config(str(config_file))
        assert len(config.cameras) == 2
        assert len(config.layouts) == 2
        assert len(config.text_overlays) == 1
        assert config.active_layout == "main"
