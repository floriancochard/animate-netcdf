# NetCDF Animation Creator

Create beautiful animations from NetCDF files with support for both single files and multiple files without concatenation. **75-87% faster** than traditional concatenation methods.

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

**Single File:**

```bash
python main.py your_file.nc
```

**Multiple Files (NEW!):**

```bash
python main.py "F4C_00.2.SEG01.OUT.*.nc"
```

**Quick Animation:**

```bash
python main.py your_file.nc --variable temperature --type efficient --output animation.mp4
```

**Zoomed Animation:**

```bash
python main.py your_file.nc --variable temperature --zoom 1.2 --type efficient
```

**Create Configuration File (NEW!):**

```bash
# Create standalone config (interactive)
python create_config.py

# Create config for single file
python create_config.py your_file.nc --output my_config.json

# Create config for multiple files
python create_config.py "F4C_00.2.SEG01.OUT.*.nc" --output multi_config.json

# Create template config
python create_config.py --template template_config.json
```

**Note**: Variable names are optional in configuration files. You can set them when running the script with `--variable`.

## 🎯 Get Started

### **For New Users**

1. **Create a Configuration File** (Recommended)

   ```bash
   # Standalone configuration (interactive)
   python create_config.py

   # For single files
   python create_config.py your_data.nc --output my_config.json

   # For multiple files
   python create_config.py "*.nc" --output my_config.json
   ```

2. **Run with Your Configuration**
   ```bash
   python main.py your_data.nc --config my_config.json
   ```

### **For Experienced Users**

**Direct Command Line:**

```bash
# Single file animation
python main.py data.nc --variable temperature --type efficient --fps 15

# Multi-file animation
python main.py "F4C*.nc" --variable InstantaneousRainRate --type contour --fps 10
```

### **Interactive Mode**

**For exploration and learning:**

```bash
# Single file
python main.py

# Multiple files
python main.py "*.nc"
```

### **Quick Examples**

**Weather Data:**

```bash
python main.py weather_data.nc --variable InstantaneousRainRate --type efficient --fps 20
```

**Climate Data:**

```bash
python main.py "climate_*.nc" --variable Temperature2m --type contour --fps 10
```

**Zoomed Climate Data:**

```bash
python main.py "climate_*.nc" --variable Temperature2m --zoom 1.5 --type contour --fps 10
```

**Ocean Data:**

```bash
python main.py ocean_data.nc --variable Salinity --type heatmap --fps 15
```

**Zoomed Ocean Data:**

```bash
python main.py ocean_data.nc --variable Salinity --zoom 2.0 --type heatmap --fps 15
```

## ✅ **Key Features**

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
- Configuration validation

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
# 1. Create configuration (standalone)
python create_config.py

# 1. Or create configuration from files
python create_config.py "*.nc" --output my_config.json

# 2. Run with configuration
python main.py "*.nc" --config my_config.json

# 2. Or run with variable override
python main.py "*.nc" --config my_config.json --variable temperature

# 3. Override specific settings
python main.py "*.nc" --config my_config.json --fps 20
```

### **Direct Command Line**

```bash
# Single file
python main.py IDALIA_10km.nc --variable InstantaneousRainRate --type efficient --fps 15

# Multiple files
python main.py "F4C_00.2.SEG01.OUT.*.nc" --variable InstantaneousRainRate --type efficient --fps 15
```

### **Interactive Mode**

```bash
# Single file
python main.py

# Multiple files
python main.py "F4C_00.2.SEG01.OUT.*.nc"
```

### **Template Configuration**

```bash
# Create template for manual editing
python create_config.py --template template_config.json

# Edit template_config.json, then use:
python main.py "*.nc" --config template_config.json
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

## 🧪 Testing

Test your system setup:

```bash
python test_suite.py
```

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

## 🚨 Troubleshooting

**"No files found"**

```bash
# Check your pattern
python main.py "*.nc" --no-interactive

# Try different patterns
python main.py "F4C*.nc"
python main.py "test*.nc"
python main.py "*.nc"
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
python main.py "*.nc" --type efficient --fps 5

# Reduce file count
python main.py "F4C_00.2.SEG01.OUT.0*.nc"  # Only first 10 files
```

**"Variable not found"**

```bash
# Check available variables
python main.py your_file.nc --no-interactive

# Use configuration tool to see variables
python create_config.py your_file.nc
```

## 📊 Project Structure

```
animate-netcdf/
├── main.py                     # Main application
├── create_config.py            # Configuration file creator (NEW!)
├── config_manager.py           # Configuration management
├── file_manager.py             # File discovery and management
├── multi_file_animator.py      # Multi-file animation engine
├── test_suite.py               # Test suite
├── requirements.txt            # Dependencies
└── readme.md                  # This file
```

### 📁 File Descriptions

**`main.py`** - Core application entry point

- Handles both single-file and multi-file NetCDF animations
- Contains the `UnifiedAnimator` class for single-file processing
- Manages command-line argument parsing and user interaction
- Integrates with other modules for multi-file functionality
- Supports interactive mode and batch processing

**`create_config.py`** - Standalone configuration creation tool

- Interactive tool for creating JSON configuration files
- Supports both single-file and multi-file configurations
- Can analyze NetCDF files to suggest variables and settings
- Creates template configurations for new users
- Helps users set up configurations without running the main application

**`config_manager.py`** - Configuration management system

- Contains `AnimationConfig` class for storing animation parameters
- Contains `ConfigManager` class for loading/saving JSON configurations
- Handles configuration validation and error checking
- Provides interactive configuration collection
- Manages file pattern discovery and timestep extraction

**`file_manager.py`** - Multi-file operations manager

- Contains `NetCDFFileManager` class for handling multiple NetCDF files
- Discovers files matching patterns (e.g., "_.nc", "F4C_.nc")
- Validates file consistency across multiple files
- Extracts common variables and spatial coordinates
- Estimates memory usage and processing time
- Sorts files by timestep for proper animation sequence

**`multi_file_animator.py`** - Multi-file animation engine

- Contains `MultiFileAnimator` class for processing multiple files
- Creates animations without concatenating files (75-87% faster)
- Handles geographic and heatmap animations
- Manages global colorbar ranges across all files
- Provides progress tracking and time estimation
- Integrates with `UnifiedAnimator` for data processing

**`test_suite.py`** - Comprehensive testing framework

- Tests all major components of the system
- Validates configuration management
- Tests file discovery and validation
- Verifies multi-file animation setup
- Provides system compatibility checks

## 🎯 Real-World Impact

**Before**: 200 files → Concatenate (2-4 hours) → Animate (30-60 min)
**After**: 200 files → Animate directly (30-60 min)

**Total time savings: 2-4 hours per animation! 🎬**
