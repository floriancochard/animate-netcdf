#!/usr/bin/env python3
"""
Script to explore the ERA5 file structure to understand data organization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import netCDF4 as nc
import xarray as xr
from pathlib import Path

def explore_era5_structure(file_path: str):
    """Explore the structure of an ERA5 file in detail."""
    print(f"\n{'='*80}")
    print(f"Exploring ERA5 file: {Path(file_path).name}")
    print(f"{'='*80}")
    
    try:
        with nc.Dataset(file_path, 'r') as ds:
            print(f"File format: {ds.data_model}")
            print(f"Root dimensions: {dict(ds.dimensions)}")
            print(f"Root variables: {list(ds.variables.keys())}")
            
            # Check each variable in detail
            for var_name, var in ds.variables.items():
                print(f"\nVariable: {var_name}")
                print(f"  Dimensions: {var.dims}")
                print(f"  Shape: {var.shape}")
                print(f"  Data type: {var.dtype}")
                print(f"  Attributes: {dict(var.ncattrs())}")
                
                # Show first few values for time variables
                if 'time' in var_name.lower():
                    try:
                        values = var[:]
                        print(f"  First 5 values: {values[:5]}")
                        if len(values) > 0:
                            print(f"  Last 5 values: {values[-5:]}")
                    except Exception as e:
                        print(f"  Error reading values: {e}")
                
                # Show first few values for data variables
                if var_name == 'ssrd':
                    try:
                        values = var[:]
                        print(f"  First 5 values: {values[:5]}")
                        if len(values) > 0:
                            print(f"  Last 5 values: {values[-5:]}")
                        print(f"  Min/Max: {values.min():.2f} / {values.max():.2f}")
                    except Exception as e:
                        print(f"  Error reading values: {e}")
                        
    except Exception as e:
        print(f"Error exploring file: {e}")

def main():
    """Main function to explore ERA5 file."""
    data_dir = Path(__file__).parent.parent / "data"
    era5_file = data_dir / "era5_mahambo_1508_1608.nc"
    
    if era5_file.exists():
        explore_era5_structure(str(era5_file))
    else:
        print(f"File not found: {era5_file}")

if __name__ == "__main__":
    main()
