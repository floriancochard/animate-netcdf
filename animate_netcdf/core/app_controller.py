#!/usr/bin/env python3
"""
Application Controller for NetCDF Animations
Simplified orchestrator for explore and visualize operations
"""

import os
import glob
from typing import Optional
from argparse import Namespace

from animate_netcdf.core.cli_parser import CLIParser
from animate_netcdf.core.config_manager import ConfigManager, AnimationConfig, OutputFormat, load_config_from_path
from animate_netcdf.core.explorer import Explorer
from animate_netcdf.core.interactive_flow import InteractiveFlow
from animate_netcdf.core.output_manager import OutputManager
from animate_netcdf.visualizers.unified_visualizer import NetCDFVisualizer
from animate_netcdf.utils.logging_utils import setup_all_logging


class AppController:
    """Main application controller for NetCDF animations."""
    
    def __init__(self) -> None:
        """Initialize the application controller."""
        setup_all_logging()
        self.args: Optional[Namespace] = None
        self.config_manager: Optional[ConfigManager] = None
        self.explorer = Explorer()
        self.interactive_flow = InteractiveFlow()
        self.output_manager = OutputManager()
        
    def run(self, args: Optional[Namespace] = None) -> bool:
        """Main entry point for the application.
        
        Args:
            args: Optional pre-parsed arguments. If None, will parse from command line.
            
        Returns:
            bool: True if operation completed successfully, False otherwise
        """
        try:
            # Parse arguments if not provided
            if args is None:
                args = CLIParser.parse_args()
            
            self.args = args
            
            # Validate arguments
            is_valid, errors = CLIParser.validate_args(args)
            if not is_valid:
                print("❌ Command line argument errors:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            
            # Route to explore or visualize
            if args.explore:
                return self.run_explore(args)
            else:
                return self.run_visualize(args)
                
        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Application error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_explore(self, args: Namespace) -> bool:
        """Handle exploration mode.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            bool: True if exploration completed successfully
        """
        if not args.input:
            print("❌ No file specified for exploration")
            print("Usage: anc -e <file>")
            return False
        
        # Check if it's a glob pattern
        if '*' in args.input or '?' in args.input:
            return self.explorer.explore_files(args.input)
        else:
            return self.explorer.explore_file(args.input)
    
    def run_visualize(self, args: Namespace) -> bool:
        """Handle visualization mode.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            bool: True if visualization completed successfully
        """
        if not args.input:
            print("❌ No file specified for visualization")
            print("Usage: anc <file> [options]")
            return False
        
        # Determine if multi-file
        is_multi_file = CLIParser.is_multi_file_pattern(args.input)
        
        # Get or create configuration
        config_path = getattr(args, 'config', None)
        if config_path:
            try:
                config = load_config_from_path(config_path)
            except FileNotFoundError as e:
                print(f"❌ {e}")
                return False
            except ValueError as e:
                print(f"❌ Invalid config file: {e}")
                return False
        else:
            config = self._get_or_create_config(args, is_multi_file)
            if not config:
                return False
        
        # Set file pattern (CLI input always defines which NetCDF files to use)
        config.file_pattern = args.input
        
        # Update config from command line arguments
        self._update_config_from_args(config, args, is_multi_file)
        
        # Validate configuration
        if not self._validate_config(config, is_multi_file):
            return False
        
        # Create visualizer and run
        visualizer = NetCDFVisualizer(config)
        return visualizer.visualize(args.input)
    
    def _get_or_create_config(self, args: Namespace, is_multi_file: bool) -> Optional[AnimationConfig]:
        """Get or create configuration.
        
        Args:
            args: Command line arguments
            is_multi_file: Whether this is a multi-file operation
            
        Returns:
            AnimationConfig: Configuration object or None if creation failed
        """
        # If variable is specified, create minimal config
        if args.variable:
            config = AnimationConfig()
            config.variable = args.variable
            return config
        
        # Otherwise, collect interactively
        print("\n" + "=" * 60)
        print("🎬 NetCDF Visualization Setup")
        print("=" * 60)
        
        try:
            config = self.interactive_flow.collect_visualization_config(
                args.input, is_multi_file
            )
            return config
        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            return None
        except Exception as e:
            print(f"❌ Error collecting configuration: {e}")
            return None
    
    def _update_config_from_args(self, config: AnimationConfig, args: Namespace, 
                                is_multi_file: bool) -> None:
        """Update configuration with command line arguments.
        
        Args:
            config: Configuration object to update
            args: Command line arguments
            is_multi_file: Whether this is a multi-file operation
        """
        # Variable
        if args.variable:
            config.variable = args.variable
        
        # Output
        if args.output:
            config.output_pattern = args.output
        else:
            # Generate output filename
            output_format = args.format or ('png' if not is_multi_file else 'mp4')
            config.output_pattern = self.output_manager.generate_output_filename(
                config.variable or 'output', output_format, None, is_multi_file
            )
        
        # Output format
        if args.format:
            config.output_format = OutputFormat(args.format)
        elif is_multi_file:
            # Default to MP4 for multi-file
            config.output_format = OutputFormat.MP4
        else:
            # Single file always PNG (not used by visualizer, but set for consistency)
            config.output_format = OutputFormat.MP4  # Visualizer handles single file as PNG
        
        # Colour palette (cmap)
        if getattr(args, 'cmap', None):
            config.cmap = args.cmap.strip()
        
        # FPS
        if args.fps != 10:
            config.fps = args.fps
        
        # Zoom
        if args.zoom != 1.0:
            config.zoom_factor = args.zoom
        
        # Percentile
        if args.percentile != 5:
            config.percentile = args.percentile
        
        # Transparent
        if args.transparent:
            config.transparent = True
        
        # Designer mode
        if args.designer_mode:
            config.designer_mode = True
        if getattr(args, 'designer_square_crop', False):
            config.designer_square_crop = True
        
        # Ignore values
        if args.ignore_values:
            config.ignore_values = args.ignore_values
        
        # Color scale range (vmin/vmax)
        if getattr(args, 'vmin', None) is not None:
            config.vmin = args.vmin
        if getattr(args, 'vmax', None) is not None:
            config.vmax = args.vmax
        
        # Overwrite
        if args.overwrite:
            config.overwrite_existing = True
        
        # Multi-file specific settings
        if is_multi_file:
            config.global_colorbar = True
            config.pre_scan_files = True
    
    def _validate_config(self, config: AnimationConfig, is_multi_file: bool) -> bool:
        """Validate configuration.
        
        Args:
            config: Configuration to validate
            is_multi_file: Whether this is a multi-file operation
            
        Returns:
            bool: True if configuration is valid
        """
        errors = []
        
        if not config.variable:
            errors.append("No variable specified")
        
        if not config.output_pattern:
            errors.append("No output pattern specified")
        
        # Validate configuration object
        is_valid, config_errors = config.get_validation_summary()
        if not is_valid:
            errors.extend(config_errors)
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
