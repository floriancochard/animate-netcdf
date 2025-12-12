#!/usr/bin/env python3
"""
Unified NetCDF Visualizer
Handles both single-file and multi-file visualization in a single class
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import xarray as xr
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from animate_netcdf.core.config_manager import AnimationConfig
from animate_netcdf.core.file_manager import NetCDFFileManager
from animate_netcdf.utils.data_processing import DataProcessor
from animate_netcdf.utils.plot_utils import PlotUtils
from animate_netcdf.utils.ffmpeg_utils import ffmpeg_manager


class NetCDFVisualizer:
    """Unified visualizer for both single and multi-file NetCDF visualization."""
    
    def __init__(self, config: AnimationConfig):
        """Initialize visualizer with configuration."""
        self.config = config
        self.data_processor = DataProcessor()
        self.plot_utils = PlotUtils()
        self.ffmpeg_manager = ffmpeg_manager
        
        # Set up cartopy logging
        self.plot_utils.setup_cartopy_logging()
        self.plot_utils.check_cartopy_maps()
    
    def visualize(self, input_path: str) -> bool:
        """Main entry point for visualization.
        
        Args:
            input_path: Path to single file or pattern for multiple files
            
        Returns:
            bool: True if visualization completed successfully
        """
        input_type = self._detect_input_type(input_path)
        
        if input_type == 'single':
            return self._visualize_single_file(input_path)
        elif input_type == 'multi':
            return self._visualize_multi_file(input_path)
        else:
            print(f"❌ Could not determine input type for: {input_path}")
            return False
    
    def _detect_input_type(self, input_path: str) -> str:
        """Detect if input is single file or multi-file pattern."""
        if '*' in input_path or '?' in input_path:
            # Glob pattern - check if multiple files match
            files = glob.glob(input_path)
            if len(files) > 1:
                return 'multi'
            elif len(files) == 1:
                return 'single'
            else:
                return 'unknown'
        else:
            # Single file path
            if os.path.exists(input_path):
                return 'single'
            else:
                return 'unknown'
    
    def _visualize_single_file(self, file_path: str) -> bool:
        """Visualize a single NetCDF file."""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"📁 Loading {file_path}...")
        try:
            ds = xr.open_dataset(file_path)
            
            # Validate variable exists
            if self.config.variable not in ds.data_vars:
                print(f"❌ Variable '{self.config.variable}' not found in file")
                print(f"Available variables: {list(ds.data_vars.keys())}")
                ds.close()
                return False
            
            # Determine output format (single file always produces PNG)
            output_file = self.config.output_pattern or self._generate_output_filename(
                self.config.variable, 'png'
            )
            
            # Create single PNG
            success = self._create_single_png(ds, file_path, output_file)
            
            ds.close()
            return success
            
        except Exception as e:
            print(f"❌ Error visualizing file: {e}")
            return False
    
    def _visualize_multi_file(self, file_pattern: str) -> bool:
        """Visualize multiple NetCDF files."""
        # Initialize file manager
        file_manager = NetCDFFileManager(file_pattern)
        files = file_manager.discover_files()
        
        if not files:
            print(f"❌ No files found matching pattern: {file_pattern}")
            return False
        
        # Validate consistency
        errors = file_manager.validate_consistency()
        if errors:
            print("❌ File consistency errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # Check variable exists in all files
        common_vars = file_manager.get_common_variables()
        if self.config.variable not in common_vars:
            print(f"❌ Variable '{self.config.variable}' not found in all files")
            print(f"Common variables: {common_vars}")
            return False
        
        # Determine output format
        output_format = self.config.output_format.value if hasattr(self.config.output_format, 'value') else 'mp4'
        
        if output_format == 'png':
            return self._create_png_sequence(file_manager, files)
        else:
            return self._create_mp4_animation(file_manager, files)
    
    def _create_single_png(self, ds: xr.Dataset, file_path: str, output_file: str) -> bool:
        """Create a single PNG from a NetCDF file."""
        print(f"\n📊 Creating PNG for {self.config.variable}...")
        
        try:
            variable = ds[self.config.variable]
            plot_type = self.config.plot_type.value if hasattr(self.config.plot_type, 'value') else 'efficient'
            
            # Get animation dimension
            animate_dim = self._get_animation_dimension(ds)
            if not animate_dim:
                animate_dim = 'time'
            
            # Prepare data for first time step
            data, lats, lons = self.data_processor.prepare_data_for_plotting(
                variable, time_step=0, animate_dim=animate_dim,
                level_index=self.config.level_index, zoom_factor=self.config.zoom_factor
            )
            
            # Apply filters
            filtered_data = self._apply_filters(data)
            
            # Create plot
            if plot_type in ['efficient', 'contour']:
                # Use designer-specific functions if in designer mode
                if self.config.designer_mode:
                    fig, ax = self.plot_utils.create_designer_geographic_plot(plot_type)
                    self.plot_utils.setup_designer_geographic_plot(ax, lats, lons, offline=self.config.offline)
                    
                    if plot_type == 'efficient':
                        im = self.plot_utils.create_designer_efficient_plot(ax, filtered_data, lats, lons)
                    else:
                        im = self.plot_utils.create_designer_contour_plot(ax, filtered_data, lats, lons)
                    
                    # No colorbar in designer mode
                else:
                    fig, ax = self.plot_utils.create_geographic_plot(plot_type)
                    self.plot_utils.setup_geographic_plot(ax, lats, lons, offline=self.config.offline)
                    
                    if plot_type == 'efficient':
                        im = self.plot_utils.create_efficient_plot(ax, filtered_data, lats, lons)
                    else:
                        im = self.plot_utils.create_contour_plot(ax, filtered_data, lats, lons)
                    
                    units = variable.attrs.get("units", "")
                    self.plot_utils.add_colorbar(im, ax, self.config.variable, units)
                    
                    # Add title if not designer mode
                    time_str = self.plot_utils.format_datetime(
                        ds[animate_dim].isel({animate_dim: 0}), animate_dim, ds
                    )
                    units_str = self.plot_utils.get_variable_subtitle(self.config.variable, ds)
                    self.plot_utils.add_title_and_subtitle(ax, self.config.variable, time_str, units_str)
            else:
                # Heatmap
                fig, ax = self.plot_utils.create_heatmap_plot()
                im = ax.imshow(filtered_data, cmap='Blues', aspect='auto')
                units = variable.attrs.get("units", "")
                self.plot_utils.add_colorbar(im, ax, self.config.variable, units)
            
            # Save with transparent background if requested or in designer mode
            save_kwargs = {'dpi': 300, 'bbox_inches': 'tight'}
            if self.config.transparent or self.config.designer_mode:
                save_kwargs['transparent'] = True
                save_kwargs['facecolor'] = 'none'
            
            plt.savefig(output_file, **save_kwargs)
            plt.close(fig)
            
            print(f"✅ PNG saved: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating PNG: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_png_sequence(self, file_manager: NetCDFFileManager, files: List[str]) -> bool:
        """Create a sequence of PNG files from multiple NetCDF files."""
        print(f"\n📊 Creating PNG sequence for {len(files)} files...")
        
        # Generate output pattern
        from animate_netcdf.core.output_manager import OutputManager
        output_manager = OutputManager()
        
        base_name = self.config.output_pattern or f"{self.config.variable}_sequence"
        if base_name.endswith('.png'):
            base_name = base_name[:-4]
        
        success_count = 0
        for i, file_path in enumerate(files):
            try:
                print(f"📁 Processing file {i+1}/{len(files)}: {os.path.basename(file_path)}")
                
                with xr.open_dataset(file_path) as ds:
                    # Generate output filename with index
                    output_file = output_manager.get_sequence_filename(base_name, i, len(files))
                    
                    # Create PNG for this file
                    if self._create_single_png(ds, file_path, output_file):
                        success_count += 1
                    else:
                        print(f"⚠️  Failed to create PNG for {file_path}")
                        
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
                continue
        
        print(f"\n✅ Created {success_count}/{len(files)} PNG files")
        return success_count > 0
    
    def _create_mp4_animation(self, file_manager: NetCDFFileManager, files: List[str]) -> bool:
        """Create an MP4 animation from multiple NetCDF files."""
        if not self.ffmpeg_manager.is_available():
            print("❌ ffmpeg not available. Cannot create video.")
            return False
        
        print(f"\n🎬 Creating MP4 animation from {len(files)} files...")
        
        # Generate output filename
        output_file = self.config.output_pattern or self._generate_output_filename(
            self.config.variable, 'mp4'
        )
        
        if os.path.exists(output_file) and not self.config.overwrite_existing:
            print(f"⚠️  Output file {output_file} already exists. Use --overwrite to overwrite.")
            return False
        
        try:
            # Get spatial coordinates from first file
            spatial_coords = file_manager.get_spatial_coordinates()
            if not spatial_coords:
                print("❌ No spatial coordinates found")
                return False
            
            # Determine coordinate names
            lat_coord = None
            lon_coord = None
            for coord in ['lat', 'latitude']:
                if coord in spatial_coords:
                    lat_coord = coord
                    break
            for coord in ['lon', 'longitude']:
                if coord in spatial_coords:
                    lon_coord = coord
                    break
            
            if not lat_coord or not lon_coord:
                print("❌ Could not determine latitude/longitude coordinates")
                return False
            
            # Pre-load data for global colorbar if needed
            global_data_range = None
            if self.config.global_colorbar and self.config.pre_scan_files:
                print("🔍 Pre-scanning files for global data range...")
                global_data_range = self._pre_scan_data_range(files)
            
            # Create figure
            plot_type = self.config.plot_type.value if hasattr(self.config.plot_type, 'value') else 'efficient'
            
            # Use designer-specific functions if in designer mode
            if self.config.designer_mode:
                fig, ax = self.plot_utils.create_designer_geographic_plot(plot_type)
            else:
                fig, ax = self.plot_utils.create_geographic_plot(plot_type)
            
            # Set up geographic plot
            lat_min = spatial_coords[lat_coord]['min']
            lat_max = spatial_coords[lat_coord]['max']
            lon_min = spatial_coords[lon_coord]['min']
            lon_max = spatial_coords[lon_coord]['max']
            
            lats = np.linspace(lat_min, lat_max, 100)
            lons = np.linspace(lon_min, lon_max, 100)
            
            if self.config.designer_mode:
                self.plot_utils.setup_designer_geographic_plot(ax, lats, lons, offline=self.config.offline)
            else:
                self.plot_utils.setup_geographic_plot(ax, lats, lons, offline=self.config.offline)
            
            # Initialize plot with first file
            initial_data = self._load_file_data(files[0])
            if initial_data is None:
                return False
            
            vmin, vmax = self._get_colorbar_range(initial_data, global_data_range)
            
            if self.config.designer_mode:
                if plot_type == 'efficient':
                    im = self.plot_utils.create_designer_efficient_plot(ax, initial_data, lats, lons, vmin, vmax)
                else:
                    levels = np.linspace(vmin, vmax, 20)
                    im = self.plot_utils.create_designer_contour_plot(ax, initial_data, lats, lons, vmin, vmax, levels=levels)
                # No colorbar in designer mode
            else:
                if plot_type == 'efficient':
                    im = self.plot_utils.create_efficient_plot(ax, initial_data, lats, lons, vmin, vmax)
                else:
                    levels = np.linspace(vmin, vmax, 20)
                    im = self.plot_utils.create_contour_plot(ax, initial_data, lats, lons, vmin, vmax, levels=levels)
                
                units = ""  # We don't have dataset access here
                self.plot_utils.add_colorbar(im, ax, self.config.variable, units)
            
            # Animation function
            def animate(frame):
                file_path = files[frame]
                data = self._load_file_data(file_path)
                
                if data is not None:
                    if plot_type == 'efficient':
                        im.set_array(data)
                    else:
                        # Remove old contour and create new one
                        for collection in ax.collections:
                            collection.remove()
                        if self.config.designer_mode:
                            new_contour = self.plot_utils.create_designer_contour_plot(
                                ax, data, lats, lons, vmin, vmax, levels=levels
                            )
                        else:
                            new_contour = self.plot_utils.create_contour_plot(
                                ax, data, lats, lons, vmin, vmax, levels=levels
                            )
                
                # Update title (only if not in designer mode)
                if not self.config.designer_mode:
                    timestep = file_manager.get_timestep_by_file(file_path)
                    ax.set_title(f'{self.config.variable} - Timestep {timestep}', fontsize=14, pad=20)
                
                return [im] if plot_type == 'efficient' else [new_contour]
            
            # Create animation
            anim = animation.FuncAnimation(
                fig, animate, frames=len(files),
                interval=1000//self.config.fps, blit=True, repeat=True
            )
            
            # Save animation
            success = self.plot_utils.save_animation_with_fallback(
                anim, output_file, self.config.fps, self.ffmpeg_manager
            )
            
            plt.close(fig)
            
            if success:
                print(f"✅ MP4 saved: {output_file}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating MP4 animation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_file_data(self, file_path: str) -> Optional[np.ndarray]:
        """Load and process data from a single file."""
        try:
            with xr.open_dataset(file_path) as ds:
                if self.config.variable not in ds.data_vars:
                    return None
                
                data_array = ds[self.config.variable]
                
                # Reduce to 2D
                data, _, _ = self.data_processor.prepare_data_for_plotting(
                    data_array, time_step=0, animate_dim='time',
                    level_index=self.config.level_index, zoom_factor=self.config.zoom_factor,
                    verbose=False
                )
                
                # Apply filters
                filtered_data = self._apply_filters(data)
                
                return filtered_data
                
        except Exception as e:
            print(f"⚠️  Error loading {file_path}: {e}")
            return None
    
    def _apply_filters(self, data: np.ndarray) -> np.ndarray:
        """Apply all configured filters to data."""
        # Apply ignore_values first
        if hasattr(self.config, 'ignore_values') and self.config.ignore_values:
            data = self.data_processor.filter_ignore_values(data, self.config.ignore_values)
        
        # Then apply percentile filtering
        if self.config.percentile > 0:
            data = self.data_processor.filter_low_values(data, self.config.percentile)
        
        return data
    
    def _pre_scan_data_range(self, files: List[str]) -> Optional[Tuple[float, float]]:
        """Pre-scan files to determine global data range."""
        all_min = float('inf')
        all_max = float('-inf')
        
        for file_path in files[:10]:  # Sample first 10 files
            data = self._load_file_data(file_path)
            if data is not None:
                file_min = np.nanmin(data)
                file_max = np.nanmax(data)
                if not np.isnan(file_min):
                    all_min = min(all_min, file_min)
                if not np.isnan(file_max):
                    all_max = max(all_max, file_max)
        
        if all_min == float('inf') or all_max == float('-inf'):
            return None
        
        print(f"📊 Global data range: {all_min:.6f} to {all_max:.6f}")
        return (all_min, all_max)
    
    def _get_colorbar_range(self, sample_data: np.ndarray, 
                           global_range: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        """Get colorbar range based on configuration."""
        if global_range and self.config.global_colorbar:
            return global_range
        else:
            return np.nanmin(sample_data), np.nanmax(sample_data)
    
    def _get_animation_dimension(self, ds: xr.Dataset) -> Optional[str]:
        """Find the first dimension that's not spatial (suitable for animation)."""
        return self.data_processor.get_animation_dimension(ds)
    
    def _generate_output_filename(self, variable: str, format: str) -> str:
        """Generate output filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{variable}.{format}"
