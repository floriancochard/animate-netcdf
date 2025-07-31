#!/usr/bin/env python3
"""
Plot Utilities for NetCDF Animations
Common plotting functionality and Cartopy setup
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import logging
import os
from typing import Tuple, Optional, Any, Dict, List
import pandas as pd
from datetime import datetime

# Import cartopy components
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    print("⚠️  Cartopy not available. Geographic plots will not work.")


class PlotUtils:
    """Common plotting utilities for NetCDF animations."""
    
    @staticmethod
    def setup_cartopy_logging():
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
    
    @staticmethod
    def check_cartopy_maps():
        """Check if cartopy maps are already downloaded and log status."""
        if not CARTOPY_AVAILABLE:
            print("⚠️  Cartopy not available for map checking")
            return
        
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
    
    @staticmethod
    def add_cartopy_features(ax):
        """Add cartopy features with download checking and logging."""
        if not CARTOPY_AVAILABLE:
            print("⚠️  Cartopy not available. Cannot add map features.")
            return
        
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
    
    @staticmethod
    def format_datetime(time_value, animate_dim='time', dataset=None):
        """Format datetime for clean display."""
        if hasattr(time_value, 'values'):
            time_value = time_value.values
        
        # Convert to pandas datetime if it's a numpy datetime64
        if isinstance(time_value, np.datetime64):
            dt = pd.Timestamp(time_value)
        else:
            dt = pd.to_datetime(time_value)
        
        # Format based on the time range
        if dataset and len(dataset[animate_dim]) > 24:  # More than a day
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        else:  # Less than a day
            return dt.strftime("%H:%M:%S UTC")
    
    @staticmethod
    def get_variable_title(variable: str) -> str:
        """Get a clean title for the variable."""
        titles = {
            'InstantaneousRainRate': 'Instantaneous Rain Rate',
            'AccumulatedRainRate': 'Accumulated Rain Rate',
            'Windspeed10m': 'Wind Speed (10m)',
            'Temperature2m': 'Temperature (2m)',
            'Salinity': 'Salinity',
            'SeaSurfaceTemperature': 'Sea Surface Temperature',
            'Precipitation': 'Precipitation',
            'WindSpeed': 'Wind Speed',
            'Temperature': 'Temperature'
        }
        return titles.get(variable, variable.replace('_', ' ').title())
    
    @staticmethod
    def get_variable_subtitle(variable: str, dataset=None) -> str:
        """Get subtitle with units."""
        if dataset and variable in dataset.data_vars:
            units = dataset[variable].attrs.get('units', '')
            if units:
                return f"Units: {units}"
        return ""
    
    @staticmethod
    def create_geographic_plot(plot_type: str, figsize: Tuple[int, int] = (15, 10)):
        """Create a geographic plot with Cartopy projection."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        fig, ax = plt.subplots(figsize=figsize, 
                              subplot_kw={'projection': ccrs.PlateCarree()})
        return fig, ax
    
    @staticmethod
    def setup_geographic_plot(ax, lats: np.ndarray, lons: np.ndarray):
        """Set up geographic plot with features and gridlines."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        # Add Cartopy features
        PlotUtils.add_cartopy_features(ax)
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7, 
                         linestyle='--', color='gray')
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Set extent
        ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], 
                     crs=ccrs.PlateCarree())
    
    @staticmethod
    def create_efficient_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                             vmin: Optional[float] = None, vmax: Optional[float] = None,
                             cmap: str = 'Blues', alpha: float = 0.8):
        """Create an efficient imshow plot on geographic axes."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        im = ax.imshow(data, cmap=cmap, alpha=alpha,
                      extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), origin='lower',
                      vmin=vmin, vmax=vmax)
        return im
    
    @staticmethod
    def create_contour_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                           vmin: Optional[float] = None, vmax: Optional[float] = None,
                           cmap: str = 'Blues', levels: int = 20):
        """Create a contour plot on geographic axes."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        if vmin is None:
            vmin = np.nanmin(data)
        if vmax is None:
            vmax = np.nanmax(data)
        
        levels_array = np.linspace(vmin, vmax, levels)
        contour = ax.contourf(lons, lats, data, levels=levels_array, cmap=cmap,
                             transform=ccrs.PlateCarree())
        return contour
    
    @staticmethod
    def create_heatmap_plot(figsize: Tuple[int, int] = (12, 8)):
        """Create a simple heatmap plot."""
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax
    
    @staticmethod
    def add_colorbar(im, ax, variable: str, units: str = ""):
        """Add colorbar with proper labeling."""
        if hasattr(im, 'set_array'):  # imshow
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        else:  # contour
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        
        label = f'{PlotUtils.get_variable_title(variable)}'
        if units:
            label += f' ({units})'
        cbar.set_label(label)
        return cbar
    
    @staticmethod
    def add_title_and_subtitle(ax, variable: str, time_str: str, units: str = ""):
        """Add title and subtitle to the plot."""
        title = PlotUtils.get_variable_title(variable)
        subtitle = f"Time: {time_str}"
        
        ax.set_title(f'{title}\n{subtitle}', fontsize=14, pad=30)
        
        if units:
            ax.text(0.5, 0.02, units, transform=ax.transAxes, ha='center', 
                   fontsize=10, style='italic')
    
    @staticmethod
    def save_animation_with_fallback(anim, output_file: str, fps: int, 
                                   ffmpeg_manager) -> bool:
        """Save animation with codec fallback logic."""
        if not ffmpeg_manager.is_available():
            print("❌ ffmpeg not available for video creation")
            return False
        
        # Get codecs to try
        codecs_to_try = ffmpeg_manager.get_codecs_to_try()
        
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
                    print(f"❌ Failed to save animation with any available codec. Last error: {e}")
                    return False
                continue
        
        return saved_successfully
    
    @staticmethod
    def generate_output_filename(variable: str, plot_type: str, 
                               output_format: str = 'mp4') -> str:
        """Generate output filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{variable}_{plot_type}_animation.{output_format}"
    
    @staticmethod
    def get_troubleshooting_tips() -> List[str]:
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