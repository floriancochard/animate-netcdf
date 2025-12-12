#!/usr/bin/env python3
"""
Group Extractor Utilities
Functions to extract variables from nested NetCDF groups
"""

import netCDF4 as nc
import numpy as np
import xarray as xr
from typing import Dict, Any, Optional, Union, Tuple
from pathlib import Path


class GroupExtractor:
    """Utility class for extracting variables from nested NetCDF groups."""
    
    @staticmethod
    def extract_variable_from_group(file_path: str, group_path: str, variable_name: str) -> Optional[np.ndarray]:
        """
        Extract a variable from a specific group path.
        
        Args:
            file_path: Path to the NetCDF file
            group_path: Path to the group (e.g., 'Stations/Betsizarai')
            variable_name: Name of the variable to extract
            
        Returns:
            numpy.ndarray: Variable data if found, None otherwise
        """
        try:
            with nc.Dataset(file_path, 'r') as ds:
                # Navigate to the group
                current_group = ds
                for group_name in group_path.split('/'):
                    if group_name in current_group.groups:
                        current_group = current_group.groups[group_name]
                    else:
                        print(f"❌ Group '{group_name}' not found in path '{group_path}'")
                        return None
                
                # Check if variable exists
                if variable_name not in current_group.variables:
                    print(f"❌ Variable '{variable_name}' not found in group '{group_path}'")
                    print(f"   Available variables: {list(current_group.variables.keys())}")
                    return None
                
                # Extract the variable
                variable = current_group.variables[variable_name]
                data = variable[:]  # Load all data
                
                print(f"✅ Successfully extracted '{variable_name}' from '{group_path}'")
                print(f"   Shape: {data.shape}")
                print(f"   Data type: {data.dtype}")
                
                return data
                
        except Exception as e:
            print(f"❌ Error extracting variable: {e}")
            return None
    
    @staticmethod
    def extract_variable_with_metadata(file_path: str, group_path: str, variable_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract a variable with its metadata from a specific group path.
        
        Args:
            file_path: Path to the NetCDF file
            group_path: Path to the group (e.g., 'Stations/Betsizarai')
            variable_name: Name of the variable to extract
            
        Returns:
            dict: Dictionary containing variable data and metadata, None if not found
        """
        try:
            with nc.Dataset(file_path, 'r') as ds:
                # Navigate to the group
                current_group = ds
                for group_name in group_path.split('/'):
                    if group_name in current_group.groups:
                        current_group = current_group.groups[group_name]
                    else:
                        print(f"❌ Group '{group_name}' not found in path '{group_path}'")
                        return None
                
                # Check if variable exists
                if variable_name not in current_group.variables:
                    print(f"❌ Variable '{variable_name}' not found in group '{group_path}'")
                    print(f"   Available variables: {list(current_group.variables.keys())}")
                    return None
                
                # Extract the variable and metadata
                variable = current_group.variables[variable_name]
                data = variable[:]
                
                # Get metadata
                metadata = {
                    'data': data,
                    'shape': data.shape,
                    'dtype': str(data.dtype),
                    'dimensions': variable.dimensions,
                    'attributes': {}
                }
                
                # Extract attributes
                for attr_name in variable.ncattrs():
                    try:
                        metadata['attributes'][attr_name] = variable.getncattr(attr_name)
                    except:
                        metadata['attributes'][attr_name] = "<error reading>"
                
                print(f"✅ Successfully extracted '{variable_name}' from '{group_path}' with metadata")
                print(f"   Shape: {metadata['shape']}")
                print(f"   Dimensions: {metadata['dimensions']}")
                print(f"   Attributes: {list(metadata['attributes'].keys())}")
                
                return metadata
                
        except Exception as e:
            print(f"❌ Error extracting variable with metadata: {e}")
            return None
    
    @staticmethod
    def extract_variable_as_xarray(file_path: str, group_path: str, variable_name: str) -> Optional[xr.DataArray]:
        """
        Extract a variable as an xarray DataArray from a specific group path.
        
        Args:
            file_path: Path to the NetCDF file
            group_path: Path to the group (e.g., 'Stations/Betsizarai')
            variable_name: Name of the variable to extract
            
        Returns:
            xarray.DataArray: Variable data as DataArray if found, None otherwise
        """
        try:
            with nc.Dataset(file_path, 'r') as ds:
                # Navigate to the group
                current_group = ds
                for group_name in group_path.split('/'):
                    if group_name in current_group.groups:
                        current_group = current_group.groups[group_name]
                    else:
                        print(f"❌ Group '{group_name}' not found in path '{group_path}'")
                        return None
                
                # Check if variable exists
                if variable_name not in current_group.variables:
                    print(f"❌ Variable '{variable_name}' not found in group '{group_path}'")
                    print(f"   Available variables: {list(current_group.variables.keys())}")
                    return None
                
                # Extract the variable
                variable = current_group.variables[variable_name]
                data = variable[:]
                
                # Create xarray DataArray
                coords = {}
                for dim_name in variable.dimensions:
                    if dim_name in current_group.dimensions:
                        dim_size = len(current_group.dimensions[dim_name])
                        coords[dim_name] = np.arange(dim_size)
                
                # Create DataArray
                da = xr.DataArray(
                    data=data,
                    coords=coords,
                    dims=variable.dimensions,
                    name=variable_name,
                    attrs={attr: variable.getncattr(attr) for attr in variable.ncattrs()}
                )
                
                print(f"✅ Successfully extracted '{variable_name}' from '{group_path}' as xarray DataArray")
                print(f"   Shape: {da.shape}")
                print(f"   Dimensions: {da.dims}")
                print(f"   Coordinates: {list(da.coords.keys())}")
                
                return da
                
        except Exception as e:
            print(f"❌ Error extracting variable as xarray: {e}")
            return None
    
    @staticmethod
    def list_variables_in_group(file_path: str, group_path: str) -> Optional[Dict[str, Any]]:
        """
        List all variables in a specific group with their metadata.
        
        Args:
            file_path: Path to the NetCDF file
            group_path: Path to the group (e.g., 'Stations/Betsizarai')
            
        Returns:
            dict: Dictionary containing variable information, None if group not found
        """
        try:
            with nc.Dataset(file_path, 'r') as ds:
                # Navigate to the group
                current_group = ds
                for group_name in group_path.split('/'):
                    if group_name in current_group.groups:
                        current_group = current_group.groups[group_name]
                    else:
                        print(f"❌ Group '{group_name}' not found in path '{group_path}'")
                        return None
                
                # Get variable information
                variables_info = {}
                for var_name, var in current_group.variables.items():
                    variables_info[var_name] = {
                        'shape': var.shape,
                        'dtype': str(var.dtype),
                        'dimensions': var.dimensions,
                        'size': var.size,
                        'attributes': {attr: var.getncattr(attr) for attr in var.ncattrs()}
                    }
                
                print(f"✅ Found {len(variables_info)} variables in group '{group_path}'")
                return variables_info
                
        except Exception as e:
            print(f"❌ Error listing variables: {e}")
            return None


def extract_swd_from_betsizarai(file_path: str = 'data/20250816.nc') -> Optional[np.ndarray]:
    """
    Convenience function to extract SWD variable from Betsizarai group.
    
    Args:
        file_path: Path to the NetCDF file
        
    Returns:
        numpy.ndarray: SWD data if found, None otherwise
    """
    return GroupExtractor.extract_variable_from_group(
        file_path, 'Stations/Betsizarai', 'SWD'
    )


def extract_swd_as_xarray(file_path: str = 'data/20250816.nc') -> Optional[xr.DataArray]:
    """
    Convenience function to extract SWD variable as xarray DataArray from Betsizarai group.
    
    Args:
        file_path: Path to the NetCDF file
        
    Returns:
        xarray.DataArray: SWD data as DataArray if found, None otherwise
    """
    return GroupExtractor.extract_variable_as_xarray(
        file_path, 'Stations/Betsizarai', 'SWD'
    )


if __name__ == "__main__":
    # Example usage
    file_path = 'data/20250816.nc'
    
    print("🔍 Extracting SWD from Betsizarai group...")
    print("=" * 50)
    
    # Method 1: Extract as numpy array
    print("\n1️⃣ Extract as numpy array:")
    swd_data = extract_swd_from_betsizarai(file_path)
    if swd_data is not None:
        print(f"   Data shape: {swd_data.shape}")
        print(f"   First 5 values: {swd_data[:5]}")
    
    # Method 2: Extract with metadata
    print("\n2️⃣ Extract with metadata:")
    swd_meta = GroupExtractor.extract_variable_with_metadata(
        file_path, 'Stations/Betsizarai', 'SWD'
    )
    if swd_meta:
        print(f"   Units: {swd_meta['attributes'].get('units', 'N/A')}")
        print(f"   Comment: {swd_meta['attributes'].get('comment', 'N/A')}")
    
    # Method 3: Extract as xarray DataArray
    print("\n3️⃣ Extract as xarray DataArray:")
    swd_xr = extract_swd_as_xarray(file_path)
    if swd_xr is not None:
        print(f"   DataArray shape: {swd_xr.shape}")
        print(f"   Coordinates: {list(swd_xr.coords.keys())}")
    
    # Method 4: List all variables in Betsizarai
    print("\n4️⃣ List all variables in Betsizarai:")
    variables = GroupExtractor.list_variables_in_group(file_path, 'Stations/Betsizarai')
    if variables:
        print(f"   Total variables: {len(variables)}")
        print(f"   Variable names: {list(variables.keys())[:10]}...")
