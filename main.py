#!/usr/bin/env python3
"""
Animation Creator for NetCDF Data
"""

import xarray as xr
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import os
import sys
import psutil
import subprocess
from datetime import datetime
import pandas as pd
import logging

class UnifiedAnimator:
    """Unified animation creator with all plotting methods."""
    
    def __init__(self, nc_file):
        """Initialize with NetCDF file path."""
        if not os.path.exists(nc_file):
            raise FileNotFoundError(f"File not found: {nc_file}")
        
        # Set up cartopy logging
        self._setup_cartopy_logging()
        
        print(f"📁 Loading {nc_file}...")
        self.ds = xr.open_dataset(nc_file)
        
        # Print dataset info
        print(f"Dimensions: {dict(self.ds.dims)}")
        print(f"Variables: {list(self.ds.data_vars.keys())}")
        # Find the first dimension that's not spatial (not lat/lon)
        animate_dim = None
        for dim in self.ds.dims:
            if dim not in ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']:
                animate_dim = dim
                break
        if animate_dim:
            print(f"Animation dimension '{animate_dim}': {len(self.ds[animate_dim])} steps")
        else:
            print("No suitable animation dimension found")
        
        # Check for ffmpeg
        self._check_ffmpeg()
        
        # Check cartopy map availability
        self._check_cartopy_maps()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available and what codecs are supported."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
                self.ffmpeg_available = False
                self.available_codecs = []
            else:
                self.ffmpeg_available = True
                # Check for available codecs
                codec_result = subprocess.run(['ffmpeg', '-codecs'], 
                                            capture_output=True, text=True)
                if codec_result.returncode == 0:
                    codec_output = codec_result.stdout
                    self.available_codecs = []
                    if 'libx264' in codec_output:
                        self.available_codecs.append('libx264')
                    if 'libxvid' in codec_output:
                        self.available_codecs.append('libxvid')
                    if 'mpeg4' in codec_output:
                        self.available_codecs.append('mpeg4')
                    print(f"📹 Available codecs: {self.available_codecs}")
                else:
                    self.available_codecs = ['mpeg4']  # Default fallback
        except FileNotFoundError:
            print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
            self.ffmpeg_available = False
            self.available_codecs = []
    
    def _setup_cartopy_logging(self):
        """Set up logging for cartopy map downloads."""
        # Configure logging for cartopy
        cartopy_logger = logging.getLogger('cartopy')
        cartopy_logger.setLevel(logging.INFO)
        
        # Create console handler if it doesn't exist
        if not cartopy_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('🗺️  Cartopy: %(message)s')
            console_handler.setFormatter(formatter)
            cartopy_logger.addHandler(console_handler)
        
        # Also set up logging for urllib3 (used by cartopy for downloads)
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.INFO)
        
        if not urllib3_logger.handlers:
            urllib3_handler = logging.StreamHandler()
            urllib3_handler.setLevel(logging.INFO)
            urllib3_formatter = logging.Formatter('📥 Download: %(message)s')
            urllib3_handler.setFormatter(urllib3_formatter)
            urllib3_logger.addHandler(urllib3_handler)
    
    def _check_cartopy_maps(self):
        """Check if cartopy maps are already downloaded and log status."""
        try:
            import cartopy.io.shapereader as shapereader
            import cartopy.io.img_tiles as img_tiles
            
            # Check for Natural Earth data directory
            ne_data_dir = os.path.expanduser('~/.local/share/cartopy')
            if os.path.exists(ne_data_dir):
                print(f"🗺️  Cartopy maps found in: {ne_data_dir}")
                
                # Check for common map files
                map_files = ['natural_earth_physical', 'natural_earth_cultural']
                for map_type in map_files:
                    map_path = os.path.join(ne_data_dir, map_type)
                    if os.path.exists(map_path):
                        print(f"🗺️  {map_type} maps available")
                    else:
                        print(f"🗺️  {map_type} maps will be downloaded when needed")
            else:
                print("🗺️  Cartopy maps will be downloaded when needed")
                
        except ImportError:
            print("⚠️  Cartopy not available for map checking")
    
    def _add_cartopy_features(self, ax):
        """Add cartopy features with download checking and logging."""
        try:
            # Check if maps are already downloaded
            ne_data_dir = os.path.expanduser('~/.local/share/cartopy')
            maps_exist = os.path.exists(ne_data_dir)
            
            if not maps_exist:
                print("🗺️  Downloading cartopy maps...")
            else:
                print("🗺️  Using existing cartopy maps")
            
            # Add features (cartopy will download if needed)
            ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
            ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
            ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='lightgray')
            
            if not maps_exist:
                print("🗺️  Cartopy maps downloaded successfully")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not add cartopy features: {e}")
            print("🗺️  Continuing without map features...")
    
    def get_variable_info(self):
        """Get information about available variables."""
        info = {}
        for var_name in self.ds.data_vars.keys():
            var = self.ds[var_name]
            info[var_name] = {
                'shape': var.shape,
                'dims': var.dims,
                'attrs': var.attrs
            }
        return info
    
    def format_datetime(self, time_value, animate_dim='time'):
        """Format datetime for clean display."""
        if hasattr(time_value, 'values'):
            time_value = time_value.values
        
        # Convert to pandas datetime if it's a numpy datetime64
        if isinstance(time_value, np.datetime64):
            dt = pd.Timestamp(time_value)
        else:
            dt = pd.to_datetime(time_value)
        
        # Format based on the time range
        if len(self.ds[animate_dim]) > 24:  # More than a day
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        else:  # Less than a day
            return dt.strftime("%H:%M:%S UTC")
    
    def get_variable_title(self, variable):
        """Get a clean title for the variable."""
        titles = {
            'InstantaneousRainRate': 'Instantaneous Rain Rate',
            'AccumulatedRainRate': 'Accumulated Rain Rate',
            'Windspeed10m': 'Wind Speed (10m)',
            'Temperature2m': 'Temperature (2m)'
        }
        return titles.get(variable, variable.replace('_', ' ').title())
    
    def get_variable_subtitle(self, variable):
        """Get subtitle with units."""
        units = self.ds[variable].attrs.get('units', '')
        if units:
            return f"Units: {units}"
        return ""
    
    def select_level_interactive(self, variable):
        """Interactively select a level for 3D data."""
        # Check if the variable has a level dimension
        if 'level' not in self.ds[variable].dims:
            return None
        
        level_count = len(self.ds.level)
        print(f"\n📊 Variable '{variable}' has {level_count} levels")
        
        # Always show all levels
        print("Available levels:")
        for i in range(level_count):
            level_val = self.ds.level[i].values
            print(f"  {i}: {level_val}")
        
        while True:
            choice = input(f"\nSelect level (0-{level_count-1}) or 'avg' for average: ").strip()
            
            if choice.lower() == 'avg':
                return None  # Will average over levels
            try:
                level_idx = int(choice)
                if 0 <= level_idx < level_count:
                    return level_idx
                else:
                    print(f"❌ Level index must be between 0 and {level_count-1}")
            except ValueError:
                print("❌ Please enter a valid number or 'avg'")
    
    def filter_low_values(self, data, percentile=5):
        """Filter out low percentile values to reduce noise."""
        if data.size == 0:
            return data
        
        # Calculate percentile threshold
        threshold = np.percentile(data[data > 0], percentile) if np.any(data > 0) else 0
        
        # Create masked array where low values are masked
        filtered_data = np.where(data >= threshold, data, np.nan)
        
        return filtered_data
    
    def prepare_data_for_plotting(self, variable, time_step=0, animate_dim='time', level_index=None):
        """Prepare data for plotting by handling extra dimensions."""

        
        # Get the data array
        data_array = self.ds[variable].isel({animate_dim: time_step})
        
        # Handle multiple non-spatial dimensions
        # Define spatial dimensions
        spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']
        
        # Find which dimensions are spatial
        spatial_dims_in_data = [dim for dim in data_array.dims if dim in spatial_dims]
        
        # If we have more than 2 dimensions, we need to reduce to 2D
        if len(data_array.dims) > 2:
            # Keep only the spatial dimensions, handle others
            non_spatial_dims = [dim for dim in data_array.dims if dim not in spatial_dims]
            
            if non_spatial_dims:
                print(f"📊 Reducing {len(data_array.dims)}D data to 2D")
                
                # If level_index is specified, select that level
                if level_index is not None and 'level' in non_spatial_dims:
                    print(f"📊 Selecting level {level_index}")
                    try:
                        data_array = data_array.isel(level=level_index)
                        non_spatial_dims.remove('level')
                    except Exception as e:
                        print(f"❌ Error selecting level {level_index}: {e}")
                        print(f"Available level indices: 0 to {len(self.ds.level)-1}")
                        raise
                
                # Average over remaining non-spatial dimensions
                for dim in non_spatial_dims:
                    print(f"📊 Averaging over dimension: {dim}")
                    data_array = data_array.mean(dim=dim)
        
        # Squeeze out any remaining singleton dimensions
        data_array = data_array.squeeze()
        
        # Convert to numpy array
        data = data_array.values
        
        # Verify we have 2D data
        if len(data.shape) != 2:
            raise ValueError(f"Data must be 2D for plotting, got shape {data.shape}. "
                           f"Available dimensions: {list(self.ds[variable].dims)}")
        
        # Get coordinates (handle both 2D and 1D coordinate cases)
        if hasattr(self.ds, 'latitude') and hasattr(self.ds, 'longitude'):
            lats = self.ds.latitude.values
            lons = self.ds.longitude.values
        elif hasattr(self.ds, 'lat') and hasattr(self.ds, 'lon'):
            lats = self.ds.lat.values
            lons = self.ds.lon.values
        else:
            # Try to get coordinates from the data array itself
            coords = data_array.coords
            if 'latitude' in coords and 'longitude' in coords:
                lats = coords['latitude'].values
                lons = coords['longitude'].values
            elif 'lat' in coords and 'lon' in coords:
                lats = coords['lat'].values
                lons = coords['lon'].values
            else:
                # Fallback: create coordinate arrays based on data shape
                lats = np.arange(data.shape[0])
                lons = np.arange(data.shape[1])
        
        return data, lats, lons
    
    def explore_dataset(self):
        """Explore and display dataset information."""
        print("\n" + "=" * 60)
        print("Dataset Explorer")
        print("=" * 60)
        
        # Show dataset info
        print(f"\nDataset Information:")
        print(f"  Dimensions: {dict(self.ds.dims)}")
        print(f"  Variables: {list(self.ds.data_vars.keys())}")
        
        # Find animation dimension
        animate_dim = None
        for dim in self.ds.dims:
            if dim not in ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']:
                animate_dim = dim
                break
        
        if animate_dim:
            print(f"  Animation dimension '{animate_dim}': {len(self.ds[animate_dim])} steps")
        else:
            print("  No suitable animation dimension found")
        
        # Show animation dimension range
        animate_dim = None
        for dim in self.ds.dims:
            if dim not in ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']:
                animate_dim = dim
                break
        
        if animate_dim and len(self.ds[animate_dim]) > 0:
            start_val = self.ds[animate_dim][0].values
            end_val = self.ds[animate_dim][-1].values
            print(f"  {animate_dim} range: {start_val} to {end_val}")
        
        # Show variable details
        print(f"\nVariable Details:")
        var_info = self.get_variable_info()
        for var_name, info in var_info.items():
            print(f"  {var_name}:")
            print(f"    Shape: {info['shape']}")
            print(f"    Dimensions: {info['dims']}")
            if info['attrs']:
                print(f"    Units: {info['attrs'].get('units', 'N/A')}")
        
        # Check spatial coordinates
        if 'latitude' in self.ds.coords and 'longitude' in self.ds.coords:
            lat = self.ds.latitude
            lon = self.ds.longitude
            print(f"\nSpatial Information:")
            print(f"  Latitude range: {lat.min().values:.2f} to {lat.max().values:.2f}")
            print(f"  Longitude range: {lon.min().values:.2f} to {lon.max().values:.2f}")
        
        # Show codec information
        codec_info = self.get_codec_info()
        print(f"\nVideo Codec Information:")
        print(f"  ffmpeg available: {codec_info['ffmpeg_available']}")
        print(f"  Available codecs: {codec_info['available_codecs']}")
        print(f"  Recommended codec: {codec_info['recommended_codec']}")
    
    def create_single_plot(self, variable, plot_type='efficient', time_step=0, animate_dim='time', level_index=None):
        """Create a single plot for preview."""
        print(f"\n📊 Creating {plot_type} plot for {variable} at time step {time_step}...")
        
        if plot_type == 'efficient':
            fig = self._create_efficient_plot(variable, time_step, animate_dim, level_index)
        elif plot_type == 'contour':
            fig = self._create_contour_plot(variable, time_step, animate_dim, level_index)
        elif plot_type == 'heatmap':
            fig = self._create_heatmap_plot(variable, time_step, animate_dim, level_index)
        else:
            print(f"❌ Unknown plot type: {plot_type}")
            return None
        
        # Save plot instead of showing in non-interactive mode
        output_file = f"{variable}_{plot_type}_plot.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"📊 Plot saved: {output_file}")
        plt.close(fig)
        return fig
    
    def _create_efficient_plot(self, variable, time_step=0, animate_dim='time', level_index=None):
        """Create an efficient single plot with Cartopy."""
        fig, ax = plt.subplots(figsize=(15, 10), 
                              subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Get data and coordinates using the helper method
        data, lats, lons = self.prepare_data_for_plotting(variable, time_step, animate_dim, level_index)
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Add Cartopy features with download checking
        self._add_cartopy_features(ax)
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, linestyle='--', color='gray')
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Set extent
        ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], 
                     crs=ccrs.PlateCarree())
        
        # Create plot
        im = ax.imshow(filtered_data, cmap='Blues', alpha=0.8,
                      extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), origin='lower')
        
        # Add colorbar and labels
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
        
        # Add title and subtitle with better positioning
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim)
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"{animate_dim.capitalize()}: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=30)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def _create_contour_plot(self, variable, time_step=0, animate_dim='time', level_index=None):
        """Create a contour single plot with Cartopy."""
        fig, ax = plt.subplots(figsize=(15, 10), 
                              subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Get data and coordinates using the helper method
        data, lats, lons = self.prepare_data_for_plotting(variable, time_step, animate_dim, level_index)
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Add Cartopy features with download checking
        self._add_cartopy_features(ax)
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, linestyle='--', color='gray')
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Set extent
        ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], 
                     crs=ccrs.PlateCarree())
        
        # Create contour plot
        levels = np.linspace(np.nanmin(filtered_data), np.nanmax(filtered_data), 20)
        contour = ax.contourf(lons, lats, filtered_data, levels=levels, cmap='Blues',
                             transform=ccrs.PlateCarree())
        
        # Add colorbar and labels
        cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
        cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
        
        # Add title and subtitle with better positioning
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim)
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"{animate_dim.capitalize()}: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=30)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def _create_heatmap_plot(self, variable, time_step=0, animate_dim='time', level_index=None):
        """Create a simple heatmap plot."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get data using the helper method
        data, _, _ = self.prepare_data_for_plotting(variable, time_step, animate_dim, level_index)
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Create heatmap
        im = ax.imshow(filtered_data, cmap='Blues', aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
        
        # Add title and subtitle
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim)
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"{animate_dim.capitalize()}: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=20)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def create_direct_animation(self, variable, output_file=None, fps=10, 
                              plot_type='efficient', title=None, animate_dim='time', level_index=None):
        """Create a direct animation (no individual frames)."""
        if output_file is None:
            output_file = f'{variable}_{plot_type}_animation.mp4'
        
        if not self.ffmpeg_available:
            print("❌ ffmpeg not available. Cannot create video.")
            return
        
        # Memory monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"💾 Initial memory usage: {initial_memory:.1f} MB")
        
        # Get data range for consistent colorbar (excluding filtered values)
        # For 3D data, we need to handle the animate_dim and level properly
        try:
            # If level_index is specified, we need to handle it in the data range calculation
            if level_index is not None and 'level' in self.ds[variable].dims:
                # Select the specific level for range calculation
                data_for_range = self.ds[variable].isel(level=level_index).values
            else:
                # Use all data (will average over levels)
                data_for_range = self.ds[variable].values
            
            filtered_all_data = self.filter_low_values(data_for_range)
            data_min = np.nanmin(filtered_all_data)
            data_max = np.nanmax(filtered_all_data)
        except Exception as e:
            print(f"Warning: Could not calculate full data range: {e}")
            # Use a sample of the data for range calculation
            sample_data, _, _ = self.prepare_data_for_plotting(variable, 0, animate_dim, level_index)
            filtered_sample = self.filter_low_values(sample_data)
            data_min = np.nanmin(filtered_sample)
            data_max = np.nanmax(filtered_sample)
        
        # Get coordinates using helper method
        _, lats, lons = self.prepare_data_for_plotting(variable, 0, animate_dim, level_index)
        
        # Create figure and axis based on plot type
        if plot_type in ['efficient', 'contour']:
            # Always use Cartopy for geographic plots
            fig, ax = plt.subplots(figsize=(15, 10), 
                                  subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Add Cartopy features with download checking
            self._add_cartopy_features(ax)
            
            # Add gridlines
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, linestyle='--', color='gray')
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            
            # Set extent
            ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], 
                         crs=ccrs.PlateCarree())
            
            if plot_type == 'efficient':
                # Initialize efficient plot
                initial_data, _, _ = self.prepare_data_for_plotting(variable, 0, animate_dim, level_index)
                filtered_initial_data = self.filter_low_values(initial_data)
                im = ax.imshow(filtered_initial_data, cmap='Blues', alpha=0.8,
                              extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                              transform=ccrs.PlateCarree(), origin='lower',
                              vmin=data_min, vmax=data_max)
                
                # Add colorbar
                cbar = plt.colorbar(im, ax=ax, shrink=0.8)
                cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
                
            else:  # contour
                # Initialize contour plot
                initial_data, _, _ = self.prepare_data_for_plotting(variable, 0, animate_dim, level_index)
                filtered_initial_data = self.filter_low_values(initial_data)
                levels = np.linspace(data_min, data_max, 20)
                contour = ax.contourf(lons, lats, filtered_initial_data, levels=levels, cmap='Blues',
                                     transform=ccrs.PlateCarree())
                
                # Add colorbar
                cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
                cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
                
                # Store the contour collection for later removal
                contour_collections = [contour]
            
        else:  # heatmap plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Initialize heatmap plot
            initial_data, _, _ = self.prepare_data_for_plotting(variable, 0, animate_dim, level_index)
            filtered_initial_data = self.filter_low_values(initial_data)
            im = ax.imshow(filtered_initial_data, cmap='Blues', aspect='auto',
                          vmin=data_min, vmax=data_max)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
        
        # Add title and subtitle
        if title is None:
            title = self.get_variable_title(variable)
        
        # Create title and subtitle text objects with better positioning
        title_text = ax.text(0.5, 1.15, '', transform=ax.transAxes, 
                           ha='center', fontsize=14, weight='bold')
        subtitle_text = ax.text(0.5, 1.11, '', transform=ax.transAxes, 
                              ha='center', fontsize=10)
        units_text = ax.text(0.5, 0.02, '', transform=ax.transAxes, 
                           ha='center', fontsize=10, style='italic')
        
        frame_count = 0
        max_frames = len(self.ds[animate_dim])
        
        def animate(frame):
            """Animation function with proper memory management."""
            nonlocal frame_count
            frame_count += 1
            
            try:
                # Check memory usage every 10 frames
                if frame_count % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"📊 Frame {frame_count}/{max_frames}, Memory: {current_memory:.1f} MB")
                
                # Get data for current frame using helper method
                data, _, _ = self.prepare_data_for_plotting(variable, frame, animate_dim, level_index)
                filtered_data = self.filter_low_values(data)
                
                # Update title and subtitle
                time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: frame}), animate_dim)
                title_text.set_text(title)
                subtitle_text.set_text(f"{animate_dim.capitalize()}: {time_str}")
                units_text.set_text(self.get_variable_subtitle(variable))
                
                # Update plot based on type
                if plot_type == 'contour':
                    # For contour plots, we need to recreate the contour each time
                    # Remove the previous contour collections
                    for collection in contour_collections:
                        if collection in ax.collections:
                            collection.remove()
                    
                    # Create new contour
                    new_contour = ax.contourf(lons, lats, filtered_data, levels=levels, cmap='Blues',
                                             transform=ccrs.PlateCarree())
                    
                    # Update the stored contour collections
                    contour_collections.clear()
                    contour_collections.append(new_contour)
                    
                    # Return all artists that need to be updated
                    return [new_contour] + [title_text, subtitle_text, units_text]
                else:
                    # Update image data
                    im.set_array(filtered_data)
                    return [im, title_text, subtitle_text, units_text]
                
            except Exception as e:
                print(f"❌ Error in animation frame {frame}: {e}")
                return []
        
        print(f"🎬 Creating {plot_type} animation with {max_frames} frames...")
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate, frames=max_frames,
            interval=1000//fps,  # Convert fps to interval
            blit=True, repeat=True,
            cache_frame_data=False  # Don't cache frames to save memory
        )
        
        # Save animation
        print(f"💾 Saving animation: {output_file}")
        
        # Choose the best available codec
        if hasattr(self, 'available_codecs') and self.available_codecs:
            if 'libx264' in self.available_codecs:
                codec = 'libx264'
            elif 'libxvid' in self.available_codecs:
                codec = 'libxvid'
            else:
                codec = 'mpeg4'
        else:
            # Fallback to mpeg4 if no codec detection
            codec = 'mpeg4'
        
        print(f"📹 Using codec: {codec}")
        
        # Try to save with the selected codec, fallback to others if it fails
        codecs_to_try = [codec]
        if codec != 'mpeg4':
            codecs_to_try.append('mpeg4')
        if codec != 'libxvid' and 'libxvid' in getattr(self, 'available_codecs', []):
            codecs_to_try.append('libxvid')
        
        saved_successfully = False
        for try_codec in codecs_to_try:
            try:
                print(f"📹 Trying codec: {try_codec}")
                anim.save(
                    output_file,
                    writer='ffmpeg',
                    fps=fps,
                    dpi=72,  # Lower DPI for better performance
                    bitrate=1000,  # Reasonable bitrate
                    codec=try_codec
                )
                saved_successfully = True
                print(f"✅ Successfully saved with codec: {try_codec}")
                break
            except Exception as e:
                print(f"❌ Failed with codec {try_codec}: {e}")
                if try_codec == codecs_to_try[-1]:  # Last codec to try
                    raise Exception(f"Failed to save animation with any available codec. Last error: {e}")
                continue
        
        plt.close(fig)
        print(f"✅ Animation saved: {output_file}")
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"💾 Final memory usage: {final_memory:.1f} MB")
        
        # Clean up
        del anim
        import gc
        gc.collect()
    
    def create_batch_animations(self, plot_type='efficient', fps=10, animate_dim='time', level_index=None):
        """Create animations for all variables."""
        print(f"\n🎬 Creating {plot_type} animations for all variables...")
        
        var_info = self.get_variable_info()
        successful = 0
        failed = 0
        
        for var_name in var_info.keys():
            print(f"\n🎬 Creating animation for {var_name}...")
            
            try:
                output_file = f"{var_name}_{plot_type}_animation.mp4"
                self.create_direct_animation(var_name, output_file, fps, plot_type, animate_dim=animate_dim, level_index=level_index)
                print(f"✅ Created: {output_file}")
                successful += 1
                
            except Exception as e:
                print(f"❌ Error creating animation for {var_name}: {e}")
                failed += 1
        
        print(f"\n📊 Batch animation summary:")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📁 Check current directory for output files")
    
    def get_codec_info(self):
        """Get information about available codecs and ffmpeg status."""
        info = {
            'ffmpeg_available': self.ffmpeg_available,
            'available_codecs': getattr(self, 'available_codecs', []),
            'recommended_codec': None
        }
        
        if hasattr(self, 'available_codecs') and self.available_codecs:
            if 'libx264' in self.available_codecs:
                info['recommended_codec'] = 'libx264'
            elif 'libxvid' in self.available_codecs:
                info['recommended_codec'] = 'libxvid'
            else:
                info['recommended_codec'] = 'mpeg4'
        else:
            info['recommended_codec'] = 'mpeg4'
        
        return info
    
    def close(self):
        """Close the dataset."""
        if hasattr(self, 'ds'):
            self.ds.close()

def main():
    """Main function for unified animation creation."""
    print("=" * 60)
    print("Unified Animation Creator for NetCDF Data")
    print("=" * 60)
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create animations from NetCDF files with clean titles and value filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python unified_animation.py
  
  # Specify NetCDF file
  python unified_animation.py IDALIA_10km.nc
  
  # Quick animation with all arguments
  python unified_animation.py IDALIA_10km.nc --variable InstantaneousRainRate --type efficient --output my_animation.mp4 --fps 15
  
  # Batch animation for all variables
  python unified_animation.py IDALIA_10km.nc --batch --type contour --fps 10
        """
    )
    
    parser.add_argument('nc_file', nargs='?', default='IDALIA_10km.nc',
                       help='Path to NetCDF file (default: IDALIA_10km.nc)')
    
    parser.add_argument('--variable', '-v', 
                       help='Variable name to animate (e.g., InstantaneousRainRate)')
    
    parser.add_argument('--type', '-t', choices=['efficient', 'contour', 'heatmap'],
                       default='efficient',
                       help='Animation/plot type (default: efficient)')
    
    parser.add_argument('--output', '-o',
                       help='Output filename (default: auto-generated)')
    
    parser.add_argument('--fps', '-f', type=int, default=10,
                       help='Frames per second (default: 10)')
    
    parser.add_argument('--batch', '-b', action='store_true',
                       help='Create animations for all variables')
    
    parser.add_argument('--plot', '-p', action='store_true',
                       help='Create single plot instead of animation')
    
    parser.add_argument('--time-step', type=int, default=0,
                       help='Time step for single plot (default: 0)')
    
    parser.add_argument('--percentile', type=int, default=5,
                       help='Percentile threshold for filtering low values (default: 5)')
    
    parser.add_argument('--animate-dim', default='time',
                       help='Dimension to animate over (default: time)')
    
    parser.add_argument('--level', '-l', type=int,
                       help='Level index for 3D data (use -1 for average over levels)')
    
    parser.add_argument('--no-interactive', action='store_true',
                       help='Skip interactive mode and use command line arguments only')
    
    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.nc_file):
        print(f"Error: File '{args.nc_file}' not found!")
        return

    try:
        # Load the animator
        print(f"\nLoading NetCDF file: {args.nc_file}")
        animator = UnifiedAnimator(args.nc_file)

        # Validate or auto-select animate_dim
        ds_dims = list(animator.ds.dims)
        spatial_dims = ['lat', 'lon', 'latitude', 'longitude', 'y', 'x', 'nj', 'ni']
        candidate_dims = [d for d in ds_dims if d not in spatial_dims]

        animate_dim = args.animate_dim
        if animate_dim not in ds_dims:
            if candidate_dims:
                print(f"⚠️  Dimension '{animate_dim}' not found. Using '{candidate_dims[0]}' instead.")
                animate_dim = candidate_dims[0]
            else:
                print(f"❌ Error: No suitable animation dimension found in file. Available dimensions: {ds_dims}")
                return
        


        # Update percentile filter if specified
        if args.percentile != 5:
            # Store the original method
            original_filter = animator.filter_low_values
            # Create a new method with the custom percentile
            def custom_filter(data, percentile=args.percentile):
                return original_filter(data, percentile)
            animator.filter_low_values = custom_filter
        
        # Handle level selection
        level_index = None
        if args.level is not None:
            if args.level == -1:
                level_index = None  # Average over levels
                print("📊 Will average over all levels")
            else:
                level_index = args.level
                print(f"📊 Will use level {level_index}")

        
        # If all required arguments are provided, run in non-interactive mode
        if args.no_interactive or (args.variable and (args.batch or args.plot or not args.no_interactive)):
            if args.batch:
                # Batch animation mode
                print(f"\n🎬 Creating batch animations...")
                print(f"Type: {args.type}")
                print(f"FPS: {args.fps}")
                animator.create_batch_animations(args.type, args.fps, animate_dim, level_index)
                
            elif args.plot:
                # Single plot mode
                print(f"\n📊 Creating single plot...")
                print(f"Variable: {args.variable}")
                print(f"Type: {args.type}")
                print(f"Time step: {args.time_step}")
                animator.create_single_plot(args.variable, args.type, args.time_step, animate_dim, level_index)
                
            else:
                # Single animation mode
                output_file = args.output or f"{args.variable}_{args.type}_animation.mp4"
                print(f"\n🎬 Creating single animation...")
                print(f"Variable: {args.variable}")
                print(f"Type: {args.type}")
                print(f"Output: {output_file}")
                print(f"FPS: {args.fps}")
                print(f"Total frames: {len(animator.ds[animate_dim])}")
                animator.create_direct_animation(args.variable, output_file, args.fps, args.type, animate_dim=animate_dim, level_index=level_index)
            
            # Clean up
            animator.close()
            return
        
        # Interactive mode
        # Explore dataset
        animator.explore_dataset()
        
        # Show main menu
        print("\n" + "=" * 60)
        print("Main Menu")
        print("=" * 60)
        print("1. Create single plot (preview)")
        print("2. Create single animation")
        print("3. Create batch animations (all variables)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Single plot
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
                return
            
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
                return
            
            # Select level if variable has level dimension
            level_index = None
            if 'level' in animator.ds[variable].dims:
                level_index = animator.select_level_interactive(variable)
            
            # Create plot
            animator.create_single_plot(variable, plot_type, animate_dim=animate_dim, level_index=level_index)
            
        elif choice == "2":
            # Single animation
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
                return
            
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
                return
            
            # Get output filename and FPS
            default_output = f"{variable}_{anim_type}_animation.mp4"
            output_file = input(f"\nOutput filename (default: {default_output}): ").strip()
            if not output_file:
                output_file = default_output
            
            fps = input("Frames per second (default: 10): ").strip()
            if not fps:
                fps = 10
            else:
                fps = int(fps)
            
            # Select level if variable has level dimension
            level_index = None
            if 'level' in animator.ds[variable].dims:
                level_index = animator.select_level_interactive(variable)
            
            # Create animation
            print(f"\n🎬 Creating {anim_type} animation...")
            print(f"Variable: {variable}")
            print(f"Output: {output_file}")
            print(f"FPS: {fps}")
            print(f"Total frames: {len(animator.ds[animate_dim])}")
            
            animator.create_direct_animation(variable, output_file, fps, anim_type, title=None, animate_dim=animate_dim, level_index=level_index)
            
        elif choice == "3":
            # Batch animations
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
                return
            
            # Get FPS
            fps = input("Frames per second (default: 10): ").strip()
            if not fps:
                fps = 10
            else:
                fps = int(fps)
            
            # Check if any variable has level dimension
            level_index = None
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
            
            # Create batch animations
            animator.create_batch_animations(anim_type, fps, animate_dim, level_index)
            
        elif choice == "4":
            print("Goodbye!")
            return
        
        else:
            print("Invalid choice!")
        
        # Clean up
        animator.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your NetCDF file is valid")
        print("2. Check that the variable has time and spatial dimensions")
        print("3. Ensure you have ffmpeg installed for video creation")
        print("4. For geographic animations, make sure you have latitude/longitude coordinates")
        print("5. If you get 'unknown encoder h264' error:")
        print("   - Install ffmpeg with h264 support: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)")
        print("   - The script will automatically try alternative codecs (mpeg4, libxvid)")
        print("   - Check available codecs with: ffmpeg -codecs | grep -E '(libx264|libxvid|mpeg4)'")

if __name__ == "__main__":
    main() 
