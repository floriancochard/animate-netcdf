#!/usr/bin/env python3
"""
Output Manager
Handles output format decisions and filename generation
"""

import os
from typing import Optional, Tuple
from datetime import datetime
from animate_netcdf.core.config_manager import OutputFormat


class OutputManager:
    """Manages output format decisions and filename generation."""
    
    @staticmethod
    def determine_output_format(input_type: str, user_choice: Optional[str] = None) -> str:
        """Determine output format based on input type and user choice.
        
        Args:
            input_type: 'single' or 'multi'
            user_choice: User-specified format ('png' or 'mp4') or None
            
        Returns:
            str: Output format ('png' or 'mp4')
        """
        if user_choice:
            return user_choice.lower()
        
        # Default behavior
        if input_type == 'single':
            return 'png'  # Single file always produces PNG
        else:
            return 'mp4'  # Multi-file defaults to MP4
    
    @staticmethod
    def generate_output_filename(variable: str, format: str, 
                                 user_specified: Optional[str] = None,
                                 is_multi_file: bool = False) -> str:
        """Generate output filename.
        
        Args:
            variable: Variable name
            format: Output format ('png' or 'mp4')
            user_specified: User-specified filename or None
            is_multi_file: Whether this is multi-file output
            
        Returns:
            str: Generated filename
        """
        if user_specified:
            # Ensure proper extension
            if is_multi_file and format == 'png':
                # For PNG sequence, remove extension if present
                if user_specified.endswith('.png'):
                    return user_specified[:-4]
                return user_specified
            else:
                # For single file or MP4, ensure correct extension
                if not user_specified.endswith(f'.{format}'):
                    if user_specified.endswith('.png') or user_specified.endswith('.mp4'):
                        # Replace existing extension
                        base = os.path.splitext(user_specified)[0]
                        return f"{base}.{format}"
                    else:
                        # Add extension
                        return f"{user_specified}.{format}"
                return user_specified
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_var = variable.replace('/', '_').replace('\\', '_')
        
        if is_multi_file and format == 'png':
            # PNG sequence - no extension (will be added per file)
            return f"{timestamp}_{safe_var}_sequence"
        else:
            # Single file or MP4
            return f"{timestamp}_{safe_var}.{format}"
    
    @staticmethod
    def validate_output_path(output_path: str, overwrite: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate output path and check for existing files.
        
        Args:
            output_path: Path to output file
            overwrite: Whether to allow overwriting
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check if directory exists
        dir_path = os.path.dirname(output_path) or '.'
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create output directory: {e}"
        
        # Check if file exists
        if os.path.exists(output_path) and not overwrite:
            return False, f"Output file already exists: {output_path}. Use --overwrite to overwrite."
        
        return True, None
    
    @staticmethod
    def get_sequence_filename(base_name: str, index: int, total: int) -> str:
        """Generate filename for sequence file.
        
        Args:
            base_name: Base name for sequence
            index: File index (0-based)
            total: Total number of files
        
        Returns:
            str: Filename with index
        """
        # Determine padding based on total count
        if total < 10:
            padding = 1
        elif total < 100:
            padding = 2
        elif total < 1000:
            padding = 3
        else:
            padding = 4
        
        return f"{base_name}_{index:0{padding}d}.png"
