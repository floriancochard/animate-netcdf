#!/usr/bin/env python3
"""
Configuration Manager for Multi-File NetCDF Animations
"""

import json
import os
import glob
from typing import Dict, Any, Optional, List
import re
from datetime import datetime


class AnimationConfig:
    """Configuration class for animation parameters."""
    
    def __init__(self):
        # Core animation parameters
        self.variable = None
        self.plot_type = 'efficient'
        self.fps = 10
        self.output_pattern = None
        self.animate_dim = 'time'
        self.level_index = None
        self.percentile = 5
        self.batch_mode = False
        self.interactive = True
        
        # Multi-file specific parameters
        self.file_pattern = None
        self.sort_by_timestep = True
        self.global_colorbar = True
        self.pre_scan_files = True
        
        # Output settings
        self.output_directory = '.'
        self.output_format = 'mp4'
        self.overwrite_existing = False
        
        # Performance settings
        self.memory_limit_mb = 2048
        self.max_files_preview = 10
        
        # Zoom settings
        self.zoom_factor = 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'variable': self.variable,
            'plot_type': self.plot_type,
            'fps': self.fps,
            'output_pattern': self.output_pattern,
            'animate_dim': self.animate_dim,
            'level_index': self.level_index,
            'percentile': self.percentile,
            'batch_mode': self.batch_mode,
            'interactive': self.interactive,
            'file_pattern': self.file_pattern,
            'sort_by_timestep': self.sort_by_timestep,
            'global_colorbar': self.global_colorbar,
            'pre_scan_files': self.pre_scan_files,
            'output_directory': self.output_directory,
            'output_format': self.output_format,
            'overwrite_existing': self.overwrite_existing,
            'memory_limit_mb': self.memory_limit_mb,
            'max_files_preview': self.max_files_preview,
            'zoom_factor': self.zoom_factor
        }
    
    def from_dict(self, config_dict: Dict[str, Any]):
        """Load configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.fps <= 0:
            errors.append("FPS must be positive")
        
        if self.fps > 60:
            errors.append("FPS should not exceed 60")
        
        if self.percentile < 0 or self.percentile > 100:
            errors.append("Percentile must be between 0 and 100")
        
        if self.plot_type not in ['efficient', 'contour', 'heatmap']:
            errors.append("Plot type must be 'efficient', 'contour', or 'heatmap'")
        
        if self.output_format not in ['mp4', 'avi', 'gif']:
            errors.append("Output format must be 'mp4', 'avi', or 'gif'")
        
        return errors


class ConfigManager:
    """Manages configuration for multi-file animations."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or 'animation_config.json'
        self.config = AnimationConfig()
        self.loaded = False
    
    def collect_interactive_config(self, available_variables: List[str], 
                                 file_count: int, sample_file: Optional[str] = None) -> AnimationConfig:
        """Collect configuration interactively from user."""
        print("\n" + "=" * 60)
        print("Configuration Setup")
        print("=" * 60)
        print(f"📁 Found {file_count} NetCDF files")
        
        # Variable selection
        print(f"\n📊 Available variables:")
        for i, var in enumerate(available_variables, 1):
            print(f"  {i}. {var}")
        
        while True:
            try:
                choice = input(f"\nSelect variable number (1-{len(available_variables)}): ").strip()
                var_idx = int(choice) - 1
                if 0 <= var_idx < len(available_variables):
                    self.config.variable = available_variables[var_idx]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(available_variables)}")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Check for level dimensions if we have a sample file
        if sample_file:
            level_index = self._check_level_dimension(sample_file, self.config.variable)
            if level_index is not None:
                self.config.level_index = level_index
        
        # Plot type selection
        print(f"\n🎨 Plot types:")
        print("1. Efficient (fast, imshow with Cartopy) - Recommended")
        print("2. Contour (detailed with Cartopy)")
        print("3. Heatmap (simple grid)")
        
        while True:
            try:
                choice = input("Select plot type (1-3): ").strip()
                plot_types = ['efficient', 'contour', 'heatmap']
                plot_idx = int(choice) - 1
                if 0 <= plot_idx < 3:
                    self.config.plot_type = plot_types[plot_idx]
                    break
                else:
                    print("❌ Please enter a number between 1 and 3")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # FPS selection
        while True:
            try:
                fps_input = input(f"\nFrames per second (default: {self.config.fps}): ").strip()
                if not fps_input:
                    break
                fps = int(fps_input)
                if 1 <= fps <= 60:
                    self.config.fps = fps
                    break
                else:
                    print("❌ FPS must be between 1 and 60")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Output settings
        # Generate default output with timestamp for multi-file mode
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"{timestamp}_{self.config.variable}_{self.config.plot_type}_multifile.{self.config.output_format}"
        output_file = input(f"\nOutput filename (default: {default_output}): ").strip()
        if output_file:
            self.config.output_pattern = output_file
        else:
            self.config.output_pattern = default_output
        
        # Advanced settings
        print(f"\n⚙️  Advanced settings:")
        
        # Percentile filtering
        while True:
            try:
                percentile_input = input(f"Percentile threshold for filtering (default: {self.config.percentile}): ").strip()
                if not percentile_input:
                    break
                percentile = int(percentile_input)
                if 0 <= percentile <= 100:
                    self.config.percentile = percentile
                    break
                else:
                    print("❌ Percentile must be between 0 and 100")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Global colorbar
        global_cb = input("Use consistent colorbar across all files? (y/n, default: y): ").strip().lower()
        if global_cb in ['n', 'no']:
            self.config.global_colorbar = False
        
        # Pre-scan files
        pre_scan = input("Pre-scan files for global data range? (y/n, default: y): ").strip().lower()
        if pre_scan in ['n', 'no']:
            self.config.pre_scan_files = False
        
        # Save configuration
        save_config = input("\n💾 Save this configuration for future use? (y/n, default: y): ").strip().lower()
        if save_config not in ['n', 'no']:
            self.save_config()
        
        return self.config
    
    def _check_level_dimension(self, sample_file: str, variable: str) -> Optional[int]:
        """Check if variable has level dimension and prompt user for selection."""
        try:
            import xarray as xr
            with xr.open_dataset(sample_file) as ds:
                if variable not in ds.data_vars:
                    return None
                
                data_array = ds[variable]
                
                # Check for level dimensions
                level_dim = None
                if 'level' in data_array.dims:
                    level_dim = 'level'
                elif 'level_w' in data_array.dims:
                    level_dim = 'level_w'
                
                if level_dim is None:
                    return None
                
                level_count = len(ds[level_dim])
                print(f"\n📊 Variable '{variable}' has {level_count} levels (dimension: {level_dim})")
                
                # Show all levels
                print("Available levels:")
                for i in range(level_count):
                    level_val = ds[level_dim][i].values
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
                        
        except Exception as e:
            print(f"⚠️  Error checking level dimension: {e}")
            return None
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)
                self.config.from_dict(config_dict)
                self.loaded = True
                print(f"📁 Loaded configuration from {self.config_file}")
                return True
            else:
                print(f"📁 No configuration file found at {self.config_file}")
                return False
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return False
    
    def save_config(self, filename: Optional[str] = None):
        """Save configuration to file."""
        try:
            save_file = filename or self.config_file
            config_dict = self.config.to_dict()
            config_dict['saved_at'] = datetime.now().isoformat()
            
            with open(save_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"💾 Configuration saved to {save_file}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def validate_config(self) -> bool:
        """Validate current configuration."""
        errors = self.config.validate()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        return True
    
    def get_config(self) -> AnimationConfig:
        """Get current configuration."""
        return self.config
    
    def set_config(self, config: AnimationConfig):
        """Set configuration."""
        self.config = config
        self.loaded = True
    
    def reset_config(self):
        """Reset configuration to defaults."""
        self.config = AnimationConfig()
        self.loaded = False


def extract_timestep_from_filename(filename: str) -> Optional[int]:
    """Extract timestep number from filename."""
    # Common patterns for timestep extraction
    patterns = [
        r'\.(\d+)\.nc$',  # .177.nc
        r'_(\d+)\.nc$',   # _177.nc
        r'\.(\d{3})\.',   # .001.
        r'_(\d{3})_',     # _001_
        r'(\d+)\.nc$',    # 177.nc
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None


def discover_netcdf_files(pattern: str) -> List[str]:
    """Discover NetCDF files matching the pattern."""
    try:
        # Handle both glob patterns and regex patterns
        if '*' in pattern or '?' in pattern:
            # Use glob pattern
            files = glob.glob(pattern)
        else:
            # Treat as regex pattern
            import re
            regex = re.compile(pattern)
            files = []
            for file in os.listdir('.'):
                if regex.match(file) and file.endswith('.nc'):
                    files.append(file)
        
        # Filter for .nc files and sort
        nc_files = [f for f in files if f.endswith('.nc')]
        return sorted(nc_files)
    except Exception as e:
        print(f"❌ Error discovering files with pattern '{pattern}': {e}")
        return []


def sort_files_by_timestep(files: List[str]) -> List[str]:
    """Sort files by extracted timestep number."""
    def get_timestep_key(filename):
        timestep = extract_timestep_from_filename(filename)
        return timestep if timestep is not None else float('inf')
    
    return sorted(files, key=get_timestep_key)


 