#!/usr/bin/env python3
"""
2-Day MNH vs ERA5 NetCDF Superimposition Tool

This script creates a unified 2-day timeseries combining:
- MNH 1508: SWD variable for 15/08 (1 day, 5-min timesteps)
- MNH 1608: SWD variable for 16/08 (1 day, 5-min timesteps) 
- ERA5: ssrd variable for both days (15/08 + 16/08, hourly timestamps)

Key features:
1. Combines two MNH files into continuous 2-day dataset
2. Aligns MNH timesteps with ERA5 timestamps
3. Converts ERA5 from J m⁻² to W m⁻² correctly
4. Creates superimposition plot spanning full 2-day period
5. Outputs unified NetCDF with all three datasets

Usage:
    python superimpose_mnh_era5_2day.py mnh_1508.nc mnh_1608.nc era5_file.nc --output output.nc
"""

import argparse
import numpy as np
import netCDF4 as nc
import os
import sys
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwoDayMNHERA5Superimposer:
    """Class to handle 2-day superimposition of MNH 1508 + 1608 vs ERA5."""
    
    def __init__(self, mnh_1508_path: str, mnh_1608_path: str, era5_file_path: str):
        """Initialize with MNH 1508, MNH 1608, and ERA5 NetCDF file paths."""
        self.mnh_1508_path = mnh_1508_path
        self.mnh_1608_path = mnh_1608_path
        self.era5_file_path = era5_file_path
        self.mnh_1508_file = None
        self.mnh_1608_file = None
        self.era5_file = None
        
    def __enter__(self):
        """Context manager entry."""
        self.mnh_1508_file = nc.Dataset(self.mnh_1508_path, 'r')
        self.mnh_1608_file = nc.Dataset(self.mnh_1608_path, 'r')
        self.era5_file = nc.Dataset(self.era5_file_path, 'r')
        logger.info(f"Opened MNH 1508 file: {self.mnh_1508_path}")
        logger.info(f"Opened MNH 1608 file: {self.mnh_1608_path}")
        logger.info(f"Opened ERA5 file: {self.era5_file_path}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.mnh_1508_file:
            self.mnh_1508_file.close()
        if self.mnh_1608_file:
            self.mnh_1608_file.close()
        if self.era5_file:
            self.era5_file.close()
    
    def extract_mnh_swd(self, mnh_file, file_label: str) -> tuple:
        """Extract SWD variable from MNH file."""
        try:
            # Navigate to Stations.Mahambo group
            mahambo_group = mnh_file.groups['Stations'].groups['Mahambo']
            
            # Extract SWD variable
            swd_var = mahambo_group.variables['SWD']
            swd_data = swd_var[:]
            
            # Extract time information
            time_var = mnh_file.variables['time_station']
            time_data = time_var[:]
            
            # Analyze timestep structure
            if len(time_data) > 1:
                time_diffs = np.diff(time_data)
                timestep_seconds = float(time_diffs[0])
                total_duration_hours = (time_data[-1] - time_data[0]) / 3600.0
            else:
                timestep_seconds = 300.0  # Default 5 minutes
                total_duration_hours = 24.0
            
            logger.info(f"=== {file_label} DATA ANALYSIS ===")
            logger.info(f"SWD data shape: {swd_data.shape}")
            logger.info(f"SWD units: {getattr(swd_var, 'units', 'No units')}")
            logger.info(f"Time data shape: {time_data.shape}")
            logger.info(f"Timestep: {timestep_seconds} seconds ({timestep_seconds/60:.1f} minutes)")
            logger.info(f"Total duration: {total_duration_hours:.1f} hours")
            logger.info(f"SWD range: {np.nanmin(swd_data):.2f} to {np.nanmax(swd_data):.2f} W m⁻²")
            
            return swd_data, time_data, timestep_seconds
            
        except KeyError as e:
            logger.error(f"Could not find required variable/group in {file_label}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting {file_label} SWD data: {e}")
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
            logger.info(f"ssrd units: {units}")
            logger.info(f"ssrd data shape: {ssrd_data.shape}")
            logger.info(f"time data shape: {time_data.shape}")
            logger.info(f"time units: {getattr(time_var, 'units', 'No units')}")
            
            # Determine time resolution
            if len(time_data) > 1:
                time_diffs = np.diff(time_data)
                time_resolution_seconds = float(time_diffs[0])
                total_duration_hours = (time_data[-1] - time_data[0]) / 3600.0
                logger.info(f"Time resolution: {time_resolution_seconds} seconds ({time_resolution_seconds/3600:.2f} hours)")
                logger.info(f"Total duration: {total_duration_hours:.1f} hours")
            else:
                time_resolution_seconds = 3600.0  # Default to 1 hour
                total_duration_hours = 24.0
                logger.warning("Could not determine time resolution, assuming 1 hour")
            
            # Convert from J m⁻² to W m⁻²
            if 'J m**-2' in units or 'J m-2' in units or 'J/m2' in units:
                logger.info(f"Converting ERA5 ssrd from J m⁻² to W m⁻²")
                ssrd_data = ssrd_data / time_resolution_seconds
                units = 'W m-2'
            elif 'W m**-2' in units or 'W m-2' in units or 'W/m2' in units:
                logger.info("ERA5 ssrd already in W m⁻², no conversion needed")
                time_resolution_seconds = 1.0
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
    
    def create_2day_timeseries(self, mnh_1508_swd: np.ndarray, mnh_1608_swd: np.ndarray,
                              mnh_timestep: float, era5_ssrd: np.ndarray, era5_time: np.ndarray) -> tuple:
        """Create unified 2-day timeseries combining all datasets."""
        logger.info("=== CREATING UNIFIED 2-DAY TIMESERIES ===")
        
        # Create datetime objects for the 2-day period
        # Assuming 15/08 starts at 00:00 and 16/08 ends at 23:59
        start_date = datetime(2024, 8, 15, 0, 0, 0)  # 15/08 00:00
        
        # Create MNH 1508 timestamps (day 1)
        mnh_1508_timestamps = []
        for i in range(len(mnh_1508_swd)):
            timestamp = start_date + timedelta(seconds=i * mnh_timestep)
            mnh_1508_timestamps.append(timestamp)
        
        # Create MNH 1608 timestamps (day 2)
        mnh_1608_timestamps = []
        for i in range(len(mnh_1608_swd)):
            timestamp = start_date + timedelta(days=1, seconds=i * mnh_timestep)
            mnh_1608_timestamps.append(timestamp)
        
        # Combine MNH data and timestamps
        mnh_combined_swd = np.concatenate([mnh_1508_swd, mnh_1608_swd])
        mnh_combined_timestamps = mnh_1508_timestamps + mnh_1608_timestamps
        
        # Convert ERA5 timestamps to datetime objects
        # Assuming ERA5 time is in seconds since some reference
        era5_timestamps = []
        for time_val in era5_time:
            # Adjust this calculation based on your ERA5 time units
            timestamp = start_date + timedelta(seconds=float(time_val))
            era5_timestamps.append(timestamp)
        
        logger.info(f"=== TIMESERIES SUMMARY ===")
        logger.info(f"MNH 1508: {len(mnh_1508_swd)} points, {mnh_1508_timestamps[0]} to {mnh_1508_timestamps[-1]}")
        logger.info(f"MNH 1608: {len(mnh_1608_swd)} points, {mnh_1608_timestamps[0]} to {mnh_1608_timestamps[-1]}")
        logger.info(f"MNH Combined: {len(mnh_combined_swd)} points, {mnh_combined_timestamps[0]} to {mnh_combined_timestamps[-1]}")
        logger.info(f"ERA5: {len(era5_ssrd)} points, {era5_timestamps[0]} to {era5_timestamps[-1]}")
        
        return (mnh_combined_swd, mnh_combined_timestamps, 
                mnh_1508_swd, mnh_1508_timestamps,
                mnh_1608_swd, mnh_1608_timestamps,
                era5_ssrd, era5_timestamps)
    
    def create_superimposition_plot(self, mnh_combined_swd: np.ndarray, mnh_combined_timestamps: list,
                                  mnh_1508_swd: np.ndarray, mnh_1508_timestamps: list,
                                  mnh_1608_swd: np.ndarray, mnh_1608_timestamps: list,
                                  era5_ssrd: np.ndarray, era5_timestamps: list,
                                  output_path: str) -> str:
        """Create superimposition plot showing all datasets on 2-day timeseries."""
        logger.info(f"Creating superimposition plot: {output_path}")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot MNH data
        ax.plot(mnh_1508_timestamps, mnh_1508_swd, 'b-', linewidth=1.5, alpha=0.8, 
                label='MNH 1508 (15/08)', markersize=2)
        ax.plot(mnh_1608_timestamps, mnh_1608_swd, 'g-', linewidth=1.5, alpha=0.8, 
                label='MNH 1608 (16/08)', markersize=2)
        
        # Plot ERA5 data
        ax.plot(era5_timestamps, era5_ssrd, 'r-o', linewidth=2, markersize=6, alpha=0.9,
                label='ERA5 (15/08 + 16/08)')
        
        # Customize plot
        ax.set_xlabel('Date/Time (15-16 August 2024)', fontsize=12)
        ax.set_ylabel('Solar Radiation (W m⁻²)', fontsize=12)
        ax.set_title('2-Day MNH vs ERA5 Solar Radiation Superimposition\nMNH 1508 + 1608 vs ERA5 (15/08 + 16/08)', 
                    fontsize=14, fontweight='bold')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, loc='upper right')
        
        # Add day separators
        day_separator = datetime(2024, 8, 16, 0, 0, 0)
        ax.axvline(x=day_separator, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(day_separator, ax.get_ylim()[1] * 0.95, '16/08', 
                rotation=90, verticalalignment='top', fontsize=10, alpha=0.7)
        
        # Adjust layout and save
        plt.tight_layout()
        plot_path = output_path.replace('.nc', '_superimposition.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Superimposition plot saved: {plot_path}")
        return plot_path
    
    def create_unified_netcdf(self, mnh_combined_swd: np.ndarray, mnh_combined_timestamps: list,
                             mnh_1508_swd: np.ndarray, mnh_1508_timestamps: list,
                             mnh_1608_swd: np.ndarray, mnh_1608_timestamps: list,
                             era5_ssrd: np.ndarray, era5_timestamps: list,
                             output_path: str, mnh_timestep: float, era5_timestep: float) -> str:
        """Create unified NetCDF file with all datasets on 2-day timeseries."""
        logger.info(f"Creating unified 2-day NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        output_file.createDimension('mnh_combined_time', len(mnh_combined_timestamps))
        output_file.createDimension('mnh_1508_time', len(mnh_1508_timestamps))
        output_file.createDimension('mnh_1608_time', len(mnh_1608_timestamps))
        output_file.createDimension('era5_time', len(era5_timestamps))
        
        # Create MNH combined variables
        mnh_combined_time_var = output_file.createVariable('mnh_combined_time', 'f8', ('mnh_combined_time',))
        mnh_combined_time_var.units = 'seconds since 2024-08-15 00:00:00'
        mnh_combined_time_var.long_name = 'MNH combined time axis (2-day period)'
        
        mnh_combined_swd_var = output_file.createVariable('mnh_combined_swd', 'f4', ('mnh_combined_time',))
        mnh_combined_swd_var.long_name = 'MNH SWD combined (15/08 + 16/08)'
        mnh_combined_swd_var.units = 'W m-2'
        mnh_combined_swd_var.description = f'Combined MNH SWD data for 2-day period (15/08 + 16/08) with {mnh_timestep/60:.1f}min timesteps'
        
        # Create MNH 1508 variables
        mnh_1508_time_var = output_file.createVariable('mnh_1508_time', 'f8', ('mnh_1508_time',))
        mnh_1508_time_var.units = 'seconds since 2024-08-15 00:00:00'
        mnh_1508_time_var.long_name = 'MNH 1508 time axis (15/08 only)'
        
        mnh_1508_swd_var = output_file.createVariable('mnh_1508_swd', 'f4', ('mnh_1508_time',))
        mnh_1508_swd_var.long_name = 'MNH 1508 SWD (15/08 only)'
        mnh_1508_swd_var.units = 'W m-2'
        mnh_1508_swd_var.description = f'MNH SWD data for 15/08 with {mnh_timestep/60:.1f}min timesteps'
        
        # Create MNH 1608 variables
        mnh_1608_time_var = output_file.createVariable('mnh_1608_time', 'f8', ('mnh_1608_time',))
        mnh_1608_time_var.units = 'seconds since 2024-08-16 00:00:00'
        mnh_1608_time_var.long_name = 'MNH 1608 time axis (16/08 only)'
        
        mnh_1608_swd_var = output_file.createVariable('mnh_1608_swd', 'f4', ('mnh_1608_time',))
        mnh_1608_swd_var.long_name = 'MNH 1608 SWD (16/08 only)'
        mnh_1608_swd_var.units = 'W m-2'
        mnh_1608_swd_var.description = f'MNH SWD data for 16/08 with {mnh_timestep/60:.1f}min timesteps'
        
        # Create ERA5 variables
        era5_time_var = output_file.createVariable('era5_time', 'f8', ('era5_time',))
        era5_time_var.units = 'seconds since 2024-08-15 00:00:00'
        era5_time_var.long_name = 'ERA5 time axis (2-day period)'
        
        era5_ssrd_var = output_file.createVariable('era5_ssrd', 'f4', ('era5_time',))
        era5_ssrd_var.long_name = 'ERA5 SSRD (Surface Solar Radiation Downward) - Converted to W m⁻²'
        era5_ssrd_var.units = 'W m-2'
        era5_ssrd_var.description = f'ERA5 SSRD data for 2-day period (15/08 + 16/08) converted from J m⁻² to W m⁻²'
        
        # Store data
        mnh_combined_time_var[:] = [(ts - mnh_combined_timestamps[0]).total_seconds() for ts in mnh_combined_timestamps]
        mnh_combined_swd_var[:] = np.array(mnh_combined_swd, dtype=np.float32)
        
        mnh_1508_time_var[:] = [(ts - mnh_1508_timestamps[0]).total_seconds() for ts in mnh_1508_timestamps]
        mnh_1508_swd_var[:] = np.array(mnh_1508_swd, dtype=np.float32)
        
        mnh_1608_time_var[:] = [(ts - mnh_1608_timestamps[0]).total_seconds() for ts in mnh_1608_timestamps]
        mnh_1608_swd_var[:] = np.array(mnh_1608_swd, dtype=np.float32)
        
        era5_time_var[:] = [(ts - era5_timestamps[0]).total_seconds() for ts in era5_timestamps]
        era5_ssrd_var[:] = np.array(era5_ssrd, dtype=np.float32)
        
        # Add global attributes
        output_file.title = "Unified 2-Day MNH vs ERA5 Solar Radiation Data"
        output_file.history = f"Created by 2-Day MNH-ERA5 Superimposer on {datetime.now().isoformat()}"
        output_file.source_mnh_1508 = self.mnh_1508_path
        output_file.source_mnh_1608 = self.mnh_1608_path
        output_file.source_era5 = self.era5_file_path
        output_file.description = "Combined 2-day timeseries with MNH 1508 + 1608 vs ERA5 superimposition"
        output_file.period = "15/08/2024 00:00 - 16/08/2024 23:59"
        output_file.mnh_timestep_seconds = mnh_timestep
        output_file.mnh_timestep_minutes = mnh_timestep / 60.0
        output_file.era5_timestep_seconds = era5_timestep
        output_file.era5_timestep_hours = era5_timestep / 3600.0
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def superimpose_2day(self, output_path: str) -> tuple:
        """Main method to create 2-day superimposition of MNH 1508 + 1608 vs ERA5."""
        logger.info("=== STARTING 2-DAY MNH vs ERA5 SUPERIMPOSITION ===")
        
        try:
            # Extract data from all files
            mnh_1508_swd, mnh_1508_time, mnh_timestep = self.extract_mnh_swd(self.mnh_1508_file, "MNH 1508")
            mnh_1608_swd, mnh_1608_time, _ = self.extract_mnh_swd(self.mnh_1608_file, "MNH 1608")
            era5_ssrd, era5_time, era5_timestep = self.extract_era5_ssrd()
            
            # Create unified 2-day timeseries
            (mnh_combined_swd, mnh_combined_timestamps,
             mnh_1508_swd, mnh_1508_timestamps,
             mnh_1608_swd, mnh_1608_timestamps,
             era5_ssrd, era5_timestamps) = self.create_2day_timeseries(
                mnh_1508_swd, mnh_1608_swd, mnh_timestep, era5_ssrd, era5_time
            )
            
            # Create superimposition plot
            plot_path = self.create_superimposition_plot(
                mnh_combined_swd, mnh_combined_timestamps,
                mnh_1508_swd, mnh_1508_timestamps,
                mnh_1608_swd, mnh_1608_timestamps,
                era5_ssrd, era5_timestamps,
                output_path
            )
            
            # Create unified NetCDF
            netcdf_path = self.create_unified_netcdf(
                mnh_combined_swd, mnh_combined_timestamps,
                mnh_1508_swd, mnh_1508_timestamps,
                mnh_1608_swd, mnh_1608_timestamps,
                era5_ssrd, era5_timestamps,
                output_path, mnh_timestep, era5_timestep
            )
            
            logger.info(f"=== 2-DAY SUPERIMPOSITION SUCCESSFUL ===")
            logger.info(f"NetCDF output: {netcdf_path}")
            logger.info(f"Plot output: {plot_path}")
            
            return netcdf_path, plot_path
            
        except Exception as e:
            logger.error(f"Error during 2-day superimposition: {e}")
            raise

def main():
    """Main function to run the 2-day MNH vs ERA5 superimposition."""
    parser = argparse.ArgumentParser(description='2-Day MNH vs ERA5 NetCDF superimposition combining MNH 1508 + 1608')
    parser.add_argument('mnh_1508_file', help='MNH 1508 NetCDF file path (15/08 data)')
    parser.add_argument('mnh_1608_file', help='MNH 1608 NetCDF file path (16/08 data)')
    parser.add_argument('era5_file', help='ERA5 NetCDF file path (15/08 + 16/08 data)')
    parser.add_argument('--output', '-o', default='unified_2day_superimposed_mnh_era5.nc', 
                       help='Output NetCDF file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if files exist
    for file_path in [args.mnh_1508_file, args.mnh_1608_file, args.era5_file]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
    
    try:
        with TwoDayMNHERA5Superimposer(args.mnh_1508_file, args.mnh_1608_file, args.era5_file) as superimposer:
            netcdf_path, plot_path = superimposer.superimpose_2day(args.output)
            logger.info(f"=== 2-DAY SUPERIMPOSITION COMPLETE ===")
            logger.info(f"NetCDF: {netcdf_path}")
            logger.info(f"Plot: {plot_path}")
            
    except Exception as e:
        logger.error(f"2-day superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
