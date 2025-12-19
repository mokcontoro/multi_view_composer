"""Configuration dataclasses and YAML loader for multi-view composer."""

from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union

from .logging_config import get_logger


logger = get_logger("config")


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


@dataclass
class CameraDefinition:
    """Definition of a camera from config."""
    name: str
    resolution: Tuple[int, int]  # (height, width)
    rotate: Optional[int] = None  # 90, 180, 270, or None
    centermark: bool = False

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> CameraDefinition:
        res = data.get("resolution", [480, 640])
        return cls(
            name=name,
            resolution=(res[0], res[1]),
            rotate=data.get("rotate"),
            centermark=data.get("centermark", False),
        )


@dataclass
class OverlayStyle:
    """Style configuration for text overlays."""
    font: str = "HERSHEY_SIMPLEX"
    font_scale: float = 0.8
    thickness: int = 2
    box_height: int = 40
    padding_left: int = 5
    padding_top: int = 30
    background_color: Tuple[int, int, int] = (0, 0, 0)

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> OverlayStyle:
        if data is None:
            return cls()
        return cls(
            font=data.get("font", "HERSHEY_SIMPLEX"),
            font_scale=data.get("font_scale", 0.8),
            thickness=data.get("thickness", 2),
            box_height=data.get("box_height", 40),
            padding_left=data.get("padding_left", 5),
            padding_top=data.get("padding_top", 30),
            background_color=tuple(data.get("background_color", [0, 0, 0])),
        )


@dataclass
class ColorRule:
    """A conditional color rule."""
    color: Tuple[int, int, int]
    when: Optional[str] = None  # condition expression, None means 'else'

    @classmethod
    def from_dict(cls, data: Dict) -> ColorRule:
        color = tuple(data.get("color", data.get("else", [255, 255, 255])))
        when = data.get("when")
        return cls(color=color, when=when)


@dataclass
class VariableCondition:
    """A single condition for conditional variables."""
    when: Optional[str]  # None means 'else'
    value: Optional[str] = None
    format: Optional[str] = None


@dataclass
class VariableConfig:
    """Configuration for a computed variable."""
    type: str  # "direct", "formula", "conditional"
    expr: Optional[str] = None  # for formula type
    conditions: List[VariableCondition] = field(default_factory=list)  # for conditional type

    @classmethod
    def from_dict(cls, data: Union[Dict, str]) -> VariableConfig:
        if isinstance(data, str):
            # Simple string = direct reference
            return cls(type="direct", expr=data)

        var_type = data.get("type", "direct")
        expr = data.get("expr")
        conditions = []

        if "conditions" in data:
            for cond in data["conditions"]:
                if "else" in cond:
                    conditions.append(VariableCondition(
                        when=None,
                        value=cond.get("else") if isinstance(cond.get("else"), str) else None,
                        format=cond.get("format")
                    ))
                else:
                    conditions.append(VariableCondition(
                        when=cond.get("when"),
                        value=cond.get("value"),
                        format=cond.get("format")
                    ))

        return cls(type=var_type, expr=expr, conditions=conditions)


@dataclass
class TextOverlayConfig:
    """Configuration for a single text overlay."""
    id: str
    template: str
    cameras: List[str]
    variables: Dict[str, VariableConfig] = field(default_factory=dict)
    color_rules: List[ColorRule] = field(default_factory=list)
    color: Optional[Tuple[int, int, int]] = None  # static color
    style: Optional[OverlayStyle] = None  # per-overlay style override
    visible_when: Optional[str] = None  # visibility condition

    @classmethod
    def from_dict(cls, data: Dict) -> TextOverlayConfig:
        variables = {}
        if "variables" in data:
            for name, var_data in data["variables"].items():
                variables[name] = VariableConfig.from_dict(var_data)

        color_rules = []
        if "color_rules" in data:
            for rule_data in data["color_rules"]:
                color_rules.append(ColorRule.from_dict(rule_data))

        static_color = None
        if "color" in data:
            static_color = tuple(data["color"])

        style = None
        if "style" in data:
            style = OverlayStyle.from_dict(data["style"])

        return cls(
            id=data["id"],
            template=data["template"],
            cameras=data.get("cameras", []),
            variables=variables,
            color_rules=color_rules,
            color=static_color,
            style=style,
            visible_when=data.get("visible_when"),
        )


@dataclass
class CentermarkConfig:
    """Configuration for centermark overlay."""
    enabled: bool = True
    size_ratio: float = 0.025
    thickness: int = 4
    color: Tuple[int, int, int] = (255, 0, 255)

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> CentermarkConfig:
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", True),
            size_ratio=data.get("size_ratio", 0.025),
            thickness=data.get("thickness", 4),
            color=tuple(data.get("color", [255, 0, 255])),
        )


@dataclass
class BorderConfig:
    """Configuration for border overlay."""
    enabled: bool = True
    thickness: int = 1
    color: Tuple[int, int, int] = (255, 255, 255)

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> BorderConfig:
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", True),
            thickness=data.get("thickness", 1),
            color=tuple(data.get("color", [255, 255, 255])),
        )


@dataclass
class LayoutNodeConfig:
    """Configuration for a layout tree node."""
    direction: Optional[str] = None  # "horizontal" or "vertical"
    camera: Optional[str] = None  # camera name for leaf nodes
    children: List[LayoutNodeConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> LayoutNodeConfig:
        if "camera" in data:
            return cls(camera=data["camera"])

        children = []
        if "children" in data:
            for child in data["children"]:
                children.append(cls.from_dict(child))

        return cls(
            direction=data.get("direction"),
            children=children,
        )


@dataclass
class ViewerConfig:
    """Main configuration for the multi-view composer."""
    # Camera definitions
    cameras: Dict[str, CameraDefinition] = field(default_factory=dict)

    # Overlay configuration
    default_overlay_style: OverlayStyle = field(default_factory=OverlayStyle)
    text_overlays: List[TextOverlayConfig] = field(default_factory=list)
    centermark: CentermarkConfig = field(default_factory=CentermarkConfig)
    border: BorderConfig = field(default_factory=BorderConfig)

    # Layout configuration
    layouts: Dict[str, LayoutNodeConfig] = field(default_factory=dict)
    active_layout: str = "main"

    @classmethod
    def from_dict(cls, data: Dict) -> ViewerConfig:
        # Parse cameras
        cameras = {}
        if "cameras" in data:
            for name, cam_data in data["cameras"].items():
                cameras[name] = CameraDefinition.from_dict(name, cam_data)

        # Parse text overlays
        text_overlays = []
        if "text_overlays" in data:
            for overlay_data in data["text_overlays"]:
                text_overlays.append(TextOverlayConfig.from_dict(overlay_data))

        # Parse layouts
        layouts = {}
        if "layouts" in data:
            for name, layout_data in data["layouts"].items():
                layouts[name] = LayoutNodeConfig.from_dict(layout_data)

        return cls(
            cameras=cameras,
            default_overlay_style=OverlayStyle.from_dict(data.get("default_overlay_style")),
            text_overlays=text_overlays,
            centermark=CentermarkConfig.from_dict(data.get("centermark")),
            border=BorderConfig.from_dict(data.get("border")),
            layouts=layouts,
            active_layout=data.get("active_layout", "main"),
        )


def load_config(config_path: str) -> ViewerConfig:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        ViewerConfig object with parsed configuration.

    Raises:
        ConfigError: If file doesn't exist, YAML is invalid, or required fields are missing.
    """
    # Check file exists
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found: {config_path}")

    # Load and parse YAML
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")

    # Validate data is a dictionary
    if data is None:
        raise ConfigError(f"Configuration file is empty: {config_path}")
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration must be a YAML mapping, got {type(data).__name__}")

    # Validate required field: layouts
    if "layouts" not in data or not data["layouts"]:
        raise ConfigError("Configuration must define at least one layout in 'layouts'")

    # Validate layouts structure
    for layout_name, layout_data in data["layouts"].items():
        _validate_layout_node(layout_name, layout_data, path=f"layouts.{layout_name}")

    # Validate active_layout references an existing layout
    active_layout = data.get("active_layout", "main")
    if active_layout not in data["layouts"]:
        available = ", ".join(data["layouts"].keys())
        raise ConfigError(
            f"active_layout '{active_layout}' not found. Available layouts: {available}"
        )

    # Validate text_overlays if present
    if "text_overlays" in data:
        for i, overlay in enumerate(data["text_overlays"]):
            _validate_text_overlay(overlay, path=f"text_overlays[{i}]")

    config = ViewerConfig.from_dict(data)
    logger.info(f"Loaded config from {config_path}: {len(config.layouts)} layout(s), "
                f"{len(config.cameras)} camera(s), {len(config.text_overlays)} overlay(s)")
    return config


def _validate_layout_node(name: str, data: Dict, path: str) -> None:
    """Validate a layout node structure."""
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: layout node must be a mapping")

    if "camera" in data:
        # Leaf node - just needs camera name
        if not isinstance(data["camera"], str):
            raise ConfigError(f"{path}.camera: must be a string")
    else:
        # Junction node - needs direction and children
        if "direction" not in data:
            raise ConfigError(f"{path}: junction node must have 'direction' (horizontal or vertical)")

        direction = data["direction"]
        if direction not in ("horizontal", "vertical"):
            raise ConfigError(f"{path}.direction: must be 'horizontal' or 'vertical', got '{direction}'")

        if "children" not in data or not data["children"]:
            raise ConfigError(f"{path}: junction node must have 'children' list")

        if len(data["children"]) < 2:
            raise ConfigError(f"{path}.children: must have at least 2 children")

        for i, child in enumerate(data["children"]):
            _validate_layout_node(name, child, path=f"{path}.children[{i}]")


def _validate_text_overlay(data: Dict, path: str) -> None:
    """Validate a text overlay configuration."""
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: text overlay must be a mapping")

    if "id" not in data:
        raise ConfigError(f"{path}: text overlay must have 'id'")

    if "template" not in data:
        raise ConfigError(f"{path}: text overlay must have 'template'")
