#!/usr/bin/env python3
"""
Simple Plotting Script for Basic MNH vs ERA5 Superimposition

This script reads the basic superimposition NetCDF file and creates simple visualizations
without complex datetime handling to avoid the object array issues.

Usage:
    python plot_basic_superimposition.py input.nc --output output.png
"""

import argparse
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_basic_superimposition(input_file: str, output_file: str = None):
    """Create simple plots from the basic superimposition NetCDF file."""
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Open the NetCDF file
    with nc.Dataset(input_file, 'r') as ds:
        logger.info(f"Reading data from: {input_file}")
        
        # Extract data
        mnh_time = ds.variables['mnh_time'][:]
        mnh_swd = ds.variables['mnh_swd'][:]
        era5_time = ds.variables['era5_time'][:]
        era5_ssrd = ds.variables['era5_ssrd'][:]
        
        # Get metadata
        mnh_units = getattr(ds.variables['mnh_swd'], 'units', 'W m-2')
        era5_units = getattr(ds.variables['era5_ssrd'], 'units', 'W m-2')
        
        logger.info(f"MNH data: {len(mnh_swd)} points, range {np.nanmin(mnh_swd):.2f} to {np.nanmax(mnh_swd):.2f} {mnh_units}")
        logger.info(f"ERA5 data: {len(era5_ssrd)} points, range {np.nanmin(era5_ssrd):.2f} to {np.nanmax(era5_ssrd):.2f} {era5_units}")
        
        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Basic MNH vs ERA5 Solar Radiation Comparison\nFull Range Data Preserved', fontsize=16, fontweight='bold')
        
        # Plot 1: MNH time series (full range)
        ax1 = axes[0, 0]
        ax1.plot(mnh_time, mnh_swd, 'b-', linewidth=2, alpha=0.8, label='MNH SWD (5-min)')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel(f'Solar Radiation ({mnh_units})')
        ax1.set_title(f'MNH SWD Time Series - FULL RANGE\n0.00 to {np.nanmax(mnh_swd):.2f} {mnh_units}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: ERA5 time series
        ax2 = axes[0, 1]
        ax2.plot(era5_time, era5_ssrd, 'r-', linewidth=2, alpha=0.8, label='ERA5 SSRD (1-hour)')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel(f'Solar Radiation ({era5_units})')
        ax2.set_title(f'ERA5 SSRD Time Series\n0.00 to {np.nanmax(era5_ssrd):.2f} {era5_units}')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Data range comparison
        ax3 = axes[1, 0]
        # Create box plots for comparison
        data_to_plot = [mnh_swd, era5_ssrd]
        labels = [f'MNH SWD\n(5-min)\nFULL RANGE', f'ERA5 SSRD\n(1-hour)']
        
        bp = ax3.boxplot(data_to_plot, labels=labels, patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightcoral')
        
        ax3.set_ylabel(f'Solar Radiation ({mnh_units})')
        ax3.set_title('Statistical Distribution Comparison')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Scatter plot (using common time range)
        ax4 = axes[1, 1]
        
        # Find common time range for comparison
        mnh_start = mnh_time[0]
        mnh_end = mnh_time[-1]
        era5_start = era5_time[0]
        era5_end = era5_time[-1]
        
        # Filter ERA5 data to MNH time range if possible
        if era5_start <= mnh_start and era5_end >= mnh_end:
            # ERA5 covers MNH time range
            era5_mask = (era5_time >= mnh_start) & (era5_time <= mnh_end)
            era5_filtered = era5_ssrd[era5_mask]
            era5_time_filtered = era5_time[era5_mask]
            
            # Interpolate MNH to ERA5 time points for comparison
            from scipy.interpolate import interp1d
            f = interp1d(mnh_time, mnh_swd, bounds_error=False, fill_value='extrapolate')
            mnh_interp = f(era5_time_filtered)
            
            # Create scatter plot
            ax4.scatter(mnh_interp, era5_filtered, alpha=0.6, s=30, c='green')
            
            # Add 1:1 line
            min_val = np.nanmin([np.nanmin(mnh_interp), np.nanmin(era5_filtered)])
            max_val = np.nanmax([np.nanmax(mnh_interp), np.nanmax(era5_filtered)])
            ax4.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='1:1 line')
            
            # Calculate correlation
            valid_mask = ~(np.isnan(mnh_interp) | np.isnan(era5_filtered))
            if valid_mask.sum() > 0:
                correlation = np.corrcoef(mnh_interp[valid_mask], era5_filtered[valid_mask])[0, 1]
                ax4.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                        transform=ax4.transAxes, fontsize=12, 
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax4.set_xlabel(f'MNH SWD ({mnh_units}) - Interpolated to ERA5 time')
            ax4.set_ylabel(f'ERA5 SSRD ({era5_units})')
            ax4.set_title('Correlation Analysis\nMNH interpolated to ERA5 time points')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
        else:
            # Time ranges don't overlap well, show info
            ax4.text(0.5, 0.5, f'Time ranges:\nMNH: {mnh_start:.0f} to {mnh_end:.0f}s\nERA5: {era5_start:.0f} to {era5_end:.0f}s\n\nNo direct comparison possible', 
                    transform=ax4.transAxes, ha='center', va='center', fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
            ax4.set_title('Time Range Comparison')
            ax4.set_xlabel('')
            ax4.set_ylabel('')
        
        # Add statistics text
        stats_text = f'MNH (FULL RANGE): mean={np.nanmean(mnh_swd):.1f}, std={np.nanstd(mnh_swd):.1f}, max={np.nanmax(mnh_swd):.1f} {mnh_units}\n'
        stats_text += f'ERA5: mean={np.nanmean(era5_ssrd):.1f}, std={np.nanstd(era5_ssrd):.1f}, max={np.nanmax(era5_ssrd):.1f} {era5_units}'
        
        fig.text(0.02, 0.02, stats_text, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        if output_file is None:
            output_file = input_file.replace('.nc', '_plot.png')
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Plot saved: {output_file}")

def main():
    """Main function to create plots from basic superimposition NetCDF."""
    parser = argparse.ArgumentParser(description='Create plots from basic MNH vs ERA5 superimposition NetCDF')
    parser.add_argument('input_file', help='Input NetCDF file path')
    parser.add_argument('--output', '-o', help='Output PNG file path (default: input_plot.png)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        plot_basic_superimposition(args.input_file, args.output)
        logger.info("Plotting completed successfully!")
        
    except Exception as e:
        logger.error(f"Plotting failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
