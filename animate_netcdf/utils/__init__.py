#!/usr/bin/env python3
"""
Utility modules for the Animate NetCDF package.

This package contains utility classes including:
- Data processing utilities
- Plot utilities
- FFmpeg utilities
- Logging utilities
- NetCDF exploration utilities
"""

from .data_processing import DataProcessor
from .plot_utils import PlotUtils
from .ffmpeg_utils import ffmpeg_manager
from .logging_utils import LoggingManager
from .netcdf_explorer import NetCDFExplorer, explore_netcdf_file, get_netcdf_groups
from .group_extractor import GroupExtractor, extract_swd_from_betsizarai, extract_swd_as_xarray

__all__ = [
    'DataProcessor',
    'PlotUtils',
    'ffmpeg_manager',
    'LoggingManager',
    'NetCDFExplorer',
    'explore_netcdf_file',
    'get_netcdf_groups',
    'GroupExtractor',
    'extract_swd_from_betsizarai',
    'extract_swd_as_xarray'
] 