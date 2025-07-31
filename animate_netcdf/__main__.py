#!/usr/bin/env python3
"""
Main entry point for the animate_netcdf package.
This allows the package to be run as: python -m animate_netcdf
"""

import sys
import os

# Add the scripts directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
scripts_dir = os.path.join(project_root, 'scripts')
sys.path.insert(0, scripts_dir)

# Import and run the main function
from main import main

if __name__ == "__main__":
    sys.exit(main()) 