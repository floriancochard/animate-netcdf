#!/usr/bin/env python3
"""
Utility modules for the Animate NetCDF package.

This package contains utility classes including:
- Data processing utilities
- Plot utilities
- FFmpeg utilities
- Logging utilities
"""

from .data_processing import DataProcessor
from .plot_utils import PlotUtils
from .ffmpeg_utils import ffmpeg_manager
from .logging_utils import LoggingManager

__all__ = [
    'DataProcessor',
    'PlotUtils',
    'ffmpeg_manager',
    'LoggingManager'
] 