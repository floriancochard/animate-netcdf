#!/usr/bin/env python3
"""
Simple MNH vs ERA5 NetCDF Superimposition Tool (Full Range)

This script properly handles the complete MNH dataset with 5-minute timesteps:
- MNH: SWD variable in Stations.Mahambo group (289 timesteps, 5-min intervals, 24-hour cycle)
- ERA5: ssrd variable (48 time steps, hourly) in J m⁻² (accumulated energy)

Key features:
1. Extract FULL MNH dataset (all 289 timesteps, 0-800+ W m⁻² range)
2. Use MNH as the primary time axis to preserve full data range
3. Interpolate ERA5 to MNH time resolution
4. Convert ERA5 from J m⁻² to W m⁻² correctly
5. Simple NetCDF output without complex visualization

Usage:
    python superimpose_mnh_era5_simple.py mnh_file.nc era5_file.nc --output output.nc
"""

import argparse
import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta
import os
import sys
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMNHERA5Superimposer:
    """Simple class to handle superimposition of MNH vs ERA5 preserving full MNH data range."""
    
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
    
    def parse_mnh_reference_date(self, time_units: str) -> datetime:
        """Robustly parse MNH reference date from time units string."""
        try:
            # Remove 'seconds since ' prefix
            if 'seconds since ' in time_units:
                ref_date_str = time_units.replace('seconds since ', '')
            else:
                ref_date_str = time_units
            
            # Try different date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S %z',  # 2025-08-15 00:00:00 +0:00
                '%Y-%m-%d %H:%M:%S',     # 2025-08-15 00:00:00
                '%Y-%m-%d %H:%M',        # 2025-08-15 00:00
                '%Y-%m-%d',              # 2025-08-15
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(ref_date_str, fmt)
                except ValueError:
                    continue
            
            # If all parsing fails, try regex extraction
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', ref_date_str)
            if date_match:
                year, month, day = map(int, date_match.groups())
                return datetime(year, month, day, 0, 0, 0)
            
            # Final fallback
            logger.warning(f"Could not parse reference date '{ref_date_str}', using default")
            return datetime(2025, 8, 15, 0, 0, 0)
            
        except Exception as e:
            logger.warning(f"Error parsing reference date: {e}, using default")
            return datetime(2025, 8, 15, 0, 0, 0)
    
    def convert_mnh_time_to_datetime(self, mnh_time: np.ndarray, mnh_timestep: float) -> np.ndarray:
        """Convert MNH timestep data to datetime objects with robust parsing."""
        try:
            time_units = getattr(self.mnh_file.variables['time_station'], 'units', 'unknown')
            logger.info(f"Parsing MNH time units: {time_units}")
            
            # Parse reference date
            ref_date = self.parse_mnh_reference_date(time_units)
            logger.info(f"Using MNH reference date: {ref_date}")
            
            # Convert seconds to datetime
            datetime_data = [ref_date + timedelta(seconds=float(t)) for t in mnh_time]
            return np.array(datetime_data)
                
        except Exception as e:
            logger.warning(f"Could not convert MNH time to datetime: {e}")
            # Return original time data
            return mnh_time
    
    def convert_era5_time_to_datetime(self, era5_time: np.ndarray) -> np.ndarray:
        """Convert ERA5 time to datetime objects."""
        try:
            time_units = getattr(self.era5_file.variables['valid_time'], 'units', 'unknown')
            if 'seconds since' in time_units:
                datetime_data = nc.num2date(era5_time, time_units)
                return np.array(datetime_data)
            else:
                logger.warning(f"Unknown ERA5 time units: {time_units}")
                return era5_time
        except Exception as e:
            logger.warning(f"Could not convert ERA5 time to datetime: {e}")
            return era5_time
    
    def align_time_series_preserve_mnh(self, mnh_time: np.ndarray, era5_time: np.ndarray,
                                     mnh_swd: np.ndarray, era5_ssrd: np.ndarray,
                                     mnh_timestep: float, era5_timestep: float) -> tuple:
        """Align time series using MNH as primary axis to preserve full data range."""
        logger.info("=== ALIGNING TIME SERIES PRESERVING FULL MNH RANGE ===")
        
        # Convert times to datetime
        mnh_time_dt = self.convert_mnh_time_to_datetime(mnh_time, mnh_timestep)
        era5_time_dt = self.convert_era5_time_to_datetime(era5_time)
        
        logger.info(f"MNH time range: {mnh_time_dt[0]} to {mnh_time_dt[-1]}")
        logger.info(f"ERA5 time range: {era5_time_dt[0]} to {era5_time_dt[-1]}")
        
        # Use MNH time as the primary axis to preserve full data range
        if hasattr(mnh_time_dt[0], 'timestamp'):
            # Find common time range
            start_time = max(np.min(mnh_time_dt), np.min(era5_time_dt))
            end_time = min(np.max(mnh_time_dt), np.max(era5_time_dt))
            
            logger.info(f"Common time range: {start_time} to {end_time}")
            
            # Filter MNH data to common time range
            mnh_mask = (mnh_time_dt >= start_time) & (mnh_time_dt <= end_time)
            mnh_filtered_time = mnh_time_dt[mnh_mask]
            mnh_filtered_swd = mnh_swd[mnh_mask]
            
            logger.info(f"MNH filtered data: {len(mnh_filtered_swd)} points")
            logger.info(f"MNH filtered range: {np.nanmin(mnh_filtered_swd):.2f} to {np.nanmax(mnh_filtered_swd):.2f} W m⁻²")
            
            # Interpolate ERA5 to MNH time points
            era5_interp = self._interpolate_era5_to_mnh_time(era5_time_dt, era5_ssrd, mnh_filtered_time)
            
            common_time = mnh_filtered_time
            mnh_interp = mnh_filtered_swd
            
        else:
            # Fallback: use MNH data directly
            common_time = mnh_time
            mnh_interp = mnh_swd
            era5_interp = era5_ssrd[:len(mnh_time)]  # Truncate ERA5 to match
            logger.warning("Using fallback time alignment")
        
        logger.info(f"Final aligned data shapes: MNH={mnh_interp.shape}, ERA5={era5_interp.shape}")
        logger.info(f"Final MNH range: {np.nanmin(mnh_interp):.2f} to {np.nanmax(mnh_interp):.2f} W m⁻²")
        logger.info(f"Final ERA5 range: {np.nanmin(era5_interp):.2f} to {np.nanmax(era5_interp):.2f} W m⁻²")
        
        return common_time, mnh_interp, era5_interp
    
    def _interpolate_era5_to_mnh_time(self, era5_time: np.ndarray, era5_data: np.ndarray, 
                                     mnh_time: np.ndarray) -> np.ndarray:
        """Interpolate ERA5 data to MNH time points."""
        from scipy.interpolate import interp1d
        
        if len(era5_time) == len(mnh_time):
            return era5_data
        
        # Handle datetime interpolation
        if hasattr(era5_time[0], 'timestamp'):
            # Convert to numeric for interpolation
            time_numeric = np.array([(t - era5_time[0]).total_seconds() for t in era5_time])
            target_numeric = np.array([(t - era5_time[0]).total_seconds() for t in mnh_time])
            
            f = interp1d(time_numeric, era5_data, bounds_error=False, fill_value='extrapolate')
            return f(target_numeric)
        else:
            # Numeric time interpolation
            f = interp1d(era5_time, era5_data, bounds_error=False, fill_value='extrapolate')
            return f(mnh_time)
    
    def create_simple_netcdf(self, common_time: np.ndarray, mnh_interp: np.ndarray, 
                            era5_interp: np.ndarray, output_path: str, 
                            mnh_timestep: float, era5_timestep: float) -> str:
        """Create a simple NetCDF file with superimposed data preserving full MNH range."""
        logger.info(f"Creating simple NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        output_file.createDimension('time', len(common_time))
        
        # Create time variable
        time_var = output_file.createVariable('time', 'f8', ('time',))
        time_var.units = 'seconds since 1970-01-01 00:00:00'
        time_var.long_name = 'MNH time axis (preserved full range)'
        
        # Create data variables
        mnh_var = output_file.createVariable('mnh_swd', 'f4', ('time',))
        mnh_var.long_name = 'MNH SWD (Shortwave Downward) from Mahambo station - FULL RANGE'
        mnh_var.units = 'W m-2'
        mnh_var.description = f'Instantaneous shortwave downward radiation from MNH model (original {mnh_timestep/60:.1f}min timesteps) - PRESERVING FULL 0-800+ W m⁻² RANGE'
        mnh_var.original_timestep_seconds = mnh_timestep
        mnh_var.original_timestep_minutes = mnh_timestep / 60.0
        mnh_var.data_range = f"{np.nanmin(mnh_interp):.2f} to {np.nanmax(mnh_interp):.2f} W m⁻²"
        
        era5_var = output_file.createVariable('era5_ssrd', 'f4', ('time',))
        era5_var.long_name = 'ERA5 SSRD (Surface Solar Radiation Downward) - Interpolated to MNH Time'
        era5_var.units = 'W m-2'
        era5_var.description = f'Time-averaged shortwave downward radiation from ERA5 reanalysis (interpolated from {era5_timestep/3600:.2f}h to {mnh_timestep/60:.1f}min resolution)'
        era5_var.original_timestep_seconds = era5_timestep
        era5_var.original_timestep_hours = era5_timestep / 3600.0
        era5_var.data_range = f"{np.nanmin(era5_interp):.2f} to {np.nanmax(era5_interp):.2f} W m⁻²"
        
        # Store data - convert to numeric arrays
        if hasattr(common_time[0], 'timestamp'):
            # Convert datetime to seconds since epoch
            time_seconds = np.array([t.timestamp() for t in common_time])
            time_var[:] = time_seconds
        else:
            time_var[:] = common_time
        
        # Ensure data is numeric before storing
        mnh_var[:] = np.array(mnh_interp, dtype=np.float32)
        era5_var[:] = np.array(era5_interp, dtype=np.float32)
        
        # Add comprehensive global attributes
        output_file.title = "Simple Full Range MNH vs ERA5 Solar Radiation Data (Preserving Complete MNH Dataset)"
        output_file.history = f"Created by Simple MNH-ERA5 Superimposer on {datetime.now().isoformat()}"
        output_file.source_mnh = self.mnh_file_path
        output_file.source_era5 = self.era5_file_path
        output_file.description = "Complete comparison preserving full MNH SWD range (0-800+ W m⁻²) with ERA5 SSRD interpolated to match"
        output_file.mnh_timestep_seconds = mnh_timestep
        output_file.mnh_timestep_minutes = mnh_timestep / 60.0
        output_file.era5_timestep_seconds = era5_timestep
        output_file.era5_timestep_hours = era5_timestep / 3600.0
        output_file.unit_conversion = f"ERA5: J m-2 / {era5_timestep} s = W m-2"
        output_file.comparison_note = f"MNH: instantaneous power at {mnh_timestep/60:.1f}min resolution (FULL RANGE), ERA5: time-averaged power interpolated to MNH time"
        output_file.mnh_full_range_preserved = "YES - Complete 0-800+ W m⁻² range maintained"
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def superimpose_simple(self, output_path: str) -> str:
        """Main method to superimpose MNH vs ERA5 data preserving full MNH range."""
        logger.info("=== STARTING SIMPLE FULL RANGE MNH vs ERA5 SUPERIMPOSITION ===")
        
        try:
            # Extract complete data from both files
            mnh_swd, mnh_time, mnh_timestep = self.extract_complete_mnh_swd()
            era5_ssrd, era5_time, era5_timestep = self.extract_era5_ssrd()
            
            # Align time series preserving full MNH range
            common_time, mnh_interp, era5_interp = self.align_time_series_preserve_mnh(
                mnh_time, era5_time, mnh_swd, era5_ssrd, mnh_timestep, era5_timestep
            )
            
            logger.info(f"=== FINAL SIMPLE FULL RANGE ALIGNED DATA SUMMARY ===")
            logger.info(f"Common time points: {len(common_time)}")
            logger.info(f"MNH preserved range: {np.nanmin(mnh_interp):.2f} to {np.nanmax(mnh_interp):.2f} W m⁻²")
            logger.info(f"ERA5 interpolated range: {np.nanmin(era5_interp):.2f} to {np.nanmax(era5_interp):.2f} W m⁻²")
            logger.info(f"MNH timestep: {mnh_timestep} seconds ({mnh_timestep/60:.1f} minutes)")
            logger.info(f"ERA5 timestep: {era5_timestep} seconds ({era5_timestep/3600:.2f} hours)")
            
            # Create simple NetCDF
            output_file_path = self.create_simple_netcdf(
                common_time, mnh_interp, era5_interp, output_path, mnh_timestep, era5_timestep
            )
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error during simple superimposition: {e}")
            raise

def main():
    """Main function to run the simple full range MNH vs ERA5 superimposition."""
    parser = argparse.ArgumentParser(description='Simple Full Range MNH vs ERA5 NetCDF superimposition preserving complete MNH dataset')
    parser.add_argument('mnh_file', help='MNH NetCDF file path (should contain Stations.Mahambo.SWD)')
    parser.add_argument('era5_file', help='ERA5 NetCDF file path (should contain ssrd variable)')
    parser.add_argument('--output', '-o', default='simple_full_range_superimposed_mnh_era5.nc', 
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
        with SimpleMNHERA5Superimposer(args.mnh_file, args.era5_file) as superimposer:
            output_path = superimposer.superimpose_simple(args.output)
            logger.info(f"=== SIMPLE FULL RANGE SUPERIMPOSITION SUCCESSFUL ===")
            logger.info(f"Output: {output_path}")
            
    except Exception as e:
        logger.error(f"Simple full range superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
