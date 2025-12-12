#!/usr/bin/env python3
"""
Script to explore the actual structure of MNH files to understand data organization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import netCDF4 as nc
import xarray as xr
from pathlib import Path

def explore_mnh_structure(file_path: str):
    """Explore the structure of an MNH file in detail."""
    print(f"\n{'='*80}")
    print(f"Exploring MNH file: {Path(file_path).name}")
    print(f"{'='*80}")
    
    try:
        with nc.Dataset(file_path, 'r') as ds:
            print(f"File format: {ds.data_model}")
            print(f"Root dimensions: {dict(ds.dimensions)}")
            print(f"Root variables: {list(ds.variables.keys())}")
            print(f"Root groups: {list(ds.groups.keys())}")
            
            # Explore Stations group
            if 'Stations' in ds.groups:
                stations = ds.groups['Stations']
                print(f"\nStations group dimensions: {dict(stations.dimensions)}")
                print(f"Stations group variables: {list(stations.variables.keys())}")
                print(f"Stations subgroups: {list(stations.groups.keys())}")
                
                # Explore Mahambo subgroup
                if 'Mahambo' in stations.groups:
                    mahambo = stations.groups['Mahambo']
                    print(f"\nMahambo group dimensions: {dict(mahambo.dimensions)}")
                    print(f"Mahambo group variables: {list(mahambo.variables.keys())}")
                    
                    # Look for time-related variables
                    time_vars = []
                    for var_name, var in mahambo.variables.items():
                        if 'time' in var_name.lower() or 'time' in str(var.dims).lower():
                            time_vars.append(var_name)
                            print(f"\nTime variable: {var_name}")
                            print(f"  Dimensions: {var.dims}")
                            print(f"  Shape: {var.shape}")
                            print(f"  Attributes: {dict(var.ncattrs())}")
                    
                    if not time_vars:
                        print("\nNo time variables found in Mahambo group")
                        print("Checking if time is inherited from parent groups...")
                        
                        # Check if time is in Stations group
                        for var_name, var in stations.variables.items():
                            if 'time' in var_name.lower() or 'time' in str(var.dims).lower():
                                print(f"\nTime variable in Stations group: {var_name}")
                                print(f"  Dimensions: {var.dims}")
                                print(f"  Shape: {var.shape}")
                                print(f"  Attributes: {dict(var.ncattrs())}")
                
                # Check other station groups
                for station_name in ['Betsizarai', 'Anosibe']:
                    if station_name in stations.groups:
                        station = stations.groups[station_name]
                        print(f"\n{station_name} group dimensions: {dict(station.dimensions)}")
                        print(f"{station_name} group variables: {list(station.variables.keys())}")
                        
                        # Look for time variables
                        for var_name, var in station.variables.items():
                            if 'time' in var_name.lower() or 'time' in str(var.dims).lower():
                                print(f"  Time variable: {var_name} - {var.dims} - {var.shape}")
            
            # Check root level for time variables
            print(f"\nRoot level time variables:")
            for var_name, var in ds.variables.items():
                if 'time' in var_name.lower() or 'time' in str(var.dims).lower():
                    print(f"  {var_name}: {var.dims} - {var.shape}")
                    print(f"    Attributes: {dict(var.ncattrs())}")
                    
    except Exception as e:
        print(f"Error exploring file: {e}")

def main():
    """Main function to explore MNH files."""
    data_dir = Path(__file__).parent.parent / "data"
    
    mnh_files = [
        data_dir / "mnh_1508.nc",
        data_dir / "mnh_1608.nc"
    ]
    
    for mnh_file in mnh_files:
        if mnh_file.exists():
            explore_mnh_structure(str(mnh_file))
        else:
            print(f"File not found: {mnh_file}")

if __name__ == "__main__":
    main()
