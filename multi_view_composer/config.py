"""Configuration dataclasses and YAML loader for teleop viewer."""

from __future__ import annotations
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union


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
    """Main configuration for the teleop viewer."""
    # Camera hardware settings
    resolutions: Dict[str, List[int]] = field(default_factory=dict)
    hardware: Dict[str, Any] = field(default_factory=dict)

    # Application settings
    input_directory: str = "./sample_images"
    fps: int = 10
    window_name: str = "Teleop Viewer"
    sensors: Dict[str, Any] = field(default_factory=dict)

    # Overlay configuration
    default_overlay_style: OverlayStyle = field(default_factory=OverlayStyle)
    text_overlays: List[TextOverlayConfig] = field(default_factory=list)
    centermark: CentermarkConfig = field(default_factory=CentermarkConfig)
    border: BorderConfig = field(default_factory=BorderConfig)

    # Layout configuration
    layouts: Dict[str, LayoutNodeConfig] = field(default_factory=dict)
    active_layout: str = "horizontal"

    @classmethod
    def from_dict(cls, data: Dict) -> ViewerConfig:
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
            resolutions=data.get("resolutions", {}),
            hardware=data.get("hardware", {}),
            input_directory=data.get("input_directory", "./sample_images"),
            fps=data.get("fps", 10),
            window_name=data.get("window_name", "Teleop Viewer"),
            sensors=data.get("sensors", {}),
            default_overlay_style=OverlayStyle.from_dict(data.get("default_overlay_style")),
            text_overlays=text_overlays,
            centermark=CentermarkConfig.from_dict(data.get("centermark")),
            border=BorderConfig.from_dict(data.get("border")),
            layouts=layouts,
            active_layout=data.get("active_layout", "horizontal"),
        )


def load_config(config_path: str) -> ViewerConfig:
    """Load configuration from a YAML file."""
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    return ViewerConfig.from_dict(data)


def get_default_text_overlays() -> List[TextOverlayConfig]:
    """Get default text overlays matching current hardcoded behavior."""
    return [
        TextOverlayConfig(
            id="status",
            template="Status: {robot_status} ({mode})",
            cameras=["back_monitor_cam", "front_monitor_cam"],
            variables={
                "mode": VariableConfig(
                    type="conditional",
                    conditions=[
                        VariableCondition(when="{is_manual_review} == true", value="Manual"),
                        VariableCondition(when=None, value="Auto"),
                    ]
                )
            },
            color_rules=[
                ColorRule(color=(51, 153, 255), when="{is_manual_review} == true"),
                ColorRule(color=(0, 0, 255), when="{robot_status} == 'ERROR'"),
                ColorRule(color=(255, 128, 0), when=None),  # else
            ],
        ),
        TextOverlayConfig(
            id="laser",
            template="Dist: {distance_display}",
            cameras=["back_monitor_cam", "ifm_camera2"],
            variables={
                "distance_cm": VariableConfig(
                    type="formula",
                    expr="{laser_distance} * 0.1"
                ),
                "distance_display": VariableConfig(
                    type="conditional",
                    conditions=[
                        VariableCondition(when="{laser_active} == false", value="N/A"),
                        VariableCondition(when="{distance_cm} > 44", value="N/A"),
                        VariableCondition(when=None, format="{distance_cm:.2f}cm"),
                    ]
                ),
            },
            color_rules=[
                ColorRule(color=(0, 0, 255), when="{laser_active} == false"),
                ColorRule(color=(0, 0, 255), when="{distance_cm} > 44"),
                ColorRule(color=(0, 255, 0), when="{distance_cm} < 31"),
                ColorRule(color=(255, 0, 0), when=None),  # else
            ],
        ),
        TextOverlayConfig(
            id="pressure",
            template="Z1: {pressure_manifold:.4f} bar | Z2: {pressure_base:.4f} bar",
            cameras=["back_monitor_cam", "front_monitor_cam"],
            color=(255, 128, 0),
            style=OverlayStyle(font_scale=0.7),
        ),
    ]
