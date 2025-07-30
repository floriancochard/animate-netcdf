#!/usr/bin/env python3
"""
Configuration File Creator for NetCDF Animations
Create configuration files for both single and multi-file animations
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

# Import our modules
try:
    from config_manager import AnimationConfig, ConfigManager
    from file_manager import NetCDFFileManager
    MULTI_FILE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Multi-file components not available: {e}")
    MULTI_FILE_AVAILABLE = False


def create_single_file_config(file_path: str, output_file: str = None) -> bool:
    """Create configuration for a single NetCDF file."""
    print(f"\n📁 Creating configuration for: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        import xarray as xr
        
        # Load dataset to get variable information
        with xr.open_dataset(file_path) as ds:
            variables = list(ds.data_vars.keys())
            dimensions = dict(ds.dims)
            
            print(f"📊 Variables: {variables}")
            print(f"📏 Dimensions: {dimensions}")
            
            # Find animation dimension
            spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']
            animate_dims = [dim for dim in dimensions.keys() if dim not in spatial_dims]
            
            if not animate_dims:
                print("❌ No suitable animation dimension found")
                return False
            
            animate_dim = animate_dims[0]
            print(f"🎬 Animation dimension: {animate_dim} ({dimensions[animate_dim]} steps)")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Create configuration
    config = AnimationConfig()
    
    # Set file-specific defaults
    config.variable = variables[0] if variables else None
    config.animate_dim = animate_dim
    config.file_pattern = file_path
    
    # Interactive configuration collection
    print(f"\n⚙️  Configuration Setup")
    print(f"=" * 40)
    
    # Variable selection
    print(f"\n📊 Available variables:")
    for i, var in enumerate(variables, 1):
        print(f"  {i}. {var}")
    
    while True:
        try:
            choice = input(f"\nSelect variable number (1-{len(variables)}): ").strip()
            var_idx = int(choice) - 1
            if 0 <= var_idx < len(variables):
                config.variable = variables[var_idx]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(variables)}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Plot type selection
    print(f"\n🎨 Plot types:")
    print("1. Efficient (fast, imshow with Cartopy) - Recommended")
    print("2. Contour (detailed with Cartopy)")
    print("3. Heatmap (simple grid)")
    
    while True:
        try:
            choice = input("Select plot type (1-3): ").strip()
            plot_types = ['efficient', 'contour', 'heatmap']
            plot_idx = int(choice) - 1
            if 0 <= plot_idx < 3:
                config.plot_type = plot_types[plot_idx]
                break
            else:
                print("❌ Please enter a number between 1 and 3")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # FPS selection
    while True:
        try:
            fps_input = input(f"\nFrames per second (default: {config.fps}): ").strip()
            if not fps_input:
                break
            fps = int(fps_input)
            if 1 <= fps <= 60:
                config.fps = fps
                break
            else:
                print("❌ FPS must be between 1 and 60")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Output settings
    default_output = f"{config.variable}_{config.plot_type}_animation.{config.output_format}"
    output_file = input(f"\nOutput filename (default: {default_output}): ").strip()
    if output_file:
        config.output_pattern = output_file
    else:
        config.output_pattern = default_output
    
    # Advanced settings
    print(f"\n⚙️  Advanced settings:")
    
    # Percentile filtering
    while True:
        try:
            percentile_input = input(f"Percentile threshold for filtering (default: {config.percentile}): ").strip()
            if not percentile_input:
                break
            percentile = int(percentile_input)
            if 0 <= percentile <= 100:
                config.percentile = percentile
                break
            else:
                print("❌ Percentile must be between 0 and 100")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Level selection (if applicable)
    if 'level' in dimensions:
        print(f"\n📊 Variable has {dimensions['level']} levels")
        level_choice = input("Select level handling: 'avg' for average, 'select' to choose level, or 'none' to skip: ").strip().lower()
        
        if level_choice == 'select':
            while True:
                try:
                    level_input = input(f"Select level index (0-{dimensions['level']-1}): ").strip()
                    level_idx = int(level_input)
                    if 0 <= level_idx < dimensions['level']:
                        config.level_index = level_idx
                        break
                    else:
                        print(f"❌ Level index must be between 0 and {dimensions['level']-1}")
                except ValueError:
                    print("❌ Please enter a valid number")
        elif level_choice == 'avg':
            config.level_index = None  # Will average over levels
        # else: skip level selection
    
    # Save configuration
    config_manager = ConfigManager()
    config_manager.set_config(config)
    
    if output_file:
        config_manager.save_config(output_file)
    else:
        config_manager.save_config()
    
    print(f"\n✅ Configuration created successfully!")
    return True


def create_multi_file_config(file_pattern: str, output_file: str = None) -> bool:
    """Create configuration for multiple NetCDF files."""
    if not MULTI_FILE_AVAILABLE:
        print("❌ Multi-file functionality not available")
        return False
    
    print(f"\n📁 Creating configuration for pattern: {file_pattern}")
    
    # Discover files
    file_manager = NetCDFFileManager(file_pattern)
    files = file_manager.discover_files()
    
    if not files:
        print(f"❌ No files found matching pattern: {file_pattern}")
        return False
    
    print(f"✅ Found {len(files)} files")
    
    # Get common variables
    common_vars = file_manager.get_common_variables()
    if not common_vars:
        print("❌ No common variables found across all files")
        return False
    
    print(f"📊 Common variables: {common_vars}")
    
    # Create configuration using the existing interactive collection
    config_manager = ConfigManager()
    config = config_manager.collect_interactive_config(common_vars, len(files))
    
    # Set file pattern
    config.file_pattern = file_pattern
    
    # Save configuration
    if output_file:
        config_manager.save_config(output_file)
    else:
        config_manager.save_config()
    
    print(f"\n✅ Multi-file configuration created successfully!")
    return True


def create_template_config(output_file: str = "template_config.json"):
    """Create a template configuration file."""
    print(f"\n📝 Creating template configuration...")
    
    config = AnimationConfig()
    
    # Set template values
    config.variable = "your_variable_name"
    config.plot_type = "efficient"
    config.fps = 10
    config.output_pattern = "animation.mp4"
    config.file_pattern = "*.nc"
    config.animate_dim = "time"
    config.percentile = 5
    config.global_colorbar = True
    config.pre_scan_files = True
    
    # Save template
    config_manager = ConfigManager()
    config_manager.set_config(config)
    config_manager.save_config(output_file)
    
    print(f"✅ Template configuration saved to: {output_file}")
    print(f"📝 Edit this file and use it with: python main.py --config {output_file}")
    return True


def main():
    """Main function for configuration creation."""
    parser = argparse.ArgumentParser(
        description="Create configuration files for NetCDF animations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create config for single file
  python create_config.py single_file.nc --output my_config.json
  
  # Create config for multiple files
  python create_config.py "F4C_00.2.SEG01.OUT.*.nc" --output multi_config.json
  
  # Create template config
  python create_config.py --template template_config.json
        """
    )
    
    parser.add_argument('input', nargs='?', 
                       help='NetCDF file or pattern (e.g., "*.nc")')
    
    parser.add_argument('--output', '-o',
                       help='Output configuration file (default: animation_config.json)')
    
    parser.add_argument('--template', '-t', action='store_true',
                       help='Create a template configuration file')
    
    parser.add_argument('--no-interactive', action='store_true',
                       help='Skip interactive mode (use defaults)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NetCDF Animation Configuration Creator")
    print("=" * 60)
    
    if args.template:
        # Create template configuration
        create_template_config(args.output or "template_config.json")
        return
    
    if not args.input:
        print("❌ Please provide a file or pattern, or use --template for a template")
        return
    
    # Determine if this is a multi-file pattern
    is_multi_file = ('*' in args.input or '?' in args.input)
    
    if is_multi_file:
        success = create_multi_file_config(args.input, args.output)
    else:
        success = create_single_file_config(args.input, args.output)
    
    if success:
        print(f"\n🎉 Configuration created successfully!")
        print(f"💡 Use it with: python main.py --config {args.output or 'animation_config.json'}")
    else:
        print(f"\n❌ Failed to create configuration")


if __name__ == "__main__":
    main() 