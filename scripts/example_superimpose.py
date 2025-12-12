#!/usr/bin/env python3
"""
Example script demonstrating NetCDF superimposition

This script shows how to use the superimposition tools with your MNH and ERA5 data.
"""

import os
import sys
import subprocess

def run_superimposition():
    """Run the MNH-ERA5 superimposition example."""
    
    # File paths
    mnh_file = "data/mnh_1508.nc"
    era5_file = "data/era5_mahambo_1508_1608.nc"
    output_file = "data/output/superimposed_mnh_era5.nc"
    
    # Check if files exist
    if not os.path.exists(mnh_file):
        print(f"Error: MNH file not found: {mnh_file}")
        return False
    
    if not os.path.exists(era5_file):
        print(f"Error: ERA5 file not found: {era5_file}")
        return False
    
    # Create output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("Starting MNH-ERA5 superimposition...")
    print(f"MNH file: {mnh_file}")
    print(f"ERA5 file: {era5_file}")
    print(f"Output: {output_file}")
    print()
    
    # Run the specialized MNH-ERA5 superimposer
    cmd = [
        sys.executable, "scripts/superimpose_mnh_era5.py",
        "--mnh-file", mnh_file,
        "--era5-file", era5_file,
        "--output", output_file,
        "--verbose"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Superimposition completed successfully!")
        print("Output:", output_file)
        
        # Check if visualization was created
        viz_file = output_file.replace('.nc', '.png')
        if os.path.exists(viz_file):
            print("Visualization:", viz_file)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running superimposition: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def explore_netcdf_files():
    """Explore the structure of the NetCDF files."""
    print("=== Exploring NetCDF File Structures ===")
    
    # MNH file structure
    print("\n1. MNH File (mnh_1508.nc):")
    print("   - High-resolution 3D atmospheric model")
    print("   - Grid: 402 x 402 x 52 levels")
    print("   - Contains: temperature, wind, pressure, etc.")
    print("   - Time dimension: 289 time steps")
    
    # ERA5 file structure
    print("\n2. ERA5 File (era5_mahambo_1508_1608.nc):")
    print("   - Single-point time series data")
    print("   - Grid: 1 x 1 point")
    print("   - Contains: surface solar radiation (ssrd)")
    print("   - Time dimension: 48 time steps")
    
    print("\n3. Superimposition Strategy:")
    print("   - Interpolate ERA5 point data to MNH grid")
    print("   - Align time dimensions")
    print("   - Create comparison visualizations")
    print("   - Save as unified NetCDF file")

def main():
    """Main function."""
    print("NetCDF Superimposition Example")
    print("=" * 40)
    
    # Explore file structures
    explore_netcdf_files()
    
    print("\n" + "=" * 40)
    
    # Run superimposition
    success = run_superimposition()
    
    if success:
        print("\n✅ Superimposition completed successfully!")
        print("\nNext steps:")
        print("1. Examine the output NetCDF file")
        print("2. View the generated visualization")
        print("3. Analyze the differences between MNH and ERA5 data")
        print("4. Modify the script to compare different variables")
    else:
        print("\n❌ Superimposition failed!")
        print("Check the error messages above for troubleshooting.")

if __name__ == '__main__':
    main()
