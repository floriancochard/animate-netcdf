#!/usr/bin/env python3
"""
Multi-File Animation Engine for NetCDF Data
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

# Import our custom modules
from config_manager import AnimationConfig, ConfigManager
from file_manager import NetCDFFileManager
from main import UnifiedAnimator  # Import the existing animator


class MultiFileAnimator:
    """Handles animations across multiple NetCDF files without concatenation."""
    
    def __init__(self, file_manager: NetCDFFileManager, config: AnimationConfig):
        self.file_manager = file_manager
        self.config = config
        self.current_animator = None
        self.global_data_range = None
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging for the multi-file animator."""
        self.logger = logging.getLogger('MultiFileAnimator')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('🎬 MultiFile: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
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
                    
                    # Get data for the variable
                    data = ds[self.config.variable].values
                    
                    # Apply filtering if needed
                    if self.config.percentile > 0:
                        data = self._filter_low_values(data, self.config.percentile)
                    
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
    
    def _filter_low_values(self, data: np.ndarray, percentile: int) -> np.ndarray:
        """Filter out low percentile values to reduce noise."""
        if data.size == 0:
            return data
        
        # Calculate percentile threshold
        threshold = np.percentile(data[data > 0], percentile) if np.any(data > 0) else 0
        
        # Create masked array where low values are masked
        filtered_data = np.where(data >= threshold, data, np.nan)
        
        return filtered_data
    
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
        
        # Pre-scan for global data range if enabled
        if self.config.global_colorbar and self.config.pre_scan_files:
            self.global_data_range = self.pre_scan_files()
        
        # Create output filename
        output_file = self._generate_output_filename()
        
        # Check if output file exists
        if os.path.exists(output_file) and not self.config.overwrite_existing:
            print(f"⚠️  Output file {output_file} already exists. Use --overwrite to overwrite.")
            return False
        
        # Create animation
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
        if self.config.output_pattern:
            # Use the configured pattern
            if self.config.output_pattern.endswith(f'.{self.config.output_format}'):
                return self.config.output_pattern
            else:
                return f"{self.config.output_pattern}.{self.config.output_format}"
        else:
            # Generate default filename
            return f"{self.config.variable}_{self.config.plot_type}_multifile.{self.config.output_format}"
    
    def _create_geographic_animation(self, output_file: str) -> bool:
        """Create geographic animation with Cartopy."""
        try:
            # Import cartopy components
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
            
            # Get spatial coordinates from first file
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
                
                # Animation function
                def animate(frame):
                    filepath = self.file_manager.sorted_files[frame]
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
                
                contour = ax.contourf(lon_min, lat_min, initial_data, levels=levels, 
                                     cmap='Blues', transform=ccrs.PlateCarree())
                
                # Add colorbar
                cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
                cbar.set_label(f'{self.config.variable} (units)')
                
                # Animation function
                def animate(frame):
                    filepath = self.file_manager.sorted_files[frame]
                    data = self._load_file_data(filepath)
                    if data is not None:
                        # Remove previous contour
                        for collection in ax.collections:
                            collection.remove()
                        
                        # Create new contour
                        new_contour = ax.contourf(lon_min, lat_min, data, levels=levels,
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
            anim.save(output_file, writer='ffmpeg', fps=self.config.fps, dpi=72)
            plt.close(fig)
            
            return True
            
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
            
            # Animation function
            def animate(frame):
                filepath = self.file_manager.sorted_files[frame]
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
            anim.save(output_file, writer='ffmpeg', fps=self.config.fps, dpi=72)
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating heatmap animation: {e}")
            return False
    
    def _load_file_data(self, filepath: str) -> Optional[np.ndarray]:
        """Load data from a single file."""
        try:
            with xr.open_dataset(filepath) as ds:
                if self.config.variable not in ds.data_vars:
                    return None
                
                # Get data
                data = ds[self.config.variable].values
                
                # Apply filtering
                if self.config.percentile > 0:
                    data = self._filter_low_values(data, self.config.percentile)
                
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


if __name__ == "__main__":
    # Test the multi-file animator
    print("Testing Multi-File Animator...")
    
    # Create test configuration
    config = AnimationConfig()
    config.variable = "test_var"
    config.plot_type = "efficient"
    config.fps = 10
    
    # Create file manager
    file_manager = NetCDFFileManager("*.nc")
    files = file_manager.discover_files()
    
    if files:
        # Create multi-file animator
        animator = MultiFileAnimator(file_manager, config)
        
        # Test configuration validation
        is_valid = animator._validate_config()
        print(f"Configuration valid: {is_valid}")
        
        # Test time estimation
        if is_valid:
            time_minutes = animator.estimate_processing_time()
            print(f"Estimated processing time: {time_minutes:.1f} minutes")
    
    print("Multi-file animator test completed!") 