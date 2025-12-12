#!/usr/bin/env python3
"""
Interactive Flow
Handles all interactive prompts for visualization configuration
"""

import os
import xarray as xr
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from animate_netcdf.core.config_manager import AnimationConfig, PlotType, OutputFormat
from animate_netcdf.utils.netcdf_explorer import NetCDFExplorer
from animate_netcdf.utils.data_processing import DataProcessor


class InteractiveFlow:
    """Handles interactive configuration collection for visualization."""
    
    def __init__(self):
        """Initialize interactive flow."""
        self.explorer = NetCDFExplorer()
        self.data_processor = DataProcessor()
    
    def collect_visualization_config(self, input_path: str, 
                                    is_multi_file: bool = False) -> Optional[AnimationConfig]:
        """Collect visualization configuration interactively.
        
        Args:
            input_path: Path to file or pattern
            is_multi_file: Whether this is a multi-file pattern
            
        Returns:
            AnimationConfig: Collected configuration or None if cancelled
        """
        config = AnimationConfig()
        
        print("\n" + "=" * 60)
        print("🎬 NetCDF Visualization Setup")
        print("=" * 60)
        
        # Step 1: Variable selection
        variable = self._select_variable(input_path, is_multi_file)
        if not variable:
            return None
        config.variable = variable
        
        # Step 2: Plot type
        plot_type = self._select_plot_type()
        if not plot_type:
            return None
        config.plot_type = PlotType(plot_type)
        
        # Step 3: Output format (for multi-file only)
        if is_multi_file:
            output_format = self._select_output_format()
            if not output_format:
                return None
            config.output_format = OutputFormat(output_format)
        
        # Step 4: Output filename
        output_file = self._get_output_filename(variable, plot_type, is_multi_file)
        if not output_file:
            return None
        config.output_pattern = output_file
        
        # Step 5: FPS (for animations)
        if plot_type in ['efficient', 'contour'] and is_multi_file:
            fps = self._get_fps()
            config.fps = fps
        
        # Step 6: Zoom factor
        zoom = self._get_zoom_factor()
        config.zoom_factor = zoom
        
        # Step 7: Percentile filtering
        percentile = self._get_percentile()
        config.percentile = percentile
        
        # Step 8: Ignore values
        ignore_values = self._get_ignore_values()
        config.ignore_values = ignore_values
        
        # Step 9: Designer mode
        designer_mode = self._get_designer_mode()
        config.designer_mode = designer_mode
        
        # Step 10: Transparent background (for PNG)
        if not is_multi_file or output_format == 'png':
            transparent = self._get_transparent_background()
            config.transparent = transparent
        
        return config
    
    def _select_variable(self, input_path: str, is_multi_file: bool) -> Optional[str]:
        """Select variable interactively."""
        print("\n📊 Step 1: Variable Selection")
        print("-" * 40)
        
        if is_multi_file:
            # For multi-file, use file manager to get common variables
            from animate_netcdf.core.file_manager import NetCDFFileManager
            file_manager = NetCDFFileManager(input_path)
            files = file_manager.discover_files()
            if not files:
                print("❌ No files found")
                return None
            
            common_vars = file_manager.get_common_variables()
            if not common_vars:
                print("❌ No common variables found")
                return None
            
            variables = common_vars
        else:
            # For single file, explore structure
            try:
                structure = self.explorer.explore_netcdf_structure(input_path)
                variables = self._extract_variables_from_structure(structure)
                if not variables:
                    print("❌ No variables found in file")
                    return None
            except Exception as e:
                print(f"❌ Error exploring file: {e}")
                return None
        
        # Display variables
        print(f"\nAvailable variables:")
        for i, var in enumerate(variables, 1):
            print(f"  {i}. {var}")
        
        # Get selection
        while True:
            try:
                choice = input(f"\nSelect variable (1-{len(variables)}): ").strip()
                var_idx = int(choice) - 1
                if 0 <= var_idx < len(variables):
                    selected = variables[var_idx]
                    print(f"✅ Selected: {selected}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(variables)}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return None
    
    def _extract_variables_from_structure(self, structure: Dict[str, Any]) -> List[str]:
        """Extract all variable names from structure."""
        variables = []
        
        def collect_vars(group_info, path=""):
            # Add variables from this group
            for var_name in group_info.get('variables', {}):
                if path:
                    variables.append(f"{path}/{var_name}")
                else:
                    variables.append(var_name)
            
            # Recursively collect from subgroups
            for sub_name, sub_info in group_info.get('groups', {}).items():
                new_path = f"{path}/{sub_name}" if path else sub_name
                collect_vars(sub_info, new_path)
        
        if 'root' in structure:
            collect_vars(structure['root'])
        
        return variables
    
    def _select_plot_type(self) -> Optional[str]:
        """Select plot type."""
        print("\n🎨 Step 2: Plot Type Selection")
        print("-" * 40)
        print("1. Efficient (fast, imshow with Cartopy) - Recommended")
        print("2. Contour (detailed with Cartopy)")
        print("3. Heatmap (simple grid)")
        
        while True:
            try:
                choice = input("\nSelect plot type (1-3): ").strip()
                if choice == "1":
                    return "efficient"
                elif choice == "2":
                    return "contour"
                elif choice == "3":
                    return "heatmap"
                else:
                    print("❌ Please enter a number between 1 and 3")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return None
    
    def _select_output_format(self) -> Optional[str]:
        """Select output format for multi-file visualization."""
        print("\n💾 Step 3: Output Format")
        print("-" * 40)
        print("1. PNG sequence (one PNG per file)")
        print("2. MP4 video (single video from all files)")
        
        while True:
            try:
                choice = input("\nSelect output format (1-2): ").strip()
                if choice == "1":
                    return "png"
                elif choice == "2":
                    return "mp4"
                else:
                    print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return None
    
    def _get_output_filename(self, variable: str, plot_type: str, 
                            is_multi_file: bool) -> Optional[str]:
        """Get output filename from user."""
        print("\n💾 Step 4: Output Filename")
        print("-" * 40)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_var = variable.replace('/', '_').replace('\\', '_')
        
        if is_multi_file:
            default = f"{timestamp}_{safe_var}_sequence"
        else:
            default = f"{timestamp}_{safe_var}.png"
        
        print(f"Default: {default}")
        filename = input("Enter output filename (or press Enter for default): ").strip()
        
        if not filename:
            filename = default
        
        return filename
    
    def _get_fps(self) -> int:
        """Get FPS from user."""
        print("\n⏱️  Step 5: Animation FPS")
        print("-" * 40)
        
        while True:
            try:
                fps_input = input("Frames per second (default: 10): ").strip()
                if not fps_input:
                    fps = 10
                else:
                    fps = int(fps_input)
                    if fps <= 0 or fps > 60:
                        print("❌ FPS must be between 1 and 60. Using default: 10")
                        fps = 10
                print(f"✅ FPS: {fps}")
                return fps
            except ValueError:
                print("❌ Invalid FPS value. Using default: 10")
                return 10
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return 10
    
    def _get_zoom_factor(self) -> float:
        """Get zoom factor from user."""
        print("\n🔍 Step 6: Zoom Factor")
        print("-" * 40)
        
        while True:
            try:
                zoom_input = input("Zoom factor (default: 1.0, no zoom): ").strip()
                if not zoom_input:
                    zoom_factor = 1.0
                else:
                    zoom_factor = float(zoom_input)
                    if zoom_factor <= 0 or zoom_factor > 10:
                        print("❌ Zoom factor must be between 0.1 and 10.0. Using default: 1.0")
                        zoom_factor = 1.0
                print(f"✅ Zoom factor: {zoom_factor}")
                return zoom_factor
            except ValueError:
                print("❌ Invalid zoom factor. Using default: 1.0")
                return 1.0
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return 1.0
    
    def _get_percentile(self) -> int:
        """Get percentile threshold from user."""
        print("\n📊 Step 7: Percentile Filtering")
        print("-" * 40)
        
        while True:
            try:
                percentile_input = input("Percentile threshold (default: 5): ").strip()
                if not percentile_input:
                    percentile = 5
                else:
                    percentile = int(percentile_input)
                    if percentile < 0 or percentile > 100:
                        print("❌ Percentile must be between 0 and 100. Using default: 5")
                        percentile = 5
                print(f"✅ Percentile: {percentile}")
                return percentile
            except ValueError:
                print("❌ Invalid percentile. Using default: 5")
                return 5
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return 5
    
    def _get_ignore_values(self) -> List[float]:
        """Get values to ignore from user."""
        print("\n🚫 Step 8: Ignore Values")
        print("-" * 40)
        print("Some NetCDF files use placeholder values (e.g., 999, -999) for missing data.")
        
        while True:
            try:
                ignore_input = input("Enter values to ignore (comma-separated, or press Enter for none): ").strip()
                if not ignore_input:
                    print("✅ No values to ignore")
                    return []
                
                values = [float(v.strip()) for v in ignore_input.split(',')]
                print(f"✅ Will ignore values: {values}")
                return values
            except ValueError:
                print("❌ Invalid input. Please enter comma-separated numbers (e.g., 999,-999)")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return []
    
    def _get_designer_mode(self) -> bool:
        """Get designer mode preference."""
        print("\n🎨 Step 9: Designer Mode")
        print("-" * 40)
        print("Designer mode: clean background, no coordinates, no title")
        
        while True:
            try:
                choice = input("Enable designer mode? (y/n, default: n): ").strip().lower()
                if not choice or choice == 'n':
                    return False
                elif choice == 'y':
                    return True
                else:
                    print("❌ Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return False
    
    def _get_transparent_background(self) -> bool:
        """Get transparent background preference."""
        print("\n🎨 Step 10: Transparent Background")
        print("-" * 40)
        
        while True:
            try:
                choice = input("Use transparent background? (y/n, default: n): ").strip().lower()
                if not choice or choice == 'n':
                    return False
                elif choice == 'y':
                    return True
                else:
                    print("❌ Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                print("\n⚠️  Operation cancelled")
                return False
