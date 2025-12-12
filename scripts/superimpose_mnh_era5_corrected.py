#!/usr/bin/env python3
"""
Corrected MNH vs ERA5 NetCDF Superimposition Tool

This script superimposes MNH and ERA5 NetCDF files with different data structures:
- ERA5: ssrd variable (48 time steps, single point) in J m⁻² (accumulated energy)
- MNH: SWD variable in Stations.Mahambo group (289 time steps, single point) in W m⁻² (instantaneous power)

The script converts ERA5 data to hourly average power (W m⁻²) for proper comparison.
Creates a 2D time series plot comparing the two datasets.

Usage:
    python superimpose_mnh_era5_corrected.py mnh_file.nc era5_file.nc --output output.nc
"""

import argparse
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, Tuple, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorrectedMNHERA5Superimposer:
    """Corrected class to handle superimposition of MNH vs ERA5 NetCDF files with proper unit conversion."""
    
    def __init__(self, mnh_file_path: str, era5_file_path: str):
        """Initialize with MNH and ERA5 NetCDF file paths."""
        self.mnh_file_path = mnh_file_path
        self.era5_file_path = era5_file_path
        self.mnh_file = None
        self.era5_file = None
        self.output_file = None
        
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
        if self.output_file:
            self.output_file.close()
    
    def extract_mnh_swd(self) -> Tuple[np.ndarray, np.ndarray]:
        """Extract SWD variable from MNH file in Stations.Mahambo group."""
        try:
            # Navigate to Stations.Mahambo group
            mahambo_group = self.mnh_file.groups['Stations'].groups['Mahambo']
            
            # Extract SWD variable
            swd_var = mahambo_group.variables['SWD']
            swd_data = swd_var[:]
            
            # Extract time information
            time_var = self.mnh_file.variables['time_station']
            time_data = time_var[:]
            
            logger.info(f"MNH SWD data shape: {swd_data.shape}")
            logger.info(f"MNH SWD units: {getattr(swd_var, 'units', 'No units')}")
            logger.info(f"MNH time data shape: {time_data.shape}")
            
            return swd_data, time_data
            
        except KeyError as e:
            logger.error(f"Could not find required variable/group in MNH file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting MNH SWD data: {e}")
            raise
    
    def extract_era5_ssrd(self) -> Tuple[np.ndarray, np.ndarray]:
        """Extract ssrd variable from ERA5 file and convert to W m⁻²."""
        try:
            # Extract ssrd variable
            ssrd_var = self.era5_file.variables['ssrd']
            ssrd_data = ssrd_var[:, 0, 0]  # Remove spatial dimensions
            
            # Extract time information
            time_var = self.era5_file.variables['valid_time']
            time_data = time_var[:]
            
            # Check units and convert if necessary
            units = getattr(ssrd_var, 'units', 'unknown')
            logger.info(f"ERA5 ssrd units: {units}")
            logger.info(f"ERA5 ssrd data shape: {ssrd_data.shape}")
            logger.info(f"ERA5 time data shape: {time_data.shape}")
            
            # Convert from J m⁻² to W m⁻² (assuming hourly accumulation)
            if 'J m**-2' in units or 'J m-2' in units:
                logger.info("Converting ERA5 ssrd from J m⁻² to W m⁻² (hourly average)")
                # Divide by 3600 seconds to get hourly average power
                ssrd_data = ssrd_data / 3600.0
                units = 'W m-2'
            elif 'W m**-2' in units or 'W m-2' in units:
                logger.info("ERA5 ssrd already in W m⁻², no conversion needed")
            else:
                logger.warning(f"Unknown ERA5 ssrd units: {units}, assuming J m⁻² and converting")
                ssrd_data = ssrd_data / 3600.0
                units = 'W m-2'
            
            logger.info(f"ERA5 ssrd converted units: {units}")
            logger.info(f"ERA5 ssrd value range: {np.nanmin(ssrd_data):.2f} to {np.nanmax(ssrd_data):.2f} W m⁻²")
            
            return ssrd_data, time_data
            
        except KeyError as e:
            logger.error(f"Could not find required variable in ERA5 file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting ERA5 ssrd data: {e}")
            raise
    
    def convert_time_to_datetime(self, time_data: np.ndarray, time_units: str) -> np.ndarray:
        """Convert NetCDF time to datetime objects."""
        try:
            if time_units != 'unknown':
                datetime_data = nc.num2date(time_data, time_units)
                return np.array(datetime_data)
            else:
                logger.warning("Unknown time units, using raw time values")
                return time_data
        except Exception as e:
            logger.warning(f"Could not convert time to datetime: {e}")
            return time_data
    
    def align_time_series(self, mnh_time: np.ndarray, era5_time: np.ndarray,
                         mnh_swd: np.ndarray, era5_ssrd: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Align MNH and ERA5 time series to common time axis."""
        logger.info("Aligning time series...")
        
        # Convert times to datetime if possible
        mnh_time_dt = self.convert_time_to_datetime(mnh_time, getattr(self.mnh_file.variables['time_station'], 'units', 'unknown'))
        era5_time_dt = self.convert_time_to_datetime(era5_time, getattr(self.era5_file.variables['valid_time'], 'units', 'unknown'))
        
        # Find common time range
        if isinstance(mnh_time_dt[0], datetime) and isinstance(era5_time_dt[0], datetime):
            start_time = max(np.min(mnh_time_dt), np.min(era5_time_dt))
            end_time = min(np.max(mnh_time_dt), np.max(era5_time_dt))
            
            # Create common time axis (hourly)
            common_time = []
            current_time = start_time
            while current_time <= end_time:
                common_time.append(current_time)
                current_time += timedelta(hours=1)
            common_time = np.array(common_time)
            
            # Interpolate both datasets to common time
            mnh_interp = self._interpolate_to_common_time(mnh_time_dt, mnh_swd, common_time)
            era5_interp = self._interpolate_to_common_time(era5_time_dt, era5_ssrd, common_time)
            
        else:
            # Fallback: use shorter time series
            min_length = min(len(mnh_time), len(era5_time))
            common_time = np.arange(min_length)
            mnh_interp = mnh_swd[:min_length]
            era5_interp = era5_ssrd[:min_length]
        
        logger.info(f"Aligned time series length: {len(common_time)}")
        return common_time, mnh_interp, era5_interp
    
    def _interpolate_to_common_time(self, source_time: np.ndarray, source_data: np.ndarray, 
                                   target_time: np.ndarray) -> np.ndarray:
        """Interpolate data to common time axis."""
        from scipy.interpolate import interp1d
        
        if len(source_time) == len(target_time):
            return source_data
        
        # Handle datetime interpolation
        if isinstance(source_time[0], datetime):
            # Convert to numeric for interpolation
            time_numeric = np.array([(t - source_time[0]).total_seconds() for t in source_time])
            target_numeric = np.array([(t - source_time[0]).total_seconds() for t in target_time])
            
            f = interp1d(time_numeric, source_data, bounds_error=False, fill_value='extrapolate')
            return f(target_numeric)
        else:
            # Numeric time interpolation
            f = interp1d(source_time, source_data, bounds_error=False, fill_value='extrapolate')
            return f(target_time)
    
    def create_superimposed_netcdf(self, common_time: np.ndarray, mnh_interp: np.ndarray, 
                                  era5_interp: np.ndarray, output_path: str) -> str:
        """Create a new NetCDF file with superimposed data."""
        logger.info(f"Creating superimposed NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        output_file.createDimension('time', len(common_time))
        
        # Create time variable
        time_var = output_file.createVariable('time', 'f8', ('time',))
        time_var.units = 'seconds since 1970-01-01 00:00:00'
        time_var.long_name = 'Common time axis'
        
        # Create data variables
        mnh_var = output_file.createVariable('mnh_swd', 'f4', ('time',))
        mnh_var.long_name = 'MNH SWD (Shortwave Downward) from Mahambo station'
        mnh_var.units = 'W m-2'
        
        era5_var = output_file.createVariable('era5_ssrd', 'f4', ('time',))
        era5_var.long_name = 'ERA5 SSRD (Surface Solar Radiation Downward) - Hourly Average'
        era5_var.units = 'W m-2'
        era5_var.note = 'Converted from J m-2 to W m-2 by dividing by 3600 seconds'
        
        # Store data
        if isinstance(common_time[0], datetime):
            # Convert datetime to seconds since epoch
            epoch = datetime(1970, 1, 1)
            time_seconds = np.array([(t - epoch).total_seconds() for t in common_time])
            time_var[:] = time_seconds
        else:
            time_var[:] = common_time
        
        mnh_var[:] = mnh_interp
        era5_var[:] = era5_interp
        
        # Add global attributes
        output_file.title = "Superimposed MNH vs ERA5 Solar Radiation Data (Corrected Units)"
        output_file.history = f"Created by Corrected MNH-ERA5 Superimposer on {datetime.now().isoformat()}"
        output_file.source_mnh = self.mnh_file_path
        output_file.source_era5 = self.era5_file_path
        output_file.description = "Comparison of MNH SWD and ERA5 SSRD variables with corrected units"
        output_file.note = "ERA5 data converted from accumulated energy (J m-2) to hourly average power (W m-2)"
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def create_2d_timeseries_plot(self, common_time: np.ndarray, mnh_interp: np.ndarray, 
                                 era5_interp: np.ndarray, output_dir: str = ".") -> str:
        """Create a 2D time series plot comparing MNH vs ERA5."""
        logger.info("Creating 2D time series plot...")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        fig.suptitle('MNH vs ERA5 Solar Radiation Comparison (Corrected Units)', fontsize=16, fontweight='bold')
        
        # Plot 1: Individual time series
        if isinstance(common_time[0], datetime):
            ax1.plot(common_time, mnh_interp, 'b-', linewidth=2, label='MNH SWD (Mahambo)', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, label='ERA5 SSRD (Hourly Avg)', alpha=0.8)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax1.set_xlabel('Time')
        else:
            ax1.plot(common_time, mnh_interp, 'b-', linewidth=2, label='MNH SWD (Mahambo)', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, label='ERA5 SSRD (Hourly Avg)', alpha=0.8)
            ax1.set_xlabel('Time Index')
        
        ax1.set_ylabel('Solar Radiation (W m⁻²)')
        ax1.set_title('Time Series Comparison (Both in W m⁻²)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Scatter plot correlation
        valid_mask = ~(np.isnan(mnh_interp) | np.isnan(era5_interp))
        if valid_mask.sum() > 0:
            ax2.scatter(mnh_interp[valid_mask], era5_interp[valid_mask], alpha=0.6, s=20)
            
            # Add 1:1 line
            min_val = np.nanmin([np.nanmin(mnh_interp), np.nanmin(era5_interp)])
            max_val = np.nanmax([np.nanmax(mnh_interp), np.nanmax(era5_interp)])
            ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='1:1 line')
            
            # Calculate correlation
            correlation = np.corrcoef(mnh_interp[valid_mask], era5_interp[valid_mask])[0, 1]
            ax2.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                    transform=ax2.transAxes, fontsize=12, 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax2.set_xlabel('MNH SWD (W m⁻²)')
            ax2.set_ylabel('ERA5 SSRD (W m⁻²)')
            ax2.set_title('Correlation Analysis')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Difference time series
        diff = mnh_interp - era5_interp
        if isinstance(common_time[0], datetime):
            ax3.plot(common_time, diff, 'g-', linewidth=2, alpha=0.8)
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax3.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax3.set_xlabel('Time')
        else:
            ax3.plot(common_time, diff, 'g-', linewidth=2, alpha=0.8)
            ax3.set_xlabel('Time Index')
        
        ax3.set_ylabel('Difference (MNH - ERA5) (W m⁻²)')
        ax3.set_title('Difference Time Series')
        ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax3.grid(True, alpha=0.3)
        
        # Add statistics
        mean_diff = np.nanmean(diff)
        std_diff = np.nanstd(diff)
        ax3.text(0.05, 0.95, f'Mean Diff: {mean_diff:.2f} ± {std_diff:.2f} W m⁻²', 
                transform=ax3.transAxes, fontsize=12,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, 'mnh_vs_era5_solar_radiation_2d_timeseries_corrected.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"2D time series plot saved: {output_path}")
        return output_path
    
    def superimpose(self, output_path: str, create_viz: bool = True) -> str:
        """Main method to superimpose MNH vs ERA5 data."""
        logger.info("Starting corrected MNH vs ERA5 superimposition...")
        
        try:
            # Extract data from both files
            mnh_swd, mnh_time = self.extract_mnh_swd()
            era5_ssrd, era5_time = self.extract_era5_ssrd()
            
            # Align time series
            common_time, mnh_interp, era5_interp = self.align_time_series(
                mnh_time, era5_time, mnh_swd, era5_ssrd
            )
            
            logger.info(f"Aligned data shapes: MNH={mnh_interp.shape}, ERA5={era5_interp.shape}")
            logger.info(f"MNH value range: {np.nanmin(mnh_interp):.2f} to {np.nanmax(mnh_interp):.2f} W m⁻²")
            logger.info(f"ERA5 value range: {np.nanmin(era5_interp):.2f} to {np.nanmax(era5_interp):.2f} W m⁻²")
            
            # Create superimposed NetCDF
            output_file_path = self.create_superimposed_netcdf(
                common_time, mnh_interp, era5_interp, output_path
            )
            
            # Create visualization
            if create_viz:
                viz_path = self.create_2d_timeseries_plot(
                    common_time, mnh_interp, era5_interp,
                    os.path.dirname(output_path)
                )
                logger.info(f"Visualization created: {viz_path}")
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error during superimposition: {e}")
            raise

def main():
    """Main function to run the corrected MNH vs ERA5 superimposition."""
    parser = argparse.ArgumentParser(description='Superimpose MNH vs ERA5 NetCDF files with corrected units')
    parser.add_argument('mnh_file', help='MNH NetCDF file path (should contain Stations.Mahambo.SWD)')
    parser.add_argument('era5_file', help='ERA5 NetCDF file path (should contain ssrd variable)')
    parser.add_argument('--output', '-o', default='superimposed_mnh_era5_corrected.nc', 
                       help='Output NetCDF file path')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization creation')
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
        with CorrectedMNHERA5Superimposer(args.mnh_file, args.era5_file) as superimposer:
            output_path = superimposer.superimpose(
                args.output,
                create_viz=not args.no_viz
            )
            logger.info(f"Superimposition completed successfully! Output: {output_path}")
            
    except Exception as e:
        logger.error(f"Superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
