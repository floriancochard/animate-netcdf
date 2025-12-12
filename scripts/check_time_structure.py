#!/usr/bin/env python3
"""
Script to check and compare time structure of ERA5 and MNH NetCDF files
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import netCDF4 as nc
import xarray as xr
import pandas as pd
from pathlib import Path
from animate_netcdf.utils.netcdf_explorer import NetCDFExplorer

def examine_time_structure(file_path: str) -> dict:
    """
    Examine the time structure of a NetCDF file.
    
    Args:
        file_path: Path to the NetCDF file
        
    Returns:
        Dictionary containing time structure information
    """
    print(f"\n{'='*60}")
    print(f"Examining time structure: {Path(file_path).name}")
    print(f"{'='*60}")
    
    try:
        # Use xarray for easier time handling
        ds = xr.open_dataset(file_path)
        
        time_info = {
            'file_path': str(file_path),
            'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
            'time_variables': {},
            'time_dimensions': {},
            'time_attributes': {}
        }
        
        # Check for time-related variables
        for var_name, var in ds.variables.items():
            if 'time' in var_name.lower() or 'time' in str(var.dims).lower():
                time_info['time_variables'][var_name] = {
                    'dimensions': list(var.dims),
                    'shape': var.shape,
                    'dtype': str(var.dtype),
                    'size': var.size,
                    'attributes': dict(var.attrs)
                }
                
                # Try to get actual time values if it's a time coordinate
                if 'time' in var_name.lower():
                    try:
                        if hasattr(var, 'values'):
                            time_values = var.values
                            if len(time_values) > 0:
                                time_info['time_variables'][var_name]['first_time'] = str(time_values[0])
                                time_info['time_variables'][var_name]['last_time'] = str(time_values[-1])
                                time_info['time_variables'][var_name]['total_timesteps'] = len(time_values)
                                
                                # Check if it's datetime-like
                                if hasattr(time_values[0], 'isoformat'):
                                    time_info['time_variables'][var_name]['is_datetime'] = True
                                    # Calculate time resolution
                                    if len(time_values) > 1:
                                        time_diff = time_values[1] - time_values[0]
                                        time_info['time_variables'][var_name]['time_resolution'] = str(time_diff)
                                else:
                                    time_info['time_variables'][var_name]['is_datetime'] = False
                    except Exception as e:
                        time_info['time_variables'][var_name]['time_processing_error'] = str(e)
        
        # Check time dimensions
        for dim_name, dim_size in ds.dims.items():
            if 'time' in dim_name.lower():
                time_info['time_dimensions'][dim_name] = {
                    'size': dim_size,
                    'is_unlimited': ds.dims[dim_name] is None
                }
        
        # Print summary
        print(f"File size: {time_info['file_size_mb']:.2f} MB")
        print(f"Time variables found: {len(time_info['time_variables'])}")
        print(f"Time dimensions found: {len(time_info['time_dimensions'])}")
        
        if time_info['time_variables']:
            print("\nTime Variables:")
            for var_name, var_info in time_info['time_variables'].items():
                print(f"  {var_name}:")
                print(f"    Shape: {var_info['shape']}")
                print(f"    Size: {var_info['size']}")
                if 'total_timesteps' in var_info:
                    print(f"    Timesteps: {var_info['total_timesteps']}")
                if 'first_time' in var_info:
                    print(f"    First: {var_info['first_time']}")
                if 'last_time' in var_info:
                    print(f"    Last: {var_info['last_time']}")
                if 'time_resolution' in var_info:
                    print(f"    Resolution: {var_info['time_resolution']}")
        
        if time_info['time_dimensions']:
            print("\nTime Dimensions:")
            for dim_name, dim_info in time_info['time_dimensions'].items():
                print(f"  {dim_name}: {dim_info['size']} (unlimited: {dim_info['is_unlimited']})")
        
        # Try to get overall time range
        try:
            if 'time' in ds.coords:
                time_coord = ds.coords['time']
                if hasattr(time_coord, 'values') and len(time_coord.values) > 0:
                    print(f"\nOverall Time Range:")
                    print(f"  Start: {time_coord.values[0]}")
                    print(f"  End: {time_coord.values[-1]}")
                    print(f"  Duration: {time_coord.values[-1] - time_coord.values[0]}")
                    print(f"  Total steps: {len(time_coord.values)}")
        except Exception as e:
            print(f"Could not determine overall time range: {e}")
        
        ds.close()
        return time_info
        
    except Exception as e:
        print(f"Error examining file: {e}")
        return {'error': str(e)}

def compare_time_structures(file_paths: list) -> dict:
    """
    Compare time structures across multiple files.
    
    Args:
        file_paths: List of file paths to compare
        
    Returns:
        Dictionary containing comparison information
    """
    print(f"\n{'='*80}")
    print("TIME STRUCTURE COMPARISON")
    print(f"{'='*80}")
    
    results = {}
    for file_path in file_paths:
        results[Path(file_path).name] = examine_time_structure(file_path)
    
    # Find common time patterns
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    successful_results = {k: v for k, v in results.items() if 'error' not in v}
    
    if len(successful_results) > 1:
        # Compare time dimensions
        time_dims = {}
        for name, result in successful_results.items():
            time_dims[name] = set(result.get('time_dimensions', {}).keys())
        
        print("\nTime Dimensions Comparison:")
        for name, dims in time_dims.items():
            print(f"  {name}: {dims}")
        
        # Compare time variable counts
        time_var_counts = {}
        for name, result in successful_results.items():
            time_var_counts[name] = len(result.get('time_variables', {}))
        
        print("\nTime Variables Count:")
        for name, count in time_var_counts.items():
            print(f"  {name}: {count}")
        
        # Check for common time variables
        all_time_vars = []
        for result in successful_results.values():
            all_time_vars.append(set(result.get('time_variables', {}).keys()))
        
        if all_time_vars:
            common_time_vars = set.intersection(*all_time_vars)
            print(f"\nCommon Time Variables: {common_time_vars}")
    
    return results

def main():
    """Main function to examine ERA5 and MNH files."""
    # Define file paths
    data_dir = Path(__file__).parent.parent / "data"
    era5_file = data_dir / "era5_mahambo_1508_1608.nc"
    mnh_1508_file = data_dir / "mnh_1508.nc"
    mnh_1608_file = data_dir / "mnh_1608.nc"
    
    files_to_examine = []
    
    if era5_file.exists():
        files_to_examine.append(str(era5_file))
    else:
        print(f"ERA5 file not found: {era5_file}")
    
    if mnh_1508_file.exists():
        files_to_examine.append(str(mnh_1508_file))
    else:
        print(f"MNH 1508 file not found: {mnh_1508_file}")
    
    if mnh_1608_file.exists():
        files_to_examine.append(str(mnh_1608_file))
    else:
        print(f"MNH 1608 file not found: {mnh_1608_file}")
    
    if not files_to_examine:
        print("No files found to examine!")
        return
    
    print(f"Found {len(files_to_examine)} files to examine:")
    for f in files_to_examine:
        print(f"  - {Path(f).name}")
    
    # Examine each file individually
    results = {}
    for file_path in files_to_examine:
        results[Path(file_path).name] = examine_time_structure(file_path)
    
    # Compare structures
    if len(files_to_examine) > 1:
        compare_time_structures(files_to_examine)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
