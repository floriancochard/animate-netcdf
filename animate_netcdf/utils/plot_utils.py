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
    import cartopy.io.shapereader as shapereader
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    shapereader = None
    print("⚠️  Cartopy not available. Geographic plots will not work.")


def _apply_hatch_to_last_collection(ax, hatch: str, edgecolor: str = 'gray', linewidth: float = 0.4):
    """Apply hatch pattern to the last added collection so it is visible under data."""
    if not ax.collections:
        return
    coll = ax.collections[-1]
    coll.set_hatch(hatch)
    coll.set_edgecolor(edgecolor)
    coll.set_linewidth(linewidth)


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
    def add_land_sea_fill(ax, land_alpha: float = 0.4, ocean_alpha: float = 0.35,
                         land_color: str = '#c4c4c4', ocean_color: str = '#9dd0e2',
                         scale: str = '50m',
                         land_hatch: Optional[str] = None, ocean_hatch: Optional[str] = None):
        """Add land and ocean fill so coasts are distinguishable when zoomed.
        scale: Natural Earth resolution — '110m' (coarse), '50m' (matches coastlines), '10m' (fine).
        Optional land_hatch/ocean_hatch add patterns (e.g. land_hatch='///').
        """
        if not CARTOPY_AVAILABLE:
            return
        try:
            # zorder=0 so data layer (drawn with higher zorder) stays on top
            ax.add_feature(cfeature.OCEAN.with_scale(scale), facecolor=ocean_color,
                          alpha=ocean_alpha, zorder=0)
            if ocean_hatch:
                _apply_hatch_to_last_collection(ax, ocean_hatch)
            ax.add_feature(cfeature.LAND.with_scale(scale), facecolor=land_color,
                          alpha=land_alpha, zorder=0)
            if land_hatch:
                _apply_hatch_to_last_collection(ax, land_hatch)
        except Exception as e:
            logging.getLogger(__name__).warning("Could not add land/sea fill: %s", e)

    @staticmethod
    def add_place_names(ax, extent: Optional[Tuple[float, float, float, float]] = None,
                       max_labels: int = 15, fontsize: int = 24, min_population: Optional[int] = None,
                       show_points: bool = True, point_color: str = 'black', point_size: float = 24,
                       point_edgecolor: str = 'white', point_edgewidth: float = 0.5):
        """Add minimal place names (cities) from Natural Earth for orientation when zoomed.
        extent: (lon_min, lon_max, lat_min, lat_max) in PlateCarree; if None, uses ax extent.
        min_population: if None, scales with view size (zoomed views use lower threshold so labels show).
        Uses finer resolution (10m/50m) when zoomed so enough cities fall in view.
        show_points: if True, draw a small marker at each city location (default True).
        point_color, point_size, point_edgecolor, point_edgewidth: marker styling.
        """
        if not CARTOPY_AVAILABLE or shapereader is None:
            return
        try:
            if extent is None:
                extent = ax.get_extent(crs=ccrs.PlateCarree())
            lon_min, lon_max, lat_min, lat_max = extent
            lon_span = abs(lon_max - lon_min)
            lat_span = abs(lat_max - lat_min)
            span_deg = max(lon_span, lat_span)
            # Use lower population threshold for zoomed views so place names appear
            if min_population is None:
                if span_deg < 1.0:
                    min_population = 0
                elif span_deg < 3.0:
                    min_population = 10000
                elif span_deg < 10.0:
                    min_population = 100000
                else:
                    min_population = 500000
            # Use finer resolution when zoomed: 10m has many more cities so labels show at zoom
            if span_deg < 5.0:
                resolution = '10m'
            elif span_deg < 20.0:
                resolution = '50m'
            else:
                resolution = '110m'
            reader = shapereader.natural_earth(resolution=resolution, category='cultural',
                                               name='populated_places')
            places = shapereader.Reader(reader).records()
            labels_added = 0
            point_lons: List[float] = []
            point_lats: List[float] = []
            for place in places:
                if labels_added >= max_labels:
                    break
                geom = place.geometry
                if geom.is_empty:
                    continue
                lon, lat = geom.x, geom.y
                if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
                    continue
                # Natural Earth uses POP_MAX/POP_MIN (uppercase in shapefile); try lowercase too
                pop = (place.attributes.get('POP_MAX') or place.attributes.get('POP_MIN') or
                      place.attributes.get('pop_max') or place.attributes.get('pop_min'))
                try:
                    pop = int(float(pop)) if pop is not None else 0
                except (TypeError, ValueError):
                    pop = 0
                if pop < min_population:
                    continue
                name = place.attributes.get('NAME', '') or place.attributes.get('name', '')
                if not name:
                    continue
                if show_points:
                    point_lons.append(lon)
                    point_lats.append(lat)
                ax.text(lon, lat, f' {name} ', fontsize=fontsize, color='black',
                       transform=ccrs.PlateCarree(), ha='left', va='center',
                       clip_on=True, alpha=0.9, zorder=15)
                labels_added += 1
            if show_points and point_lons:
                ax.scatter(point_lons, point_lats, s=point_size, c=point_color,
                          edgecolors=point_edgecolor, linewidths=point_edgewidth,
                          transform=ccrs.PlateCarree(), zorder=14, clip_on=True, alpha=0.9)
        except Exception as e:
            logging.getLogger(__name__).warning("Could not add place names: %s", e)

    @staticmethod
    def add_cartopy_features(ax, land_sea_fill: bool = True,
                            land_color: Optional[str] = None, ocean_color: Optional[str] = None,
                            land_alpha: Optional[float] = None, ocean_alpha: Optional[float] = None,
                            land_hatch: Optional[str] = None, ocean_hatch: Optional[str] = None,
                            land_sea_scale: Optional[str] = None):
        """Add cartopy features with download checking and logging.
        When land_sea_fill is True, adds ocean and land fill so coasts
        are distinguishable when zoomed. land_sea_scale: '110m'|'50m'|'10m'
        (default 50m to match coastlines). Optional land/ocean color, alpha, hatch.
        """
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
            
            # Land/sea fill first (under coastlines) so zoomed coasts are readable
            if land_sea_fill:
                scale = land_sea_scale if land_sea_scale in ('110m', '50m', '10m') else '50m'
                kwargs: Dict[str, Any] = {'scale': scale}
                if land_color is not None:
                    kwargs['land_color'] = land_color
                if ocean_color is not None:
                    kwargs['ocean_color'] = ocean_color
                if land_alpha is not None:
                    kwargs['land_alpha'] = land_alpha
                if ocean_alpha is not None:
                    kwargs['ocean_alpha'] = ocean_alpha
                if land_hatch is not None:
                    kwargs['land_hatch'] = land_hatch
                if ocean_hatch is not None:
                    kwargs['ocean_hatch'] = ocean_hatch
                PlotUtils.add_land_sea_fill(ax, **kwargs)
            
            # Coastlines and borders on top of data (zorder > data layer)
            ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=1.5, edgecolor='black', alpha=0.9, zorder=10)
            ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1.0, edgecolor='darkred', alpha=0.8, zorder=10)
            
            if not maps_exist:
                print("🗺️  Cartopy maps downloaded successfully")
            else:
                print("🗺️  Map features added successfully")
                
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
    def setup_geographic_plot(ax, lats: np.ndarray, lons: np.ndarray,
                             show_land_sea: bool = True, show_place_names: bool = False,
                             place_names_min_population: Optional[int] = None,
                             map_land_color: Optional[str] = None, map_ocean_color: Optional[str] = None,
                             map_land_alpha: Optional[float] = None, map_ocean_alpha: Optional[float] = None,
                             map_land_hatch: Optional[str] = None, map_ocean_hatch: Optional[str] = None,
                             map_land_sea_scale: Optional[str] = None):
        """Set up geographic plot with features and gridlines.
        When show_land_sea is True, adds land/ocean fill so coasts are clear when zoomed.
        map_land_sea_scale: '110m'|'50m'|'10m' for land/sea resolution (default 50m).
        map_* options control colors, opacity, and optional hatch patterns.
        """
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        # Set extent first so land/sea and coastlines are clipped to the view (fixes zoomed display)
        ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()],
                     crs=ccrs.PlateCarree())
        
        # Add Cartopy features (optionally with land/sea fill and map styling)
        PlotUtils.add_cartopy_features(
            ax, land_sea_fill=show_land_sea,
            land_color=map_land_color, ocean_color=map_ocean_color,
            land_alpha=map_land_alpha, ocean_alpha=map_ocean_alpha,
            land_hatch=map_land_hatch, ocean_hatch=map_ocean_hatch,
            land_sea_scale=map_land_sea_scale,
        )
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.7,
                         linestyle='--', color='gray')
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Place names are added after the data layer in the visualizer so they render on top
        # and are included when saving animation (avoids blit omitting static text).
    
    @staticmethod
    def create_efficient_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                             vmin: Optional[float] = None, vmax: Optional[float] = None,
                             cmap: str = 'Blues', alpha: float = 0.7):
        """Create an efficient imshow plot on geographic axes.
        Default alpha=0.7 so land/sea fill shows through when show_land_sea is True.
        """
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        im = ax.imshow(data, cmap=cmap, alpha=alpha,
                      extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), origin='lower',
                      vmin=vmin, vmax=vmax, zorder=5)
        return im
    
    @staticmethod
    def create_contour_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                           vmin: Optional[float] = None, vmax: Optional[float] = None,
                           cmap: str = 'Blues', levels: int = 20, alpha: float = 0.6):
        """Create a contour plot on geographic axes."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        if vmin is None:
            vmin = np.nanmin(data)
        if vmax is None:
            vmax = np.nanmax(data)
        
        levels_array = np.linspace(vmin, vmax, levels)
        contour = ax.contourf(lons, lats, data, levels=levels_array, cmap=cmap,
                             transform=ccrs.PlateCarree(), zorder=5, alpha=alpha)
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
                                   ffmpeg_manager, dpi: Optional[int] = None,
                                   bitrate: Optional[int] = None) -> bool:
        """Save animation with codec fallback logic.
        
        Args:
            dpi: DPI for frame size (default 72; use 100 for designer/high-res).
            bitrate: Video bitrate in kbps (default 1000; use 5000 for designer/high-res).
        """
        if not ffmpeg_manager.is_available():
            print("❌ ffmpeg not available for video creation")
            return False
        
        if dpi is None:
            dpi = 72
        if bitrate is None:
            bitrate = 1000
        
        # Get codecs to try
        codecs_to_try = ffmpeg_manager.get_codecs_to_try()
        
        saved_successfully = False
        for try_codec in codecs_to_try:
            try:
                print(f"📹 Trying codec: {try_codec} (dpi={dpi}, bitrate={bitrate} kbps)")
                anim.save(
                    output_file,
                    writer='ffmpeg',
                    fps=fps,
                    dpi=dpi,
                    bitrate=bitrate,
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
    def save_animation_gif(anim, output_file: str, fps: int,
                          dpi: Optional[int] = None) -> bool:
        """Save animation as GIF using matplotlib's PillowWriter.

        Args:
            anim: Matplotlib FuncAnimation instance.
            output_file: Path for the output GIF file.
            fps: Frames per second.
            dpi: DPI for frame size (default 72; use 100 for designer/high-res).

        Returns:
            bool: True if saved successfully, False if Pillow is missing or save failed.
        """
        if dpi is None:
            dpi = 72
        try:
            writer = animation.PillowWriter(fps=fps)
            print(f"🖼️  Saving GIF (dpi={dpi})...")
            anim.save(output_file, writer=writer, dpi=dpi)
            return True
        except ImportError as e:
            print("❌ Pillow required for GIF export. Install with: pip install Pillow")
            return False
        except Exception as e:
            print(f"❌ Error saving GIF: {e}")
            return False
    
    @staticmethod
    def generate_output_filename(variable: str, plot_type: str, 
                               output_format: str = 'mp4') -> str:
        """Generate output filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{variable}_{plot_type}_animation.{output_format}"
    
    @staticmethod
    def create_designer_geographic_plot(plot_type: str = 'efficient', figsize: Optional[Tuple[int, int]] = None,
                                        square_crop: bool = False):
        """Create a geographic plot for designer mode with transparent background.
        
        When square_crop is True, uses a square figure with no margins so the final
        output is a square centered on the map content.
        """
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        if figsize is None:
            figsize = (10, 10) if square_crop else (15, 10)
        
        fig, ax = plt.subplots(figsize=figsize,
                              subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Set completely transparent background
        fig.patch.set_alpha(0.0)
        fig.patch.set_facecolor('none')
        ax.patch.set_alpha(0.0)
        ax.patch.set_facecolor('none')
        
        if square_crop:
            # Remove all padding/margins so the axis fills the figure
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        
        return fig, ax
    
    @staticmethod
    def setup_designer_geographic_plot(ax, lats: np.ndarray, lons: np.ndarray,
                                       square_crop: bool = False,
                                       show_map_contours: bool = False,
                                       show_land_sea: bool = True,
                                       show_place_names: bool = False,
                                       place_names_min_population: Optional[int] = None,
                                       map_land_color: Optional[str] = None,
                                       map_ocean_color: Optional[str] = None,
                                       map_land_alpha: Optional[float] = None,
                                       map_ocean_alpha: Optional[float] = None,
                                       map_land_hatch: Optional[str] = None,
                                       map_ocean_hatch: Optional[str] = None,
                                       map_land_sea_scale: Optional[str] = None):
        """Set up geographic plot for designer mode: only data and topography.
        
        When square_crop is True, sets the map extent to a square region centered on
        the data (crops the longer dimension so the output is a filled square).
        When show_map_contours is True, adds coastlines and borders (map contours).
        When show_land_sea is True, adds land/ocean fill so coasts are distinguishable when zoomed.
        map_land_sea_scale: '110m'|'50m'|'10m' for land/sea resolution (default 50m).
        map_* options control colors, opacity, and optional hatch patterns.
        """
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        # Set extent first so land/sea and coastlines are clipped to the view (fixes zoomed display)
        lon_min, lon_max = float(lons.min()), float(lons.max())
        lat_min, lat_max = float(lats.min()), float(lats.max())
        if square_crop:
            lon_span = lon_max - lon_min
            lat_span = lat_max - lat_min
            side = min(lon_span, lat_span)  # crop to square filled with map content
            center_lon = (lon_min + lon_max) / 2
            center_lat = (lat_min + lat_max) / 2
            extent_used = (center_lon - side / 2, center_lon + side / 2,
                          center_lat - side / 2, center_lat + side / 2)
            ax.set_extent(extent_used, crs=ccrs.PlateCarree())
        else:
            extent_used = (lon_min, lon_max, lat_min, lat_max)
            ax.set_extent(extent_used, crs=ccrs.PlateCarree())
        
        # Land/sea fill so coasts are distinguishable when zoomed
        if show_land_sea:
            scale = map_land_sea_scale if map_land_sea_scale in ('110m', '50m', '10m') else '50m'
            kwargs: Dict[str, Any] = {'scale': scale}
            if map_land_color is not None:
                kwargs['land_color'] = map_land_color
            if map_ocean_color is not None:
                kwargs['ocean_color'] = map_ocean_color
            if map_land_alpha is not None:
                kwargs['land_alpha'] = map_land_alpha
            if map_ocean_alpha is not None:
                kwargs['ocean_alpha'] = map_ocean_alpha
            if map_land_hatch is not None:
                kwargs['land_hatch'] = map_land_hatch
            if map_ocean_hatch is not None:
                kwargs['ocean_hatch'] = map_ocean_hatch
            PlotUtils.add_land_sea_fill(ax, **kwargs)
        # Optional extra land shading
        try:
            ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m'),
                         alpha=0.15, facecolor='lightgray', zorder=0)
        except Exception:
            pass
        
        if show_map_contours:
            # Add coastlines and borders on top of data (zorder > data layer)
            try:
                ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=1.5,
                               edgecolor='black', alpha=0.9, zorder=10)
                ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1.0,
                               edgecolor='darkred', alpha=0.8, zorder=10)
            except Exception:
                pass
        
        # Place names are added after the data layer in the visualizer so they render on top
        # and are included when saving animation (avoids blit omitting static text).
        
        # Explicitly remove all gridlines and labels
        gl = ax.gridlines(draw_labels=False, linewidth=0, alpha=0)
        gl.xlines = False
        gl.ylines = False
        
        # Remove all axis labels, ticks, and spines
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Remove spines (borders)
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    @staticmethod
    def create_designer_efficient_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                                     vmin: Optional[float] = None, vmax: Optional[float] = None,
                                     cmap: str = 'Blues', alpha: float = 0.65):
        """Create an efficient imshow plot for designer mode.
        Default alpha=0.65 so land/sea fill shows through when show_land_sea is True.
        """
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        im = ax.imshow(data, cmap=cmap, alpha=alpha,
                      extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), origin='lower',
                      vmin=vmin, vmax=vmax, zorder=5)
        return im
    
    @staticmethod
    def create_designer_contour_plot(ax, data: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                                   vmin: Optional[float] = None, vmax: Optional[float] = None,
                                   cmap: str = 'Blues', levels: int = 20, alpha: float = 0.65):
        """Create a contour plot for designer mode."""
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy not available for geographic plots")
        
        if vmin is None:
            vmin = np.nanmin(data)
        if vmax is None:
            vmax = np.nanmax(data)
        
        levels_array = np.linspace(vmin, vmax, levels)
        contour = ax.contourf(lons, lats, data, levels=levels_array, cmap=cmap,
                             transform=ccrs.PlateCarree(), zorder=5, alpha=alpha)
        return contour
    
    @staticmethod
    def add_designer_colorbar(im, ax, variable: str, units: str = ""):
        """Add colorbar for designer mode without labels."""
        if hasattr(im, 'set_array'):  # imshow
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        else:  # contour
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        
        # Remove colorbar label for designer mode
        cbar.set_label('')
        return cbar
    
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