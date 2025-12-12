#!/usr/bin/env python3
"""
Data Processing Utilities for NetCDF Animations
Common data filtering, coordinate handling, and dimension reduction
"""

import numpy as np
import xarray as xr
from typing import Tuple, Optional, List, Any


class DataProcessor:
    """Handles common data processing operations for NetCDF animations."""
    
    # Define spatial dimensions that should be preserved
    SPATIAL_DIMS = [
        'lat', 'lon', 'latitude', 'longitude', 'y', 'x', 
        'nj', 'ni', 'nj_u', 'ni_u', 'nj_v', 'ni_v',
        'latitude_u', 'longitude_u', 'latitude_v', 'longitude_v'
    ]
    
    @staticmethod
    def filter_low_values(data: np.ndarray, percentile: int = 5) -> np.ndarray:
        """Filter out low percentile values to reduce noise."""
        if data.size == 0:
            return data
        
        # Ensure data is numeric and convert to float if needed
        if not np.issubdtype(data.dtype, np.number):
            data = data.astype(float)
        
        # Calculate percentile threshold
        positive_data = data[data > 0]
        if len(positive_data) > 0:
            threshold = np.percentile(positive_data, percentile)
        else:
            threshold = 0
        
        # Create masked array where low values are masked
        filtered_data = np.where(data >= threshold, data, np.nan)
        
        return filtered_data
    
    @staticmethod
    def filter_ignore_values(data: np.ndarray, ignore_values: List[float]) -> np.ndarray:
        """Filter out specific values (e.g., placeholder values like 999).
        
        Args:
            data: Input data array
            ignore_values: List of values to mask (set to NaN)
            
        Returns:
            np.ndarray: Data array with ignored values set to NaN
        """
        if data.size == 0 or not ignore_values:
            return data
        
        # Ensure data is numeric and convert to float if needed
        if not np.issubdtype(data.dtype, np.number):
            data = data.astype(float)
        
        # Create a mask for all values to ignore
        mask = np.zeros_like(data, dtype=bool)
        for ignore_val in ignore_values:
            # Use a small tolerance for floating point comparison
            mask |= np.isclose(data, ignore_val, rtol=1e-5, atol=1e-8)
        
        # Set ignored values to NaN
        filtered_data = data.copy()
        filtered_data[mask] = np.nan
        
        return filtered_data
    
    @staticmethod
    def prepare_data_for_plotting(data_array: xr.DataArray, 
                                 time_step: int = 0, 
                                 animate_dim: str = 'time',
                                 level_index: Optional[int] = None,
                                 zoom_factor: float = 1.0,
                                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare data for plotting by handling extra dimensions and zooming."""
        
        # Get the data array for the specific time step
        if animate_dim in data_array.dims:
            data_array = data_array.isel({animate_dim: time_step})
        
        # Find which dimensions are spatial
        spatial_dims_in_data = [dim for dim in data_array.dims if dim in DataProcessor.SPATIAL_DIMS]
        
        # If we have more than 2 dimensions, we need to reduce to 2D
        if len(data_array.dims) > 2:
            # Keep only the spatial dimensions, handle others
            non_spatial_dims = [dim for dim in data_array.dims if dim not in DataProcessor.SPATIAL_DIMS]
            
            if non_spatial_dims:
                if verbose:
                    print(f"📊 Reducing {len(data_array.dims)}D data to 2D")
                
                # If level_index is specified, select that level
                if level_index is not None and ('level' in non_spatial_dims or 'level_w' in non_spatial_dims):
                    level_dim = 'level' if 'level' in non_spatial_dims else 'level_w'
                    if verbose:
                        print(f"📊 Selecting level {level_index} from dimension {level_dim}")
                    try:
                        data_array = data_array.isel({level_dim: level_index})
                        non_spatial_dims.remove(level_dim)
                    except Exception as e:
                        print(f"❌ Error selecting level {level_index} from {level_dim}: {e}")
                        if level_dim in data_array.dims:
                            print(f"Available level indices: 0 to {len(data_array[level_dim])-1}")
                        raise
                
                # Average over remaining non-spatial dimensions
                for dim in non_spatial_dims:
                    if verbose:
                        print(f"📊 Averaging over dimension: {dim}")
                    data_array = data_array.mean(dim=dim)
        
        # Squeeze out any remaining singleton dimensions
        data_array = data_array.squeeze()
        
        # Convert to numpy array
        data = data_array.values
        
        # Handle single-point data (1x1 spatial dimensions)
        if len(data.shape) == 0:  # Scalar data
            if verbose:
                print(f"📊 Single-point data detected, creating 1x1 array")
            data = np.array([[data]])
        elif len(data.shape) == 1:  # 1D data
            if verbose:
                print(f"📊 1D data detected, reshaping to 2D")
            data = data.reshape(-1, 1)
        
        # Verify we have 2D data
        if len(data.shape) != 2:
            raise ValueError(f"Data must be 2D for plotting, got shape {data.shape}. "
                           f"Available dimensions: {list(data_array.dims)}")
        
        # Get coordinates
        lats, lons = DataProcessor._extract_coordinates(data_array)
        
        # Apply zoom factor if specified
        if zoom_factor != 1.0:
            data, lats, lons = DataProcessor._apply_zoom(data, lats, lons, zoom_factor)
        
        return data, lats, lons
    
    @staticmethod
    def _extract_coordinates(data_array: xr.DataArray) -> Tuple[np.ndarray, np.ndarray]:
        """Extract latitude and longitude coordinates from data array."""
        # Try to get coordinates from the data array itself
        coords = data_array.coords
        
        # Check for common coordinate names
        if 'latitude' in coords and 'longitude' in coords:
            lats = coords['latitude'].values
            lons = coords['longitude'].values
        elif 'lat' in coords and 'lon' in coords:
            lats = coords['lat'].values
            lons = coords['lon'].values
        else:
            # Check for other coordinate names that might be spatial
            available_coords = list(coords.keys())
            print(f"📊 Available coordinates: {available_coords}")
            
            # Look for any coordinate that might be spatial
            spatial_coords = []
            for coord_name in available_coords:
                coord = coords[coord_name]
                # Check if coordinate matches data dimensions (1D or 2D)
                if (len(coord.shape) == 1 and coord.shape[0] in [data_array.shape[0], data_array.shape[1]]) or \
                   (len(coord.shape) == 2 and coord.shape == (data_array.shape[0], data_array.shape[1])):
                    spatial_coords.append(coord_name)
            
            if len(spatial_coords) >= 2:
                # Use the first two spatial coordinates found
                coord1 = coords[spatial_coords[0]].values
                coord2 = coords[spatial_coords[1]].values
                
                # Ensure coordinates are numeric
                try:
                    coord1 = coord1.astype(float)
                    coord2 = coord2.astype(float)
                except (ValueError, TypeError):
                    print(f"⚠️  Could not convert coordinates to float, using indices")
                    lats = np.arange(data_array.shape[0])
                    lons = np.arange(data_array.shape[1])
                    return lats, lons
                
                # Determine which is lat/lon based on typical ranges
                if np.max(coord1) > np.max(coord2):
                    lats = coord2
                    lons = coord1
                else:
                    lats = coord1
                    lons = coord2
                
                print(f"📊 Using coordinates: {spatial_coords[0]} and {spatial_coords[1]}")
            else:
                # Fallback: create coordinate arrays based on data shape
                print(f"⚠️  No spatial coordinates found, using array indices")
                # Handle single-point data
                if len(data_array.shape) == 0:
                    lats = np.array([0.0])
                    lons = np.array([0.0])
                elif len(data_array.shape) == 1:
                    lats = np.arange(data_array.shape[0])
                    lons = np.array([0.0])
                else:
                    lats = np.arange(data_array.shape[0])
                    lons = np.arange(data_array.shape[1])
        
        # Ensure coordinates are numeric
        try:
            lats = lats.astype(float)
            lons = lons.astype(float)
        except (ValueError, TypeError):
            print(f"⚠️  Could not convert coordinates to float, using indices")
            lats = np.arange(data_array.shape[0])
            lons = np.arange(data_array.shape[1])
        
        return lats, lons
    
    @staticmethod
    def _apply_zoom(data: np.ndarray, lats: np.ndarray, lons: np.ndarray, 
                    zoom_factor: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Apply zoom factor to crop the domain."""
        if zoom_factor <= 0:
            raise ValueError("Zoom factor must be positive")
        
        if zoom_factor == 1.0:
            return data, lats, lons
        
        # Calculate new dimensions
        original_height, original_width = data.shape
        
        # For zoom_factor > 1, we crop the domain
        # For zoom_factor < 1, we expand the domain (not typically useful)
        if zoom_factor > 1.0:
            # Calculate new dimensions (crop)
            new_height = int(original_height / zoom_factor)
            new_width = int(original_width / zoom_factor)
            
            # Calculate crop boundaries (center the crop)
            start_row = (original_height - new_height) // 2
            end_row = start_row + new_height
            start_col = (original_width - new_width) // 2
            end_col = start_col + new_width
            
            # Only print zoom info once per animation
            if not hasattr(DataProcessor, '_zoom_applied'):
                print(f"🔍 Applying zoom factor {zoom_factor:.2f}")
                print(f"   Original size: {original_width} x {original_height}")
                print(f"   Cropped size: {new_width} x {new_height}")
                print(f"   Crop boundaries: rows {start_row}:{end_row}, cols {start_col}:{end_col}")
                DataProcessor._zoom_applied = True
            
            # Crop data
            cropped_data = data[start_row:end_row, start_col:end_col]
            
            # Crop coordinates
            if len(lats.shape) == 2:
                # 2D coordinates
                cropped_lats = lats[start_row:end_row, start_col:end_col]
                cropped_lons = lons[start_row:end_row, start_col:end_col]
            else:
                # 1D coordinates
                cropped_lats = lats[start_row:end_row]
                cropped_lons = lons[start_col:end_col]
            
            return cropped_data, cropped_lats, cropped_lons
        else:
            # For zoom_factor < 1, we could expand the domain, but this is less common
            print(f"⚠️  Zoom factor {zoom_factor} < 1.0, using original domain")
            return data, lats, lons
    
    @staticmethod
    def reset_zoom_flag():
        """Reset the zoom application flag."""
        if hasattr(DataProcessor, '_zoom_applied'):
            delattr(DataProcessor, '_zoom_applied')
    
    @staticmethod
    def get_animation_dimension(dataset: xr.Dataset) -> Optional[str]:
        """Find the best dimension for animation, prioritizing time-related dimensions."""
        # Define time-related dimension patterns (in order of preference)
        time_patterns = ['time', 'Time', 'TIME', 'time_station', 'step', 'Step', 'STEP']
        
        # First, look for time-related dimensions
        for pattern in time_patterns:
            for dim in dataset.dims:
                if pattern in dim and dim not in DataProcessor.SPATIAL_DIMS:
                    return dim
        
        # If no time-related dimension found, look for the largest non-spatial dimension
        non_spatial_dims = [dim for dim in dataset.dims if dim not in DataProcessor.SPATIAL_DIMS]
        if not non_spatial_dims:
            return None
        
        # Return the dimension with the most steps
        return max(non_spatial_dims, key=lambda dim: len(dataset[dim]))
    
    @staticmethod
    def get_spatial_dimensions(dataset: xr.Dataset) -> List[str]:
        """Get list of spatial dimensions in the dataset."""
        return [dim for dim in dataset.dims if dim in DataProcessor.SPATIAL_DIMS]
    
    @staticmethod
    def get_non_spatial_dimensions(dataset: xr.Dataset) -> List[str]:
        """Get list of non-spatial dimensions in the dataset."""
        return [dim for dim in dataset.dims if dim not in DataProcessor.SPATIAL_DIMS] 