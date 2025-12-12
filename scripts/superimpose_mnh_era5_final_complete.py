#!/usr/bin/env python3
"""
Final Complete MNH vs ERA5 NetCDF Superimposition Tool

This script properly handles the complete MNH dataset with 5-minute timesteps:
- MNH: SWD variable in Stations.Mahambo group (289 timesteps, 5-min intervals, 24-hour cycle)
- ERA5: ssrd variable (48 time steps, hourly) in J m⁻² (accumulated energy)

Key features:
1. Extract FULL MNH dataset (all 289 timesteps, 0-800+ W m⁻² range)
2. Handle 5-minute timestep structure properly
3. Convert ERA5 from J m⁻² to W m⁻² correctly
4. Robust datetime parsing and time alignment
5. Comprehensive visualization and analysis

Usage:
    python superimpose_mnh_era5_final_complete.py mnh_file.nc era5_file.nc --output output.nc
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
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalCompleteMNHERA5Superimposer:
    """Final, complete class to handle superimposition of MNH vs ERA5 with proper timestep handling."""
    
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
    
    def extract_complete_mnh_swd(self) -> Tuple[np.ndarray, np.ndarray, float]:
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
    
    def extract_era5_ssrd(self) -> Tuple[np.ndarray, np.ndarray, float]:
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
    
    def align_time_series_complete(self, mnh_time: np.ndarray, era5_time: np.ndarray,
                                 mnh_swd: np.ndarray, era5_ssrd: np.ndarray,
                                 mnh_timestep: float, era5_timestep: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Align MNH and ERA5 time series accounting for different temporal resolutions."""
        logger.info("=== ALIGNING TIME SERIES WITH DIFFERENT RESOLUTIONS ===")
        
        # Convert times to datetime
        mnh_time_dt = self.convert_mnh_time_to_datetime(mnh_time, mnh_timestep)
        era5_time_dt = self.convert_era5_time_to_datetime(era5_time)
        
        logger.info(f"MNH time range: {mnh_time_dt[0]} to {mnh_time_dt[-1]}")
        logger.info(f"ERA5 time range: {era5_time_dt[0]} to {era5_time_dt[-1]}")
        
        # Find common time range
        if isinstance(mnh_time_dt[0], datetime) and isinstance(era5_time_dt[0], datetime):
            start_time = max(np.min(mnh_time_dt), np.min(era5_time_dt))
            end_time = min(np.max(mnh_time_dt), np.max(era5_time_dt))
            
            logger.info(f"Common time range: {start_time} to {end_time}")
            
            # Create common time axis (use ERA5 resolution for comparison)
            common_time = []
            current_time = start_time
            while current_time <= end_time:
                common_time.append(current_time)
                current_time += timedelta(seconds=era5_timestep)
            common_time = np.array(common_time)
            
            logger.info(f"Common time axis: {len(common_time)} points at {era5_timestep/3600:.2f}h resolution")
            
            # Interpolate both datasets to common time
            mnh_interp = self._interpolate_to_common_time(mnh_time_dt, mnh_swd, common_time)
            era5_interp = self._interpolate_to_common_time(era5_time_dt, era5_ssrd, common_time)
            
        else:
            # Fallback: use shorter time series
            min_length = min(len(mnh_time), len(era5_time))
            common_time = np.arange(min_length)
            mnh_interp = mnh_swd[:min_length]
            era5_interp = era5_ssrd[:min_length]
            logger.warning("Using fallback time alignment")
        
        logger.info(f"Aligned data shapes: MNH={mnh_interp.shape}, ERA5={era5_interp.shape}")
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
    
    def create_comprehensive_netcdf(self, common_time: np.ndarray, mnh_interp: np.ndarray, 
                                  era5_interp: np.ndarray, output_path: str, 
                                  mnh_timestep: float, era5_timestep: float) -> str:
        """Create a comprehensive NetCDF file with superimposed data."""
        logger.info(f"Creating comprehensive NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        output_file.createDimension('time', len(common_time))
        
        # Create time variable
        time_var = output_file.createVariable('time', 'f8', ('time',))
        time_var.units = 'seconds since 1970-01-01 00:00:00'
        time_var.long_name = 'Common time axis (aligned)'
        
        # Create data variables
        mnh_var = output_file.createVariable('mnh_swd', 'f4', ('time',))
        mnh_var.long_name = 'MNH SWD (Shortwave Downward) from Mahambo station'
        mnh_var.units = 'W m-2'
        mnh_var.description = f'Instantaneous shortwave downward radiation from MNH model (original {mnh_timestep/60:.1f}min timesteps)'
        mnh_var.original_timestep_seconds = mnh_timestep
        mnh_var.original_timestep_minutes = mnh_timestep / 60.0
        
        era5_var = output_file.createVariable('era5_ssrd', 'f4', ('time',))
        era5_var.long_name = 'ERA5 SSRD (Surface Solar Radiation Downward) - Time Average'
        era5_var.units = 'W m-2'
        era5_var.description = f'Time-averaged shortwave downward radiation from ERA5 reanalysis (averaged over {era5_timestep/3600:.2f}h periods)'
        era5_var.original_timestep_seconds = era5_timestep
        era5_var.original_timestep_hours = era5_timestep / 3600.0
        
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
        
        # Add comprehensive global attributes
        output_file.title = "Final Complete MNH vs ERA5 Solar Radiation Data (Corrected Units & Timesteps)"
        output_file.history = f"Created by Final Complete MNH-ERA5 Superimposer on {datetime.now().isoformat()}"
        output_file.source_mnh = self.mnh_file_path
        output_file.source_era5 = self.era5_file_path
        output_file.description = "Complete comparison of MNH SWD and ERA5 SSRD variables with corrected units and proper timestep handling"
        output_file.mnh_timestep_seconds = mnh_timestep
        output_file.mnh_timestep_minutes = mnh_timestep / 60.0
        output_file.era5_timestep_seconds = era5_timestep
        output_file.era5_timestep_hours = era5_timestep / 3600.0
        output_file.unit_conversion = f"ERA5: J m-2 / {era5_timestep} s = W m-2"
        output_file.comparison_note = f"MNH: instantaneous power at {mnh_timestep/60:.1f}min resolution, ERA5: time-averaged power at {era5_timestep/3600:.2f}h resolution"
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def create_comprehensive_visualization(self, common_time: np.ndarray, mnh_interp: np.ndarray, 
                                        era5_interp: np.ndarray, mnh_timestep: float, era5_timestep: float,
                                        output_dir: str = ".") -> str:
        """Create comprehensive visualization showing the complete comparison."""
        logger.info("Creating comprehensive visualization...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))
        
        # Grid layout: 4 rows, 2 columns
        gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)
        
        # Plot 1: Complete time series comparison
        ax1 = fig.add_subplot(gs[0, :])
        if isinstance(common_time[0], datetime):
            ax1.plot(common_time, mnh_interp, 'b-', linewidth=2, 
                    label=f'MNH SWD (Mahambo) - {mnh_timestep/60:.1f}min timesteps', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, 
                    label=f'ERA5 SSRD - {era5_timestep/3600:.2f}h averages', alpha=0.8)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax1.set_xlabel('Time')
        else:
            ax1.plot(common_time, mnh_interp, 'b-', linewidth=2, 
                    label=f'MNH SWD (Mahambo) - {mnh_timestep/60:.1f}min timesteps', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, 
                    label=f'ERA5 SSRD - {era5_timestep/3600:.2f}h averages', alpha=0.8)
            ax1.set_xlabel('Time Index')
        
        ax1.set_ylabel('Solar Radiation (W m⁻²)')
        ax1.set_title(f'Final Complete MNH vs ERA5 Solar Radiation Comparison\nBoth in W m⁻² - Different Temporal Resolutions', 
                     fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Scatter plot correlation
        ax2 = fig.add_subplot(gs[1, 0])
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
            
            ax2.set_xlabel(f'MNH SWD (W m⁻²) - {mnh_timestep/60:.1f}min')
            ax2.set_ylabel(f'ERA5 SSRD (W m⁻²) - {era5_timestep/3600:.2f}h')
            ax2.set_title('Correlation Analysis')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Difference time series
        ax3 = fig.add_subplot(gs[1, 1])
        diff = mnh_interp - era5_interp
        if isinstance(common_time[0], datetime):
            ax3.plot(common_time, diff, 'g-', linewidth=2, alpha=0.8)
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax3.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax3.set_xlabel('Time')
        else:
            ax3.plot(common_time, diff, 'g-', linewidth=2, alpha=0.8)
            ax3.set_xlabel('Time Index')
        
        ax3.set_ylabel('Difference (MNH - ERA5) (W m⁻²)')
        ax3.set_title(f'Difference Time Series\nMNH {mnh_timestep/60:.1f}min - ERA5 {era5_timestep/3600:.2f}h')
        ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax3.grid(True, alpha=0.3)
        
        # Add statistics
        mean_diff = np.nanmean(diff)
        std_diff = np.nanstd(diff)
        ax3.text(0.05, 0.95, f'Mean Diff: {mean_diff:.2f} ± {std_diff:.2f} W m⁻²', 
                transform=ax3.transAxes, fontsize=12,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 4: Data range comparison
        ax4 = fig.add_subplot(gs[2, :])
        if isinstance(common_time[0], datetime):
            # Create time-of-day analysis
            hours = np.array([t.hour + t.minute/60.0 for t in common_time])
            ax4.scatter(hours, mnh_interp, c='blue', alpha=0.6, s=20, label=f'MNH SWD ({mnh_timestep/60:.1f}min)')
            ax4.scatter(hours, era5_interp, c='red', alpha=0.6, s=20, label=f'ERA5 SSRD ({era5_timestep/3600:.2f}h)')
            ax4.set_xlabel('Hour of Day')
            ax4.set_ylabel('Solar Radiation (W m⁻²)')
            ax4.set_title('Solar Radiation by Time of Day')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            ax4.set_xlim(0, 24)
        
        # Plot 5: Statistical summary
        ax5 = fig.add_subplot(gs[3, :])
        # Create box plots for comparison
        data_to_plot = [mnh_interp[valid_mask], era5_interp[valid_mask]]
        labels = [f'MNH SWD\n({mnh_timestep/60:.1f}min)', f'ERA5 SSRD\n({era5_timestep/3600:.2f}h)']
        
        bp = ax5.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightcoral')
        
        ax5.set_ylabel('Solar Radiation (W m⁻²)')
        ax5.set_title('Statistical Distribution Comparison')
        ax5.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f'MNH: mean={np.nanmean(mnh_interp):.1f}, std={np.nanstd(mnh_interp):.1f}, max={np.nanmax(mnh_interp):.1f} W m⁻²\n'
        stats_text += f'ERA5: mean={np.nanmean(era5_interp):.1f}, std={np.nanstd(era5_interp):.1f}, max={np.nanmax(era5_interp):.1f} W m⁻²'
        ax5.text(0.02, 0.98, stats_text, transform=ax5.transAxes, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                verticalalignment='top')
        
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, 'final_complete_mnh_vs_era5_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Comprehensive visualization saved: {output_path}")
        return output_path
    
    def superimpose_complete(self, output_path: str, create_viz: bool = True) -> str:
        """Main method to superimpose MNH vs ERA5 data with complete handling."""
        logger.info("=== STARTING FINAL COMPLETE MNH vs ERA5 SUPERIMPOSITION ===")
        
        try:
            # Extract complete data from both files
            mnh_swd, mnh_time, mnh_timestep = self.extract_complete_mnh_swd()
            era5_ssrd, era5_time, era5_timestep = self.extract_era5_ssrd()
            
            # Align time series with proper resolution handling
            common_time, mnh_interp, era5_interp = self.align_time_series_complete(
                mnh_time, era5_time, mnh_swd, era5_ssrd, mnh_timestep, era5_timestep
            )
            
            logger.info(f"=== FINAL ALIGNED DATA SUMMARY ===")
            logger.info(f"Common time points: {len(common_time)}")
            logger.info(f"MNH interpolated range: {np.nanmin(mnh_interp):.2f} to {np.nanmax(mnh_interp):.2f} W m⁻²")
            logger.info(f"ERA5 interpolated range: {np.nanmin(era5_interp):.2f} to {np.nanmax(era5_interp):.2f} W m⁻²")
            logger.info(f"MNH timestep: {mnh_timestep} seconds ({mnh_timestep/60:.1f} minutes)")
            logger.info(f"ERA5 timestep: {era5_timestep} seconds ({era5_timestep/3600:.2f} hours)")
            
            # Create comprehensive NetCDF
            output_file_path = self.create_comprehensive_netcdf(
                common_time, mnh_interp, era5_interp, output_path, mnh_timestep, era5_timestep
            )
            
            # Create comprehensive visualization
            if create_viz:
                viz_path = self.create_comprehensive_visualization(
                    common_time, mnh_interp, era5_interp, mnh_timestep, era5_timestep,
                    os.path.dirname(output_path)
                )
                logger.info(f"Comprehensive visualization created: {viz_path}")
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error during complete superimposition: {e}")
            raise

def main():
    """Main function to run the final complete MNH vs ERA5 superimposition."""
    parser = argparse.ArgumentParser(description='Final Complete MNH vs ERA5 NetCDF superimposition with proper timestep handling')
    parser.add_argument('mnh_file', help='MNH NetCDF file path (should contain Stations.Mahambo.SWD)')
    parser.add_argument('era5_file', help='ERA5 NetCDF file path (should contain ssrd variable)')
    parser.add_argument('--output', '-o', default='final_complete_superimposed_mnh_era5.nc', 
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
        with FinalCompleteMNHERA5Superimposer(args.mnh_file, args.era5_file) as superimposer:
            output_path = superimposer.superimpose_complete(
                args.output,
                create_viz=not args.no_viz
            )
            logger.info(f"=== FINAL COMPLETE SUPERIMPOSITION SUCCESSFUL ===")
            logger.info(f"Output: {output_path}")
            
    except Exception as e:
        logger.error(f"Final complete superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
