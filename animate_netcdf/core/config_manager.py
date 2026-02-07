#!/usr/bin/env python3
"""
Configuration Manager for Multi-File NetCDF Animations
Enhanced with better validation and error handling
"""

import json
import os
import glob
from typing import Dict, Any, Optional, List, Tuple, Callable
import re
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps


class OutputFormat(Enum):
    """Enumeration for output formats."""
    PNG = "png"
    MP4 = "mp4"
    AVI = "avi"
    GIF = "gif"


def validate_config(func: Callable) -> Callable:
    """Decorator to validate configuration before executing a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function with validation
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'config'):
            is_valid, errors = self.config.get_validation_summary()
            if not is_valid:
                print("⚠️  Configuration validation warnings:")
                for error in errors:
                    print(f"  - {error}")
                
                # Check for critical errors
                critical_errors = [e for e in errors if any(keyword in e.lower() for keyword in ['invalid', 'cannot', 'must be'])]
                if critical_errors:
                    print("❌ Critical configuration errors detected. Operation may fail.")
                    proceed = input("Continue anyway? (y/n): ").strip().lower()
                    if proceed not in ['y', 'yes']:
                        return False
        
        return func(self, *args, **kwargs)
    return wrapper


def require_config(func: Callable) -> Callable:
    """Decorator to require valid configuration before executing a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function with configuration requirement
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'config'):
            # Check if configuration is loaded
            if not self.loaded:
                print("❌ No configuration loaded. Please load or create a configuration first.")
                return False
            
            # Check if configuration is valid
            is_valid, errors = self.config.get_validation_summary()
            if not is_valid:
                print("❌ Configuration is invalid:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # Check for required fields
            missing_fields = self.config.get_missing_required_fields()
            if missing_fields:
                print("❌ Missing required configuration fields:")
                for field in missing_fields:
                    print(f"  - {field}")
                return False
        
        return func(self, *args, **kwargs)
    return wrapper


@dataclass
class AnimationConfig:
    """Enhanced configuration class for animation parameters.
    
    This class holds all configuration parameters for NetCDF animations,
    including both single-file and multi-file animation settings.
    Provides comprehensive validation and type safety through enums.
    """
    
    # Core animation parameters
    variable: Optional[str] = None
    plot_type: str = 'efficient'
    fps: int = 10
    output_pattern: Optional[str] = None
    animate_dim: str = 'time'
    level_index: Optional[int] = None
    percentile: int = 0
    batch_mode: bool = False
    interactive: bool = True
    
    # Multi-file specific parameters
    file_pattern: Optional[str] = None
    sort_by_timestep: bool = True
    global_colorbar: bool = True
    pre_scan_files: bool = True
    
    # Output settings
    output_directory: str = '.'
    output_format: OutputFormat = OutputFormat.MP4
    overwrite_existing: bool = False
    
    # Performance settings
    memory_limit_mb: int = 2048
    max_files_preview: int = 10
    
    # Zoom settings
    zoom_factor: float = 1.0
    
    # Map and visualization settings
    cmap: Optional[str] = None  # Matplotlib colormap name (e.g. 'Blues', 'viridis')
    
    # Designer mode settings
    designer_mode: bool = False
    designer_square_crop: bool = False  # Square output centered on map, no padding
    
    # Output appearance settings
    transparent: bool = False
    
    # Data filtering settings
    ignore_values: List[float] = field(default_factory=list)
    
    # Color scale range (optional; if set, overrides data-based min/max)
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    
    # Validation errors
    _validation_errors: List[str] = field(default_factory=list, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of configuration
        """
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
            'output_format': self.output_format.value,
            'overwrite_existing': self.overwrite_existing,
            'memory_limit_mb': self.memory_limit_mb,
            'max_files_preview': self.max_files_preview,
            'zoom_factor': self.zoom_factor,
            'cmap': self.cmap,
            'designer_mode': self.designer_mode,
            'designer_square_crop': self.designer_square_crop,
            'transparent': self.transparent,
            'ignore_values': self.ignore_values,
            'vmin': self.vmin,
            'vmax': self.vmax
        }
    
    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary with validation.
        
        Args:
            config_dict: Dictionary containing configuration parameters
        """
        self._validation_errors.clear()
        
        for key, value in config_dict.items():
            if hasattr(self, key):
                # Handle enum conversions
                if key == 'plot_type':
                    # Always use efficient; ignore value from file
                    continue
                elif key == 'output_format' and isinstance(value, str):
                    try:
                        value = OutputFormat(value)
                    except ValueError:
                        self._validation_errors.append(f"Invalid output_format: {value}. Must be one of {[f.value for f in OutputFormat]}")
                        continue
                
                elif key == 'cmap':
                    if value is not None and not isinstance(value, str):
                        self._validation_errors.append("cmap must be a string or None")
                        continue
                    # Accept any string; matplotlib will validate at plot time
                    pass
                elif key == 'ignore_values':
                    # Ensure ignore_values is a list of floats
                    if isinstance(value, list):
                        try:
                            value = [float(v) for v in value]
                        except (ValueError, TypeError):
                            self._validation_errors.append(f"Invalid ignore_values: {value}. Must be a list of numbers")
                            continue
                    elif value is None:
                        value = []
                    else:
                        # Try to convert single value to list
                        try:
                            value = [float(value)]
                        except (ValueError, TypeError):
                            self._validation_errors.append(f"Invalid ignore_values: {value}. Must be a list of numbers")
                            continue
                elif key in ('vmin', 'vmax'):
                    if value is not None:
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            self._validation_errors.append(f"Invalid {key}: must be a number or None")
                            continue
                
                setattr(self, key, value)
            else:
                # Ignore unknown keys for backward compatibility
                pass
    
    def validate(self) -> List[str]:
        """Enhanced validation with detailed error messages.
        
        Returns:
            List[str]: List of validation error messages
        """
        errors: List[str] = []
        
        # FPS validation
        if self.fps <= 0:
            errors.append("FPS must be positive")
        elif self.fps > 60:
            errors.append("FPS should not exceed 60 for performance reasons")
        
        # Percentile validation
        if self.percentile < 0 or self.percentile > 100:
            errors.append("Percentile must be between 0 and 100")
        
        # Zoom factor validation
        if self.zoom_factor <= 0:
            errors.append("Zoom factor must be positive")
        elif self.zoom_factor > 125:
            errors.append("Zoom factor should not exceed 125 for reasonable performance")
        
        # Memory limit validation
        if self.memory_limit_mb <= 0:
            errors.append("Memory limit must be positive")
        elif self.memory_limit_mb > 32768:  # 32GB
            errors.append("Memory limit should not exceed 32768 MB (32GB)")
        
        # File pattern validation
        if self.file_pattern and not self._validate_file_pattern(self.file_pattern):
            errors.append(f"Invalid file pattern: {self.file_pattern}")
        
        # Output directory validation
        if self.output_directory and not os.path.exists(self.output_directory):
            try:
                os.makedirs(self.output_directory, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory '{self.output_directory}': {e}")
        
        # Variable name validation
        if self.variable and not self._validate_variable_name(self.variable):
            errors.append(f"Invalid variable name: {self.variable}")
        
        # Color scale range validation (vmin must be < vmax when both set)
        if self.vmin is not None and self.vmax is not None:
            if self.vmin >= self.vmax:
                errors.append("vmin must be less than vmax when both are set")
        
        # Animation dimension validation
        if self.animate_dim and not self._validate_dimension_name(self.animate_dim):
            errors.append(f"Invalid animation dimension: {self.animate_dim}")
        
        return errors
    
    def _validate_file_pattern(self, pattern: str) -> bool:
        """Validate file pattern.
        
        Args:
            pattern: File pattern to validate
            
        Returns:
            bool: True if pattern is valid
        """
        if not pattern:
            return False
        
        # Check for basic NetCDF file extension
        if not pattern.endswith('.nc') and not pattern.endswith('*'):
            return False
        
        # Check for reasonable pattern length
        if len(pattern) > 200:
            return False
        
        return True
    
    def _validate_variable_name(self, variable: str) -> bool:
        """Validate variable name.
        
        Args:
            variable: Variable name to validate
            
        Returns:
            bool: True if variable name is valid
        """
        if not variable:
            return False
        
        # Check for reasonable variable name
        if len(variable) > 100:
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', variable):
            return False
        
        return True
    
    def _validate_dimension_name(self, dimension: str) -> bool:
        """Validate dimension name.
        
        Args:
            dimension: Dimension name to validate
            
        Returns:
            bool: True if dimension name is valid
        """
        if not dimension:
            return False
        
        # Check for reasonable dimension name
        if len(dimension) > 50:
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', dimension):
            return False
        
        return True
    
    def get_validation_summary(self) -> Tuple[bool, List[str]]:
        """Get validation summary with errors.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = self.validate()
        return len(errors) == 0, errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            bool: True if configuration is valid
        """
        return len(self.validate()) == 0
    
    def get_missing_required_fields(self) -> List[str]:
        """Get list of missing required fields.
        
        Returns:
            List[str]: List of missing required field names
        """
        missing: List[str] = []
        
        if not self.variable:
            missing.append("variable")
        
        if not self.file_pattern:
            missing.append("file_pattern")
        
        return missing
    
    def has_required_fields(self) -> bool:
        """Check if all required fields are present.
        
        Returns:
            bool: True if all required fields are present
        """
        return len(self.get_missing_required_fields()) == 0
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get comprehensive configuration status.
        
        Returns:
            Dict[str, Any]: Dictionary containing configuration status information
        """
        is_valid, errors = self.get_validation_summary()
        missing_fields = self.get_missing_required_fields()
        
        return {
            'valid': is_valid,
            'has_required_fields': len(missing_fields) == 0,
            'validation_errors': errors,
            'missing_fields': missing_fields,
            'output_format': self.output_format.value,
            'variable': self.variable,
            'file_pattern': self.file_pattern,
            'fps': self.fps,
            'zoom_factor': self.zoom_factor
        }


def load_config_from_path(path: str) -> AnimationConfig:
    """Load visualization configuration from a JSON or YAML file.

    Args:
        path: Path to config file (.json, .yaml, or .yml).

    Returns:
        AnimationConfig: Configuration populated from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the format is unsupported, or the file content is invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == '.json':
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e
    elif ext in ('.yaml', '.yml'):
        try:
            import yaml
        except ImportError:
            raise ValueError(
                "YAML config files require PyYAML. Install with: pip install pyyaml"
            ) from None
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Invalid YAML in config file: {e}") from e
        if data is None:
            data = {}
    else:
        raise ValueError(
            f"Unsupported config format: '{ext}'. Use .json, .yaml, or .yml"
        )

    config = AnimationConfig()
    config.from_dict(data)
    return config


class ConfigManager:
    """Enhanced configuration manager with better error handling and validation.
    
    This class manages the loading, saving, and validation of animation
    configurations. It provides both interactive and programmatic interfaces
    for configuration management.
    """
    
    def __init__(self, config_file: Optional[str] = None) -> None:
        """Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file or 'animation_config.json'
        self.config = AnimationConfig()
        self.loaded = False
        self.load_errors: List[str] = []
    
    def collect_interactive_config(self, available_variables: List[str], 
                                 file_count: int, sample_file: Optional[str] = None) -> AnimationConfig:
        """Collect configuration interactively from user with enhanced validation.
        
        Args:
            available_variables: List of available variables in the dataset
            file_count: Number of files being processed
            sample_file: Optional sample file for level dimension checking
            
        Returns:
            AnimationConfig: Collected configuration object
        """
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
        
        # FPS selection with validation
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"{timestamp}_{self.config.variable}_multifile.{self.config.output_format.value}"
        output_file = input(f"\nOutput filename (default: {default_output}): ").strip()
        if output_file:
            self.config.output_pattern = output_file
        else:
            self.config.output_pattern = default_output
        
        # Advanced settings
        print(f"\n⚙️  Advanced settings:")
        
        # Percentile filtering with validation
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
        
        # Fixed color scale range (vmin, vmax)
        print(f"\n📐 Color scale range: set fixed min/max (e.g. 285,305 for temperature in K)")
        print("   Leave empty to use data-based range.")
        while True:
            try:
                range_input = input("Enter min,max (e.g. 285,305) or press Enter for data range: ").strip()
                if not range_input:
                    self.config.vmin = None
                    self.config.vmax = None
                    break
                parts = [p.strip() for p in range_input.replace(',', ' ').split()]
                if len(parts) == 2:
                    vmin_val = float(parts[0])
                    vmax_val = float(parts[1])
                    if vmin_val < vmax_val:
                        self.config.vmin = vmin_val
                        self.config.vmax = vmax_val
                        print(f"✅ Color scale: {self.config.vmin} to {self.config.vmax}")
                        break
                    else:
                        print("❌ Min must be less than max")
                else:
                    print("❌ Enter two numbers separated by comma (e.g. 285,305)")
            except ValueError:
                print("❌ Invalid input. Enter two numbers (e.g. 285,305)")
        
        # Zoom factor with validation
        while True:
            try:
                zoom_input = input(f"Zoom factor (default: {self.config.zoom_factor}): ").strip()
                if not zoom_input:
                    break
                zoom_factor = float(zoom_input)
                if 0.1 <= zoom_factor <= 125.0:
                    self.config.zoom_factor = zoom_factor
                    break
                else:
                    print("❌ Zoom factor must be between 0.1 and 125.0")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Ignore values
        print(f"\n🔍 Some NetCDF files use placeholder values (e.g., 999, -999) for missing data.")
        print("   These values should be ignored during plotting.")
        while True:
            try:
                ignore_input = input("Enter values to ignore (comma-separated, e.g., 999,-999, or press Enter for none): ").strip()
                if not ignore_input:
                    self.config.ignore_values = []
                    break
                
                # Parse comma-separated values
                values = [float(v.strip()) for v in ignore_input.split(',')]
                self.config.ignore_values = values
                print(f"✅ Will ignore values: {values}")
                break
            except ValueError:
                print("❌ Invalid input. Please enter comma-separated numbers (e.g., 999,-999)")
        
        # Validate configuration before saving
        is_valid, errors = self.config.get_validation_summary()
        if not is_valid:
            print("\n⚠️  Configuration validation warnings:")
            for error in errors:
                print(f"  - {error}")
        
        # Save configuration
        save_config = input("\n💾 Save this configuration for future use? (y/n, default: y): ").strip().lower()
        if save_config not in ['n', 'no']:
            self.save_config()
        
        return self.config
    
    def _check_level_dimension(self, sample_file: str, variable: str) -> Optional[int]:
        """Check if variable has level dimension and prompt user for selection.
        
        Args:
            sample_file: Path to sample file for checking
            variable: Variable name to check
            
        Returns:
            Optional[int]: Selected level index or None for average
        """
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
        """Load configuration from file with enhanced error handling.
        
        Returns:
            bool: True if configuration loaded successfully
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)
                
                self.config.from_dict(config_dict)
                self.loaded = True
                
                # Validate loaded configuration
                is_valid, errors = self.config.get_validation_summary()
                if not is_valid:
                    print(f"⚠️  Configuration validation warnings in {self.config_file}:")
                    for error in errors:
                        print(f"  - {error}")
                
                print(f"📁 Loaded configuration from {self.config_file}")
                return True
            else:
                print(f"📁 No configuration file found at {self.config_file}")
                return False
        except json.JSONDecodeError as e:
            self.load_errors.append(f"Invalid JSON in {self.config_file}: {e}")
            print(f"❌ Error loading configuration: Invalid JSON format")
            return False
        except Exception as e:
            self.load_errors.append(f"Error loading {self.config_file}: {e}")
            print(f"❌ Error loading configuration: {e}")
            return False
    
    def save_config(self, filename: Optional[str] = None) -> None:
        """Save configuration to file with validation.
        
        Args:
            filename: Optional filename to save to (uses default if None)
        """
        try:
            save_file = filename or self.config_file
            
            # Validate before saving
            is_valid, errors = self.config.get_validation_summary()
            if not is_valid:
                print("⚠️  Configuration has validation warnings:")
                for error in errors:
                    print(f"  - {error}")
                
                save_anyway = input("Save configuration anyway? (y/n): ").strip().lower()
                if save_anyway not in ['y', 'yes']:
                    print("❌ Configuration not saved")
                    return
            
            config_dict = self.config.to_dict()
            config_dict['saved_at'] = datetime.now().isoformat()
            config_dict['version'] = '1.0'
            
            with open(save_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"💾 Configuration saved to {save_file}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def validate_config(self) -> bool:
        """Validate current configuration with detailed feedback.
        
        Returns:
            bool: True if configuration is valid
        """
        is_valid, errors = self.config.get_validation_summary()
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # Check for missing required fields
        missing_fields = self.config.get_missing_required_fields()
        if missing_fields:
            print("⚠️  Missing required fields:")
            for field in missing_fields:
                print(f"  - {field}")
            return False
        
        print("✅ Configuration is valid")
        return True
    
    def get_config(self) -> AnimationConfig:
        """Get current configuration.
        
        Returns:
            AnimationConfig: Current configuration object
        """
        return self.config
    
    def set_config(self, config: AnimationConfig) -> None:
        """Set configuration with validation.
        
        Args:
            config: Configuration object to set
        """
        self.config = config
        self.loaded = True
        
        # Validate the new configuration
        is_valid, errors = self.config.get_validation_summary()
        if not is_valid:
            print("⚠️  Configuration validation warnings:")
            for error in errors:
                print(f"  - {error}")
    
    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self.config = AnimationConfig()
        self.loaded = False
        self.load_errors.clear()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration.
        
        Returns:
            Dict[str, Any]: Configuration summary dictionary
        """
        summary = {
            'loaded': self.loaded,
            'valid': self.config.is_valid(),
            'missing_fields': self.config.get_missing_required_fields(),
            'validation_errors': self.config.validate(),
            'load_errors': self.load_errors.copy()
        }
        
        if self.loaded:
            summary.update({
                'variable': self.config.variable,
                'fps': self.config.fps,
                'file_pattern': self.config.file_pattern,
                'output_pattern': self.config.output_pattern
            })
        
        return summary
    
    def print_config_status(self) -> None:
        """Print a detailed configuration status."""
        print("\n" + "=" * 60)
        print("Configuration Status")
        print("=" * 60)
        
        summary = self.get_config_summary()
        
        print(f"📁 Loaded: {summary['loaded']}")
        print(f"✅ Valid: {summary['valid']}")
        
        if summary['missing_fields']:
            print(f"⚠️  Missing fields: {', '.join(summary['missing_fields'])}")
        
        if summary['validation_errors']:
            print(f"❌ Validation errors: {len(summary['validation_errors'])}")
            for error in summary['validation_errors']:
                print(f"  - {error}")
        
        if summary['load_errors']:
            print(f"❌ Load errors: {len(summary['load_errors'])}")
            for error in summary['load_errors']:
                print(f"  - {error}")
        
        if summary['loaded'] and summary['valid']:
            print(f"\n📊 Configuration Details:")
            print(f"  Variable: {summary.get('variable', 'Not set')}")
            print(f"  FPS: {summary.get('fps', 'Not set')}")
            print(f"  File pattern: {summary.get('file_pattern', 'Not set')}")
            print(f"  Output pattern: {summary.get('output_pattern', 'Not set')}")


def extract_timestep_from_filename(filename: str) -> Optional[int]:
    """Extract timestep number from filename.
    
    Args:
        filename: Filename to extract timestep from
        
    Returns:
        Optional[int]: Timestep number if found, None otherwise
    """
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
    """Discover NetCDF files matching the pattern.
    
    Args:
        pattern: File pattern to match
        
    Returns:
        List[str]: List of matching NetCDF files
    """
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
    """Sort files by extracted timestep number.
    
    Args:
        files: List of filenames to sort
        
    Returns:
        List[str]: Sorted list of filenames
    """
    def get_timestep_key(filename: str) -> float:
        timestep = extract_timestep_from_filename(filename)
        return timestep if timestep is not None else float('inf')
    
    return sorted(files, key=get_timestep_key)


 