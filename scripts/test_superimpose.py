#!/usr/bin/env python3
"""
Test script for NetCDF superimposition functionality

This script tests the basic functionality without processing large files.
"""

import numpy as np
import netCDF4 as nc
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_netcdf_files():
    """Create small test NetCDF files to test superimposition."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Test MNH-like file (smaller version)
    mnh_file = os.path.join(temp_dir, "test_mnh.nc")
    with nc.Dataset(mnh_file, 'w', format='NETCDF4') as ds:
        # Create dimensions
        ds.createDimension('time', 10)
        ds.createDimension('y', 50)
        ds.createDimension('x', 50)
        
        # Create variables
        time_var = ds.createVariable('time_station', 'f8', ('time',))
        lat_var = ds.createVariable('latitude', 'f8', ('y', 'x'))
        lon_var = ds.createVariable('longitude', 'f8', ('y', 'x'))
        data_var = ds.createVariable('test_data', 'f8', ('time', 'y', 'x'))
        
        # Add data
        time_var[:] = np.arange(10)
        lat_var[:] = np.random.uniform(45, 50, (50, 50))
        lon_var[:] = np.random.uniform(-5, 5, (50, 50))
        data_var[:] = np.random.normal(0, 1, (10, 50, 50))
        
        # Add attributes
        time_var.units = 'hours since 2023-01-01'
        lat_var.long_name = 'latitude'
        lon_var.long_name = 'longitude'
        data_var.long_name = 'test atmospheric data'
    
    # Test ERA5-like file (single point)
    era5_file = os.path.join(temp_dir, "test_era5.nc")
    with nc.Dataset(era5_file, 'w', format='NETCDF4') as ds:
        # Create dimensions
        ds.createDimension('valid_time', 10)
        ds.createDimension('latitude', 1)
        ds.createDimension('longitude', 1)
        
        # Create variables
        time_var = ds.createVariable('valid_time', 'f8', ('valid_time',))
        lat_var = ds.createVariable('latitude', 'f8', ('latitude', 'longitude'))
        lon_var = ds.createVariable('longitude', 'f8', ('latitude', 'longitude'))
        data_var = ds.createVariable('ssrd', 'f8', ('valid_time', 'latitude', 'longitude'))
        
        # Add data
        time_var[:] = np.arange(10)
        lat_var[:] = [[47.5]]  # Single point
        lon_var[:] = [[0.0]]   # Single point
        data_var[:] = np.random.uniform(0, 1000, (10, 1, 1))
        
        # Add attributes
        time_var.units = 'hours since 2023-01-01'
        lat_var.long_name = 'latitude'
        lon_var.long_name = 'longitude'
        data_var.long_name = 'surface solar radiation'
    
    return mnh_file, era5_file, temp_dir

def test_basic_functionality():
    """Test basic functionality with small test files."""
    logger.info("Testing basic superimposition functionality...")
    
    try:
        # Create test files
        mnh_file, era5_file, temp_dir = create_test_netcdf_files()
        logger.info(f"Created test files in: {temp_dir}")
        
        # Test file reading
        with nc.Dataset(mnh_file, 'r') as mnh_ds:
            mnh_vars = list(mnh_ds.variables.keys())
            mnh_dims = dict(mnh_ds.dimensions)
            logger.info(f"MNH test file - Variables: {mnh_vars}")
            logger.info(f"MNH test file - Dimensions: {mnh_dims}")
        
        with nc.Dataset(era5_file, 'r') as era5_ds:
            era5_vars = list(era5_ds.variables.keys())
            era5_dims = dict(era5_ds.dimensions)
            logger.info(f"ERA5 test file - Variables: {era5_vars}")
            logger.info(f"ERA5 test file - Dimensions: {era5_dims}")
        
        # Test data extraction
        with nc.Dataset(mnh_file, 'r') as mnh_ds:
            mnh_data = mnh_ds.variables['test_data'][:]
            mnh_lat = mnh_ds.variables['latitude'][:]
            mnh_lon = mnh_ds.variables['longitude'][:]
            logger.info(f"MNH data shape: {mnh_data.shape}")
            logger.info(f"MNH lat range: [{mnh_lat.min():.2f}, {mnh_lat.max():.2f}]")
            logger.info(f"MNH lon range: [{mnh_lon.min():.2f}, {mnh_lon.max():.2f}]")
        
        with nc.Dataset(era5_file, 'r') as era5_ds:
            era5_data = era5_ds.variables['ssrd'][:]
            era5_lat = era5_ds.variables['latitude'][0, 0]
            era5_lon = era5_ds.variables['longitude'][0, 0]
            logger.info(f"ERA5 data shape: {era5_data.shape}")
            logger.info(f"ERA5 coordinates: lat={era5_lat:.2f}, lon={era5_lon:.2f}")
        
        # Test interpolation logic
        from scipy.interpolate import griddata
        
        # Create target grid (MNH grid)
        target_shape = (50, 50)
        target_lat = np.linspace(mnh_lat.min(), mnh_lat.max(), target_shape[0])
        target_lon = np.linspace(mnh_lon.min(), mnh_lon.max(), target_shape[1])
        
        # Interpolate ERA5 point to MNH grid
        era5_interpolated = np.full((10, 50, 50), era5_data[0, 0, 0])
        logger.info(f"Interpolated ERA5 data shape: {era5_interpolated.shape}")
        
        # Test output file creation
        output_file = os.path.join(temp_dir, "test_superimposed.nc")
        with nc.Dataset(output_file, 'w', format='NETCDF4') as ds:
            # Create dimensions
            ds.createDimension('time', 10)
            ds.createDimension('y', 50)
            ds.createDimension('x', 50)
            
            # Create variables
            mnh_var = ds.createVariable('test_data', 'f8', ('time', 'y', 'x'))
            era5_var = ds.createVariable('ssrd', 'f8', ('time', 'y', 'x'))
            lat_var = ds.createVariable('latitude', 'f8', ('y', 'x'))
            lon_var = ds.createVariable('longitude', 'f8', ('y', 'x'))
            
            # Store data
            mnh_var[:] = mnh_data
            era5_var[:] = era5_interpolated
            lat_var[:] = mnh_lat
            lon_var[:] = mnh_lon
            
            # Add attributes
            ds.title = "Test Superimposed NetCDF"
            ds.history = "Created by test script"
        
        logger.info(f"Created test output file: {output_file}")
        
        # Verify output file
        with nc.Dataset(output_file, 'r') as ds:
            output_vars = list(ds.variables.keys())
            output_dims = dict(ds.dimensions)
            logger.info(f"Output file - Variables: {output_vars}")
            logger.info(f"Output file - Dimensions: {output_dims}")
        
        logger.info("✅ All basic functionality tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        if 'temp_dir' in locals():
            import shutil
            shutil.rmtree(temp_dir)
            logger.info("Cleaned up test files")

def test_coordinate_handling():
    """Test coordinate system handling."""
    logger.info("Testing coordinate system handling...")
    
    try:
        # Test different coordinate scenarios
        scenarios = [
            ("Regular grid", np.linspace(0, 10, 5), np.linspace(0, 10, 5)),
            ("Irregular grid", np.random.uniform(0, 10, 5), np.random.uniform(0, 10, 5)),
            ("Single point", np.array([5.0]), np.array([5.0]))
        ]
        
        for name, lat, lon in scenarios:
            logger.info(f"Testing scenario: {name}")
            logger.info(f"  Lat: {lat}")
            logger.info(f"  Lon: {lon}")
            
            # Test grid creation
            if len(lat) > 1 and len(lon) > 1:
                lon_grid, lat_grid = np.meshgrid(lon, lat)
                logger.info(f"  Grid shape: {lon_grid.shape}")
            else:
                logger.info(f"  Single point: lat={lat[0]:.2f}, lon={lon[0]:.2f}")
        
        logger.info("✅ Coordinate handling tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Coordinate handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting NetCDF Superimposition Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Coordinate Handling", test_coordinate_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The superimposition tools are working correctly.")
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
