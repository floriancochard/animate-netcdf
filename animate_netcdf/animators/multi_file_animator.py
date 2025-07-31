#!/usr/bin/env python3
"""
Multi-File NetCDF Animator
Handles animations across multiple NetCDF files without concatenation.
"""

import os
import sys
import psutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import List, Optional, Dict, Any, Tuple
import xarray as xr
import logging
from datetime import datetime
import subprocess
import os

# Import our custom modules
from animate_netcdf.core.config_manager import AnimationConfig, ConfigManager
from animate_netcdf.core.file_manager import NetCDFFileManager

# Import utilities from the new modular structure
from animate_netcdf.utils.ffmpeg_utils import ffmpeg_manager
from animate_netcdf.utils.data_processing import DataProcessor
from animate_netcdf.utils.plot_utils import PlotUtils


class MultiFileAnimator:
    """Handles animations across multiple NetCDF files without concatenation."""
    
    def __init__(self, file_manager: NetCDFFileManager, config: AnimationConfig):
        self.file_manager = file_manager
        self.config = config
        self.global_data_range = None
        
        # Use the new utility classes
        self.ffmpeg_manager = ffmpeg_manager
        self.data_processor = DataProcessor()
        self.plot_utils = PlotUtils()
        
        # Add caching for efficient processing
        self.data_cache = {}  # Cache for pre-loaded data
        self.spatial_coords_cache = None  # Cache for spatial coordinates
        self.pre_loaded = False  # Flag to track if data is pre-loaded
        
    def pre_load_all_data(self) -> bool:
        """Pre-load all file data into memory for efficient processing."""
        print("📦 Pre-loading all file data into memory...")
        
        total_files = len(self.file_manager.sorted_files)
        all_min = float('inf')
        all_max = float('-inf')
        
        for i, filepath in enumerate(self.file_manager.sorted_files):
            try:
                print(f"📦 Loading file {i+1}/{total_files}: {os.path.basename(filepath)}")
                
                # Load and process data
                data = self._load_file_data(filepath)
                if data is not None:
                    # Cache the processed data
                    self.data_cache[filepath] = data
                    
                    # Update global range
                    file_min = np.nanmin(data)
                    file_max = np.nanmax(data)
                    
                    if not np.isnan(file_min):
                        all_min = min(all_min, file_min)
                    if not np.isnan(file_max):
                        all_max = max(all_max, file_max)
                else:
                    print(f"⚠️  Failed to load data from {filepath}")
                    
            except Exception as e:
                print(f"⚠️  Error loading {filepath}: {e}")
                continue
        
        if all_min == float('inf') or all_max == float('-inf'):
            print("⚠️  Could not determine global data range")
            return False
        
        # Set global data range
        self.global_data_range = (all_min, all_max)
        print(f"📊 Global data range: {all_min:.6f} to {all_max:.6f}")
        
        # Cache spatial coordinates from first file
        self.spatial_coords_cache = self.file_manager.get_spatial_coordinates()
        
        self.pre_loaded = True
        print(f"✅ Pre-loaded {len(self.data_cache)} files into memory")
        return True
    
    def pre_scan_files(self) -> Tuple[float, float]:
        """Pre-scan all files to determine global data range."""
        if not self.config.pre_scan_files:
            return None, None
        
        print("🔍 Pre-scanning files for global data range...")
        
        all_min = float('inf')
        all_max = float('-inf')
        total_files = len(self.file_manager.sorted_files)
        
        for i, filepath in enumerate(self.file_manager.sorted_files):
            try:
                print(f"📊 Scanning file {i+1}/{total_files}: {os.path.basename(filepath)}")
                
                with xr.open_dataset(filepath) as ds:
                    if self.config.variable not in ds.data_vars:
                        continue
                    
                    # Get the data array and reduce to 2D
                    data_array = ds[self.config.variable]
                    
                    # Define spatial dimensions
                    spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v', 
                                   'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v']
                    
                    # If we have more than 2 dimensions, we need to reduce to 2D
                    if len(data_array.dims) > 2:
                        # Keep only the spatial dimensions, handle others
                        non_spatial_dims = [dim for dim in data_array.dims if dim not in spatial_dims]
                        
                        if non_spatial_dims:
                            # If level_index is specified, select that level
                            if self.config.level_index is not None and ('level' in non_spatial_dims or 'level_w' in non_spatial_dims):
                                level_dim = 'level' if 'level' in non_spatial_dims else 'level_w'
                                try:
                                    data_array = data_array.isel({level_dim: self.config.level_index})
                                    non_spatial_dims.remove(level_dim)
                                except Exception as e:
                                    print(f"❌ Error selecting level {self.config.level_index} from {level_dim}: {e}")
                                    continue
                            
                            # Average over remaining non-spatial dimensions
                            for dim in non_spatial_dims:
                                data_array = data_array.mean(dim=dim)
                    
                    # Squeeze out any remaining singleton dimensions
                    data_array = data_array.squeeze()
                    
                    # Convert to numpy array
                    data = data_array.values
                    
                    # Verify we have 2D data
                    if len(data.shape) != 2:
                        print(f"⚠️  Skipping file {filepath}: data shape {data.shape} is not 2D")
                        continue
                    
                    # Apply filtering if needed
                    if self.config.percentile > 0:
                        # Apply filtering directly without creating temporary animator
                        data = self.data_processor.filter_low_values(data, self.config.percentile)
                    
                    # Update global range
                    file_min = np.nanmin(data)
                    file_max = np.nanmax(data)
                    
                    if not np.isnan(file_min):
                        all_min = min(all_min, file_min)
                    if not np.isnan(file_max):
                        all_max = max(all_max, file_max)
                
            except Exception as e:
                print(f"⚠️  Error scanning {filepath}: {e}")
                continue
        
        if all_min == float('inf') or all_max == float('-inf'):
            print("⚠️  Could not determine global data range")
            return None, None
        
        print(f"📊 Global data range: {all_min:.6f} to {all_max:.6f}")
        return all_min, all_max
    

    
    def get_troubleshooting_tips(self):
        """Get troubleshooting tips for common issues."""
        tips = [
            "1. Make sure your NetCDF files are valid and contain the specified variable",
            "2. Check that the variable has spatial dimensions (lat/lon or latitude/longitude)",
            "3. Ensure you have ffmpeg installed for video creation",
            "4. For geographic animations, make sure you have latitude/longitude coordinates",
            "5. If you get 'unknown encoder h264' error:",
            "   - Install ffmpeg with h264 support: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)",
            "   - The script will automatically try alternative codecs (mpeg4, libxvid)",
            "   - Check available codecs with: ffmpeg -codecs | grep -E '(libx264|libxvid|mpeg4)'",
            "6. For memory issues, try reducing the number of files or using a smaller subset",
            "7. Check that all files have the same variable and coordinate structure"
        ]
        return tips

    def create_animation_sequence(self) -> bool:
        """Create animation from multiple files."""
        print(f"\n🎬 Creating multi-file animation...")
        print(f"📁 Files: {len(self.file_manager.sorted_files)}")
        print(f"📊 Variable: {self.config.variable}")
        print(f"🎨 Type: {self.config.plot_type}")
        print(f"📹 FPS: {self.config.fps}")
        
        # Show estimated time
        time_minutes = self.estimate_processing_time()
        print(f"⏱️  Estimated time: {time_minutes:.1f} minutes")
        
        # Show memory estimate
        memory_mb = self.file_manager.estimate_memory_usage(self.config.variable)
        print(f"💾 Estimated memory: {memory_mb:.1f} MB")
        
        # Validate configuration
        if not self._validate_config():
            return False
        
        # EFFICIENT PROCESSING: Pre-load all data into memory
        if self.config.global_colorbar and self.config.pre_scan_files:
            # Use the new pre-loading method instead of pre-scanning
            if not self.pre_load_all_data():
                print("❌ Failed to pre-load data")
                return False
        else:
            # If not using global colorbar, still pre-load for efficiency
            if not self.pre_load_all_data():
                print("❌ Failed to pre-load data")
                return False
        
        # Create output filename
        output_file = self._generate_output_filename()
        
        # Check if output file exists
        if os.path.exists(output_file) and not self.config.overwrite_existing:
            print(f"⚠️  Output file {output_file} already exists. Use --overwrite to overwrite.")
            return False
        
        # Create animation using cached data
        try:
            if self.config.plot_type in ['efficient', 'contour']:
                success = self._create_geographic_animation(output_file)
            else:
                success = self._create_heatmap_animation(output_file)
            
            if success:
                print(f"✅ Animation saved: {output_file}")
                return True
            else:
                print("❌ Failed to create animation")
                return False
                
        except Exception as e:
            print(f"❌ Error creating animation: {e}")
            print("\nTroubleshooting tips:")
            for tip in self.get_troubleshooting_tips():
                print(f"   {tip}")
            return False
    
    def _validate_config(self) -> bool:
        """Validate configuration for multi-file animation."""
        errors = []
        
        if not self.config.variable:
            errors.append("No variable specified")
        
        if not self.file_manager.sorted_files:
            errors.append("No files to process")
        
        if self.config.variable:
            common_vars = self.file_manager.get_common_variables()
            if self.config.variable not in common_vars:
                errors.append(f"Variable '{self.config.variable}' not found in all files")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def _generate_output_filename(self) -> str:
        """Generate output filename based on configuration."""
        # Always generate a fresh timestamp to prevent overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.config.output_pattern:
            # Check if the output pattern already contains a timestamp pattern (YYYYMMDD_HHMMSS)
            import re
            timestamp_pattern = r'^\d{8}_\d{6}_'
            if re.match(timestamp_pattern, self.config.output_pattern):
                # Remove the old timestamp and add new one
                base_pattern = re.sub(timestamp_pattern, '', self.config.output_pattern)
                return f"{timestamp}_{base_pattern}"
            
            # Use the configured pattern as is
            if self.config.output_pattern.endswith(f'.{self.config.output_format}'):
                return self.config.output_pattern
            else:
                return f"{self.config.output_pattern}.{self.config.output_format}"
        else:
            # Generate default filename with timestamp to prevent overwriting
            return f"{timestamp}_{self.config.variable}_{self.config.plot_type}_multifile.{self.config.output_format}"
    
    def _create_geographic_animation(self, output_file: str) -> bool:
        """Create geographic animation with Cartopy."""
        try:
            # Import cartopy components
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
            
            # Get spatial coordinates (use cached if available)
            if self.spatial_coords_cache:
                spatial_coords = self.spatial_coords_cache
            else:
                spatial_coords = self.file_manager.get_spatial_coordinates()
            
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
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(15, 10), 
                                  subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Add Cartopy features
            ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
            ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
            ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='lightgray')
            
            # Add gridlines
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, 
                             linestyle='--', color='gray')
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            
            # Set extent based on spatial coordinates
            lat_min = spatial_coords[lat_coord]['min']
            lat_max = spatial_coords[lat_coord]['max']
            lon_min = spatial_coords[lon_coord]['min']
            lon_max = spatial_coords[lon_coord]['max']
            
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], 
                         crs=ccrs.PlateCarree())
            
            # Initialize plot based on type
            if self.config.plot_type == 'efficient':
                # Initialize with first file data
                initial_data = self._load_file_data(self.file_manager.sorted_files[0])
                if initial_data is None:
                    return False
                
                # Set colorbar range
                vmin, vmax = self._get_colorbar_range(initial_data)
                
                im = ax.imshow(initial_data, cmap='Blues', alpha=0.8,
                              extent=[lon_min, lon_max, lat_min, lat_max],
                              transform=ccrs.PlateCarree(), origin='lower',
                              vmin=vmin, vmax=vmax)
                
                # Add colorbar
                cbar = plt.colorbar(im, ax=ax, shrink=0.8)
                cbar.set_label(f'{self.config.variable} (units)')
                
                # Animation function (uses cached data for efficiency)
                def animate(frame):
                    filepath = self.file_manager.sorted_files[frame]
                    # Use cached data if available, otherwise load from file
                    if self.pre_loaded and filepath in self.data_cache:
                        data = self.data_cache[filepath]
                    else:
                        data = self._load_file_data(filepath)
                    
                    if data is not None:
                        im.set_array(data)
                    
                    # Update title
                    timestep = self.file_manager.get_timestep_by_file(filepath)
                    ax.set_title(f'{self.config.variable} - Timestep {timestep}', 
                               fontsize=14, pad=20)
                    
                    return [im]
                
            else:  # contour
                # Initialize with first file data
                initial_data = self._load_file_data(self.file_manager.sorted_files[0])
                if initial_data is None:
                    return False
                
                # Set colorbar range
                vmin, vmax = self._get_colorbar_range(initial_data)
                levels = np.linspace(vmin, vmax, 20)
                
                # Create coordinate arrays for contour plot
                lons = np.linspace(lon_min, lon_max, initial_data.shape[1])
                lats = np.linspace(lat_min, lat_max, initial_data.shape[0])
                lon_grid, lat_grid = np.meshgrid(lons, lats)
                
                contour = ax.contourf(lon_grid, lat_grid, initial_data, levels=levels, 
                                     cmap='Blues', transform=ccrs.PlateCarree())
                
                # Add colorbar
                cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
                cbar.set_label(f'{self.config.variable} (units)')
                
                # Animation function (uses cached data for efficiency)
                def animate(frame):
                    filepath = self.file_manager.sorted_files[frame]
                    # Use cached data if available, otherwise load from file
                    if self.pre_loaded and filepath in self.data_cache:
                        data = self.data_cache[filepath]
                    else:
                        data = self._load_file_data(filepath)
                    
                    if data is not None:
                        # Remove previous contour
                        for collection in ax.collections:
                            collection.remove()
                        
                        # Create new contour
                        new_contour = ax.contourf(lon_grid, lat_grid, data, levels=levels,
                                                 cmap='Blues', transform=ccrs.PlateCarree())
                    
                    # Update title
                    timestep = self.file_manager.get_timestep_by_file(filepath)
                    ax.set_title(f'{self.config.variable} - Timestep {timestep}', 
                               fontsize=14, pad=20)
                    
                    return [new_contour]
            
            # Create animation
            anim = animation.FuncAnimation(
                fig, animate, frames=len(self.file_manager.sorted_files),
                interval=1000//self.config.fps, blit=True, repeat=True
            )
            
            # Save animation
            success = self.plot_utils.save_animation_with_fallback(anim, output_file, self.config.fps, self.ffmpeg_manager)
            plt.close(fig)
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating geographic animation: {e}")
            return False
    
    def _create_heatmap_animation(self, output_file: str) -> bool:
        """Create simple heatmap animation."""
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Initialize with first file data
            initial_data = self._load_file_data(self.file_manager.sorted_files[0])
            if initial_data is None:
                return False
            
            # Set colorbar range
            vmin, vmax = self._get_colorbar_range(initial_data)
            
            im = ax.imshow(initial_data, cmap='Blues', aspect='auto',
                          vmin=vmin, vmax=vmax)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(f'{self.config.variable} (units)')
            
            # Animation function (uses cached data for efficiency)
            def animate(frame):
                filepath = self.file_manager.sorted_files[frame]
                # Use cached data if available, otherwise load from file
                if self.pre_loaded and filepath in self.data_cache:
                    data = self.data_cache[filepath]
                else:
                    data = self._load_file_data(filepath)
                
                if data is not None:
                    im.set_array(data)
                
                # Update title
                timestep = self.file_manager.get_timestep_by_file(filepath)
                ax.set_title(f'{self.config.variable} - Timestep {timestep}', 
                           fontsize=14, pad=20)
                
                return [im]
            
            # Create animation
            anim = animation.FuncAnimation(
                fig, animate, frames=len(self.file_manager.sorted_files),
                interval=1000//self.config.fps, blit=True, repeat=True
            )
            
            # Save animation
            success = self.plot_utils.save_animation_with_fallback(anim, output_file, self.config.fps, self.ffmpeg_manager)
            plt.close(fig)
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating heatmap animation: {e}")
            return False
    
    def _load_file_data(self, filepath: str) -> Optional[np.ndarray]:
        """Load data from a single file and reduce to 2D for plotting."""
        # Check if data is already cached
        if self.pre_loaded and filepath in self.data_cache:
            return self.data_cache[filepath]
        
        try:
            with xr.open_dataset(filepath) as ds:
                if self.config.variable not in ds.data_vars:
                    return None
                
                # Get the data array
                data_array = ds[self.config.variable]
                
                # Handle multiple non-spatial dimensions
                # Define spatial dimensions
                spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v', 
                               'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v']
                
                # Find which dimensions are spatial
                spatial_dims_in_data = [dim for dim in data_array.dims if dim in spatial_dims]
                
                # If we have more than 2 dimensions, we need to reduce to 2D
                if len(data_array.dims) > 2:
                    # Keep only the spatial dimensions, handle others
                    non_spatial_dims = [dim for dim in data_array.dims if dim not in spatial_dims]
                    
                    if non_spatial_dims:
                        # If level_index is specified, select that level
                        if self.config.level_index is not None and ('level' in non_spatial_dims or 'level_w' in non_spatial_dims):
                            level_dim = 'level' if 'level' in non_spatial_dims else 'level_w'
                            try:
                                data_array = data_array.isel({level_dim: self.config.level_index})
                                non_spatial_dims.remove(level_dim)
                            except Exception as e:
                                print(f"❌ Error selecting level {self.config.level_index} from {level_dim}: {e}")
                                if level_dim in ds.dims:
                                    print(f"Available level indices: 0 to {len(ds[level_dim])-1}")
                                raise
                        
                        # Average over remaining non-spatial dimensions
                        for dim in non_spatial_dims:
                            data_array = data_array.mean(dim=dim)
                
                # Squeeze out any remaining singleton dimensions
                data_array = data_array.squeeze()
                
                # Convert to numpy array
                data = data_array.values
                
                # Verify we have 2D data
                if len(data.shape) != 2:
                    raise ValueError(f"Data must be 2D for plotting, got shape {data.shape}. "
                                   f"Available dimensions: {list(ds[self.config.variable].dims)}")
                
                # Apply filtering
                if self.config.percentile > 0:
                    # Apply filtering directly without creating temporary animator
                    data = self.data_processor.filter_low_values(data, self.config.percentile)
                
                return data
                
        except Exception as e:
            print(f"⚠️  Error loading {filepath}: {e}")
            return None
    

    
    def _get_colorbar_range(self, sample_data: np.ndarray) -> Tuple[float, float]:
        """Get colorbar range based on configuration."""
        if self.global_data_range and self.config.global_colorbar:
            return self.global_data_range
        else:
            # Use local range
            return np.nanmin(sample_data), np.nanmax(sample_data)
    
    def estimate_processing_time(self) -> float:
        """Estimate processing time in minutes."""
        total_files = len(self.file_manager.sorted_files)
        avg_file_size = self.file_manager.get_total_size_mb() / total_files
        
        # Rough estimation: 1 minute per 100MB of data
        estimated_minutes = (avg_file_size * total_files) / 100
        
        # Adjust based on plot type
        if self.config.plot_type == 'contour':
            estimated_minutes *= 1.5  # Contour plots are slower
        elif self.config.plot_type == 'heatmap':
            estimated_minutes *= 0.7  # Heatmaps are faster
        
        return max(1.0, estimated_minutes)  # At least 1 minute
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024


 