#!/usr/bin/env python3
"""
NetCDF Explorer Utilities
Functions to explore NetCDF file structure, including groups and subgroups
"""

import netCDF4 as nc
import xarray as xr
from typing import Dict, List, Any, Optional
from pathlib import Path


class NetCDFExplorer:
    """Utility class for exploring NetCDF file structure and metadata."""
    
    @staticmethod
    def explore_netcdf_structure(file_path: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        Explore the complete structure of a NetCDF file including groups and subgroups.
        
        Args:
            file_path: Path to the NetCDF file
            max_depth: Maximum depth to explore (prevents infinite recursion)
            
        Returns:
            Dictionary containing the complete file structure
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Use netCDF4 for detailed group exploration
            with nc.Dataset(file_path, 'r') as ds:
                structure = {
                    'file_path': str(file_path),
                    'file_size_mb': file_path.stat().st_size / (1024 * 1024),
                    'format': ds.data_model,
                    'root': NetCDFExplorer._explore_groups(ds, max_depth, 0)
                }
                return structure
        except Exception as e:
            raise RuntimeError(f"Error reading NetCDF file {file_path}: {e}")
    
    @staticmethod
    def _explore_groups(dataset: nc.Dataset, max_depth: int, current_depth: int) -> Dict[str, Any]:
        """
        Recursively explore groups in a NetCDF dataset.
        
        Args:
            dataset: NetCDF dataset or group
            max_depth: Maximum depth to explore
            current_depth: Current exploration depth
            
        Returns:
            Dictionary containing group information
        """
        if current_depth >= max_depth:
            return {'error': f'Maximum depth {max_depth} reached'}
        
        group_info = {
            'name': dataset.name if hasattr(dataset, 'name') else 'root',
            'path': dataset.path if hasattr(dataset, 'path') else '/',
            'dimensions': {name: len(dim) for name, dim in dataset.dimensions.items()},
            'variables': {},
            'groups': {},
            'attributes': {attr: dataset.getncattr(attr) for attr in dataset.ncattrs()}
        }
        
        # For root dataset, we want to show the actual structure
        if current_depth == 0:
            group_info['name'] = 'root'
            group_info['path'] = '/'
        
        # Explore variables
        for var_name, var in dataset.variables.items():
            # Safely get dtype itemsize
            try:
                if hasattr(var.dtype, 'itemsize'):
                    itemsize = var.dtype.itemsize
                else:
                    # Fallback: try to get itemsize from numpy
                    import numpy as np
                    np_dtype = np.dtype(var.dtype)
                    itemsize = np_dtype.itemsize
            except (TypeError, ValueError, AttributeError):
                # If all else fails, use a default itemsize
                itemsize = 8  # Default to 8 bytes (double precision)
            
            group_info['variables'][var_name] = {
                'dimensions': list(var.dimensions),
                'shape': var.shape,
                'dtype': str(var.dtype),
                'attributes': {attr: var.getncattr(attr) for attr in var.ncattrs()},
                'size_mb': var.size * itemsize / (1024 * 1024) if var.size > 0 else 0
            }
        
        # Explore subgroups
        for group_name, group in dataset.groups.items():
            group_info['groups'][group_name] = NetCDFExplorer._explore_groups(
                group, max_depth, current_depth + 1
            )
        
        return group_info
    
    @staticmethod
    def print_structure_summary(structure: Dict[str, Any], indent: str = "") -> None:
        """
        Print a human-readable summary of the NetCDF structure.
        
        Args:
            structure: Structure dictionary from explore_netcdf_structure
            indent: Indentation string for nested output
        """
        print(f"{indent}📁 File: {structure['file_path']}")
        print(f"{indent}📊 Size: {structure['file_size_mb']:.2f} MB")
        print(f"{indent}🔧 Format: {structure['format']}")
        
        if 'root' in structure:
            root_info = structure['root']
            print(f"{indent}📂 Root Dataset:")
            print(f"{indent}  📏 Dimensions: {len(root_info.get('dimensions', {}))}")
            print(f"{indent}  🔢 Variables: {len(root_info.get('variables', {}))}")
            print(f"{indent}  📁 Groups: {len(root_info.get('groups', {}))}")
            
            # Show some variable examples
            if root_info.get('variables'):
                var_names = list(root_info['variables'].keys())[:5]
                print(f"{indent}    Variable examples: {', '.join(var_names)}")
                if len(root_info['variables']) > 5:
                    print(f"{indent}    ... and {len(root_info['variables']) - 5} more")
            
            # Show groups
            if root_info.get('groups'):
                print(f"{indent}    Groups: {', '.join(root_info['groups'].keys())}")
                # Recursively print subgroups
                NetCDFExplorer._print_groups_summary(root_info['groups'], indent + "    ")
    
    @staticmethod
    def _print_groups_summary(groups: Dict[str, Any], indent: str = "") -> None:
        """Print summary of groups recursively."""
        for group_name, group_info in groups.items():
            if isinstance(group_info, dict) and 'error' not in group_info:
                print(f"{indent}📂 Group: {group_name}")
                
                # Print dimensions
                if group_info.get('dimensions'):
                    dims_str = ", ".join([f"{k}={v}" for k, v in group_info['dimensions'].items()])
                    print(f"{indent}  📏 Dimensions: {dims_str}")
                
                # Print variables count
                var_count = len(group_info.get('variables', {}))
                if var_count > 0:
                    print(f"{indent}  🔢 Variables: {var_count}")
                    
                    # Show first few variables
                    var_names = list(group_info['variables'].keys())[:5]
                    if var_names:
                        print(f"{indent}    Examples: {', '.join(var_names)}")
                        if len(group_info['variables']) > 5:
                            print(f"{indent}    ... and {len(group_info['variables']) - 5} more")
                
                # Print subgroups count
                subgroup_count = len(group_info.get('groups', {}))
                if subgroup_count > 0:
                    print(f"{indent}  📁 Subgroups: {subgroup_count}")
                
                # Recursively print subgroups
                if group_info.get('groups'):
                    NetCDFExplorer._print_groups_summary(group_info['groups'], indent + "  ")
            else:
                print(f"{indent}❌ {group_name}: {group_info}")
    
    @staticmethod
    def get_variable_paths(structure: Dict[str, Any], base_path: str = "") -> List[str]:
        """
        Get all variable paths in the NetCDF file.
        
        Args:
            structure: Structure dictionary from explore_netcdf_structure
            base_path: Base path for current recursion level
            
        Returns:
            List of variable paths (e.g., ['/temperature', '/group1/pressure'])
        """
        paths = []
        
        def _collect_paths(groups: Dict[str, Any], current_path: str):
            for group_name, group_info in groups.items():
                if isinstance(group_info, dict) and 'error' not in group_info:
                    # Add variables from this group
                    for var_name in group_info.get('variables', {}):
                        var_path = f"{current_path}/{var_name}" if current_path else f"/{var_name}"
                        paths.append(var_path)
                    
                    # Recursively process subgroups
                    if group_info.get('groups'):
                        new_path = f"{current_path}/{group_name}" if current_path else f"/{group_name}"
                        _collect_paths(group_info['groups'], new_path)
        
        _collect_paths(structure.get('root', {}), base_path)
        return paths
    
    @staticmethod
    def compare_netcdf_files(file_paths: List[str]) -> Dict[str, Any]:
        """
        Compare the structure of multiple NetCDF files.
        
        Args:
            file_paths: List of file paths to compare
            
        Returns:
            Dictionary containing comparison information
        """
        if len(file_paths) < 2:
            raise ValueError("Need at least 2 files to compare")
        
        structures = {}
        for file_path in file_paths:
            try:
                structures[file_path] = NetCDFExplorer.explore_netcdf_structure(file_path)
            except Exception as e:
                structures[file_path] = {'error': str(e)}
        
        # Find common variables across all files
        all_variable_paths = []
        for file_path, structure in structures.items():
            if 'error' not in structure:
                all_variable_paths.append(set(NetCDFExplorer.get_variable_paths(structure)))
        
        common_variables = set.intersection(*all_variable_paths) if all_variable_paths else set()
        
        comparison = {
            'files': structures,
            'common_variables': list(common_variables),
            'total_files': len(file_paths),
            'successful_reads': len([s for s in structures.values() if 'error' not in s])
        }
        
        return comparison


def explore_netcdf_file(file_path: str, print_summary: bool = True) -> Dict[str, Any]:
    """
    Convenience function to explore a single NetCDF file.
    
    Args:
        file_path: Path to the NetCDF file
        print_summary: Whether to print a summary to stdout
        
    Returns:
        Dictionary containing the file structure
    """
    explorer = NetCDFExplorer()
    structure = explorer.explore_netcdf_structure(file_path)
    
    if print_summary:
        print("=" * 80)
        print("NetCDF File Structure Explorer")
        print("=" * 80)
        explorer.print_structure_summary(structure)
        print("=" * 80)
    
    return structure


def get_netcdf_groups(file_path: str) -> List[str]:
    """
    Get a simple list of group names in a NetCDF file.
    
    Args:
        file_path: Path to the NetCDF file
        
    Returns:
        List of group names
    """
    try:
        with nc.Dataset(file_path, 'r') as ds:
            return list(ds.groups.keys())
    except Exception as e:
        print(f"Error reading NetCDF file: {e}")
        return []


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python netcdf_explorer.py <netcdf_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        structure = explore_netcdf_file(file_path)
        print(f"\n✅ Successfully explored {file_path}")
        print(f"📊 Total variables found: {len(NetCDFExplorer.get_variable_paths(structure))}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
