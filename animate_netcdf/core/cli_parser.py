#!/usr/bin/env python3
"""
Command Line Interface Parser for NetCDF Animations
Extracted from main.py for better organization
"""

import argparse
import os
import sys
from typing import Dict, Any, Optional, Tuple, List


class CLIParser:
    """Handles command-line argument parsing for NetCDF animations."""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create the main argument parser.
        
        Returns:
            argparse.ArgumentParser: Configured argument parser with all options
        """
        parser = argparse.ArgumentParser(
            description="Create animations from NetCDF files with clean titles and value filtering",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Interactive mode
  python main.py
  
  # Single NetCDF file
  python main.py IDALIA_10km.nc
  
  # Multiple NetCDF files (NEW!)
  python main.py "F4C_00.2.SEG01.OUT.*.nc"
  
  # Quick animation with all arguments
  python main.py IDALIA_10km.nc --variable InstantaneousRainRate --type efficient --output my_animation.mp4 --fps 15
  
  # Multi-file animation with configuration
  python main.py "F4C_00.2.SEG01.OUT.*.nc" --config my_config.json
  
  # Batch animation for all variables
  python main.py IDALIA_10km.nc --batch --type contour --fps 10
            """
        )
        
        # Main input argument
        parser.add_argument('input_pattern', nargs='*', default=['IDALIA_10km.nc'],
                           help='Path to NetCDF file or pattern for multiple files (e.g., "F4C_00.2.SEG01.OUT.*.nc")')
        
        # Core animation parameters
        parser.add_argument('--variable', '-v', 
                           help='Variable name to animate (e.g., InstantaneousRainRate)')
        
        parser.add_argument('--type', '-t', choices=['efficient', 'contour', 'heatmap'],
                           default='efficient',
                           help='Animation/plot type (default: efficient)')
        
        parser.add_argument('--output', '-o',
                           help='Output filename (default: auto-generated)')
        
        parser.add_argument('--fps', '-f', type=int, default=10,
                           help='Frames per second (default: 10)')
        
        # Processing modes
        parser.add_argument('--batch', '-b', action='store_true',
                           help='Create animations for all variables')
        
        parser.add_argument('--plot', '-p', action='store_true',
                           help='Create single plot instead of animation')
        
        parser.add_argument('--time-step', type=int, default=0,
                           help='Time step for single plot (default: 0)')
        
        # Data processing parameters
        parser.add_argument('--percentile', type=int, default=5,
                           help='Percentile threshold for filtering low values (default: 5)')
        
        parser.add_argument('--animate-dim', default='time',
                           help='Dimension to animate over (default: time)')
        
        parser.add_argument('--level', '-l', type=int,
                           help='Level index for 3D data (use -1 for average over levels)')
        
        parser.add_argument('--zoom', '-z', type=float, default=1.0,
                           help='Zoom factor for cropping domain (default: 1.0, no zoom)')
        
        # Configuration and control
        parser.add_argument('--config', '-c',
                           help='Load configuration from JSON file')
        
        parser.add_argument('--save-config',
                           help='Save current configuration to JSON file')
        
        parser.add_argument('--overwrite', action='store_true',
                           help='Overwrite existing output files')
        
        parser.add_argument('--no-interactive', action='store_true',
                           help='Skip interactive mode and use command line arguments only')
        
        # Multi-file specific arguments
        parser.add_argument('--pre-scan', action='store_true', default=True,
                           help='Pre-scan files for global data range (default: True)')
        
        parser.add_argument('--global-colorbar', action='store_true', default=True,
                           help='Use consistent colorbar across all files (default: True)')
        
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
        if hasattr(args, 'input_pattern') and args.input_pattern:
            # Convert list to single pattern if multiple files were passed
            if isinstance(args.input_pattern, list) and len(args.input_pattern) > 1:
                # Multiple files were passed, reconstruct pattern
                args.input_pattern = CLIParser._reconstruct_pattern(args.input_pattern)
            elif isinstance(args.input_pattern, list) and len(args.input_pattern) == 1:
                # Single file, extract from list
                args.input_pattern = args.input_pattern[0]
            elif isinstance(args.input_pattern, list) and len(args.input_pattern) == 0:
                # No files specified, use default
                args.input_pattern = 'IDALIA_10km.nc'
        
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
            
            # Check if basenames follow a pattern (e.g., F4C_00.2.SEG01.OUT.001, F4C_00.2.SEG01.OUT.002)
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
                else:
                    # Fallback to simple wildcard
                    return f"*{ext}"
        
        # Fallback: join all files with space (not ideal but functional)
        return " ".join(file_paths)
    
    @staticmethod
    def validate_args(args: argparse.Namespace) -> Tuple[bool, List[str]]:
        """Validate parsed arguments and return (is_valid, errors).
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        errors: List[str] = []
        
        # Validate FPS
        if args.fps <= 0 or args.fps > 60:
            errors.append("FPS must be between 1 and 60")
        
        # Validate percentile
        if args.percentile < 0 or args.percentile > 100:
            errors.append("Percentile must be between 0 and 100")
        
        # Validate zoom factor
        if args.zoom <= 0 or args.zoom > 10:
            errors.append("Zoom factor must be between 0.1 and 10.0")
        
        # Validate level index
        if args.level is not None and args.level < -1:
            errors.append("Level index must be -1 (average) or >= 0")
        
        # Validate time step
        if args.time_step < 0:
            errors.append("Time step must be >= 0")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def print_usage_examples() -> None:
        """Print usage examples to help users understand the tool."""
        print("""
📖 Usage Examples:

🔹 Single File Animations:
  python main.py your_file.nc
  python main.py data.nc --variable temperature --type efficient --fps 15
  python main.py data.nc --variable rainfall --zoom 1.5 --type contour

🔹 Multi-File Animations:
  python main.py "F4C_00.2.SEG01.OUT.*.nc"
  python main.py "*.nc" --variable InstantaneousRainRate --type efficient
  python main.py "climate_*.nc" --config my_config.json

🔹 Configuration Management:
  python create_config.py                    # Create standalone config
  python create_config.py "*.nc"            # Create config from files
  python main.py "*.nc" --config config.json # Use existing config

🔹 Batch Processing:
  python main.py data.nc --batch --type contour
  python main.py data.nc --batch --fps 20 --zoom 1.2

🔹 Single Plots:
  python main.py data.nc --plot --variable temperature
  python main.py data.nc --plot --time-step 5 --variable rainfall

🔹 Advanced Options:
  python main.py data.nc --percentile 10    # Filter more aggressively
  python main.py data.nc --level 2          # Use specific level
  python main.py data.nc --animate-dim time # Specify animation dimension
        """)
    
    @staticmethod
    def get_mode_from_args(args: argparse.Namespace) -> str:
        """Determine the operation mode from arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            str: Operation mode ('interactive', 'non_interactive', 'batch', 'single_plot')
        """
        if args.batch:
            return "batch"
        elif args.plot:
            return "single_plot"
        elif args.no_interactive or (args.variable and (args.batch or args.plot or not args.no_interactive)):
            return "non_interactive"
        else:
            return "interactive"
    
    @staticmethod
    def is_multi_file_pattern(input_pattern: str) -> bool:
        """Check if input pattern is for multiple files.
        
        Args:
            input_pattern: File pattern to check
            
        Returns:
            bool: True if pattern contains wildcards for multiple files
        """
        return '*' in input_pattern or '?' in input_pattern 