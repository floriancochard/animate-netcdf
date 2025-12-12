#!/usr/bin/env python3
"""
NetCDF Superimposition Tool

This script superimposes two NetCDF files with different data structures by:
1. Interpolating data to common coordinate systems
2. Handling different grid resolutions and time dimensions
3. Creating visualizations of the superimposed data
4. Saving the result as a new NetCDF file

Usage:
    python superimpose_netcdf.py file1.nc file2.nc --output output.nc --variable1 var1 --variable2 var2
"""

import argparse
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import griddata, interp1d
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, Tuple, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetCDFSuperimposer:
    """Class to handle superimposition of NetCDF files with different structures."""
    
    def __init__(self, file1_path: str, file2_path: str):
        """Initialize with two NetCDF file paths."""
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.file1 = None
        self.file2 = None
        self.output_file = None
        
    def __enter__(self):
        """Context manager entry."""
        self.file1 = nc.Dataset(self.file1_path, 'r')
        self.file2 = nc.Dataset(self.file2_path, 'r')
        logger.info(f"Opened files: {self.file1_path} and {self.file2_path}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.file1:
            self.file1.close()
        if self.file2:
            self.file2.close()
        if self.output_file:
            self.output_file.close()
            
    def analyze_files(self) -> Dict:
        """Analyze the structure of both NetCDF files."""
        logger.info("Analyzing NetCDF file structures...")
        
        analysis = {
            'file1': {
                'dimensions': dict(self.file1.dimensions),
                'variables': list(self.file1.variables.keys()),
                'data_vars': {},
                'coords': {}
            },
            'file2': {
                'dimensions': dict(self.file2.dimensions),
                'variables': list(self.file2.variables.keys()),
                'data_vars': {},
                'coords': {}
            }
        }
        
        # Analyze file 1
        for var_name in self.file1.variables:
            var = self.file1.variables[var_name]
            if hasattr(var, 'shape') and len(var.shape) > 0:
                if var_name in ['latitude', 'longitude', 'time', 'level', 'time_station']:
                    analysis['file1']['coords'][var_name] = {
                        'shape': var.shape,
                        'dtype': var.dtype,
                        'long_name': getattr(var, 'long_name', 'No description')
                    }
                else:
                    analysis['file1']['data_vars'][var_name] = {
                        'shape': var.shape,
                        'dtype': var.dtype,
                        'long_name': getattr(var, 'long_name', 'No description')
                    }
        
        # Analyze file 2
        for var_name in self.file2.variables:
            var = self.file2.variables[var_name]
            if hasattr(var, 'shape') and len(var.shape) > 0:
                if var_name in ['latitude', 'longitude', 'time', 'level', 'valid_time']:
                    analysis['file2']['coords'][var_name] = {
                        'shape': var.shape,
                        'dtype': var.dtype,
                        'long_name': getattr(var, 'long_name', 'No description')
                    }
                else:
                    analysis['file2']['data_vars'][var_name] = {
                        'shape': var.shape,
                        'dtype': var.dtype,
                        'long_name': getattr(var, 'long_name', 'No description')
                    }
        
        logger.info(f"File 1: {len(analysis['file1']['data_vars'])} data variables, {len(analysis['file1']['coords'])} coordinate variables")
        logger.info(f"File 2: {len(analysis['file2']['data_vars'])} data variables, {len(analysis['file2']['coords'])} coordinate variables")
        
        return analysis
    
    def get_coordinate_system(self, file_obj: nc.Dataset) -> Dict:
        """Extract coordinate system information from a NetCDF file."""
        coords = {}
        
        # Try to find time dimension
        time_vars = [var for var in file_obj.variables if 'time' in var.lower()]
        if time_vars:
            time_var = time_vars[0]
            coords['time'] = {
                'name': time_var,
                'values': file_obj.variables[time_var][:],
                'units': getattr(file_obj.variables[time_var], 'units', 'unknown')
            }
        
        # Try to find spatial dimensions
        spatial_dims = []
        for dim_name, dim in file_obj.dimensions.items():
            if dim_name not in ['time', 'level', 'time_station', 'valid_time']:
                spatial_dims.append(dim_name)
        
        if len(spatial_dims) >= 2:
            coords['spatial'] = {
                'dimensions': spatial_dims,
                'sizes': [file_obj.dimensions[dim].size for dim in spatial_dims]
            }
            
            # Try to find lat/lon variables
            lat_vars = [var for var in file_obj.variables if 'lat' in var.lower()]
            lon_vars = [var for var in file_obj.variables if 'lon' in var.lower()]
            
            if lat_vars and lon_vars:
                coords['latitude'] = {
                    'name': lat_vars[0],
                    'values': file_obj.variables[lat_vars[0]][:]
                }
                coords['longitude'] = {
                    'name': lon_vars[0],
                    'values': file_obj.variables[lon_vars[0]][:]
                }
        
        return coords
    
    def interpolate_to_common_grid(self, var1: np.ndarray, var2: np.ndarray, 
                                  coords1: Dict, coords2: Dict) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Interpolate two variables to a common coordinate system."""
        logger.info("Interpolating variables to common grid...")
        
        # Determine common grid resolution
        if 'spatial' in coords1 and 'spatial' in coords2:
            # Both have spatial dimensions
            if coords1['spatial']['sizes'] == coords2['spatial']['sizes']:
                # Same grid size, no interpolation needed
                common_grid = coords1['spatial']['sizes']
                var1_interp = var1
                var2_interp = var2
            else:
                # Different grid sizes, interpolate to finer grid
                common_grid = [max(s1, s2) for s1, s2 in zip(coords1['spatial']['sizes'], coords2['spatial']['sizes'])]
                var1_interp = self._interpolate_spatial(var1, coords1, common_grid)
                var2_interp = self._interpolate_spatial(var2, coords2, common_grid)
        else:
            # One or both are point data
            common_grid = [1, 1]  # Single point
            var1_interp = var1.flatten() if var1.size > 1 else var1
            var2_interp = var2.flatten() if var2.size > 1 else var2
        
        # Handle time dimension
        if 'time' in coords1 and 'time' in coords2:
            common_time = self._align_time_dimensions(coords1['time'], coords2['time'])
            var1_interp = self._interpolate_time(var1_interp, coords1['time'], common_time)
            var2_interp = self._interpolate_time(var2_interp, coords2['time'], common_time)
        
        return var1_interp, var2_interp, {'grid': common_grid, 'time': common_time if 'time' in coords1 and 'time' in coords2 else None}
    
    def _interpolate_spatial(self, var: np.ndarray, coords: Dict, target_grid: list) -> np.ndarray:
        """Interpolate spatial variable to target grid."""
        if len(var.shape) <= 2:
            # 2D or 1D data, use griddata
            if 'latitude' in coords and 'longitude' in coords:
                lat = coords['latitude']['values']
                lon = coords['longitude']['values']
                
                # Create target grid
                lat_target = np.linspace(lat.min(), lat.max(), target_grid[0])
                lon_target = np.linspace(lon.min(), lon.max(), target_grid[1])
                lon_grid, lat_grid = np.meshgrid(lon_target, lat_target)
                
                # Flatten source coordinates and values
                lat_flat = lat.flatten()
                lon_flat = lon.flatten()
                var_flat = var.flatten()
                
                # Remove NaN values
                valid_mask = ~np.isnan(var_flat)
                if valid_mask.any():
                    points = np.column_stack([lon_flat[valid_mask], lat_flat[valid_mask]])
                    values = var_flat[valid_mask]
                    
                    # Interpolate
                    var_interp = griddata(points, values, (lon_grid, lat_grid), method='linear', fill_value=np.nan)
                    return var_interp
                else:
                    return np.full(target_grid, np.nan)
            else:
                # No lat/lon, just resize
                return self._resize_array(var, target_grid)
        else:
            # 3D+ data, handle each level separately
            result = np.zeros(target_grid + list(var.shape[2:]))
            for i in range(var.shape[2]):
                result[:, :, i] = self._interpolate_spatial(var[:, :, i], coords, target_grid)
            return result
    
    def _resize_array(self, arr: np.ndarray, target_shape: list) -> np.ndarray:
        """Simple array resizing using nearest neighbor interpolation."""
        from scipy.ndimage import zoom
        
        if len(arr.shape) != len(target_shape):
            # Pad or truncate dimensions
            if len(arr.shape) < len(target_shape):
                arr = np.expand_dims(arr, axis=0)
            else:
                arr = arr.squeeze()
        
        zoom_factors = [t / s for t, s in zip(target_shape, arr.shape)]
        return zoom(arr, zoom_factors, order=0)
    
    def _align_time_dimensions(self, time1: Dict, time2: Dict) -> np.ndarray:
        """Align time dimensions between two datasets."""
        # Convert to datetime objects if possible
        try:
            if time1['units'] != 'unknown':
                time1_dt = nc.num2date(time1['values'], time1['units'])
            else:
                time1_dt = time1['values']
                
            if time2['units'] != 'unknown':
                time2_dt = nc.num2date(time2['values'], time2['units'])
            else:
                time2_dt = time2['values']
            
            # Find common time range
            start_time = max(np.min(time1_dt), np.min(time2_dt))
            end_time = min(np.max(time1_dt), np.max(time2_dt))
            
            # Create common time axis
            if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                common_time = np.arange(start_time, end_time, timedelta(hours=1))
            else:
                # Fallback to numeric time
                common_time = np.linspace(start_time, end_time, min(len(time1['values']), len(time2['values'])))
                
            return common_time
            
        except Exception as e:
            logger.warning(f"Could not align time dimensions: {e}")
            # Return shorter time axis
            return time1['values'] if len(time1['values']) <= len(time2['values']) else time2['values']
    
    def _interpolate_time(self, var: np.ndarray, source_time: Dict, target_time: np.ndarray) -> np.ndarray:
        """Interpolate variable along time dimension."""
        if len(var.shape) == 1:
            # 1D time series
            if len(source_time['values']) == len(target_time):
                return var
            else:
                f = interp1d(source_time['values'], var, bounds_error=False, fill_value='extrapolate')
                return f(target_time)
        else:
            # Multi-dimensional, interpolate along time axis
            result = np.zeros([len(target_time)] + list(var.shape[1:]))
            for i in range(var.shape[1]):
                if len(var.shape) == 2:
                    f = interp1d(source_time['values'], var[:, i], bounds_error=False, fill_value='extrapolate')
                    result[:, i] = f(target_time)
                else:
                    # Handle higher dimensions
                    for j in range(var.shape[2]):
                        f = interp1d(source_time['values'], var[:, i, j], bounds_error=False, fill_value='extrapolate')
                        result[:, i, j] = f(target_time)
            return result
    
    def create_superimposed_netcdf(self, var1_name: str, var2_name: str, 
                                  output_path: str, var1_interp: np.ndarray, 
                                  var2_interp: np.ndarray, common_coords: Dict) -> str:
        """Create a new NetCDF file with superimposed data."""
        logger.info(f"Creating superimposed NetCDF file: {output_path}")
        
        # Create output file
        output_file = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # Create dimensions
        if common_coords['grid']:
            output_file.createDimension('x', common_coords['grid'][0])
            output_file.createDimension('y', common_coords['grid'][1])
        
        if common_coords['time'] is not None:
            output_file.createDimension('time', len(common_coords['time']))
        
        # Create variables
        var1_var = output_file.createVariable(var1_name, var1_interp.dtype, 
                                            ('time', 'y', 'x') if common_coords['time'] is not None else ('y', 'x'))
        var2_var = output_file.createVariable(var2_name, var2_interp.dtype, 
                                            ('time', 'y', 'x') if common_coords['time'] is not None else ('y', 'x'))
        
        # Add attributes
        var1_var.long_name = f"Superimposed {var1_name} from {os.path.basename(self.file1_path)}"
        var2_var.long_name = f"Superimposed {var2_name} from {os.path.basename(self.file2_path)}"
        
        # Store data
        if common_coords['time'] is not None:
            var1_var[:] = var1_interp
            var2_var[:] = var2_interp
        else:
            var1_var[:] = var1_interp
            var2_var[:] = var2_interp
        
        # Add global attributes
        output_file.title = f"Superimposed NetCDF: {var1_name} and {var2_name}"
        output_file.history = f"Created by NetCDF Superimposer on {datetime.now().isoformat()}"
        output_file.source1 = self.file1_path
        output_file.source2 = self.file2_path
        
        output_file.close()
        logger.info(f"Successfully created: {output_path}")
        return output_path
    
    def create_visualization(self, var1_interp: np.ndarray, var2_interp: np.ndarray, 
                           var1_name: str, var2_name: str, common_coords: Dict, 
                           output_dir: str = ".") -> str:
        """Create visualization of superimposed data."""
        logger.info("Creating visualization...")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Superimposed NetCDF Data: {var1_name} vs {var2_name}', fontsize=16)
        
        # Plot variable 1
        if len(var1_interp.shape) >= 2:
            im1 = axes[0, 0].imshow(var1_interp[0] if len(var1_interp.shape) == 3 else var1_interp, 
                                    cmap='viridis', aspect='auto')
            axes[0, 0].set_title(f'{var1_name} (File 1)')
            plt.colorbar(im1, ax=axes[0, 0])
        else:
            axes[0, 0].plot(var1_interp)
            axes[0, 0].set_title(f'{var1_name} (File 1)')
            axes[0, 0].set_xlabel('Index')
            axes[0, 0].set_ylabel('Value')
        
        # Plot variable 2
        if len(var2_interp.shape) >= 2:
            im2 = axes[0, 1].imshow(var2_interp[0] if len(var2_interp.shape) == 3 else var2_interp, 
                                    cmap='plasma', aspect='auto')
            axes[0, 1].set_title(f'{var2_name} (File 2)')
            plt.colorbar(im2, ax=axes[0, 1])
        else:
            axes[0, 1].plot(var2_interp)
            axes[0, 1].set_title(f'{var2_name} (File 2)')
            axes[0, 1].set_xlabel('Index')
            axes[0, 1].set_ylabel('Value')
        
        # Plot difference
        if var1_interp.shape == var2_interp.shape:
            diff = var1_interp - var2_interp
            if len(diff.shape) >= 2:
                im_diff = axes[1, 0].imshow(diff[0] if len(diff.shape) == 3 else diff, 
                                           cmap='RdBu_r', aspect='auto')
                axes[1, 0].set_title(f'Difference ({var1_name} - {var2_name})')
                plt.colorbar(im_diff, ax=axes[1, 0])
            else:
                axes[1, 0].plot(diff)
                axes[1, 0].set_title(f'Difference ({var1_name} - {var2_name})')
                axes[1, 0].set_xlabel('Index')
                axes[1, 0].set_ylabel('Difference')
        
        # Plot correlation if time series
        if common_coords['time'] is not None and len(var1_interp.shape) == 3:
            # Calculate correlation at each grid point
            corr = np.zeros((var1_interp.shape[1], var1_interp.shape[2]))
            for i in range(var1_interp.shape[1]):
                for j in range(var1_interp.shape[2]):
                    if not (np.isnan(var1_interp[:, i, j]).all() or np.isnan(var2_interp[:, i, j]).all()):
                        valid_mask = ~(np.isnan(var1_interp[:, i, j]) | np.isnan(var2_interp[:, i, j]))
                        if valid_mask.sum() > 1:
                            corr[i, j] = np.corrcoef(var1_interp[valid_mask, i, j], 
                                                    var2_interp[valid_mask, i, j])[0, 1]
                        else:
                            corr[i, j] = np.nan
                    else:
                        corr[i, j] = np.nan
            
            im_corr = axes[1, 1].imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
            axes[1, 1].set_title(f'Correlation ({var1_name} vs {var2_name})')
            plt.colorbar(im_corr, ax=axes[1, 1])
        
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, f'superimposed_{var1_name}_{var2_name}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved: {output_path}")
        return output_path
    
    def superimpose(self, var1_name: str, var2_name: str, output_path: str, 
                   create_viz: bool = True) -> str:
        """Main method to superimpose two variables from different NetCDF files."""
        logger.info(f"Starting superimposition of {var1_name} and {var2_name}")
        
        try:
            # Analyze files
            analysis = self.analyze_files()
            
            # Extract variables
            if var1_name not in self.file1.variables:
                raise ValueError(f"Variable {var1_name} not found in {self.file1_path}")
            if var2_name not in self.file2.variables:
                raise ValueError(f"Variable {var2_name} not found in {self.file2_path}")
            
            var1 = self.file1.variables[var1_name][:]
            var2 = self.file2.variables[var2_name][:]
            
            logger.info(f"Variable 1 shape: {var1.shape}")
            logger.info(f"Variable 2 shape: {var2.shape}")
            
            # Get coordinate systems
            coords1 = self.get_coordinate_system(self.file1)
            coords2 = self.get_coordinate_system(self.file2)
            
            # Interpolate to common grid
            var1_interp, var2_interp, common_coords = self.interpolate_to_common_grid(
                var1, var2, coords1, coords2
            )
            
            logger.info(f"Interpolated shapes: {var1_interp.shape}, {var2_interp.shape}")
            
            # Create superimposed NetCDF
            output_file_path = self.create_superimposed_netcdf(
                var1_name, var2_name, output_path, var1_interp, var2_interp, common_coords
            )
            
            # Create visualization
            if create_viz:
                viz_path = self.create_visualization(
                    var1_interp, var2_interp, var1_name, var2_name, common_coords,
                    os.path.dirname(output_path)
                )
                logger.info(f"Visualization created: {viz_path}")
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error during superimposition: {e}")
            raise

def main():
    """Main function to run the NetCDF superimposition."""
    parser = argparse.ArgumentParser(description='Superimpose two NetCDF files with different structures')
    parser.add_argument('file1', help='First NetCDF file path')
    parser.add_argument('file2', help='Second NetCDF file path')
    parser.add_argument('--output', '-o', default='superimposed.nc', help='Output NetCDF file path')
    parser.add_argument('--variable1', '-v1', required=True, help='Variable name from first file')
    parser.add_argument('--variable2', '-v2', required=True, help='Variable name from second file')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization creation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if files exist
    if not os.path.exists(args.file1):
        logger.error(f"File 1 not found: {args.file1}")
        sys.exit(1)
    if not os.path.exists(args.file2):
        logger.error(f"File 2 not found: {args.file2}")
        sys.exit(1)
    
    try:
        with NetCDFSuperimposer(args.file1, args.file2) as superimposer:
            output_path = superimposer.superimpose(
                args.variable1, 
                args.variable2, 
                args.output,
                create_viz=not args.no_viz
            )
            logger.info(f"Superimposition completed successfully! Output: {output_path}")
            
    except Exception as e:
        logger.error(f"Superimposition failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
