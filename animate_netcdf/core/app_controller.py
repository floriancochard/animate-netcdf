#!/usr/bin/env python3
"""
Application Controller for NetCDF Animations
Manages different modes of operation and coordinates between components
"""

import os
import sys
from typing import Optional, Dict, Any, List
from argparse import Namespace

from animate_netcdf.core.cli_parser import CLIParser
from animate_netcdf.core.config_manager import ConfigManager, AnimationConfig
from animate_netcdf.core.file_manager import NetCDFFileManager
from animate_netcdf.animators.single_file_animator import SingleFileAnimator
from animate_netcdf.animators.multi_file_animator import MultiFileAnimator
from animate_netcdf.utils.logging_utils import setup_all_logging


class AppController:
    """Main application controller for NetCDF animations.
    
    This class orchestrates the entire animation creation process, handling
    different modes of operation (interactive, non-interactive, batch, etc.)
    and coordinating between various components like file management,
    configuration, and animation creation.
    """
    
    def __init__(self) -> None:
        """Initialize the application controller."""
        setup_all_logging()
        self.args: Optional[Namespace] = None
        self.config_manager: Optional[ConfigManager] = None
        self.mode: Optional[str] = None
        
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
            
            # Determine operation mode
            self.mode = CLIParser.get_mode_from_args(args)
            
            # Initialize configuration manager
            self.config_manager = ConfigManager(args.config if args.config else None)
            
            # Adjust mode based on loaded configuration
            if self.mode == "interactive" and not args.variable:
                # Check if we have a loaded configuration with a variable
                # Try to load the configuration if not already loaded
                if not self.config_manager.loaded:
                    self.config_manager.load_config()
                
                if self.config_manager.loaded:
                    config = self.config_manager.get_config()
                    if config.variable:
                        self.mode = "non_interactive"
            
            # Handle different modes
            if self.mode == "interactive":
                return self._handle_interactive_mode()
            elif self.mode == "non_interactive":
                return self._handle_non_interactive_mode()
            elif self.mode == "batch":
                return self._handle_batch_mode()
            elif self.mode == "single_plot":
                return self._handle_single_plot_mode()
            else:
                print(f"❌ Unknown mode: {self.mode}")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Application error: {e}")
            return False
    
    def _handle_interactive_mode(self) -> bool:
        """Handle interactive mode.
        
        Returns:
            bool: True if interactive mode completed successfully
        """
        print("=" * 60)
        print("Unified Animation Creator for NetCDF Data")
        print("=" * 60)
        
        # If no input pattern is provided, start interactive file selection
        if self.args.input_pattern is None:
            return self._handle_file_selection_interactive()
        
        # Check if this is a multi-file pattern
        is_multi_file = CLIParser.is_multi_file_pattern(self.args.input_pattern)
        
        if is_multi_file:
            return self._handle_multi_file_interactive()
        else:
            return self._handle_single_file_interactive()
    
    def _handle_single_file_interactive(self) -> bool:
        """Handle interactive mode for single file.
        
        Returns:
            bool: True if single file interactive mode completed successfully
        """
        # Check if input pattern is None (should not happen in this method)
        if self.args.input_pattern is None:
            print("❌ No file specified")
            return False
            
        # Check if file exists
        if not os.path.exists(self.args.input_pattern):
            print(f"❌ File not found: {self.args.input_pattern}")
            return False
        
        try:
            # Create single file animator
            animator = SingleFileAnimator(self.args.input_pattern)
            
            # Explore dataset
            animator.explore_dataset()
            
            # Show main menu
            return self._show_interactive_menu(animator)
            
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
    
    def _handle_file_selection_interactive(self) -> bool:
        """Handle interactive file selection when no file is specified.
        
        Returns:
            bool: True if file selection completed successfully
        """
        print("\n📁 No file specified. Please select a file or pattern:")
        print("1. Enter a single NetCDF file path")
        print("2. Enter a file pattern (e.g., *.nc, F4C_*.nc)")
        print("3. Browse current directory for NetCDF files")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            file_path = input("Enter the path to your NetCDF file: ").strip()
            if not file_path:
                print("❌ No file path provided")
                return False
            
            # Update the args object with the selected file
            self.args.input_pattern = file_path
            return self._handle_single_file_interactive()
            
        elif choice == "2":
            pattern = input("Enter the file pattern (e.g., *.nc, F4C_*.nc): ").strip()
            if not pattern:
                print("❌ No pattern provided")
                return False
            
            # Update the args object with the selected pattern
            self.args.input_pattern = pattern
            return self._handle_multi_file_interactive()
            
        elif choice == "3":
            # Browse current directory for NetCDF files
            nc_files = []
            for file in os.listdir('.'):
                if file.endswith('.nc') or file.endswith('.NC'):
                    nc_files.append(file)
            
            if not nc_files:
                print("❌ No NetCDF files found in current directory")
                return False
            
            print("\n📁 NetCDF files found in current directory:")
            for i, file in enumerate(nc_files, 1):
                print(f"{i}. {file}")
            
            file_choice = input(f"\nSelect file number (1-{len(nc_files)}): ").strip()
            try:
                file_idx = int(file_choice) - 1
                selected_file = nc_files[file_idx]
                self.args.input_pattern = selected_file
                return self._handle_single_file_interactive()
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return False
                
        elif choice == "4":
            print("Goodbye!")
            return True
        else:
            print("❌ Invalid choice")
            return False
    
    def _handle_multi_file_interactive(self) -> bool:
        """Handle interactive mode for multiple files.
        
        Returns:
            bool: True if multi-file interactive mode completed successfully
        """
        print(f"\n🎬 Multi-file mode detected")
        print(f"📁 Pattern: {self.args.input_pattern}")
        
        # Initialize file manager
        file_manager = NetCDFFileManager(self.args.input_pattern)
        files = file_manager.discover_files()
        
        if not files:
            print(f"❌ No files found matching pattern: {self.args.input_pattern}")
            return False
        
        # Validate file consistency
        consistency_errors = file_manager.validate_consistency()
        if consistency_errors:
            print("❌ File consistency errors:")
            for error in consistency_errors:
                print(f"  - {error}")
            return False
        
        # Get common variables
        common_vars = file_manager.get_common_variables()
        if not common_vars:
            print("❌ No common variables found across all files")
            return False
        
        print(f"📊 Common variables: {common_vars}")
        
        # Get sample file for level detection
        sample_file = file_manager.get_sample_file()
        
        # Collect interactive configuration
        config = self.config_manager.collect_interactive_config(common_vars, len(files), sample_file)
        
        # Set file pattern
        config.file_pattern = self.args.input_pattern
        
        # Create multi-file animator with the interactive configuration
        multi_animator = MultiFileAnimator(file_manager, config)
        
        # Create animation
        success = multi_animator.create_animation_sequence()
        
        if success:
            print("✅ Multi-file animation completed successfully!")
        else:
            print("❌ Multi-file animation failed")
        
        return success
    
    def _handle_non_interactive_mode(self) -> bool:
        """Handle non-interactive mode.
        
        Returns:
            bool: True if non-interactive mode completed successfully
        """
        # If no input pattern is provided, fall back to interactive mode
        if self.args.input_pattern is None:
            print("⚠️  No file specified, falling back to interactive mode")
            return self._handle_interactive_mode()
        
        # Check if this is a multi-file pattern
        is_multi_file = CLIParser.is_multi_file_pattern(self.args.input_pattern)
        
        if is_multi_file:
            return self._handle_multi_file_non_interactive()
        else:
            return self._handle_single_file_non_interactive()
    
    def _handle_single_file_non_interactive(self) -> bool:
        """Handle non-interactive mode for single file.
        
        Returns:
            bool: True if single file non-interactive mode completed successfully
        """
        if not os.path.exists(self.args.input_pattern):
            print(f"❌ File not found: {self.args.input_pattern}")
            return False
        
        try:
            # Create single file animator
            animator = SingleFileAnimator(self.args.input_pattern)
            
            # Handle level selection
            level_index: Optional[int] = None
            if self.args.level is not None:
                if self.args.level == -1:
                    level_index = None  # Average over levels
                    print("📊 Will average over all levels")
                else:
                    level_index = self.args.level
                    print(f"📊 Will use level {level_index}")
            
            # Update percentile filter if specified
            if self.args.percentile != 5:
                original_filter = animator.filter_low_values
                def custom_filter(data, percentile=self.args.percentile):
                    return original_filter(data, percentile)
                animator.filter_low_values = custom_filter
            
            # Determine animate dimension
            animate_dim = self.args.animate_dim
            ds_dims = list(animator.ds.dims)
            spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v',
                           'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v']
            candidate_dims = [d for d in ds_dims if d not in spatial_dims]
            
            if animate_dim not in ds_dims:
                if candidate_dims:
                    print(f"⚠️  Dimension '{animate_dim}' not found. Using '{candidate_dims[0]}' instead.")
                    animate_dim = candidate_dims[0]
                else:
                    print(f"❌ Error: No suitable animation dimension found in file. Available dimensions: {ds_dims}")
                    return False
            
            # Check if variable is required but not provided
            if not self.args.variable:
                print("💡 Available variables:")
                var_info = animator.get_variable_info()
                for i, (var_name, info) in enumerate(var_info.items(), 1):
                    units = info['attrs'].get('units', 'N/A')
                    print(f"  {i}. {var_name} (units: {units})")
                print("\n❌ No variable specified.")
                print("Options:")
                print("1. Use --variable to specify a variable")
                print("2. Switch to interactive mode")
                print("3. Exit")
                
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == "1":
                    print("Please run the command again with --variable <variable_name>")
                    return False
                elif choice == "2":
                    print("\nSwitching to interactive mode...")
                    return self._show_interactive_menu(animator)
                elif choice == "3":
                    print("Goodbye!")
                    return True
                else:
                    print("Invalid choice!")
                    return False
            
            # Create animation
            if self.args.output:
                output_file = self.args.output
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{timestamp}_{self.args.variable}_{self.args.type}_animation.mp4"
            
            print(f"\n🎬 Creating single animation...")
            print(f"Variable: {self.args.variable}")
            print(f"Type: {self.args.type}")
            print(f"Output: {output_file}")
            print(f"FPS: {self.args.fps}")
            print(f"Total frames: {len(animator.ds[animate_dim])}")
            
            success = animator.create_animation(
                self.args.variable, output_file, self.args.fps, self.args.type,
                animate_dim=animate_dim, level_index=level_index, zoom_factor=self.args.zoom
            )
            
            # Clean up
            animator.close()
            return success
            
        except Exception as e:
            print(f"❌ Error in non-interactive mode: {e}")
            return False
    
    def _handle_multi_file_non_interactive(self) -> bool:
        """Handle non-interactive mode for multiple files.
        
        Returns:
            bool: True if multi-file non-interactive mode completed successfully
        """
        print(f"\n🎬 Multi-file mode detected")
        print(f"📁 Pattern: {self.args.input_pattern}")
        
        # Initialize file manager
        file_manager = NetCDFFileManager(self.args.input_pattern)
        files = file_manager.discover_files()
        
        if not files:
            print(f"❌ No files found matching pattern: {self.args.input_pattern}")
            return False
        
        # Validate file consistency
        consistency_errors = file_manager.validate_consistency()
        if consistency_errors:
            print("❌ File consistency errors:")
            for error in consistency_errors:
                print(f"  - {error}")
            return False
        
        # Load or create configuration
        config = self._get_or_create_config(file_manager, files)
        if not config:
            return False
        
        # Set the file pattern for the current operation
        config.file_pattern = self.args.input_pattern
        
        # Update configuration with command line arguments
        self._update_config_from_args(config)
        
        # Check if variable is required but not provided
        if not config.variable and not self.args.variable:
            print("❌ No variable specified. Falling back to interactive mode for variable selection.")
            return self._handle_multi_file_interactive()
        
        # Validate configuration
        if not self.config_manager.validate_config():
            return False
        
        # Save configuration if requested
        if self.args.save_config:
            self.config_manager.save_config(self.args.save_config)
        
        # Create multi-file animator
        multi_animator = MultiFileAnimator(file_manager, config)
        
        # Create animation
        success = multi_animator.create_animation_sequence()
        
        if success:
            print("✅ Multi-file animation completed successfully!")
        else:
            print("❌ Multi-file animation failed")
        
        return success
    
    def _handle_batch_mode(self) -> bool:
        """Handle batch mode for creating animations for all variables.
        
        Returns:
            bool: True if batch mode completed successfully
        """
        if not os.path.exists(self.args.input_pattern):
            print(f"❌ File not found: {self.args.input_pattern}")
            return False
        
        try:
            # Create single file animator
            animator = SingleFileAnimator(self.args.input_pattern)
            
            # Handle level selection
            level_index: Optional[int] = None
            if self.args.level is not None:
                if self.args.level == -1:
                    level_index = None  # Average over levels
                    print("📊 Will average over all levels")
                else:
                    level_index = self.args.level
                    print(f"📊 Will use level {level_index}")
            
            # Update percentile filter if specified
            if self.args.percentile != 5:
                original_filter = animator.filter_low_values
                def custom_filter(data, percentile=self.args.percentile):
                    return original_filter(data, percentile)
                animator.filter_low_values = custom_filter
            
            # Determine animate dimension
            animate_dim = self.args.animate_dim
            ds_dims = list(animator.ds.dims)
            spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v',
                           'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v']
            candidate_dims = [d for d in ds_dims if d not in spatial_dims]
            
            if animate_dim not in ds_dims:
                if candidate_dims:
                    print(f"⚠️  Dimension '{animate_dim}' not found. Using '{candidate_dims[0]}' instead.")
                    animate_dim = candidate_dims[0]
                else:
                    print(f"❌ Error: No suitable animation dimension found in file. Available dimensions: {ds_dims}")
                    return False
            
            print(f"\n🎬 Creating batch animations...")
            print(f"Type: {self.args.type}")
            print(f"FPS: {self.args.fps}")
            
            success = animator.create_batch_animations(
                self.args.type, self.args.fps, animate_dim, level_index, self.args.zoom
            )
            
            # Clean up
            animator.close()
            return success
            
        except Exception as e:
            print(f"❌ Error in batch mode: {e}")
            return False
    
    def _handle_single_plot_mode(self) -> bool:
        """Handle single plot mode.
        
        Returns:
            bool: True if single plot mode completed successfully
        """
        if not os.path.exists(self.args.input_pattern):
            print(f"❌ File not found: {self.args.input_pattern}")
            return False
        
        # Check if variable is required
        if not self.args.variable:
            print("❌ No variable specified. Please set --variable.")
            return False
        
        try:
            # Create single file animator
            animator = SingleFileAnimator(self.args.input_pattern)
            
            # Handle level selection
            level_index: Optional[int] = None
            if self.args.level is not None:
                if self.args.level == -1:
                    level_index = None  # Average over levels
                    print("📊 Will average over all levels")
                else:
                    level_index = self.args.level
                    print(f"📊 Will use level {level_index}")
            
            # Determine animate dimension
            animate_dim = self.args.animate_dim
            ds_dims = list(animator.ds.dims)
            spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v',
                           'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v']
            candidate_dims = [d for d in ds_dims if d not in spatial_dims]
            
            if animate_dim not in ds_dims:
                if candidate_dims:
                    print(f"⚠️  Dimension '{animate_dim}' not found. Using '{candidate_dims[0]}' instead.")
                    animate_dim = candidate_dims[0]
                else:
                    print(f"❌ Error: No suitable animation dimension found in file. Available dimensions: {ds_dims}")
                    return False
            
            print(f"\n📊 Creating single plot...")
            print(f"Variable: {self.args.variable}")
            print(f"Type: {self.args.type}")
            print(f"Time step: {self.args.time_step}")
            
            success = animator.create_single_plot(
                self.args.variable, self.args.type, self.args.time_step,
                animate_dim, level_index, self.args.zoom
            )
            
            # Clean up
            animator.close()
            return success
            
        except Exception as e:
            print(f"❌ Error in single plot mode: {e}")
            return False
    
    def _get_or_create_config(self, file_manager: NetCDFFileManager, files: List[str]) -> Optional[AnimationConfig]:
        """Get or create configuration for multi-file processing.
        
        Args:
            file_manager: File manager instance
            files: List of discovered files
            
        Returns:
            Optional[AnimationConfig]: Configuration object or None if creation failed
        """
        # Check if we already have a loaded configuration
        if self.config_manager.loaded:
            config = self.config_manager.get_config()
            print(f"📁 Using loaded configuration")
            print(f"   Variable: {config.variable}")
            print(f"   Plot type: {config.plot_type.value}")
            print(f"   FPS: {config.fps}")
            return config
        
        # Try to load configuration from command line argument
        if self.args.config:
            if self.config_manager.load_config():
                config = self.config_manager.get_config()
                print(f"📁 Loaded configuration from {self.args.config}")
                return config
            else:
                print(f"❌ Failed to load configuration from {self.args.config}")
                return None
        
        # Try to load default configuration file if no --config specified
        if not self.args.config:
            # Try to load the default config file
            if self.config_manager.load_config():
                config = self.config_manager.get_config()
                # Set the file pattern for the current operation
                config.file_pattern = self.args.input_pattern
                print(f"📁 Loaded default configuration from {self.config_manager.config_file}")
                print(f"   Variable: {config.variable}")
                print(f"   Plot type: {config.plot_type.value}")
                print(f"   FPS: {config.fps}")
                return config
            else:
                print(f"📁 No default configuration file found, will create new configuration")
        
        # Create new configuration interactively
        print(f"📁 Creating new configuration...")
        first_file = file_manager.get_sample_file()
        if not first_file:
            print("❌ No sample file available")
            return None
        
        # Get common variables
        common_vars = file_manager.get_common_variables()
        if not common_vars:
            print("❌ No common variables found across all files")
            return None
        
        print(f"✅ All files have consistent structure")
        print(f"📊 Common variables: {common_vars}")
        
        # Collect configuration interactively
        config = self.config_manager.collect_interactive_config(common_vars, len(files), first_file)
        
        # Set file pattern
        config.file_pattern = self.args.input_pattern
        
        return config
    
    def _update_config_from_args(self, config: AnimationConfig) -> None:
        """Update configuration with command line arguments.
        
        Args:
            config: Configuration object to update
        """
        if self.args.variable:
            config.variable = self.args.variable
        
        if self.args.output:
            config.output_pattern = self.args.output
        if self.args.fps != 10:
            config.fps = self.args.fps
        if self.args.percentile != 5:
            config.percentile = self.args.percentile
        if self.args.type != 'efficient':
            from config_manager import PlotType
            config.plot_type = PlotType(self.args.type)
        if self.args.zoom != 1.0:
            config.zoom_factor = self.args.zoom
        if self.args.overwrite:
            config.overwrite_existing = True
        if not self.args.pre_scan:
            config.pre_scan_files = False
        if not self.args.global_colorbar:
            config.global_colorbar = False
    
    def _show_interactive_menu(self, animator: SingleFileAnimator) -> bool:
        """Show interactive menu for single file.
        
        Args:
            animator: Single file animator instance
            
        Returns:
            bool: True if menu interaction completed successfully
        """
        print("\n" + "=" * 60)
        print("Main Menu")
        print("=" * 60)
        print("1. Create single plot (preview)")
        print("2. Create single animation")
        print("3. Create batch animations (all variables)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            return self._handle_interactive_single_plot(animator)
        elif choice == "2":
            return self._handle_interactive_single_animation(animator)
        elif choice == "3":
            return self._handle_interactive_batch_animation(animator)
        elif choice == "4":
            print("Goodbye!")
            return True
        else:
            print("Invalid choice!")
            return False
    
    def _handle_interactive_single_plot(self, animator: SingleFileAnimator) -> bool:
        """Handle interactive single plot creation.
        
        Args:
            animator: Single file animator instance
            
        Returns:
            bool: True if plot creation completed successfully
        """
        print("\n" + "=" * 60)
        print("Single Plot Creator")
        print("=" * 60)
        
        # Show variables
        var_info = animator.get_variable_info()
        for i, (var_name, info) in enumerate(var_info.items(), 1):
            units = info['attrs'].get('units', 'N/A')
            print(f"{i}. {var_name} (units: {units})")
        
        # Select variable
        var_choice = input(f"\nSelect variable number (1-{len(var_info)}): ").strip()
        try:
            var_idx = int(var_choice) - 1
            variable = list(var_info.keys())[var_idx]
        except (ValueError, IndexError):
            print("Invalid choice!")
            return False
        
        # Select plot type
        print("\nPlot types:")
        print("1. Efficient (fast, imshow with Cartopy)")
        print("2. Contour (detailed with Cartopy)")
        print("3. Heatmap (simple grid)")
        
        plot_choice = input("Select plot type (1-3): ").strip()
        plot_types = ['efficient', 'contour', 'heatmap']
        try:
            plot_idx = int(plot_choice) - 1
            plot_type = plot_types[plot_idx]
        except (ValueError, IndexError):
            print("Invalid choice!")
            return False
        
        # Select level if variable has level dimension
        level_index: Optional[int] = None
        if 'level' in animator.ds[variable].dims:
            level_index = animator.select_level_interactive(variable)
        
        # Get zoom factor
        zoom_input = input("Zoom factor (default: 1.0, no zoom): ").strip()
        if not zoom_input:
            zoom_factor = 1.0
        else:
            try:
                zoom_factor = float(zoom_input)
                if zoom_factor <= 0:
                    print("❌ Zoom factor must be positive. Using 1.0 (no zoom)")
                    zoom_factor = 1.0
            except ValueError:
                print("❌ Invalid zoom factor. Using 1.0 (no zoom)")
                zoom_factor = 1.0
        
        # Create plot
        return animator.create_single_plot(variable, plot_type, animate_dim='time', level_index=level_index, zoom_factor=zoom_factor)
    
    def _handle_interactive_single_animation(self, animator: SingleFileAnimator) -> bool:
        """Handle interactive single animation creation.
        
        Args:
            animator: Single file animator instance
            
        Returns:
            bool: True if animation creation completed successfully
        """
        print("\n" + "=" * 60)
        print("Single Animation Creator")
        print("=" * 60)
        
        # Show variables
        var_info = animator.get_variable_info()
        for i, (var_name, info) in enumerate(var_info.items(), 1):
            units = info['attrs'].get('units', 'N/A')
            print(f"{i}. {var_name} (units: {units})")
        
        # Select variable
        var_choice = input(f"\nSelect variable number (1-{len(var_info)}): ").strip()
        try:
            var_idx = int(var_choice) - 1
            variable = list(var_info.keys())[var_idx]
        except (ValueError, IndexError):
            print("Invalid choice!")
            return False
        
        # Select animation type
        print("\nAnimation types:")
        print("1. Efficient (fast, imshow with Cartopy) - Recommended")
        print("2. Contour (detailed with Cartopy)")
        print("3. Heatmap (simple grid)")
        
        type_choice = input("Select animation type (1-3): ").strip()
        anim_types = ['efficient', 'contour', 'heatmap']
        try:
            type_idx = int(type_choice) - 1
            anim_type = anim_types[type_idx]
        except (ValueError, IndexError):
            print("Invalid choice!")
            return False
        
        # Get output filename and FPS
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"{timestamp}_{variable}_{anim_type}_animation.mp4"
        output_file = input(f"\nOutput filename (default: {default_output}): ").strip()
        if not output_file:
            output_file = default_output
        
        fps = input("Frames per second (default: 10): ").strip()
        if not fps:
            fps = 10
        else:
            try:
                fps = int(fps)
            except ValueError:
                print(f"❌ Invalid FPS value: {fps}. Using default: 10")
                fps = 10
        
        # Select level if variable has level dimension
        level_index: Optional[int] = None
        if 'level' in animator.ds[variable].dims:
            level_index = animator.select_level_interactive(variable)
        
        # Get zoom factor
        zoom_input = input("Zoom factor (default: 1.0, no zoom): ").strip()
        if not zoom_input:
            zoom_factor = 1.0
        else:
            try:
                zoom_factor = float(zoom_input)
                if zoom_factor <= 0:
                    print("❌ Zoom factor must be positive. Using 1.0 (no zoom)")
                    zoom_factor = 1.0
            except ValueError:
                print("❌ Invalid zoom factor. Using 1.0 (no zoom)")
                zoom_factor = 1.0
        
        # Create animation
        print(f"\n🎬 Creating {anim_type} animation...")
        print(f"Variable: {variable}")
        print(f"Output: {output_file}")
        print(f"FPS: {fps}")
        print(f"Zoom factor: {zoom_factor}")
        print(f"Total frames: {len(animator.ds['time'])}")
        
        return animator.create_animation(variable, output_file, fps, anim_type, animate_dim='time', level_index=level_index, zoom_factor=zoom_factor)
    
    def _handle_interactive_batch_animation(self, animator: SingleFileAnimator) -> bool:
        """Handle interactive batch animation creation.
        
        Args:
            animator: Single file animator instance
            
        Returns:
            bool: True if batch animation creation completed successfully
        """
        print("\n" + "=" * 60)
        print("Batch Animation Creator")
        print("=" * 60)
        
        # Select animation type
        print("Animation types:")
        print("1. Efficient (fast, imshow with Cartopy) - Recommended")
        print("2. Contour (detailed with Cartopy)")
        print("3. Heatmap (simple grid)")
        
        type_choice = input("Select animation type (1-3): ").strip()
        anim_types = ['efficient', 'contour', 'heatmap']
        try:
            type_idx = int(type_choice) - 1
            anim_type = anim_types[type_idx]
        except (ValueError, IndexError):
            print("Invalid choice!")
            return False
        
        # Get FPS
        fps = input("Frames per second (default: 10): ").strip()
        if not fps:
            fps = 10
        else:
            try:
                fps = int(fps)
            except ValueError:
                print(f"❌ Invalid FPS value: {fps}. Using default: 10")
                fps = 10
        
        # Check if any variable has level dimension
        level_index: Optional[int] = None
        var_info = animator.get_variable_info()
        has_level_dim = any('level' in info['dims'] for info in var_info.values())
        
        if has_level_dim:
            print(f"\n📊 Some variables have level dimensions.")
            level_choice = input("Select level handling: 'avg' for average over levels, 'select' to choose specific level: ").strip()
            
            if level_choice.lower() == 'select':
                # Use the first variable with level dimension to get level info
                for var_name, info in var_info.items():
                    if 'level' in info['dims']:
                        level_index = animator.select_level_interactive(var_name)
                        break
            else:
                level_index = None  # Average over levels
        
        # Get zoom factor
        zoom_input = input("Zoom factor (default: 1.0, no zoom): ").strip()
        if not zoom_input:
            zoom_factor = 1.0
        else:
            try:
                zoom_factor = float(zoom_input)
                if zoom_factor <= 0:
                    print("❌ Zoom factor must be positive. Using 1.0 (no zoom)")
                    zoom_factor = 1.0
            except ValueError:
                print("❌ Invalid zoom factor. Using 1.0 (no zoom)")
                zoom_factor = 1.0
        
        # Create batch animations
        return animator.create_batch_animations(anim_type, fps, 'time', level_index, zoom_factor) 