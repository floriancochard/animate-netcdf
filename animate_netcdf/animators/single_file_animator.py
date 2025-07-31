#!/usr/bin/env python3
"""
Single File Animator for NetCDF Animations
Handles animations for individual NetCDF files
"""

import os
import psutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import xarray as xr
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from .base_animator import BaseAnimator
from animate_netcdf.utils.data_processing import DataProcessor
from animate_netcdf.utils.plot_utils import PlotUtils


class SingleFileAnimator(BaseAnimator):
    """Handles animations for single NetCDF files."""
    
    def __init__(self, nc_file: str):
        """Initialize with NetCDF file path."""
        super().__init__()
        
        if not os.path.exists(nc_file):
            raise FileNotFoundError(f"File not found: {nc_file}")
        
        print(f"📁 Loading {nc_file}...")
        self.ds = xr.open_dataset(nc_file)
        
        # Print dataset info
        print(f"Dimensions: {dict(self.ds.dims)}")
        print(f"Variables: {list(self.ds.data_vars.keys())}")
        
        # Find animation dimension
        animate_dim = self.get_animation_dimension(self.ds)
        if animate_dim:
            print(f"Animation dimension '{animate_dim}': {len(self.ds[animate_dim])} steps")
        else:
            print("No suitable animation dimension found")
    
    def get_variable_info(self) -> Dict[str, Any]:
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
    
    def select_level_interactive(self, variable: str) -> Optional[int]:
        """Interactively select a level for 3D data."""
        # Check if the variable has a level dimension
        level_dim = None
        if 'level' in self.ds[variable].dims:
            level_dim = 'level'
        elif 'level_w' in self.ds[variable].dims:
            level_dim = 'level_w'
        
        if level_dim is None:
            return None
        
        level_count = len(self.ds[level_dim])
        print(f"\n📊 Variable '{variable}' has {level_count} levels (dimension: {level_dim})")
        
        # Always show all levels
        print("Available levels:")
        for i in range(level_count):
            level_val = self.ds[level_dim][i].values
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
        animate_dim = self.get_animation_dimension(self.ds)
        if animate_dim:
            print(f"  Animation dimension '{animate_dim}': {len(self.ds[animate_dim])} steps")
        else:
            print("  No suitable animation dimension found")
        
        # Show animation dimension range
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
    
    def create_single_plot(self, variable: str, plot_type: str = 'efficient', 
                          time_step: int = 0, animate_dim: str = 'time', 
                          level_index: Optional[int] = None, zoom_factor: float = 1.0) -> bool:
        """Create a single plot for preview."""
        print(f"\n📊 Creating {plot_type} plot for {variable} at time step {time_step}...")
        
        try:
            if plot_type == 'efficient':
                fig = self._create_efficient_plot(variable, time_step, animate_dim, level_index, zoom_factor)
            elif plot_type == 'contour':
                fig = self._create_contour_plot(variable, time_step, animate_dim, level_index, zoom_factor)
            elif plot_type == 'heatmap':
                fig = self._create_heatmap_plot(variable, time_step, animate_dim, level_index, zoom_factor)
            else:
                print(f"❌ Unknown plot type: {plot_type}")
                return False
            
            # Save plot instead of showing in non-interactive mode
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{timestamp}_{variable}_{plot_type}_plot.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"📊 Plot saved: {output_file}")
            plt.close(fig)
            return True
            
        except Exception as e:
            print(f"❌ Error creating plot: {e}")
            return False
    
    def _create_efficient_plot(self, variable: str, time_step: int = 0, 
                              animate_dim: str = 'time', level_index: Optional[int] = None, 
                              zoom_factor: float = 1.0):
        """Create an efficient single plot with Cartopy."""
        fig, ax = self.plot_utils.create_geographic_plot('efficient')
        
        # Get data and coordinates using the helper method
        data, lats, lons = self.prepare_data_for_plotting(
            self.ds[variable], time_step, animate_dim, level_index, zoom_factor
        )
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Set up geographic plot
        self.plot_utils.setup_geographic_plot(ax, lats, lons)
        
        # Create plot
        im = self.plot_utils.create_efficient_plot(ax, filtered_data, lats, lons)
        
        # Add colorbar and labels
        units = self.ds[variable].attrs.get("units", "units")
        self.plot_utils.add_colorbar(im, ax, variable, units)
        
        # Add title and subtitle
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim, self.ds)
        units_str = self.get_variable_subtitle(variable, self.ds)
        self.plot_utils.add_title_and_subtitle(ax, variable, time_str, units_str)
        
        plt.tight_layout()
        return fig
    
    def _create_contour_plot(self, variable: str, time_step: int = 0, 
                            animate_dim: str = 'time', level_index: Optional[int] = None, 
                            zoom_factor: float = 1.0):
        """Create a contour single plot with Cartopy."""
        fig, ax = self.plot_utils.create_geographic_plot('contour')
        
        # Get data and coordinates using the helper method
        data, lats, lons = self.prepare_data_for_plotting(
            self.ds[variable], time_step, animate_dim, level_index, zoom_factor
        )
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Set up geographic plot
        self.plot_utils.setup_geographic_plot(ax, lats, lons)
        
        # Create contour plot
        contour = self.plot_utils.create_contour_plot(ax, filtered_data, lats, lons)
        
        # Add colorbar and labels
        units = self.ds[variable].attrs.get("units", "units")
        self.plot_utils.add_colorbar(contour, ax, variable, units)
        
        # Add title and subtitle
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim, self.ds)
        units_str = self.get_variable_subtitle(variable, self.ds)
        self.plot_utils.add_title_and_subtitle(ax, variable, time_str, units_str)
        
        plt.tight_layout()
        return fig
    
    def _create_heatmap_plot(self, variable: str, time_step: int = 0, 
                            animate_dim: str = 'time', level_index: Optional[int] = None, 
                            zoom_factor: float = 1.0):
        """Create a simple heatmap plot."""
        fig, ax = self.plot_utils.create_heatmap_plot()
        
        # Get data using the helper method
        data, _, _ = self.prepare_data_for_plotting(
            self.ds[variable], time_step, animate_dim, level_index, zoom_factor
        )
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Create heatmap
        im = ax.imshow(filtered_data, cmap='Blues', aspect='auto')
        
        # Add colorbar
        units = self.ds[variable].attrs.get("units", "units")
        self.plot_utils.add_colorbar(im, ax, variable, units)
        
        # Add title and subtitle
        time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: time_step}), animate_dim, self.ds)
        units_str = self.get_variable_subtitle(variable, self.ds)
        self.plot_utils.add_title_and_subtitle(ax, variable, time_str, units_str)
        
        plt.tight_layout()
        return fig
    
    def create_animation(self, variable: str, output_file: Optional[str] = None, 
                        fps: int = 10, plot_type: str = 'efficient', title: Optional[str] = None,
                        animate_dim: str = 'time', level_index: Optional[int] = None, 
                        zoom_factor: float = 1.0) -> bool:
        """Create a direct animation (no individual frames)."""
        if output_file is None:
            output_file = self.generate_output_filename(variable, plot_type)
        
        # Reset zoom flag for this animation
        self.reset_zoom_flag()
        
        if not self.is_ffmpeg_available():
            print("❌ ffmpeg not available. Cannot create video.")
            return False
        
        # Memory monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"💾 Initial memory usage: {initial_memory:.1f} MB")
        
        # Get data range for consistent colorbar (excluding filtered values)
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
            sample_data, _, _ = self.prepare_data_for_plotting(
                self.ds[variable], 0, animate_dim, level_index, zoom_factor, verbose=False
            )
            filtered_sample = self.filter_low_values(sample_data)
            data_min = np.nanmin(filtered_sample)
            data_max = np.nanmax(filtered_sample)
        
        # Get coordinates using helper method
        try:
            _, lats, lons = self.prepare_data_for_plotting(
                self.ds[variable], 0, animate_dim, level_index, zoom_factor, verbose=False
            )
        except Exception as e:
            print(f"❌ Error preparing data: {e}")
            # Fallback: create coordinate arrays based on data shape
            data_shape = self.ds[variable].shape
            if len(data_shape) >= 2:
                lats = np.arange(data_shape[-2])
                lons = np.arange(data_shape[-1])
            else:
                raise ValueError(f"Cannot determine coordinates for variable {variable}")
        
        # Create figure and axis based on plot type
        if plot_type in ['efficient', 'contour']:
            # Always use Cartopy for geographic plots
            fig, ax = self.plot_utils.create_geographic_plot(plot_type)
            
            # Set up geographic plot
            self.plot_utils.setup_geographic_plot(ax, lats, lons)
            
            if plot_type == 'efficient':
                # Initialize efficient plot
                initial_data, _, _ = self.prepare_data_for_plotting(
                    self.ds[variable], 0, animate_dim, level_index, zoom_factor, verbose=False
                )
                filtered_initial_data = self.filter_low_values(initial_data)
                im = self.plot_utils.create_efficient_plot(ax, filtered_initial_data, lats, lons, data_min, data_max)
                
                # Add colorbar
                units = self.ds[variable].attrs.get("units", "units")
                self.plot_utils.add_colorbar(im, ax, variable, units)
                
            else:  # contour
                # Initialize contour plot
                initial_data, _, _ = self.prepare_data_for_plotting(
                    self.ds[variable], 0, animate_dim, level_index, zoom_factor, verbose=False
                )
                filtered_initial_data = self.filter_low_values(initial_data)
                levels = np.linspace(data_min, data_max, 20)
                contour = self.plot_utils.create_contour_plot(ax, filtered_initial_data, lats, lons, data_min, data_max, levels=20)
                
                # Add colorbar
                units = self.ds[variable].attrs.get("units", "units")
                self.plot_utils.add_colorbar(contour, ax, variable, units)
                
                # Store the contour collection for later removal
                contour_collections = [contour]
            
        else:  # heatmap plot
            fig, ax = self.plot_utils.create_heatmap_plot()
            
            # Initialize heatmap plot
            initial_data, _, _ = self.prepare_data_for_plotting(
                self.ds[variable], 0, animate_dim, level_index, zoom_factor, verbose=False
            )
            filtered_initial_data = self.filter_low_values(initial_data)
            im = ax.imshow(filtered_initial_data, cmap='Blues', aspect='auto', vmin=data_min, vmax=data_max)
            
            # Add colorbar
            units = self.ds[variable].attrs.get("units", "units")
            self.plot_utils.add_colorbar(im, ax, variable, units)
        
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
                data, _, _ = self.prepare_data_for_plotting(
                    self.ds[variable], frame, animate_dim, level_index, zoom_factor, verbose=False
                )
                filtered_data = self.filter_low_values(data)
                
                # Update title and subtitle
                time_str = self.format_datetime(self.ds[animate_dim].isel({animate_dim: frame}), animate_dim, self.ds)
                title_text.set_text(title)
                subtitle_text.set_text(f"{animate_dim.capitalize()}: {time_str}")
                units_text.set_text(self.get_variable_subtitle(variable, self.ds))
                
                # Update plot based on type
                if plot_type == 'contour':
                    # For contour plots, we need to recreate the contour each time
                    # Remove the previous contour collections
                    for collection in contour_collections:
                        if collection in ax.collections:
                            collection.remove()
                    
                    # Create new contour
                    new_contour = self.plot_utils.create_contour_plot(ax, filtered_data, lats, lons, data_min, data_max, levels=20)
                    
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
        if hasattr(self.ffmpeg_manager, 'available_codecs') and self.ffmpeg_manager.available_codecs:
            if 'libx264' in self.ffmpeg_manager.available_codecs:
                codec = 'libx264'
            elif 'libxvid' in self.ffmpeg_manager.available_codecs:
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
        if codec != 'libxvid' and 'libxvid' in getattr(self.ffmpeg_manager, 'available_codecs', []):
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
        
        return saved_successfully
    
    def create_batch_animations(self, plot_type: str = 'efficient', fps: int = 10, 
                               animate_dim: str = 'time', level_index: Optional[int] = None, 
                               zoom_factor: float = 1.0) -> bool:
        """Create animations for all variables."""
        print(f"\n🎬 Creating {plot_type} animations for all variables...")
        
        var_info = self.get_variable_info()
        successful = 0
        failed = 0
        
        for var_name in var_info.keys():
            print(f"\n🎬 Creating animation for {var_name}...")
            
            try:
                # Add timestamp to prevent overwriting
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{timestamp}_{var_name}_{plot_type}_animation.mp4"
                success = self.create_animation(var_name, output_file, fps, plot_type, 
                                              animate_dim=animate_dim, level_index=level_index, 
                                              zoom_factor=zoom_factor)
                if success:
                    print(f"✅ Created: {output_file}")
                    successful += 1
                else:
                    failed += 1
                
            except Exception as e:
                print(f"❌ Error creating animation for {var_name}: {e}")
                failed += 1
        
        print(f"\n📊 Batch animation summary:")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📁 Check current directory for output files")
        
        return successful > 0
    
    def close(self):
        """Close the dataset."""
        if hasattr(self, 'ds'):
            self.ds.close() 