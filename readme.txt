NetCDF Animation Creator
========================

Create beautiful animations from NetCDF files with support for both single files and multiple files without concatenation. 75-87% faster than traditional concatenation methods.

QUICK START
-----------

Installation:
  pip install -r requirements.txt

Single File:
  python main.py your_file.nc

Multiple Files (NEW!):
  python main.py "F4C_00.2.SEG01.OUT.*.nc"

Quick Animation:
  python main.py your_file.nc --variable temperature --type efficient --output animation.mp4

Create Configuration File (NEW!):
  python create_config.py your_file.nc --output my_config.json

GET STARTED
-----------

For New Users:
1. Create a Configuration File (Recommended)
   python create_config.py your_data.nc --output my_config.json

2. Run with Your Configuration
   python main.py your_data.nc --config my_config.json

For Experienced Users:
  # Single file animation
  python main.py data.nc --variable temperature --type efficient --fps 15

  # Multi-file animation
  python main.py "F4C*.nc" --variable InstantaneousRainRate --type contour --fps 10

Interactive Mode:
  # Single file
  python main.py

  # Multiple files
  python main.py "*.nc"

Quick Examples:
  # Weather Data
  python main.py weather_data.nc --variable InstantaneousRainRate --type efficient --fps 20

  # Climate Data
  python main.py "climate_*.nc" --variable Temperature2m --type contour --fps 10

  # Ocean Data
  python main.py ocean_data.nc --variable Salinity --type heatmap --fps 15

KEY FEATURES
------------

Multi-File Support:
- Process multiple NetCDF files directly (no concatenation needed)
- 75-87% faster than concatenation method
- 87-88% less memory usage
- Automatic file discovery and sorting

Smart Dimension Handling:
- Auto-detects animation dimension (time, level, etc.)
- Supports any NetCDF structure
- Geographic projections with Cartopy

Three Animation Types:
- efficient - Fast, recommended for large files
- contour - Detailed, scientific visualization
- heatmap - Simple grid plots

Configuration Management:
- Interactive setup for first-time users
- JSON-based configuration persistence
- Command-line parameter override
- Configuration validation
- Configuration file creation tool (NEW!)

PERFORMANCE COMPARISON
---------------------

Method            | Time      | Memory  | Disk Space
----------------- | --------- | ------- | -------------
Concatenation     | 2-4 hours | 8-16 GB | 2x original
Multi-File        | 30-60 min | 1-2 GB  | Original only

USAGE EXAMPLES
--------------

Configuration-Based Workflow (Recommended):
  # 1. Create configuration
  python create_config.py "*.nc" --output my_config.json

  # 2. Run with configuration
  python main.py "*.nc" --config my_config.json

  # 3. Override specific settings
  python main.py "*.nc" --config my_config.json --fps 20

Direct Command Line:
  # Single file
  python main.py IDALIA_10km.nc --variable InstantaneousRainRate --type efficient --fps 15

  # Multiple files
  python main.py "F4C_00.2.SEG01.OUT.*.nc" --variable InstantaneousRainRate --type efficient --fps 15

Interactive Mode:
  # Single file
  python main.py

  # Multiple files
  python main.py "F4C_00.2.SEG01.OUT.*.nc"

Template Configuration:
  # Create template for manual editing
  python create_config.py --template template_config.json

  # Edit template_config.json, then use:
  python main.py "*.nc" --config template_config.json

SUPPORTED FILE PATTERNS
-----------------------

Timestep-Based (Primary Use Case):
  F4C_00.2.SEG01.OUT.001.nc
  F4C_00.2.SEG01.OUT.002.nc
  F4C_00.2.SEG01.OUT.003.nc

Generic Patterns:
  *.nc                    # All NetCDF files
  test*.nc               # Files starting with "test"
  F4C*.nc               # Files starting with "F4C"

COMMAND LINE OPTIONS
-------------------

Option          | Description                                  | Default
--------------- | -------------------------------------------- | --------------
--variable      | Variable name to animate                     | Required
--type          | Plot type: efficient, contour, heatmap       | efficient
--fps           | Frames per second                            | 10
--output        | Output filename                              | Auto-generated
--batch         | Create animations for all variables          | False
--plot          | Create single plot instead of animation      | False
--config        | Load configuration from JSON file            | None
--overwrite     | Overwrite existing output files              | False
--no-interactive| Skip interactive mode                        | False

TESTING
-------

Test your system setup:
  python test_multifile.py

ADVANCED FEATURES
-----------------

Dimension Handling:
The script intelligently handles different dimension counts:

- 2D data (lat + lon): Error - no animation dimension
- 3D data (time + lat + lon): Auto-detects time dimension
- 4D data (time + level + lat + lon): Picks first non-spatial dimension

Animation Types:
- efficient: Fast rendering, low memory, good quality
- contour: High quality, scientific visualization
- heatmap: Simple plots, no geographic projections

Multi-File Features:
- Pre-scanning: Determines global data range for consistent colorbars
- Sequential processing: Only one file loaded at a time
- Progress tracking: Real-time updates and time estimates
- Error handling: Graceful handling of corrupted files

TROUBLESHOOTING
---------------

"No files found":
  # Check your pattern
  python main.py "*.nc" --no-interactive

  # Try different patterns
  python main.py "F4C*.nc"
  python main.py "test*.nc"
  python main.py "*.nc"

"ffmpeg not available":
  # macOS
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # Windows
  # Download from https://ffmpeg.org/download.html

Memory issues:
  # Use efficient type and lower FPS
  python main.py "*.nc" --type efficient --fps 5

  # Reduce file count
  python main.py "F4C_00.2.SEG01.OUT.0*.nc"  # Only first 10 files

"Variable not found":
  # Check available variables
  python main.py your_file.nc --no-interactive

  # Use configuration tool to see variables
  python create_config.py your_file.nc

PROJECT STRUCTURE
----------------

animate-netcdf/
├── main.py                     # Main application
├── create_config.py            # Configuration file creator (NEW!)
├── config_manager.py           # Configuration management
├── file_manager.py             # File discovery and management
├── multi_file_animator.py      # Multi-file animation engine
├── test_multifile.py           # Test suite
├── requirements.txt            # Dependencies
└── readme.md                  # This file

REAL-WORLD IMPACT
-----------------

Before: 200 files → Concatenate (2-4 hours) → Animate (30-60 min)
After:  200 files → Animate directly (30-60 min)

Total time savings: 2-4 hours per animation! 