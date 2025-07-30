#!/usr/bin/env python3
"""
Animation Creator for NetCDF Data
"""

import xarray as xr
import numpy as np
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

class UnifiedAnimator:
    """Unified animation creator with all plotting methods."""
    
    def __init__(self, nc_file):
        """Initialize with NetCDF file path."""
        if not os.path.exists(nc_file):
            raise FileNotFoundError(f"File not found: {nc_file}")
        
        print(f"📁 Loading {nc_file}...")
        self.ds = xr.open_dataset(nc_file)
        
        # Print dataset info
        print(f"Dimensions: {dict(self.ds.dims)}")
        print(f"Variables: {list(self.ds.data_vars.keys())}")
        print(f"Time steps: {len(self.ds.time)}")
        
        # Check for ffmpeg
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
                self.ffmpeg_available = False
            else:
                self.ffmpeg_available = True
        except FileNotFoundError:
            print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
            self.ffmpeg_available = False
    
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
    
    def format_datetime(self, time_value):
        """Format datetime for clean display."""
        if hasattr(time_value, 'values'):
            time_value = time_value.values
        
        # Convert to pandas datetime if it's a numpy datetime64
        if isinstance(time_value, np.datetime64):
            dt = pd.Timestamp(time_value)
        else:
            dt = pd.to_datetime(time_value)
        
        # Format based on the time range
        if len(self.ds.time) > 24:  # More than a day
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
    
    def filter_low_values(self, data, percentile=5):
        """Filter out low percentile values to reduce noise."""
        if data.size == 0:
            return data
        
        # Calculate percentile threshold
        threshold = np.percentile(data[data > 0], percentile) if np.any(data > 0) else 0
        
        # Create masked array where low values are masked
        filtered_data = np.where(data >= threshold, data, np.nan)
        
        return filtered_data
    
    def explore_dataset(self):
        """Explore and display dataset information."""
        print("\n" + "=" * 60)
        print("Dataset Explorer")
        print("=" * 60)
        
        # Show dataset info
        print(f"\nDataset Information:")
        print(f"  Dimensions: {dict(self.ds.dims)}")
        print(f"  Variables: {list(self.ds.data_vars.keys())}")
        print(f"  Time steps: {len(self.ds.time)}")
        
        # Show time range
        if len(self.ds.time) > 0:
            start_time = self.format_datetime(self.ds.time[0])
            end_time = self.format_datetime(self.ds.time[-1])
            print(f"  Time range: {start_time} to {end_time}")
        
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
    
    def create_single_plot(self, variable, plot_type='efficient', time_step=0):
        """Create a single plot for preview."""
        print(f"\n📊 Creating {plot_type} plot for {variable} at time step {time_step}...")
        
        if plot_type == 'efficient':
            fig = self._create_efficient_plot(variable, time_step)
        elif plot_type == 'contour':
            fig = self._create_contour_plot(variable, time_step)
        elif plot_type == 'heatmap':
            fig = self._create_heatmap_plot(variable, time_step)
        else:
            print(f"❌ Unknown plot type: {plot_type}")
            return None
        
        plt.show()
        return fig
    
    def _create_efficient_plot(self, variable, time_step=0):
        """Create an efficient single plot with Cartopy."""
        fig, ax = plt.subplots(figsize=(15, 10), 
                              subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Get data and coordinates
        data = self.ds[variable].isel(time=time_step).values
        lats = self.ds.latitude.values
        lons = self.ds.longitude.values
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Add Cartopy features
        ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
        ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='lightgray')
        
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
        time_str = self.format_datetime(self.ds.time.isel(time=time_step))
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"Time: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=30)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def _create_contour_plot(self, variable, time_step=0):
        """Create a contour single plot with Cartopy."""
        fig, ax = plt.subplots(figsize=(15, 10), 
                              subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Get data and coordinates
        data = self.ds[variable].isel(time=time_step).values
        lats = self.ds.latitude.values
        lons = self.ds.longitude.values
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Add Cartopy features
        ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
        ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='lightgray')
        
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
        time_str = self.format_datetime(self.ds.time.isel(time=time_step))
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"Time: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=30)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def _create_heatmap_plot(self, variable, time_step=0):
        """Create a simple heatmap plot."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get data
        data = self.ds[variable].isel(time=time_step).values
        
        # Filter low values
        filtered_data = self.filter_low_values(data)
        
        # Create heatmap
        im = ax.imshow(filtered_data, cmap='Blues', aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(f'{self.get_variable_title(variable)} ({self.ds[variable].attrs.get("units", "units")})')
        
        # Add title and subtitle
        time_str = self.format_datetime(self.ds.time.isel(time=time_step))
        title = f"{self.get_variable_title(variable)}"
        subtitle = f"Time: {time_str}"
        units = self.get_variable_subtitle(variable)
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=20)
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
        
        plt.tight_layout()
        return fig
    
    def create_direct_animation(self, variable, output_file=None, fps=10, 
                              plot_type='efficient', title=None):
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
        all_data = self.ds[variable].values
        filtered_all_data = self.filter_low_values(all_data)
        data_min = np.nanmin(filtered_all_data)
        data_max = np.nanmax(filtered_all_data)
        
        # Get coordinates
        lats = self.ds.latitude.values
        lons = self.ds.longitude.values
        
        # Create figure and axis based on plot type
        if plot_type in ['efficient', 'contour']:
            # Always use Cartopy for geographic plots
            fig, ax = plt.subplots(figsize=(15, 10), 
                                  subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Add Cartopy features
            ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
            ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
            ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='lightgray')
            
            # Add gridlines
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, linestyle='--', color='gray')
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            
            # Set extent
            ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], 
                         crs=ccrs.PlateCarree())
            
            if plot_type == 'efficient':
                # Initialize efficient plot
                initial_data = self.ds[variable].isel(time=0).values
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
                initial_data = self.ds[variable].isel(time=0).values
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
            initial_data = self.ds[variable].isel(time=0).values
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
        max_frames = len(self.ds.time)
        
        def animate(frame):
            """Animation function with proper memory management."""
            nonlocal frame_count
            frame_count += 1
            
            try:
                # Check memory usage every 10 frames
                if frame_count % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"📊 Frame {frame_count}/{max_frames}, Memory: {current_memory:.1f} MB")
                
                # Get data for current frame
                data = self.ds[variable].isel(time=frame).values
                filtered_data = self.filter_low_values(data)
                
                # Update title and subtitle
                time_str = self.format_datetime(self.ds.time.isel(time=frame))
                title_text.set_text(title)
                subtitle_text.set_text(f"Time: {time_str}")
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
        anim.save(
            output_file,
            writer='ffmpeg',
            fps=fps,
            dpi=72,  # Lower DPI for better performance
            bitrate=1000  # Reasonable bitrate
        )
        
        plt.close(fig)
        print(f"✅ Animation saved: {output_file}")
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"💾 Final memory usage: {final_memory:.1f} MB")
        
        # Clean up
        del anim
        import gc
        gc.collect()
    
    def create_batch_animations(self, plot_type='efficient', fps=10):
        """Create animations for all variables."""
        print(f"\n🎬 Creating {plot_type} animations for all variables...")
        
        var_info = self.get_variable_info()
        successful = 0
        failed = 0
        
        for var_name in var_info.keys():
            print(f"\n🎬 Creating animation for {var_name}...")
            
            try:
                output_file = f"{var_name}_{plot_type}_animation.mp4"
                self.create_direct_animation(var_name, output_file, fps, plot_type)
                print(f"✅ Created: {output_file}")
                successful += 1
                
            except Exception as e:
                print(f"❌ Error creating animation for {var_name}: {e}")
                failed += 1
        
        print(f"\n📊 Batch animation summary:")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📁 Check current directory for output files")
    
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
        
        # Update percentile filter if specified
        if args.percentile != 5:
            animator.filter_low_values = lambda data, percentile=args.percentile: animator.filter_low_values(data, percentile)
        
        # If all required arguments are provided, run in non-interactive mode
        if args.no_interactive or (args.variable and (args.batch or args.plot or not args.no_interactive)):
            if args.batch:
                # Batch animation mode
                print(f"\n🎬 Creating batch animations...")
                print(f"Type: {args.type}")
                print(f"FPS: {args.fps}")
                animator.create_batch_animations(args.type, args.fps)
                
            elif args.plot:
                # Single plot mode
                print(f"\n📊 Creating single plot...")
                print(f"Variable: {args.variable}")
                print(f"Type: {args.type}")
                print(f"Time step: {args.time_step}")
                animator.create_single_plot(args.variable, args.type, args.time_step)
                
            else:
                # Single animation mode
                output_file = args.output or f"{args.variable}_{args.type}_animation.mp4"
                print(f"\n🎬 Creating single animation...")
                print(f"Variable: {args.variable}")
                print(f"Type: {args.type}")
                print(f"Output: {output_file}")
                print(f"FPS: {args.fps}")
                print(f"Total frames: {len(animator.ds.time)}")
                animator.create_direct_animation(args.variable, output_file, args.fps, args.type)
            
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
            
            # Create plot
            animator.create_single_plot(variable, plot_type)
            
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
            
            # Create animation
            print(f"\n🎬 Creating {anim_type} animation...")
            print(f"Variable: {variable}")
            print(f"Output: {output_file}")
            print(f"FPS: {fps}")
            print(f"Total frames: {len(animator.ds.time)}")
            
            animator.create_direct_animation(variable, output_file, fps, anim_type)
            
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
            
            # Create batch animations
            animator.create_batch_animations(anim_type, fps)
            
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

if __name__ == "__main__":
    main() 
