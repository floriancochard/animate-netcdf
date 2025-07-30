#!/usr/bin/env python3
"""
File Manager for Multi-File NetCDF Animations
"""

import os
import glob
import re
from typing import List, Optional, Dict, Any, Tuple
import xarray as xr
from config_manager import extract_timestep_from_filename, discover_netcdf_files, sort_files_by_timestep


class NetCDFFileManager:
    """Manages NetCDF files for multi-file animations."""
    
    def __init__(self, file_pattern: str):
        self.file_pattern = file_pattern
        self.files = []
        self.sorted_files = []
        self.file_info = {}
        self.discovered = False
        
    def discover_files(self) -> List[str]:
        """Discover and validate NetCDF files."""
        print(f"🔍 Discovering files with pattern: {self.file_pattern}")
        
        # Discover files
        self.files = discover_netcdf_files(self.file_pattern)
        
        if not self.files:
            print(f"❌ No NetCDF files found matching pattern: {self.file_pattern}")
            return []
        
        print(f"📁 Found {len(self.files)} NetCDF files")
        
        # Validate files and extract information
        valid_files = []
        for file in self.files:
            try:
                info = self._extract_file_info(file)
                if info:
                    self.file_info[file] = info
                    valid_files.append(file)
                else:
                    print(f"⚠️  Skipping invalid file: {file}")
            except Exception as e:
                print(f"⚠️  Error processing file {file}: {e}")
        
        self.files = valid_files
        self.discovered = True
        
        if not self.files:
            print("❌ No valid NetCDF files found")
            return []
        
        # Sort files by timestep
        self.sorted_files = sort_files_by_timestep(self.files)
        
        print(f"✅ Validated {len(self.files)} files")
        self._print_file_summary()
        
        return self.sorted_files
    
    def _extract_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Extract information from a NetCDF file."""
        try:
            with xr.open_dataset(filepath) as ds:
                info = {
                    'path': filepath,
                    'timestep': extract_timestep_from_filename(filepath),
                    'variables': list(ds.data_vars.keys()),
                    'dimensions': dict(ds.sizes),  # Use sizes instead of dims to avoid deprecation warning
                    'coordinates': list(ds.coords.keys()),
                    'file_size_mb': os.path.getsize(filepath) / (1024 * 1024)
                }
                
                # Extract spatial coordinates
                spatial_coords = {}
                for coord in ['lat', 'lon', 'latitude', 'longitude']:
                    if coord in ds.coords:
                        spatial_coords[coord] = {
                            'min': float(ds[coord].min().values),
                            'max': float(ds[coord].max().values),
                            'size': len(ds[coord])
                        }
                info['spatial_coords'] = spatial_coords
                
                return info
                
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return None
    
    def _print_file_summary(self):
        """Print summary of discovered files."""
        if not self.sorted_files:
            return
        
        print(f"\n📊 File Summary:")
        print(f"  Total files: {len(self.sorted_files)}")
        
        # Show first few files
        preview_count = min(5, len(self.sorted_files))
        print(f"  First {preview_count} files:")
        for i, file in enumerate(self.sorted_files[:preview_count]):
            timestep = self.file_info[file]['timestep']
            size_mb = self.file_info[file]['file_size_mb']
            print(f"    {i+1}. {os.path.basename(file)} (timestep: {timestep}, size: {size_mb:.1f}MB)")
        
        if len(self.sorted_files) > preview_count:
            print(f"    ... and {len(self.sorted_files) - preview_count} more files")
        
        # Show timestep range
        timesteps = [info['timestep'] for info in self.file_info.values() if info['timestep'] is not None]
        if timesteps:
            print(f"  Timestep range: {min(timesteps)} to {max(timesteps)}")
        
        # Show common variables
        all_variables = set()
        for info in self.file_info.values():
            all_variables.update(info['variables'])
        
        print(f"  Common variables: {', '.join(sorted(all_variables))}")
    
    def get_common_variables(self) -> List[str]:
        """Get variables that are present in all files."""
        if not self.file_info:
            return []
        
        # Find variables present in all files
        all_variables = set()
        for i, info in enumerate(self.file_info.values()):
            if i == 0:
                all_variables = set(info['variables'])
            else:
                all_variables &= set(info['variables'])
        
        return sorted(list(all_variables))
    
    def get_spatial_coordinates(self) -> Dict[str, Any]:
        """Get spatial coordinate information from the first file."""
        if not self.file_info:
            return {}
        
        first_file = list(self.file_info.values())[0]
        return first_file.get('spatial_coords', {})
    
    def validate_consistency(self) -> List[str]:
        """Validate consistency across all files."""
        errors = []
        
        if not self.file_info:
            errors.append("No files to validate")
            return errors
        
        # Check if all files have the same variables
        common_vars = self.get_common_variables()
        if not common_vars:
            errors.append("No common variables found across all files")
        
        # Check spatial coordinate consistency
        first_coords = None
        for filepath, info in self.file_info.items():
            if first_coords is None:
                first_coords = info['spatial_coords']
            else:
                if info['spatial_coords'] != first_coords:
                    errors.append(f"Spatial coordinates differ between files")
                    break
        
        # Check file sizes (warn if they vary significantly)
        sizes = [info['file_size_mb'] for info in self.file_info.values()]
        if len(sizes) > 1:
            size_std = (max(sizes) - min(sizes)) / max(sizes)
            if size_std > 0.1:  # More than 10% variation
                print(f"⚠️  Warning: File sizes vary significantly (std: {size_std:.2%})")
        
        return errors
    
    def get_file_by_timestep(self, timestep: int) -> Optional[str]:
        """Get file path by timestep number."""
        for filepath, info in self.file_info.items():
            if info['timestep'] == timestep:
                return filepath
        return None
    
    def get_timestep_by_file(self, filepath: str) -> Optional[int]:
        """Get timestep number by file path."""
        info = self.file_info.get(filepath)
        return info['timestep'] if info else None
    
    def get_total_size_mb(self) -> float:
        """Get total size of all files in MB."""
        return sum(info['file_size_mb'] for info in self.file_info.values())
    
    def estimate_memory_usage(self, variable: str) -> float:
        """Estimate memory usage for a variable across all files."""
        if not self.file_info:
            return 0.0
        
        # Get variable shape from first file
        first_info = list(self.file_info.values())[0]
        if variable not in first_info['variables']:
            return 0.0
        
        # Estimate based on file size and number of files
        avg_file_size = self.get_total_size_mb() / len(self.file_info)
        estimated_mb = avg_file_size * len(self.file_info)
        
        return estimated_mb
    
    def get_file_range(self, start_timestep: Optional[int] = None, 
                      end_timestep: Optional[int] = None) -> List[str]:
        """Get files within a timestep range."""
        if not self.sorted_files:
            return []
        
        if start_timestep is None and end_timestep is None:
            return self.sorted_files
        
        filtered_files = []
        for filepath in self.sorted_files:
            timestep = self.get_timestep_by_file(filepath)
            if timestep is None:
                continue
            
            if start_timestep is not None and timestep < start_timestep:
                continue
            if end_timestep is not None and timestep > end_timestep:
                continue
            
            filtered_files.append(filepath)
        
        return filtered_files
    
    def preview_files(self, max_files: int = 5) -> List[Dict[str, Any]]:
        """Get preview information for first few files."""
        preview = []
        for i, filepath in enumerate(self.sorted_files[:max_files]):
            info = self.file_info[filepath].copy()
            info['index'] = i
            info['filename'] = os.path.basename(filepath)
            preview.append(info)
        
        return preview


class FilePatternMatcher:
    """Helper class for matching file patterns."""
    
    @staticmethod
    def is_glob_pattern(pattern: str) -> bool:
        """Check if pattern contains glob characters."""
        return '*' in pattern or '?' in pattern or '[' in pattern
    
    @staticmethod
    def is_regex_pattern(pattern: str) -> bool:
        """Check if pattern looks like a regex pattern."""
        return pattern.startswith('^') or pattern.endswith('$') or '\\' in pattern
    
    @staticmethod
    def create_glob_pattern(base_pattern: str) -> str:
        """Create a glob pattern from a base pattern."""
        # Handle common NetCDF file patterns
        if '*' not in base_pattern and '?' not in base_pattern:
            # Assume it's a base pattern, add wildcards
            if base_pattern.endswith('.nc'):
                # Replace the last part before .nc with wildcard
                parts = base_pattern.split('.')
                if len(parts) >= 2:
                    parts[-2] = '*'
                    return '.'.join(parts)
            else:
                # Add wildcard for common patterns
                return f"{base_pattern}*.nc"
        
        return base_pattern
    
    @staticmethod
    def validate_pattern(pattern: str) -> bool:
        """Validate if pattern is reasonable."""
        if not pattern:
            return False
        
        # Check for basic NetCDF file extension
        if not pattern.endswith('.nc') and not pattern.endswith('*'):
            return False
        
        return True


 