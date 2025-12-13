#!/usr/bin/env python3
"""
Animate NetCDF - A comprehensive tool for creating animations from NetCDF data files.

This package provides functionality for:
- Single file animations
- Multi-file animations
- Interactive and batch processing
- Configuration management
- File discovery and validation
"""

__version__ = "1.7.3"
__author__ = "Florian Cochard"
__email__ = "florian@weatherwise.fr"

# Import main components for easy access
from .core.app_controller import AppController
from .core.config_manager import ConfigManager, AnimationConfig
from .core.file_manager import NetCDFFileManager
from .core.cli_parser import CLIParser

from .visualizers.unified_visualizer import NetCDFVisualizer

from .utils.data_processing import DataProcessor
from .utils.plot_utils import PlotUtils
from .utils.ffmpeg_utils import ffmpeg_manager
from .utils.logging_utils import LoggingManager

__all__ = [
    'AppController',
    'ConfigManager', 
    'AnimationConfig',
    'NetCDFFileManager',
    'CLIParser',
    'NetCDFVisualizer',
    'DataProcessor',
    'PlotUtils',
    'ffmpeg_manager',
    'LoggingManager'
]
