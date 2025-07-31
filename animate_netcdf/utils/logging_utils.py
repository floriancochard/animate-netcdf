#!/usr/bin/env python3
"""
Logging Utilities for NetCDF Animations
Centralized logging setup and management
"""

import logging
from typing import Optional


class LoggingManager:
    """Manages logging setup for different components."""
    
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO, 
                    format_string: str = None, emoji: str = "📝") -> logging.Logger:
        """Set up a logger with consistent formatting."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Avoid adding duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            
            if format_string is None:
                format_string = f'{emoji} {name}: %(message)s'
            
            formatter = logging.Formatter(format_string)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
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
    def setup_multi_file_logging():
        """Set up logging for multi-file animator."""
        return LoggingManager.setup_logger('MultiFileAnimator', emoji='🎬')
    
    @staticmethod
    def setup_single_file_logging():
        """Set up logging for single file animator."""
        return LoggingManager.setup_logger('SingleFileAnimator', emoji='🎬')
    
    @staticmethod
    def setup_config_logging():
        """Set up logging for configuration manager."""
        return LoggingManager.setup_logger('ConfigManager', emoji='⚙️')
    
    @staticmethod
    def setup_file_manager_logging():
        """Set up logging for file manager."""
        return LoggingManager.setup_logger('FileManager', emoji='📁')


# Global logging setup function
def setup_all_logging():
    """Set up logging for all components."""
    LoggingManager.setup_cartopy_logging()
    LoggingManager.setup_multi_file_logging()
    LoggingManager.setup_single_file_logging()
    LoggingManager.setup_config_logging()
    LoggingManager.setup_file_manager_logging() 