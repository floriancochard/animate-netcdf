#!/usr/bin/env python3
"""
Base Animator for NetCDF Animations
Abstract base class defining common interface for all animators
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import xarray as xr
from animate_netcdf.utils.ffmpeg_utils import ffmpeg_manager
from animate_netcdf.utils.data_processing import DataProcessor
from animate_netcdf.utils.plot_utils import PlotUtils
from animate_netcdf.utils.logging_utils import LoggingManager


class BaseAnimator(ABC):
    """Abstract base class for all animators."""
    
    def __init__(self):
        """Initialize base animator with common utilities."""
        self.ffmpeg_manager = ffmpeg_manager
        self.data_processor = DataProcessor()
        self.plot_utils = PlotUtils()
        self.logger = LoggingManager.setup_logger(self.__class__.__name__)
        
        # Set up cartopy logging
        self.plot_utils.setup_cartopy_logging()
        self.plot_utils.check_cartopy_maps()
    
    @abstractmethod
    def create_animation(self, **kwargs) -> bool:
        """Create animation - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def create_single_plot(self, **kwargs) -> bool:
        """Create single plot - must be implemented by subclasses."""
        pass
    
    def filter_low_values(self, data: np.ndarray, percentile: int = 5) -> np.ndarray:
        """Filter out low percentile values to reduce noise."""
        return self.data_processor.filter_low_values(data, percentile)
    
    def prepare_data_for_plotting(self, data_array: xr.DataArray, 
                                 time_step: int = 0, 
                                 animate_dim: str = 'time',
                                 level_index: Optional[int] = None,
                                 zoom_factor: float = 1.0,
                                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare data for plotting by handling extra dimensions and zooming."""
        return self.data_processor.prepare_data_for_plotting(
            data_array, time_step, animate_dim, level_index, zoom_factor, verbose
        )
    
    def get_animation_dimension(self, dataset: xr.Dataset) -> Optional[str]:
        """Find the first dimension that's not spatial (suitable for animation)."""
        return self.data_processor.get_animation_dimension(dataset)
    
    def format_datetime(self, time_value, animate_dim='time', dataset=None):
        """Format datetime for clean display."""
        return self.plot_utils.format_datetime(time_value, animate_dim, dataset)
    
    def get_variable_title(self, variable: str) -> str:
        """Get a clean title for the variable."""
        return self.plot_utils.get_variable_title(variable)
    
    def get_variable_subtitle(self, variable: str, dataset=None) -> str:
        """Get subtitle with units."""
        return self.plot_utils.get_variable_subtitle(variable, dataset)
    
    def save_animation_with_fallback(self, anim, output_file: str, fps: int) -> bool:
        """Save animation with codec fallback logic."""
        return self.plot_utils.save_animation_with_fallback(anim, output_file, fps, self.ffmpeg_manager)
    
    def generate_output_filename(self, variable: str, plot_type: str, 
                               output_format: str = 'mp4') -> str:
        """Generate output filename with timestamp."""
        return self.plot_utils.generate_output_filename(variable, plot_type, output_format)
    
    def get_troubleshooting_tips(self) -> List[str]:
        """Get troubleshooting tips for common issues."""
        return self.plot_utils.get_troubleshooting_tips()
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        return self.ffmpeg_manager.is_available()
    
    def get_codec_info(self) -> Dict[str, Any]:
        """Get information about available codecs and ffmpeg status."""
        return self.ffmpeg_manager.get_codec_info()
    
    def reset_zoom_flag(self):
        """Reset the zoom application flag."""
        self.data_processor.reset_zoom_flag() 