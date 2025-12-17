# Teleop Viewer

A high-performance teleop image viewer for robotics applications with multi-camera support, configurable sensor overlays, and flexible YAML-based layouts.

## Features

- Multi-camera image processing and display
- **Fully configurable text overlays** via YAML (templates, colors, conditions)
- **Flexible layout system** - define camera arrangements in config
- Automatic camera filtering - only processes cameras used in layouts
- Image caching and parallel processing for high performance

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run the viewer
python teleop_viewer_improved.py

# With custom config
python teleop_viewer_improved.py -c config.yaml
```

### Controls
- `q` or `ESC`: Quit
- `n`: Next frame

## Benchmark Results

| Version | FPS | ms/frame | Speedup |
|---------|-----|----------|---------|
| Original (`teleop_viewer.py`) | 20.5 | 48.69 | 1.0x |
| Improved (`teleop_viewer_improved.py`) | 56.7 | 17.63 | **2.76x** |

Run the benchmark:
```bash
python benchmark.py -n 50
```

## Configuration

All settings are configured via `config.yaml`:

### Text Overlays

Define unlimited text overlays with templates, variables, and conditional colors:

```yaml
text_overlays:
  - id: status
    template: "Status: {robot_status} ({mode})"
    cameras: [back_monitor_cam, front_monitor_cam]
    variables:
      mode:
        type: conditional
        conditions:
          - when: "{is_manual_review} == true"
            value: "Manual"
          - else: "Auto"
    color_rules:
      - when: "{is_manual_review} == true"
        color: [51, 153, 255]  # BGR orange
      - else: [255, 128, 0]

  - id: laser
    template: "Dist: {distance_display}"
    cameras: [back_monitor_cam, ifm_camera2]
    variables:
      distance_cm:
        type: formula
        expr: "{laser_distance} * 0.1"
      distance_display:
        type: conditional
        conditions:
          - when: "{laser_active} == false"
            value: "N/A"
          - else:
            format: "{distance_cm:.2f}cm"
```

### Layouts

Define camera arrangements as trees:

```yaml
layouts:
  horizontal:
    direction: horizontal
    children:
      - direction: vertical
        children:
          - camera: ee_cam
          - camera: ifm_camera1
      - camera: ifm_camera2
      - direction: horizontal
        children:
          - camera: front_monitor_cam
          - camera: back_monitor_cam

active_layout: "horizontal"
```

Only cameras defined in layouts are processed (unused cameras are skipped for performance).

### Available Template Variables

From sensor data:
- `{laser_distance}` - float (mm)
- `{laser_active}` - bool
- `{pressure_manifold}` - float (bar)
- `{pressure_base}` - float (bar)
- `{robot_status}` - string
- `{is_manual_review}` - bool

## Example

Run the example script:

```bash
python -m teleop_view_image_generator.examples.example
```

Programmatic usage:

```python
from teleop_view_image_generator import TeleopImageGenerator

# Create generator from config file
generator = TeleopImageGenerator("config.yaml")

# Feed camera images
generator.update_camera_image("ee_cam", cv2_image, active=True)

# Update sensor data for overlays
generator.update_sensor_data(
    laser_distance=25.0,
    robot_status="SCANNING",
)

# Generate output frame
frames = generator.generate_frame()
```

## Project Structure

```
teleop_viewer/
├── teleop_viewer_improved.py     # Main viewer application
├── teleop_view_image_generator/  # Core image processing package
│   ├── __init__.py
│   ├── generator.py              # TeleopImageGenerator class
│   ├── camera.py                 # Camera configurations
│   ├── layout.py                 # Layout management
│   ├── overlays.py               # Sensor overlay rendering
│   ├── config.py                 # Configuration dataclasses
│   ├── template_engine.py        # Template rendering engine
│   └── examples/
│       └── example.py
├── config.yaml                   # Configuration file
├── benchmark.py                  # Performance benchmark
└── sample_images/                # Test images
```
