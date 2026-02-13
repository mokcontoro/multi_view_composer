"""Camera configuration and data structures."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
import numpy as np
import cv2

from .config import CameraDefinition


# Rotation mapping: degrees to OpenCV constant
ROTATION_MAP = {
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    -90: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


@dataclass
class CameraConfig:
    """Runtime configuration for a single camera."""

    name: str
    resolution: Tuple[int, int, int]  # (height, width, channels)
    rotate: Optional[int]  # cv2 rotation constant or None
    centermark: bool

    # Computed target sizes for each layout (set during initialization)
    target_sizes: List[Tuple[int, int]] = field(default_factory=list)

    # Runtime data
    active: bool = False
    raw_image: Optional[np.ndarray] = None
    processed_images: List[Optional[np.ndarray]] = field(default_factory=list)

    def get_effective_resolution(self) -> Tuple[int, int, int]:
        """Get resolution after rotation (only 90/270 swap dimensions)."""
        if self.rotate in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE):
            return (self.resolution[1], self.resolution[0], self.resolution[2])
        return self.resolution


def create_camera_configs(
    camera_definitions: Dict[str, CameraDefinition], num_layouts: int = 1
) -> Dict[str, CameraConfig]:
    """
    Create camera configs from definitions.

    Args:
        camera_definitions: Dict of camera definitions from config
        num_layouts: Number of output layouts

    Returns:
        Dict mapping camera name to CameraConfig
    """
    configs = {}

    for name, definition in camera_definitions.items():
        h, w = definition.resolution
        rotate_cv = ROTATION_MAP.get(definition.rotate) if definition.rotate else None

        configs[name] = CameraConfig(
            name=name,
            resolution=(h, w, 3),
            rotate=rotate_cv,
            centermark=definition.centermark,
            target_sizes=[(h, w)] * num_layouts,
            processed_images=[None] * num_layouts,
        )

    return configs
