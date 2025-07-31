#!/usr/bin/env python3
"""
Core modules for the Animate NetCDF package.

This package contains the main application logic including:
- Application controller
- Configuration management
- File management
- Command line interface
"""

from .app_controller import AppController
from .config_manager import ConfigManager, AnimationConfig
from .file_manager import NetCDFFileManager
from .cli_parser import CLIParser

__all__ = [
    'AppController',
    'ConfigManager',
    'AnimationConfig', 
    'NetCDFFileManager',
    'CLIParser'
]
