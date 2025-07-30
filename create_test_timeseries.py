#!/usr/bin/env python3
"""
Create a test NetCDF file with multiple time steps for animation testing.
"""

import xarray as xr
import numpy as np
import pandas as pd

def create_test_timeseries():
    """Create a test NetCDF file with multiple time steps."""
    
    # Create time dimension with multiple time points
    times = pd.date_range('2023-04-19T14:00:00', '2023-04-19T15:00:00', freq='5min')
    
    # Create spatial dimensions
    lats = np.linspace(48.49, 48.94, 100)
    lons = np.linspace(1.86, 2.54, 100)
    levels = np.linspace(5, 15118, 10)  # Reduced levels for testing
    
    # Create coordinates
    coords = {
        'time': times,
        'level': levels,
        'lat': lats,
        'lon': lons
    }
    
    # Create a moving pattern for SWD (solar radiation)
    data_vars = {}
    
    # Create SWD with a moving pattern
    swd_data = np.zeros((len(times), len(levels), len(lats), len(lons)))
    
    for t, time in enumerate(times):
        # Create a moving circular pattern
        center_lat = 48.7 + 0.1 * np.sin(2 * np.pi * t / len(times))
        center_lon = 2.2 + 0.2 * np.cos(2 * np.pi * t / len(times))
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                # Distance from center
                dist = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
                
                # Create a Gaussian pattern that moves
                intensity = 1000 * np.exp(-dist**2 / 0.01) * (1 + 0.5 * np.sin(2 * np.pi * t / len(times)))
                
                # Add some variation with level
                for k, level in enumerate(levels):
                    level_factor = 1 - (level / levels[-1]) * 0.5  # Decrease with height
                    swd_data[t, k, i, j] = intensity * level_factor
    
    # Create CLDFR (cloud fraction) with complementary pattern
    cldfr_data = np.zeros((len(times), len(levels), len(lats), len(lons)))
    
    for t, time in enumerate(times):
        # Inverse pattern to SWD
        center_lat = 48.7 + 0.1 * np.sin(2 * np.pi * t / len(times) + np.pi)
        center_lon = 2.2 + 0.2 * np.cos(2 * np.pi * t / len(times) + np.pi)
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                dist = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
                intensity = 0.8 * np.exp(-dist**2 / 0.02) * (1 + 0.3 * np.sin(2 * np.pi * t / len(times) + np.pi))
                
                for k, level in enumerate(levels):
                    level_factor = 1 - (level / levels[-1]) * 0.3
                    cldfr_data[t, k, i, j] = min(1.0, intensity * level_factor)
    
    # Create the dataset
    ds = xr.Dataset(
        {
            'SWD': xr.DataArray(
                swd_data,
                dims=['time', 'level', 'lat', 'lon'],
                coords=coords,
                attrs={'units': 'W m-2', 'long_name': 'Shortwave Downward Radiation'}
            ),
            'CLDFR': xr.DataArray(
                cldfr_data,
                dims=['time', 'level', 'lat', 'lon'],
                coords=coords,
                attrs={'units': '1', 'long_name': 'Cloud Fraction'}
            )
        },
        coords=coords
    )
    
    # Add attributes
    ds.time.attrs = {'long_name': 'time axis', 'standard_name': 'time', 'axis': 'T'}
    ds.lat.attrs = {'long_name': 'latitude', 'standard_name': 'latitude', 'units': 'degrees_north'}
    ds.lon.attrs = {'long_name': 'longitude', 'standard_name': 'longitude', 'units': 'degrees_east'}
    ds.level.attrs = {'long_name': 'vertical level', 'units': 'm'}
    
    return ds

if __name__ == "__main__":
    print("Creating test NetCDF file with multiple time steps...")
    
    ds = create_test_timeseries()
    
    # Save to file
    output_file = "test-timeseries.nc"
    ds.to_netcdf(output_file)
    
    print(f"✅ Created {output_file}")
    print(f"📊 Dataset info:")
    print(f"  Time steps: {len(ds.time)}")
    print(f"  Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
    print(f"  Variables: {list(ds.data_vars.keys())}")
    print(f"  Dimensions: {dict(ds.dims)}")
    
    ds.close() 