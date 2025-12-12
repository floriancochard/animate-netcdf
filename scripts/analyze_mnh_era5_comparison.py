#!/usr/bin/env python3
"""
Comprehensive MNH vs ERA5 Analysis Tool

This script analyzes and compares MNH and ERA5 NetCDF files:
- MNH 1508: SWD variable in Stations.Mahambo group
- MNH 1608: SWD variable in Stations.Mahambo group  
- ERA5: ssrd variable

Creates comprehensive 2D time series plots and statistical analysis.

Usage:
    python analyze_mnh_era5_comparison.py --mnh-1508 mnh_1508.nc --mnh-1608 mnh_1608.nc --era5 era5.nc --output-dir output/
"""

import argparse
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, Tuple, List, Optional
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MNHERA5Analyzer:
    """Comprehensive analyzer for MNH vs ERA5 data comparison."""
    
    def __init__(self, mnh_1508_path: str, mnh_1608_path: str, era5_path: str):
        """Initialize with file paths."""
        self.mnh_1508_path = mnh_1508_path
        self.mnh_1608_path = mnh_1608_path
        self.era5_path = era5_path
        self.mnh_1508_file = None
        self.mnh_1608_file = None
        self.era5_file = None
        
    def __enter__(self):
        """Context manager entry."""
        self.mnh_1508_file = nc.Dataset(self.mnh_1508_path, 'r')
        self.mnh_1608_file = nc.Dataset(self.mnh_1608_path, 'r')
        self.era5_file = nc.Dataset(self.era5_path, 'r')
        logger.info(f"Opened MNH 1508: {self.mnh_1508_path}")
        logger.info(f"Opened MNH 1608: {self.mnh_1608_path}")
        logger.info(f"Opened ERA5: {self.era5_path}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.mnh_1508_file:
            self.mnh_1508_file.close()
        if self.mnh_1608_file:
            self.mnh_1608_file.close()
        if self.era5_file:
            self.era5_file.close()
    
    def extract_mnh_swd(self, mnh_file: nc.Dataset, label: str) -> Tuple[np.ndarray, np.ndarray]:
        """Extract SWD variable from MNH file in Stations.Mahambo group."""
        try:
            mahambo_group = mnh_file.groups['Stations'].groups['Mahambo']
            swd_var = mahambo_group.variables['SWD']
            swd_data = swd_var[:]
            
            time_var = mnh_file.variables['time_station']
            time_data = time_var[:]
            
            logger.info(f"{label} SWD data shape: {swd_data.shape}")
            logger.info(f"{label} time data shape: {time_data.shape}")
            
            return swd_data, time_data
            
        except Exception as e:
            logger.error(f"Error extracting {label} SWD data: {e}")
            raise
    
    def extract_era5_ssrd(self) -> Tuple[np.ndarray, np.ndarray]:
        """Extract ssrd variable from ERA5 file."""
        try:
            ssrd_var = self.era5_file.variables['ssrd']
            ssrd_data = ssrd_var[:, 0, 0]  # Remove spatial dimensions
            
            time_var = self.era5_file.variables['valid_time']
            time_data = time_var[:]
            
            logger.info(f"ERA5 ssrd data shape: {ssrd_data.shape}")
            logger.info(f"ERA5 time data shape: {time_data.shape}")
            
            return ssrd_data, time_data
            
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
    
    def align_all_time_series(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Align all three time series to common time axis."""
        logger.info("Aligning all time series...")
        
        # Extract data
        mnh_1508_swd, mnh_1508_time = self.extract_mnh_swd(self.mnh_1508_file, "MNH 1508")
        mnh_1608_swd, mnh_1608_time = self.extract_mnh_swd(self.mnh_1608_file, "MNH 1608")
        era5_ssrd, era5_time = self.extract_era5_ssrd()
        
        # Convert times to datetime
        mnh_1508_time_dt = self.convert_time_to_datetime(
            mnh_1508_time, 
            getattr(self.mnh_1508_file.variables['time_station'], 'units', 'unknown')
        )
        mnh_1608_time_dt = self.convert_time_to_datetime(
            mnh_1608_time, 
            getattr(self.mnh_1608_file.variables['time_station'], 'units', 'unknown')
        )
        era5_time_dt = self.convert_time_to_datetime(
            era5_time, 
            getattr(self.era5_file.variables['valid_time'], 'units', 'unknown')
        )
        
        # Find common time range
        if (isinstance(mnh_1508_time_dt[0], datetime) and 
            isinstance(mnh_1608_time_dt[0], datetime) and 
            isinstance(era5_time_dt[0], datetime)):
            
            start_time = max(np.min(mnh_1508_time_dt), np.min(mnh_1608_time_dt), np.min(era5_time_dt))
            end_time = min(np.max(mnh_1508_time_dt), np.max(mnh_1608_time_dt), np.max(era5_time_dt))
            
            # Create common time axis (hourly)
            common_time = []
            current_time = start_time
            while current_time <= end_time:
                common_time.append(current_time)
                current_time += timedelta(hours=1)
            common_time = np.array(common_time)
            
            # Interpolate all datasets to common time
            mnh_1508_interp = self._interpolate_to_common_time(mnh_1508_time_dt, mnh_1508_swd, common_time)
            mnh_1608_interp = self._interpolate_to_common_time(mnh_1608_time_dt, mnh_1608_swd, common_time)
            era5_interp = self._interpolate_to_common_time(era5_time_dt, era5_ssrd, common_time)
            
        else:
            # Fallback: use shortest time series
            min_length = min(len(mnh_1508_time), len(mnh_1608_time), len(era5_time))
            common_time = np.arange(min_length)
            mnh_1508_interp = mnh_1508_swd[:min_length]
            mnh_1608_interp = mnh_1608_swd[:min_length]
            era5_interp = era5_ssrd[:min_length]
        
        logger.info(f"Aligned time series length: {len(common_time)}")
        return common_time, mnh_1508_interp, mnh_1608_interp, era5_interp
    
    def _interpolate_to_common_time(self, source_time: np.ndarray, source_data: np.ndarray, 
                                   target_time: np.ndarray) -> np.ndarray:
        """Interpolate data to common time axis."""
        from scipy.interpolate import interp1d
        
        if len(source_time) == len(target_time):
            return source_data
        
        if isinstance(source_time[0], datetime):
            time_numeric = np.array([(t - source_time[0]).total_seconds() for t in source_time])
            target_numeric = np.array([(t - source_time[0]).total_seconds() for t in target_time])
            
            f = interp1d(time_numeric, source_data, bounds_error=False, fill_value='extrapolate')
            return f(target_numeric)
        else:
            f = interp1d(source_time, source_data, bounds_error=False, fill_value='extrapolate')
            return f(target_time)
    
    def create_comprehensive_analysis_plot(self, common_time: np.ndarray, mnh_1508_interp: np.ndarray,
                                         mnh_1608_interp: np.ndarray, era5_interp: np.ndarray,
                                         output_dir: str = ".") -> str:
        """Create comprehensive 2D time series analysis plot."""
        logger.info("Creating comprehensive analysis plot...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))
        
        # Grid layout: 3 rows, 3 columns
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: All time series comparison
        ax1 = fig.add_subplot(gs[0, :])
        if isinstance(common_time[0], datetime):
            ax1.plot(common_time, mnh_1508_interp, 'b-', linewidth=2, label='MNH 1508 SWD', alpha=0.8)
            ax1.plot(common_time, mnh_1608_interp, 'g-', linewidth=2, label='MNH 1608 SWD', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, label='ERA5 SSRD', alpha=0.8)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax1.set_xlabel('Time')
        else:
            ax1.plot(common_time, mnh_1508_interp, 'b-', linewidth=2, label='MNH 1508 SWD', alpha=0.8)
            ax1.plot(common_time, mnh_1608_interp, 'g-', linewidth=2, label='MNH 1608 SWD', alpha=0.8)
            ax1.plot(common_time, era5_interp, 'r-', linewidth=2, label='ERA5 SSRD', alpha=0.8)
            ax1.set_xlabel('Time Index')
        
        ax1.set_ylabel('Solar Radiation (W m⁻²)')
        ax1.set_title('Comprehensive MNH vs ERA5 Solar Radiation Comparison', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: MNH 1508 vs ERA5 correlation
        ax2 = fig.add_subplot(gs[1, 0])
        valid_mask = ~(np.isnan(mnh_1508_interp) | np.isnan(era5_interp))
        if valid_mask.sum() > 0:
            ax2.scatter(mnh_1508_interp[valid_mask], era5_interp[valid_mask], alpha=0.6, s=20, color='blue')
            correlation = np.corrcoef(mnh_1508_interp[valid_mask], era5_interp[valid_mask])[0, 1]
            ax2.text(0.05, 0.95, f'Corr: {correlation:.3f}', transform=ax2.transAxes, fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            min_val = np.nanmin([np.nanmin(mnh_1508_interp), np.nanmin(era5_interp)])
            max_val = np.nanmax([np.nanmax(mnh_1508_interp), np.nanmax(era5_interp)])
            ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
            
            ax2.set_xlabel('MNH 1508 SWD (W m⁻²)')
            ax2.set_ylabel('ERA5 SSRD (W m⁻²)')
            ax2.set_title('MNH 1508 vs ERA5')
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: MNH 1608 vs ERA5 correlation
        ax3 = fig.add_subplot(gs[1, 1])
        valid_mask = ~(np.isnan(mnh_1608_interp) | np.isnan(era5_interp))
        if valid_mask.sum() > 0:
            ax3.scatter(mnh_1608_interp[valid_mask], era5_interp[valid_mask], alpha=0.6, s=20, color='green')
            correlation = np.corrcoef(mnh_1608_interp[valid_mask], era5_interp[valid_mask])[0, 1]
            ax3.text(0.05, 0.95, f'Corr: {correlation:.3f}', transform=ax3.transAxes, fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            min_val = np.nanmin([np.nanmin(mnh_1608_interp), np.nanmin(era5_interp)])
            max_val = np.nanmax([np.nanmax(mnh_1608_interp), np.nanmax(era5_interp)])
            ax3.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
            
            ax3.set_xlabel('MNH 1608 SWD (W m⁻²)')
            ax3.set_ylabel('ERA5 SSRD (W m⁻²)')
            ax3.set_title('MNH 1608 vs ERA5')
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: MNH 1508 vs MNH 1608 correlation
        ax4 = fig.add_subplot(gs[1, 2])
        valid_mask = ~(np.isnan(mnh_1508_interp) | np.isnan(mnh_1608_interp))
        if valid_mask.sum() > 0:
            ax4.scatter(mnh_1508_interp[valid_mask], mnh_1608_interp[valid_mask], alpha=0.6, s=20, color='purple')
            correlation = np.corrcoef(mnh_1508_interp[valid_mask], mnh_1608_interp[valid_mask])[0, 1]
            ax4.text(0.05, 0.95, f'Corr: {correlation:.3f}', transform=ax4.transAxes, fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            min_val = np.nanmin([np.nanmin(mnh_1508_interp), np.nanmin(mnh_1608_interp)])
            max_val = np.nanmax([np.nanmax(mnh_1508_interp), np.nanmax(mnh_1608_interp)])
            ax4.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
            
            ax4.set_xlabel('MNH 1508 SWD (W m⁻²)')
            ax4.set_ylabel('MNH 1608 SWD (W m⁻²)')
            ax4.set_title('MNH 1508 vs MNH 1608')
            ax4.grid(True, alpha=0.3)
        
        # Plot 5: Difference time series
        ax5 = fig.add_subplot(gs[2, :])
        diff_1508 = mnh_1508_interp - era5_interp
        diff_1608 = mnh_1608_interp - era5_interp
        
        if isinstance(common_time[0], datetime):
            ax5.plot(common_time, diff_1508, 'b-', linewidth=2, label='MNH 1508 - ERA5', alpha=0.8)
            ax5.plot(common_time, diff_1608, 'g-', linewidth=2, label='MNH 1608 - ERA5', alpha=0.8)
            ax5.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax5.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax5.set_xlabel('Time')
        else:
            ax5.plot(common_time, diff_1508, 'b-', linewidth=2, label='MNH 1508 - ERA5', alpha=0.8)
            ax5.plot(common_time, diff_1608, 'g-', linewidth=2, label='MNH 1608 - ERA5', alpha=0.8)
            ax5.set_xlabel('Time Index')
        
        ax5.set_ylabel('Difference (W m⁻²)')
        ax5.set_title('Difference Time Series (MNH - ERA5)', fontsize=14, fontweight='bold')
        ax5.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Add statistics
        mean_diff_1508 = np.nanmean(diff_1508)
        std_diff_1508 = np.nanstd(diff_1508)
        mean_diff_1608 = np.nanmean(diff_1608)
        std_diff_1608 = np.nanstd(diff_1608)
        
        stats_text = f'MNH 1508 - ERA5: {mean_diff_1508:.2f} ± {std_diff_1508:.2f} W m⁻²\n'
        stats_text += f'MNH 1608 - ERA5: {mean_diff_1608:.2f} ± {std_diff_1608:.2f} W m⁻²'
        
        ax5.text(0.02, 0.98, stats_text, transform=ax5.transAxes, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                verticalalignment='top')
        
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, 'comprehensive_mnh_vs_era5_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Comprehensive analysis plot saved: {output_path}")
        return output_path
    
    def create_statistical_summary(self, common_time: np.ndarray, mnh_1508_interp: np.ndarray,
                                 mnh_1608_interp: np.ndarray, era5_interp: np.ndarray,
                                 output_dir: str = ".") -> str:
        """Create statistical summary and save to file."""
        logger.info("Creating statistical summary...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate statistics
        stats = {
            'MNH_1508_SWD': {
                'mean': np.nanmean(mnh_1508_interp),
                'std': np.nanstd(mnh_1508_interp),
                'min_val': np.nanmin(mnh_1508_interp),
                'max_val': np.nanmax(mnh_1508_interp),
                'count': np.sum(~np.isnan(mnh_1508_interp))
            },
            'MNH_1608_SWD': {
                'mean': np.nanmean(mnh_1608_interp),
                'std': np.nanstd(mnh_1608_interp),
                'min_val': np.nanmin(mnh_1608_interp),
                'max_val': np.nanmax(mnh_1608_interp),
                'count': np.sum(~np.isnan(mnh_1608_interp))
            },
            'ERA5_SSRD': {
                'mean': np.nanmean(era5_interp),
                'std': np.nanstd(era5_interp),
                'min_val': np.nanmin(era5_interp),
                'max_val': np.nanmax(era5_interp),
                'count': np.sum(~np.isnan(era5_interp))
            }
        }
        
        # Calculate correlations
        valid_mask_1508 = ~(np.isnan(mnh_1508_interp) | np.isnan(era5_interp))
        valid_mask_1608 = ~(np.isnan(mnh_1608_interp) | np.isnan(era5_interp))
        valid_mask_mnh = ~(np.isnan(mnh_1508_interp) | np.isnan(mnh_1608_interp))
        
        if valid_mask_1508.sum() > 1:
            stats['correlation_MNH1508_vs_ERA5'] = np.corrcoef(
                mnh_1508_interp[valid_mask_1508], era5_interp[valid_mask_1508]
            )[0, 1]
        
        if valid_mask_1608.sum() > 1:
            stats['correlation_MNH1608_vs_ERA5'] = np.corrcoef(
                mnh_1608_interp[valid_mask_1608], era5_interp[valid_mask_1608]
            )[0, 1]
        
        if valid_mask_mnh.sum() > 1:
            stats['correlation_MNH1508_vs_MNH1608'] = np.corrcoef(
                mnh_1508_interp[valid_mask_mnh], mnh_1608_interp[valid_mask_mnh]
            )[0, 1]
        
        # Calculate differences
        diff_1508 = mnh_1508_interp - era5_interp
        diff_1608 = mnh_1608_interp - era5_interp
        
        stats['difference_MNH1508_vs_ERA5'] = {
            'mean': np.nanmean(diff_1508),
            'std': np.nanstd(diff_1508),
            'rmse': np.sqrt(np.nanmean(diff_1508**2)),
            'mae': np.nanmean(np.abs(diff_1508))
        }
        
        stats['difference_MNH1608_vs_ERA5'] = {
            'mean': np.nanmean(diff_1608),
            'std': np.nanstd(diff_1608),
            'rmse': np.sqrt(np.nanmean(diff_1608**2)),
            'mae': np.nanmean(np.abs(diff_1608))
        }
        
        # Save to file
        output_path = os.path.join(output_dir, 'statistical_summary.txt')
        with open(output_path, 'w') as f:
            f.write("MNH vs ERA5 Solar Radiation Analysis - Statistical Summary\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Time Series Length: {len(common_time)}\n\n")
            
            f.write("DESCRIPTIVE STATISTICS:\n")
            f.write("-" * 30 + "\n")
            for var_name, var_stats in stats.items():
                if isinstance(var_stats, dict) and 'mean' in var_stats:
                    f.write(f"\n{var_name}:\n")
                    f.write(f"  Mean: {var_stats['mean']:.2f} W m⁻²\n")
                    f.write(f"  Std:  {var_stats['std']:.2f} W m⁻²\n")
                    f.write(f"  Min:  {var_stats['min_val']:.2f} W m⁻²\n")
                    f.write(f"  Max:  {var_stats['max_val']:.2f} W m⁻²\n")
                    f.write(f"  Count: {var_stats['count']}\n")
            
            f.write("\nCORRELATION ANALYSIS:\n")
            f.write("-" * 30 + "\n")
            for key, value in stats.items():
                if key.startswith('correlation_'):
                    f.write(f"{key}: {value:.3f}\n")
            
            f.write("\nDIFFERENCE ANALYSIS:\n")
            f.write("-" * 30 + "\n")
            for key, value in stats.items():
                if key.startswith('difference_'):
                    f.write(f"\n{key}:\n")
                    f.write(f"  Mean Difference: {value['mean']:.2f} W m⁻²\n")
                    f.write(f"  Std Difference:  {value['std']:.2f} W m⁻²\n")
                    f.write(f"  RMSE:            {value['rmse']:.2f} W m⁻²\n")
                    f.write(f"  MAE:             {value['mae']:.2f} W m⁻²\n")
        
        logger.info(f"Statistical summary saved: {output_path}")
        return output_path
    
    def analyze(self, output_dir: str = ".") -> Dict[str, str]:
        """Main analysis method."""
        logger.info("Starting comprehensive MNH vs ERA5 analysis...")
        
        try:
            # Align all time series
            common_time, mnh_1508_interp, mnh_1608_interp, era5_interp = self.align_all_time_series()
            
            logger.info(f"Aligned data shapes: MNH1508={mnh_1508_interp.shape}, "
                       f"MNH1608={mnh_1608_interp.shape}, ERA5={era5_interp.shape}")
            
            # Create comprehensive plot
            plot_path = self.create_comprehensive_analysis_plot(
                common_time, mnh_1508_interp, mnh_1608_interp, era5_interp, output_dir
            )
            
            # Create statistical summary
            stats_path = self.create_statistical_summary(
                common_time, mnh_1508_interp, mnh_1608_interp, era5_interp, output_dir
            )
            
            return {
                'plot': plot_path,
                'statistics': stats_path
            }
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise

def main():
    """Main function to run the comprehensive analysis."""
    parser = argparse.ArgumentParser(description='Comprehensive MNH vs ERA5 analysis')
    parser.add_argument('--mnh-1508', required=True, help='MNH 1508 NetCDF file path')
    parser.add_argument('--mnh-1608', required=True, help='MNH 1608 NetCDF file path')
    parser.add_argument('--era5', required=True, help='ERA5 NetCDF file path')
    parser.add_argument('--output-dir', '-o', default='data/output', help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if files exist
    for file_path in [args.mnh_1508, args.mnh_1608, args.era5]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
    
    try:
        with MNHERA5Analyzer(args.mnh_1508, args.mnh_1608, args.era5) as analyzer:
            results = analyzer.analyze(args.output_dir)
            logger.info(f"Analysis completed successfully!")
            logger.info(f"Plot: {results['plot']}")
            logger.info(f"Statistics: {results['statistics']}")
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
