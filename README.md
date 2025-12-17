# Teleop Viewer

A high-performance teleop image viewer for robotics applications with multi-camera support, sensor overlays, and configurable layouts.

## Features

- Multi-camera image processing and display
- Sensor data overlays (laser distance, pressure, robot status)
- Configurable camera layouts (horizontal/vertical)
- Image caching and parallel processing for high performance

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run the optimized viewer
python teleop_viewer_improved.py

# With custom config
python teleop_viewer_improved.py -c config.yaml -i ./sample_images --fps 30
```

### Controls
- `q` or `ESC`: Quit
- `n`: Next frame

## Benchmark Results

| Version | FPS | ms/frame | Speedup |
|---------|-----|----------|---------|
| Original (`teleop_viewer.py`) | 16.3 | 61.39 | 1.0x |
| Improved (`teleop_viewer_improved.py`) | 54.9 | 18.23 | 3.37x |

Run the benchmark:
```bash
python benchmark.py -n 50
```

## Example

Run the example script with synthetic images (no external files needed):

```bash
python -m teleop_view_image_generator.examples.example
```

This demonstrates how to use `TeleopImageGenerator` programmatically:

```python
from teleop_view_image_generator import TeleopImageGenerator

# Create generator with config
generator = TeleopImageGenerator(config)

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
├── teleop_viewer.py              # Original implementation
├── teleop_viewer_improved.py     # Optimized version using package
├── teleop_view_image_generator/  # Core image processing package
│   ├── __init__.py
│   ├── generator.py              # TeleopImageGenerator class
│   ├── camera.py                 # Camera configurations
│   ├── layout.py                 # Layout management
│   ├── overlays.py               # Sensor overlay rendering
│   └── examples/                 # Example scripts
│       └── example.py
├── config.yaml                   # Configuration file
├── benchmark.py                  # Performance benchmark
└── sample_images/                # Test images
```

## Configuration

Edit `config.yaml` to customize:
- Camera resolutions
- Hardware settings (elbow cam, camera mount)
- Sensor values
- FPS and display options
