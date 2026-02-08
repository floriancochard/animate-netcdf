#!/usr/bin/env python3
"""
Main entry point for the animate_netcdf package.
This allows the package to be run as: python -m animate_netcdf
"""

import sys
from animate_netcdf.core.app_controller import AppController


def show_help():
    """Show help information."""
    print("""
🎬 NetCDF Animation Creator (anc)

USAGE:
    anc [command] [options]

COMMANDS:
    -e, --explore    Explore NetCDF file structure
    (no flag)        Visualize NetCDF data (interactive or non-interactive)

EXAMPLES:
    anc -e file.nc                    # Explore file structure
    anc file.nc                       # Visualize (interactive mode)
    anc file.nc --variable temp       # Visualize (non-interactive)
    anc *.nc --variable temp --format png  # Multi-file PNG sequence
    anc *.nc --variable temp --format mp4  # Multi-file MP4 video
    anc *.nc --config viz.yaml        # Visualize using config file (skips interactive menu)

OPTIONS:
    --config, -c        Path to config file (JSON or YAML). Skips interactive menu; CLI overrides file.
    --variable, -v      Variable name to visualize
    --output, -o        Output filename
    --format            Output format (png or mp4)
    --fps               Frames per second (default: 10)
    --zoom, -z          Zoom factor (default: 1.0)
    --zoom-lat          Latitude to center zoom on (with --zoom-lon)
    --zoom-lon          Longitude to center zoom on (with --zoom-lat)
    --percentile        Percentile threshold (default: 0)
    --transparent       Use transparent background
    --designer-mode     Clean background, no coordinates
    --designer-square-crop  Square output, no padding (use with --designer-mode)
    --designer-show-map-contours  Show map contours/coastlines (use with --designer-mode)
    --overwrite         Overwrite existing files

For detailed help:
    anc --help
""")


def main():
    """Main entry point for the application."""
    try:
        # Check for help
        if len(sys.argv) > 1 and sys.argv[1] in ['help', '--help', '-h']:
            show_help()
            return 0
        
        # Run application controller
        controller = AppController()
        success = controller.run()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
