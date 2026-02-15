#!/usr/bin/env python3
"""
Simplified Command Line Interface Parser for NetCDF Animations
Two main commands: explore and visualize
"""

import argparse
import os
from typing import Optional, Tuple, List


class CLIParser:
    """Simplified CLI parser for NetCDF animations."""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create the main argument parser.
        
        Returns:
            argparse.ArgumentParser: Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="NetCDF Data Explorer and Visualizer",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Explore a file
  anc -e file.nc
  
  # Visualize a file (interactive)
  anc file.nc
  
  # Visualize a file (non-interactive)
  anc file.nc --variable temperature --output out.png
  
  # Visualize multiple files as PNG sequence
  anc *.nc --variable temperature --format png
  
  # Visualize multiple files as MP4 video
  anc *.nc --variable temperature --format mp4
  
  # Visualize using a config file (skips interactive menu)
  anc *.nc --config viz.yaml
            """
        )
        
        # Main input argument - accept multiple files (shell may expand glob patterns)
        parser.add_argument('input', nargs='*', default=None,
                           help='Path to NetCDF file(s) or pattern for multiple files')
        
        # Exploration flag
        parser.add_argument('-e', '--explore', action='store_true',
                           help='Explore NetCDF file structure instead of visualizing')
        
        # Visualization options
        parser.add_argument('--variable', '-v',
                           help='Variable name to visualize')
        
        parser.add_argument('--output', '-o',
                           help='Output filename or pattern')
        
        parser.add_argument('--format', choices=['png', 'mp4', 'gif'], default=None,
                           help='Output format (png for sequence, mp4 for video, gif for animated GIF). Auto-detected if not specified.')
        
        parser.add_argument('--fps', type=int, default=10,
                           help='Frames per second for animations (default: 10)')
        
        parser.add_argument('--zoom', '-z', type=float, default=1.0,
                           help='Zoom factor for cropping domain (default: 1.0)')
        parser.add_argument('--zoom-lat', type=float, default=None,
                           help='Latitude to center zoom on (use with --zoom-lon and --zoom > 1)')
        parser.add_argument('--zoom-lon', type=float, default=None,
                           help='Longitude to center zoom on (use with --zoom-lat and --zoom > 1)')
        
        parser.add_argument('--percentile', type=int, default=5,
                           help='Percentile threshold for filtering low values (default: 0)')
        
        parser.add_argument('--transparent', action='store_true',
                           help='Use transparent background for PNG output')
        
        parser.add_argument('--designer-mode', action='store_true',
                           help='Enable designer mode: clean background, no coordinates, no title')
        parser.add_argument('--designer-square-crop', action='store_true',
                           help='[Designer mode] Crop output to a square centered on the map, no padding/margins')
        parser.add_argument('--designer-full-domain', action='store_true',
                           help='[Designer mode] Use full NetCDF domain as rectangle (no zoom; whole file extent)')
        parser.add_argument('--designer-show-map-contours', action='store_true',
                           help='[Designer mode] Show map contours (coastlines and borders)')
        
        parser.add_argument('--no-land-sea', action='store_true',
                           help='Disable land/ocean fill (coasts less visible when zoomed)')
        parser.add_argument('--map-land-sea-scale', type=str, choices=['110m', '50m', '10m'], default=None,
                           help='Land/sea resolution: 110m (coarse), 50m (default), 10m (fine)')
        parser.add_argument('--show-place-names', action='store_true',
                           help='Add minimal city labels for orientation when zoomed')
        
        parser.add_argument('--ignore-values', nargs='+', type=float, default=[],
                           help='Values to ignore/mask (e.g., --ignore-values 999 -999)')
        
        parser.add_argument('--cmap',
                           help='Matplotlib colormap name (e.g. viridis, Blues, YlOrRd, RdYlBu_r)')
        
        parser.add_argument('--vmin', type=float, default=None,
                           help='Minimum value for color scale (e.g. 285 for temperature in K)')
        parser.add_argument('--vmax', type=float, default=None,
                           help='Maximum value for color scale (e.g. 305 for temperature in K)')
        parser.add_argument('--data-alpha', type=float, default=None,
                           help='Data layer opacity 0–1 (e.g. 1.0 = fully opaque; use if data looks too transparent)')
        
        parser.add_argument('--overwrite', action='store_true',
                           help='Overwrite existing output files')
        
        parser.add_argument('-c', '--config',
                           help='Path to config file (JSON or YAML). Loads visualization parameters from file and skips the interactive menu. CLI options override file values.')
        
        return parser
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """Parse command line arguments.
        
        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = CLIParser.create_parser()
        args = parser.parse_args()
        
        # Handle shell-expanded glob patterns
        if args.input:
            if len(args.input) == 0:
                args.input = None
            elif len(args.input) == 1:
                # Single file or pattern
                input_path = args.input[0]
                # Check if it's a glob pattern
                if '*' in input_path or '?' in input_path:
                    # Keep as pattern
                    args.input = input_path
                elif os.path.exists(input_path):
                    # Single file
                    args.input = input_path
                else:
                    # Try glob expansion
                    import glob
                    expanded = glob.glob(input_path)
                    if len(expanded) > 1:
                        # Multiple files found - reconstruct pattern
                        args.input = CLIParser._reconstruct_pattern(expanded)
                    elif len(expanded) == 1:
                        # Single file found
                        args.input = expanded[0]
                    else:
                        # No files found, keep original
                        args.input = input_path
            else:
                # Multiple files provided (shell expanded glob)
                # Reconstruct pattern from file list
                args.input = CLIParser._reconstruct_pattern(args.input)
        
        return args
    
    @staticmethod
    def _reconstruct_pattern(file_paths: List[str]) -> str:
        """Reconstruct a glob pattern from a list of file paths.
        
        Args:
            file_paths: List of file paths that were shell-expanded
            
        Returns:
            str: Reconstructed glob pattern
        """
        if not file_paths:
            return ""
        
        # If all files have the same extension, create a pattern
        extensions = set()
        basenames = []
        
        for path in file_paths:
            if os.path.isfile(path):
                basename, ext = os.path.splitext(path)
                extensions.add(ext)
                basenames.append(basename)
        
        # If all files have the same extension and similar naming pattern
        if len(extensions) == 1:
            ext = list(extensions)[0]
            
            # Check if basenames follow a pattern (e.g., file.001, file.002)
            if len(basenames) > 1:
                # Try to find common prefix and suffix
                common_prefix = os.path.commonprefix(basenames)
                common_suffix = ""
                
                # Find common suffix by reversing and finding common prefix
                reversed_basenames = [name[::-1] for name in basenames]
                common_reversed_prefix = os.path.commonprefix(reversed_basenames)
                if common_reversed_prefix:
                    common_suffix = common_reversed_prefix[::-1]
                
                # Create pattern
                if common_prefix and common_suffix:
                    pattern = f"{common_prefix}*{common_suffix}{ext}"
                    return pattern
                elif common_prefix:
                    pattern = f"{common_prefix}*{ext}"
                    return pattern
        
        # Fallback: use first file's directory with wildcard
        if file_paths:
            dir_path = os.path.dirname(file_paths[0]) or '.'
            ext = os.path.splitext(file_paths[0])[1]
            return f"{dir_path}/*{ext}"
        
        return "*"
    
    @staticmethod
    def validate_args(args: argparse.Namespace) -> Tuple[bool, List[str]]:
        """Validate parsed arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Validate FPS
        if args.fps <= 0 or args.fps > 60:
            errors.append("FPS must be between 1 and 60")
        
        # Validate percentile
        if args.percentile < 0 or args.percentile > 100:
            errors.append("Percentile must be between 0 and 100")
        
        # Validate zoom factor
        if args.zoom <= 0 or args.zoom > 125:
            errors.append("Zoom factor must be between 0.1 and 125.0")
        
        # Validate zoom center (both or neither; lat in [-90,90], lon in [-180,360])
        zoom_lat = getattr(args, 'zoom_lat', None)
        zoom_lon = getattr(args, 'zoom_lon', None)
        if zoom_lat is not None or zoom_lon is not None:
            if zoom_lat is None or zoom_lon is None:
                errors.append("Zoom center requires both --zoom-lat and --zoom-lon")
            else:
                if not -90 <= zoom_lat <= 90:
                    errors.append("--zoom-lat must be between -90 and 90")
                if not -180 <= zoom_lon <= 360:
                    errors.append("--zoom-lon must be between -180 and 360")
        
        # Validate vmin/vmax if both provided
        vmin = getattr(args, 'vmin', None)
        vmax = getattr(args, 'vmax', None)
        if vmin is not None and vmax is not None and vmin >= vmax:
            errors.append("--vmin must be less than --vmax")
        
        # Check if input is required
        if not args.explore and (not args.input or args.input is None):
            errors.append("Input file or pattern required for visualization")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def is_multi_file_pattern(input_pattern) -> bool:
        """Check if input pattern is for multiple files.
        
        Args:
            input_pattern: File pattern to check (str, list, or None)
            
        Returns:
            bool: True if pattern contains wildcards for multiple files
        """
        if input_pattern is None:
            return False
        
        # Handle list input (from shell expansion)
        if isinstance(input_pattern, list):
            return len(input_pattern) > 1
        
        # Handle string input
        if isinstance(input_pattern, str):
            return '*' in input_pattern or '?' in input_pattern
        
        return False
