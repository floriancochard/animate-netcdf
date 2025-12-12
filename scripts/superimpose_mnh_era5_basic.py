#!/usr/bin/env python3
"""
Basic MNH vs ERA5 NetCDF Superimposition Tool (Full Range)

This script properly handles the complete MNH dataset with 5-minute timesteps:
- MNH: SWD variable in Stations.Mahambo group (289 timesteps, 5-min intervals, 24-hour cycle)
- ERA5: ssrd variable (48 time steps, hourly) in J m⁻² (accumulated energy)

Key features:
1. Extract FULL MNH dataset (all 289 timesteps, 0-800+ W m⁻² range)
2. Simple time alignment without complex datetime handling
3. Convert ERA5 from J m⁻² to W m⁻² correctly
4. Basic NetCDF output preserving full MNH range

Usage:
    python superimpose_mnh_era5_basic.py mnh_file.nc era5_file.nc --output output.nc
"""

import argparse
import numpy as np
import netCDF4 as nc
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasicMNHERA5Superimposer:
    """Basic class to handle superimposition of MNH vs ERA5 preserving full MNH data range."""
    
    def __init__(self, mnh_file_path: str, era5_file_path: str):
        """Initialize with MNH and ERA5 NetCDF file paths."""
        self.mnh_file_path = mnh_file_path
        self.era5_file_path = era5_file_path
        self.mnh_file = None
        self.era5_file = None
        
    def __enter__(self):
        """Context manager entry."""
        self.mnh_file = nc.Dataset(self.mnh_file_path, 'r')
        self.era5_file = nc.Dataset(self.era5_file_path, 'r')
        logger.info(f"Opened MNH file: {self.mnh_file_path}")
        logger.info(f"Opened ERA5 file: {self.era5_file_path}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.mnh_file:
            self.mnh_file.close()
        if self.era5_file:
            self.era5_file.close()
    
    def extract_complete_mnh_swd(self) -> tuple:
        """Extract COMPLETE SWD variable from MNH file with proper timestep analysis."""
        try:
            # Navigate to Stations.Mahambo group
            mahambo_group = self.mnh_file.groups['Stations'].groups['Mahambo']
            
            # Extract SWD variable - ALL data
            swd_var = mahambo_group.variables['SWD']
            swd_data = swd_var[:]
            
            # Extract time information
            time_var = self.mnh_file.variables['time_station']
            time_data = time_var[:]
            
            # Analyze timestep structure
            if len(time_data) > 1:
                time_diffs = np.diff(time_data)
                timestep_seconds = float(time_diffs[0])  # Assume constant timestep
                total_duration_hours = (time_data[-1] - time_data[0]) / 3600.0
            else:
                timestep_seconds = 300.0  # Default 5 minutes
                total_duration_hours = 24.0
            
            logger.info(f"=== MNH COMPLETE DATA ANALYSIS ===")
            logger.info(f"MNH SWD data shape: {swd_data.shape}")
            logger.info(f"MNH SWD units: {getattr(swd_var, 'units', 'No units')}")
            logger.info(f"MNH SWD long_name: {getattr(swd_var, 'long_name', 'No description')}")
            logger.info(f"MNH time data shape: {time_data.shape}")
            logger.info(f"MNH time units: {getattr(time_var, 'units', 'No units')}")
            logger.info(f"MNH timestep: {timestep_seconds} seconds ({timestep_seconds/60:.1f} minutes)")
            logger.info(f"MNH total duration: {total_duration_hours:.1f} hours")
            logger.info(f"MNH SWD full range: {np.nanmin(swd_data):.2f} to {np.nanmax(swd_data):.2f} W m⁻²")
            logger.info(f"MNH SWD non-zero count: {np.sum(swd_data > 0)} out of {len(swd_data)}")
            logger.info(f"MNH SWD max non-zero value: {np.max(swd_data[swd_data > 0]) if np.any(swd_data > 0) else 0:.2f} W m⁻²")
            
            return swd_data, time_data, timestep_seconds
            
        except KeyError as e:
            logger.error(f"Could not find required variable/group in MNH file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting MNH SWD data: {e}")
            raise
    
    def extract_era5_ssrd(self) -> tuple:
        """Extract ssrd variable from ERA5 file and convert to W m⁻²."""
        try:
            # Extract ssrd variable
            ssrd_var = self.era5_file.variables['ssrd']
            ssrd_data = ssrd_var[:, 0, 0]  # Remove spatial dimensions
            
            # Extract time information
            time_var = self.era5_file.variables['valid_time']
            time_data = time_var[:]
            
            # Check units and determine time resolution
            units = getattr(ssrd_var, 'units', 'unknown')
            logger.info(f"=== ERA5 DATA ANALYSIS ===")
            logger.info(f"ERA5 ssrd units: {units}")
            logger.info(f"ERA5 ssrd data shape: {ssrd_data.shape}")
            logger.info(f"ERA5 time data shape: {time_data.shape}")
            logger.info(f"ERA5 time units: {getattr(time_var, 'units', 'No units')}")
            
            # Determine time resolution by checking time differences
            if len(time_data) > 1:
                time_diffs = np.diff(time_data)
                time_resolution_seconds = float(time_diffs[0])  # Assume constant resolution
                total_duration_hours = (time_data[-1] - time_data[0]) / 3600.0
                logger.info(f"ERA5 time resolution: {time_resolution_seconds} seconds ({time_resolution_seconds/3600:.2f} hours)")
                logger.info(f"ERA5 total duration: {total_duration_hours:.1f} hours")
            else:
                time_resolution_seconds = 3600.0  # Default to 1 hour
                total_duration_hours = 24.0
                logger.warning("Could not determine time resolution, assuming 1 hour (3600 seconds)")
            
            # Convert from J m⁻² to W m⁻²
            if 'J m**-2' in units or 'J m-2' in units or 'J/m2' in units:
                logger.info(f"Converting ERA5 ssrd from J m⁻² to W m⁻² using {time_resolution_seconds} second time resolution")
                logger.info(f"Formula: W m⁻² = J m⁻² / {time_resolution_seconds} seconds")
                
                # Divide by time resolution to get average power
                ssrd_data = ssrd_data / time_resolution_seconds
                units = 'W m-2'
                
            elif 'W m**-2' in units or 'W m-2' in units or 'W/m2' in units:
                logger.info("ERA5 ssrd already in W m⁻², no conversion needed")
                time_resolution_seconds = 1.0  # No conversion factor needed
                
            else:
                logger.warning(f"Unknown ERA5 ssrd units: {units}, assuming J m⁻² and converting")
                ssrd_data = ssrd_data / time_resolution_seconds
                units = 'W m-2'
            
            logger.info(f"ERA5 ssrd converted units: {units}")
            logger.info(f"ERA5 ssrd value range: {np.nanmin(ssrd_data):.2f} to {np.nanmax(ssrd_data):.2f} W m⁻²")
            
            return ssrd_data, time_data, time_resolution_seconds
            
        except KeyError as e:
            logger.error(f"Could not find required variable in ERA5 file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting ERA5 ssrd data: {e}")
            raise
    
    def create_basic_netcdf(self, mnh_swd: np.ndarray, mnh_time: np.ndarray, 
                           era5_ssrd: np.ndarray, era5_time: np.ndarray,
                           output_path: str, mnh_timestep: float, era5_timestep: float) -> str:
        """Create a basic NetCDF file with both datasets side by side."""
        logger.info(f"Creating basic NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        output_file.createDimension('mnh_time', len(mnh_time))
        output_file.createDimension('era5_time', len(era5_time))
        
        # Create MNH variables
        mnh_time_var = output_file.createVariable('mnh_time', 'f8', ('mnh_time',))
        mnh_time_var.units = getattr(self.mnh_file.variables['time_station'], 'units', 'seconds')
        mnh_time_var.long_name = 'MNH time axis (original)'
        
        mnh_swd_var = output_file.createVariable('mnh_swd', 'f4', ('mnh_time',))
        mnh_swd_var.long_name = 'MNH SWD (Shortwave Downward) from Mahambo station - FULL RANGE'
        mnh_swd_var.units = 'W m-2'
        mnh_swd_var.description = f'Instantaneous shortwave downward radiation from MNH model (original {mnh_timestep/60:.1f}min timesteps) - PRESERVING FULL 0-800+ W m⁻² RANGE'
        mnh_swd_var.original_timestep_seconds = mnh_timestep
        mnh_swd_var.original_timestep_minutes = mnh_timestep / 60.0
        mnh_swd_var.data_range = f"{np.nanmin(mnh_swd):.2f} to {np.nanmax(mnh_swd):.2f} W m⁻²"
        
        # Create ERA5 variables
        era5_time_var = output_file.createVariable('era5_time', 'f8', ('era5_time',))
        era5_time_var.units = getattr(self.era5_file.variables['valid_time'], 'units', 'seconds')
        era5_time_var.long_name = 'ERA5 time axis (original)'
        
        era5_ssrd_var = output_file.createVariable('era5_ssrd', 'f4', ('era5_time',))
        era5_ssrd_var.long_name = 'ERA5 SSRD (Surface Solar Radiation Downward) - Converted to W m⁻²'
        era5_ssrd_var.units = 'W m-2'
        era5_ssrd_var.description = f'Time-averaged shortwave downward radiation from ERA5 reanalysis (converted from J m⁻² to W m⁻²)'
        era5_ssrd_var.original_timestep_seconds = era5_timestep
        era5_ssrd_var.original_timestep_hours = era5_timestep / 3600.0
        era5_ssrd_var.data_range = f"{np.nanmin(era5_ssrd):.2f} to {np.nanmax(era5_ssrd):.2f} W m⁻²"
        
        # Store data
        mnh_time_var[:] = mnh_time
        mnh_swd_var[:] = np.array(mnh_swd, dtype=np.float32)
        era5_time_var[:] = era5_time
        era5_ssrd_var[:] = np.array(era5_ssrd, dtype=np.float32)
        
        # Add comprehensive global attributes
        output_file.title = "Basic Full Range MNH vs ERA5 Solar Radiation Data (Side by Side)"
        output_file.history = f"Created by Basic MNH-ERA5 Superimposer on {datetime.now().isoformat()}"
        output_file.source_mnh = self.mnh_file_path
        output_file.source_era5 = self.era5_file_path
        output_file.description = "Complete comparison preserving full MNH SWD range (0-800+ W m⁻²) with ERA5 SSRD converted to W m⁻²"
        output_file.mnh_timestep_seconds = mnh_timestep
        output_file.mnh_timestep_minutes = mnh_timestep / 60.0
        output_file.era5_timestep_seconds = era5_timestep
        output_file.era5_timestep_hours = era5_timestep / 3600.0
        output_file.unit_conversion = f"ERA5: J m-2 / {era5_timestep} s = W m-2"
        output_file.comparison_note = f"MNH: instantaneous power at {mnh_timestep/60:.1f}min resolution (FULL RANGE), ERA5: time-averaged power at {era5_timestep/3600:.2f}h resolution"
        output_file.mnh_full_range_preserved = "YES - Complete 0-800+ W m⁻² range maintained"
        output_file.data_structure = "Side-by-side datasets (no interpolation) for maximum data preservation"
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def superimpose_basic(self, output_path: str) -> str:
        """Main method to superimpose MNH vs ERA5 data preserving full MNH range."""
        logger.info("=== STARTING BASIC FULL RANGE MNH vs ERA5 SUPERIMPOSITION ===")
        
        try:
            # Extract complete data from both files
            mnh_swd, mnh_time, mnh_timestep = self.extract_complete_mnh_swd()
            era5_ssrd, era5_time, era5_timestep = self.extract_era5_ssrd()
            
            logger.info(f"=== FINAL BASIC DATA SUMMARY ===")
            logger.info(f"MNH data points: {len(mnh_swd)}")
            logger.info(f"MNH preserved range: {np.nanmin(mnh_swd):.2f} to {np.nanmax(mnh_swd):.2f} W m⁻²")
            logger.info(f"ERA5 data points: {len(era5_ssrd)}")
            logger.info(f"ERA5 converted range: {np.nanmin(era5_ssrd):.2f} to {np.nanmax(era5_ssrd):.2f} W m⁻²")
            logger.info(f"MNH timestep: {mnh_timestep} seconds ({mnh_timestep/60:.1f} minutes)")
            logger.info(f"ERA5 timestep: {era5_timestep} seconds ({era5_timestep/3600:.2f} hours)")
            
            # Create basic NetCDF with side-by-side data
            output_file_path = self.create_basic_netcdf(
                mnh_swd, mnh_time, era5_ssrd, era5_time, output_path, mnh_timestep, era5_timestep
            )
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error during basic superimposition: {e}")
            raise

def main():
    """Main function to run the basic full range MNH vs ERA5 superimposition."""
    parser = argparse.ArgumentParser(description='Basic Full Range MNH vs ERA5 NetCDF superimposition preserving complete MNH dataset')
    parser.add_argument('mnh_file', help='MNH NetCDF file path (should contain Stations.Mahambo.SWD)')
    parser.add_argument('era5_file', help='ERA5 NetCDF file path (should contain ssrd variable)')
    parser.add_argument('--output', '-o', default='basic_full_range_superimposed_mnh_era5.nc', 
                       help='Output NetCDF file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if files exist
    if not os.path.exists(args.mnh_file):
        logger.error(f"MNH file not found: {args.mnh_file}")
        sys.exit(1)
    if not os.path.exists(args.era5_file):
        logger.error(f"ERA5 file not found: {args.era5_file}")
        sys.exit(1)
    
    try:
        with BasicMNHERA5Superimposer(args.mnh_file, args.era5_file) as superimposer:
            output_path = superimposer.superimpose_basic(args.output)
            logger.info(f"=== BASIC FULL RANGE SUPERIMPOSITION SUCCESSFUL ===")
            logger.info(f"Output: {output_path}")
            
    except Exception as e:
        logger.error(f"Basic full range superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
