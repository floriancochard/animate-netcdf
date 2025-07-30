# NetCDF Animation Creator - Get Started Guide

A powerful tool for creating animations from NetCDF files with support for time, level, latitude, and longitude dimensions.

## 🚀 Quick Start

### 1. Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Make sure ffmpeg is installed for video creation
# On macOS: brew install ffmpeg
# On Ubuntu: sudo apt install ffmpeg
# On Windows: Download from https://ffmpeg.org/
```

### 2. Basic Usage

```bash
# Explore your NetCDF file
python main.py your_file.nc

# Create a simple animation (auto-selects best dimension)
python main.py your_file.nc --variable temperature --type efficient --output animation.mp4

# Specify the animation dimension manually
python main.py your_file.nc --variable temperature --animate-dim level --output animation.mp4
```

## 📋 Command Line Options

| Option          | Description                                  | Default        |
| --------------- | -------------------------------------------- | -------------- |
| `--variable`    | Variable name to animate                     | Required       |
| `--type`        | Plot type: `efficient`, `contour`, `heatmap` | `efficient`    |
| `--animate-dim` | Dimension to animate over                    | Auto-detected  |
| `--output`      | Output filename                              | Auto-generated |
| `--fps`         | Frames per second                            | `10`           |
| `--batch`       | Create animations for all variables          | False          |
| `--plot`        | Create single plot instead of animation      | False          |
| `--percentile`  | Filter low values percentile                 | `5`            |

## 🎬 Animation Types

### Efficient (Recommended)

- Fast rendering with Cartopy
- Good for large datasets
- Geographic projections

```bash
python main.py data.nc --variable temperature --type efficient
```

### Contour

- Detailed contour plots
- Better for scientific visualization
- Geographic projections

```bash
python main.py data.nc --variable temperature --type contour
```

### Heatmap

- Simple grid-based plots
- Good for quick previews
- No geographic projections

```bash
python main.py data.nc --variable temperature --type heatmap
```

## 📊 Supported File Structures

The script automatically handles any combination of these dimensions:

- **Time series**: `time + lat + lon`
- **Vertical profiles**: `level + lat + lon`
- **4D data**: `time + level + lat + lon`
- **Different coordinate names**: `latitude/longitude` or `lat/lon`

### Examples

**Weather data (time series):**

```bash
python main.py weather.nc --variable temperature --animate-dim time
```

**Atmospheric profiles (vertical levels):**

```bash
python main.py atmosphere.nc --variable temperature --animate-dim level
```

**Ocean data (4D):**

```bash
python main.py ocean.nc --variable salinity --animate-dim time
```

## 📐 Dimension Handling

The script intelligently handles different dimension counts:

### **2 Dimensions (e.g., `lat + lon`)**

```bash
Dimensions: {'lat': 500, 'lon': 500}
```

**Result**: ❌ **Error** - "No suitable animation dimension found"

- Only spatial dimensions exist
- No dimension to animate over
- Script will exit with clear error message

### **3 Dimensions (e.g., `time + lat + lon` or `level + lat + lon`)**

```bash
Dimensions: {'time': 100, 'lat': 500, 'lon': 500}
# OR
Dimensions: {'level': 58, 'lat': 500, 'lon': 500}
```

**Result**: ✅ **Works perfectly**

- Script auto-detects the non-spatial dimension (`time` or `level`)
- Creates animation over that dimension
- Your current file is this case!

### **4 Dimensions (e.g., `time + level + lat + lon`)**

```bash
Dimensions: {'time': 100, 'level': 58, 'lat': 500, 'lon': 500}
```

**Result**: ✅ **Works with choice**

- Script picks the **first** non-spatial dimension it finds
- Priority order: `time` → `level` → other dimensions
- You can override with `--animate-dim time` or `--animate-dim level`

### **How Auto-Detection Works**

The script uses this logic:

```python
spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']
candidate_dims = [d for d in ds_dims if d not in spatial_dims]
```

**Examples:**

- `{'time': 100, 'lat': 500, 'lon': 500}` → picks `time`
- `{'level': 58, 'lat': 500, 'lon': 500}` → picks `level`
- `{'time': 100, 'level': 58, 'lat': 500, 'lon': 500}` → picks `time` (first found)
- `{'lat': 500, 'lon': 500}` → no candidates, error

## 🔧 Advanced Usage

### Batch Processing

Create animations for all variables in your file:

```bash
python main.py data.nc --batch --type efficient --fps 15
```

### Single Plot Preview

Create a static plot to preview your data:

```bash
python main.py data.nc --variable temperature --plot --time-step 10
```

### Custom Filtering

Adjust the percentile threshold for filtering low values:

```bash
python main.py data.nc --variable temperature --percentile 10
```

### High-Quality Output

```bash
python main.py data.nc --variable temperature --type contour --fps 20 --output high_quality.mp4
```

## 🛠️ Troubleshooting

### Common Issues

**"Dimension 'time' not found"**

- Your file doesn't have a time dimension
- The script will auto-select an alternative dimension
- Use `--animate-dim` to specify the correct dimension

**"No suitable animation dimension found"**

- Your file only has spatial dimensions (lat/lon)
- Add a time or level dimension to your data

**"ffmpeg not available"**

- Install ffmpeg: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Ubuntu)

**Memory issues with large files**

- Use `--type efficient` for better performance
- Reduce FPS: `--fps 5`
- Use smaller datasets for testing

### Performance Tips

- **Large files**: Use `--type efficient` and lower FPS
- **Memory issues**: Monitor memory usage in output
- **Quality vs speed**: `efficient` for speed, `contour` for quality
- **Preview first**: Use `--plot` to check data before animating

## 📁 Output Files

The script creates MP4 video files with:

- Geographic projections (efficient/contour types)
- Color-coded data values
- Animated dimension labels
- Memory usage monitoring
- Progress indicators

## 🔍 Exploring Your Data

Before creating animations, explore your file structure:

```bash
python main.py your_file.nc
```

This will show:

- Available dimensions and their sizes
- Available variables
- Suggested animation dimension
- Spatial coordinate ranges

## 📝 Examples

### Quick Test

```bash
# Test with auto-detection
python main.py data.nc --variable temperature --type efficient --output test.mp4
```

### Production Quality

```bash
# High-quality output
python main.py data.nc --variable temperature --type contour --fps 15 --output final.mp4
```

### All Variables

```bash
# Create animations for everything
python main.py data.nc --batch --type efficient --fps 10
```

### Custom Settings

```bash
# Full control
python main.py data.nc \
  --variable temperature \
  --type contour \
  --animate-dim level \
  --fps 20 \
  --percentile 10 \
  --output custom_animation.mp4
```

## 🎯 Best Practices

1. **Start simple**: Use auto-detection first
2. **Preview data**: Use `--plot` to check your data
3. **Test with small files**: Verify settings before processing large datasets
4. **Monitor memory**: Watch memory usage in output
5. **Use efficient type**: For large files or when speed matters
6. **Adjust FPS**: Lower FPS for large files, higher for smooth playback

## 📞 Getting Help

If you encounter issues:

1. Check the file structure: `python main.py your_file.nc`
2. Try different plot types: `efficient`, `contour`, `heatmap`
3. Adjust FPS and filtering settings
4. Monitor memory usage in the output
5. Use `--plot` to preview data before animating

The script is designed to work with virtually any NetCDF file structure and will provide clear error messages if something goes wrong.
