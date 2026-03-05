"""Tests for config module validation."""

import pytest

from multi_view_composer import load_config, ConfigError
from multi_view_composer.config import (
    TitleConfig,
    LayoutNodeConfig,
    ColorRule,
    VariableConfig,
)


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


class TestTitleConfigParsing:
    def test_string_form(self):
        title = TitleConfig.from_dict("My Camera")
        assert title.text == "My Camera"
        assert title.opacity == 0.5  # default

    def test_dict_form_with_opacity(self):
        title = TitleConfig.from_dict({"text": "My Camera", "opacity": 0.8})
        assert title.text == "My Camera"
        assert title.opacity == 0.8

    def test_none_returns_none(self):
        assert TitleConfig.from_dict(None) is None

    def test_title_in_config(self, tmp_path):
        config_file = tmp_path / "title.yaml"
        config_file.write_text("""
cameras:
  cam1:
    resolution: [480, 640]
    title:
      text: "Camera 1"
      opacity: 0.7
  cam2:
    resolution: [480, 640]
    title: "Camera 2"
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
""")
        config = load_config(str(config_file))
        assert config.cameras["cam1"].title.text == "Camera 1"
        assert config.cameras["cam1"].title.opacity == 0.7
        assert config.cameras["cam2"].title.text == "Camera 2"
        assert config.cameras["cam2"].title.opacity == 0.5


class TestWeightParsing:
    def test_weight_field(self):
        node = LayoutNodeConfig.from_dict({"camera": "cam1", "weight": 0.6})
        assert node.camera == "cam1"
        assert node.weight == 0.6

    def test_no_weight_defaults_to_none(self):
        node = LayoutNodeConfig.from_dict({"camera": "cam1"})
        assert node.weight is None

    def test_weights_in_config(self, tmp_path):
        config_file = tmp_path / "weights.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
        weight: 0.4
      - camera: cam2
        weight: 0.6
""")
        config = load_config(str(config_file))
        children = config.layouts["main"].children
        assert children[0].weight == 0.4
        assert children[1].weight == 0.6


class TestColorRuleParsing:
    def test_when_clause(self):
        rule = ColorRule.from_dict({"when": "{level} >= 70", "color": [0, 255, 0]})
        assert rule.when == "{level} >= 70"
        assert rule.color == (0, 255, 0)

    def test_else_clause(self):
        rule = ColorRule.from_dict({"else": [0, 0, 255]})
        assert rule.when is None
        assert rule.color == (0, 0, 255)

    def test_color_rules_in_config(self, tmp_path):
        config_file = tmp_path / "color_rules.yaml"
        config_file.write_text("""
layouts:
  main:
    direction: horizontal
    children:
      - camera: cam1
      - camera: cam2
text_overlays:
  - id: level
    template: "Level: {level}"
    cameras: [cam1]
    color_rules:
      - when: "{level} >= 70"
        color: [0, 255, 0]
      - else: [0, 0, 255]
""")
        config = load_config(str(config_file))
        rules = config.text_overlays[0].color_rules
        assert len(rules) == 2
        assert rules[0].when == "{level} >= 70"
        assert rules[1].when is None


class TestVariableParsing:
    def test_formula_type(self):
        var = VariableConfig.from_dict({
            "type": "formula",
            "expr": "{speed} * 3.6",
        })
        assert var.type == "formula"
        assert var.expr == "{speed} * 3.6"

    def test_conditional_type(self):
        var = VariableConfig.from_dict({
            "type": "conditional",
            "conditions": [
                {"when": "{mode} == 'auto'", "value": "AUTO"},
                {"else": "STANDBY"},
            ],
        })
        assert var.type == "conditional"
        assert len(var.conditions) == 2
        assert var.conditions[0].when == "{mode} == 'auto'"
        assert var.conditions[0].value == "AUTO"
        assert var.conditions[1].when is None
        assert var.conditions[1].value == "STANDBY"

    def test_direct_string_shorthand(self):
        var = VariableConfig.from_dict("{temperature}")
        assert var.type == "direct"
        assert var.expr == "{temperature}"

    def test_direct_dict_form(self):
        var = VariableConfig.from_dict({"type": "direct", "expr": "{val}"})
        assert var.type == "direct"
        assert var.expr == "{val}"
