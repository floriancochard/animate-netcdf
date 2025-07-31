# NetCDF Animation Creator

Create beautiful animations from NetCDF files with support for both single files and multiple files without concatenation. **75-87% faster** than traditional concatenation methods.

## 🚀 Quick Start

### Installation

```bash
# Install the package (one-time setup)
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Basic Usage

**Interactive Mode (Recommended):**

```bash
anc
```

**Single File:**

```bash
anc your_file.nc
```

**Multiple Files:**

```bash
anc *.nc
```

**Quick Animation:**

```bash
anc your_file.nc --variable temperature --type efficient --output animation.mp4
```

### Interactive File Selection

When you run `anc` without any arguments, you'll get an interactive menu:

1. **Enter a single NetCDF file path** - Manually specify a file
2. **Enter a file pattern** - Use patterns like `*.nc` or `F4C_*.nc`
3. **Browse current directory** - See all NetCDF files in the current directory
4. **Exit** - Quit the application

This makes it easy to get started without remembering file names or patterns!

**Zoomed Animation:**

```bash
anc your_file.nc --variable temperature --zoom 1.2 --type efficient
```

### Configuration Setup

```bash
# Create standalone config (interactive)
anc config

# Create config for single file
anc config your_file.nc --output my_config.json

# Create config for multiple files
anc config F4C_00.2.SEG01.OUT.*.nc --output multi_config.json

# Create template config
anc config --template template_config.json
```

**Note**: Variable names are optional in configuration files. You can set them when running the script with `--variable`.

## ✅ Key Features

### ✅ **Multi-File Support**

- Process multiple NetCDF files directly (no concatenation needed)
- **75-87% faster** than concatenation method
- **87-88% less memory** usage
- Automatic file discovery and sorting

### ✅ **Smart Dimension Handling**

- Auto-detects animation dimension (time, level, etc.)
- Supports any NetCDF structure
- Geographic projections with Cartopy

### ✅ **Three Animation Types**

- **`efficient`** - Fast, recommended for large files
- **`contour`** - Detailed, scientific visualization
- **`heatmap`** - Simple grid plots

### ✅ **Configuration Management**

- Interactive setup for first-time users
- JSON-based configuration persistence
- Command-line parameter override
- Configuration validation with comprehensive error checking

### ✅ **Zoom Functionality**

- Crop domain by specified zoom factor
- Center-based cropping maintains aspect ratio
- Works with all plot types (efficient, contour, heatmap)
- Supports both single and multi-file animations

## 📊 Performance Comparison

| Method            | Time      | Memory  | Disk Space    |
| ----------------- | --------- | ------- | ------------- |
| **Concatenation** | 2-4 hours | 8-16 GB | 2x original   |
| **Multi-File**    | 30-60 min | 1-2 GB  | Original only |

## 🎬 Usage Examples

### **Configuration-Based Workflow** (Recommended)

```bash
# 1. Create configuration
anc config *.nc --output my_config.json

# 2. Run with configuration
anc "*.nc" --config my_config.json

# 3. Override specific settings
anc "*.nc" --config my_config.json --fps 20
```

### **Direct Command Line**

```bash
# Interactive mode (file selection)
anc

# Single file
anc your_file.nc --variable InstantaneousRainRate --type efficient --fps 15

# Multiple files
anc F4C_00.2.SEG01.OUT.*.nc --variable InstantaneousRainRate --type efficient --fps 15
```

### **Interactive Mode**

```bash
# Launch interactive file selection
anc

# Interactive mode with file specified
anc your_file.nc
anc F4C_00.2.SEG01.OUT.*.nc
```

### **Quick Examples**

**Weather Data:**

```bash
anc weather_data.nc --variable InstantaneousRainRate --type efficient --fps 20
```

**Climate Data:**

```bash
anc climate_*.nc --variable Temperature2m --type contour --fps 10
```

**Ocean Data:**

```bash
anc ocean_data.nc --variable Salinity --type heatmap --fps 15
```

## 📁 Supported File Patterns

### Timestep-Based (Primary Use Case)

```
F4C_00.2.SEG01.OUT.001.nc
F4C_00.2.SEG01.OUT.002.nc
F4C_00.2.SEG01.OUT.003.nc
```

### Generic Patterns

```
*.nc                    # All NetCDF files
test*.nc               # Files starting with "test"
F4C*.nc               # Files starting with "F4C"
```

## 🔧 Command Line Options

| Option             | Description                                    | Default        |
| ------------------ | ---------------------------------------------- | -------------- |
| `--variable`       | Variable name to animate                       | Required       |
| `--type`           | Plot type: `efficient`, `contour`, `heatmap`   | `efficient`    |
| `--fps`            | Frames per second                              | `10`           |
| `--output`         | Output filename                                | Auto-generated |
| `--batch`          | Create animations for all variables            | False          |
| `--plot`           | Create single plot instead of animation        | False          |
| `--config`         | Load configuration from JSON file              | None           |
| `--overwrite`      | Overwrite existing output files                | False          |
| `--no-interactive` | Skip interactive mode                          | False          |
| `--zoom`           | Zoom factor for cropping domain (default: 1.0) | 1.0            |

## 📖 Advanced Features

### Dimension Handling

The script intelligently handles different dimension counts:

- **2D data** (lat + lon): ❌ Error - no animation dimension
- **3D data** (time + lat + lon): ✅ Auto-detects time dimension
- **4D data** (time + level + lat + lon): ✅ Picks first non-spatial dimension

### Animation Types

- **`efficient`**: Fast rendering, low memory, good quality
- **`contour`**: High quality, scientific visualization
- **`heatmap`**: Simple plots, no geographic projections

### Multi-File Features

- **Pre-scanning**: Determines global data range for consistent colorbars
- **Sequential processing**: Only one file loaded at a time
- **Progress tracking**: Real-time updates and time estimates
- **Error handling**: Graceful handling of corrupted files

### Zoom Functionality

- **Center-based cropping**: Maintains aspect ratio by cropping from center
- **Zoom factor examples**:
  - `1.0`: No zoom (original domain)
  - `1.2`: Crop to 83% of original size (500×500 → 416×416)
  - `1.5`: Crop to 67% of original size (500×500 → 333×333)
  - `2.0`: Crop to 50% of original size (500×500 → 250×250)
- **Works with all plot types**: efficient, contour, and heatmap
- **Multi-file support**: Applied consistently across all files

## 🧪 Testing

### Quick System Check

```bash
# Validate your setup
anc validate

# Run comprehensive test suite
anc test --full

# Test specific components
anc test --categories config files animation
```

### Test Categories

- `config` - Configuration management
- `files` - File discovery and validation
- `animation` - Multi-file animation setup
- `system` - System compatibility checks
- `utilities` - Data processing and plot utilities
- `cli` - Command line interface
- `integration` - End-to-end workflows
- `error_handling` - Error handling and recovery
- `performance` - Performance and memory management

## 🚨 Troubleshooting

**"No files found"**

```bash
# Check your pattern
anc "*.nc" --no-interactive

# Try different patterns
anc F4C*.nc
anc test*.nc
anc *.nc
```

**"ffmpeg not available"**

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

**Memory issues**

```bash
# Use efficient type and lower FPS
anc "*.nc" --type efficient --fps 5

# Reduce file count
anc F4C_00.2.SEG01.OUT.0*.nc  # Only first 10 files
```

**"Variable not found"**

```bash
# Check available variables
anc your_file.nc --no-interactive

# Use configuration tool to see variables
anc config your_file.nc

# Or use interactive mode to explore files
anc
```

## 🎯 Real-World Impact

**Before**: 200 files → Concatenate (2-4 hours) → Animate (30-60 min)
**After**: 200 files → Animate directly (30-60 min)

**Total time savings: 2-4 hours per animation! 🎬**
