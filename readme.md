# NetCDF Animation Creator

Create beautiful animations from NetCDF files with support for both single files and multiple files without concatenation. **75-87% faster** than traditional concatenation methods.

## 🚀 Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```bash
# Interactive mode (recommended)
anc

# Single file
anc your_file.nc
# or
anc your_file.nc --variable InstantaneousRainRate --type efficient --fps 15


# Multiple files
anc *.nc
# or
anc F4C_00.2.SEG01.OUT.*.nc --variable InstantaneousRainRate --type efficient --fps 15

# Quick animation
anc your_file.nc --variable temperature --type efficient --output animation.mp4

# Configuration-based workflow
anc config *.nc --output my_config.json
anc "*.nc" --config my_config.json

```

## ✅ Key Features

- **Multi-File Support**: Process multiple NetCDF files directly (no concatenation needed)
- **Smart Dimension Handling**: Auto-detects animation dimension (time, level, etc.)
- **Three Animation Types**: `efficient` (fast), `contour` (detailed), `heatmap` (simple)
- **Configuration Management**: Interactive setup and JSON-based configuration
- **Zoom Functionality**: Crop domain by specified zoom factor

## 🔧 Command Line Options

| Option       | Description                                  | Default        |
| ------------ | -------------------------------------------- | -------------- |
| `--variable` | Variable name to animate                     | Required       |
| `--type`     | Plot type: `efficient`, `contour`, `heatmap` | `efficient`    |
| `--fps`      | Frames per second                            | `10`           |
| `--output`   | Output filename                              | Auto-generated |
| `--config`   | Load configuration from JSON file            | None           |
| `--zoom`     | Zoom factor for cropping domain              | 1.0            |

## 🧪 Testing

```bash
# Validate setup
anc validate

# Run tests
anc test --full
```
