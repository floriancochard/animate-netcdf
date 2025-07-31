#!/usr/bin/env python3
"""
Animation Creator for NetCDF Data
Refactored main entry point using the new modular architecture
"""

import sys
import os

# Add the parent directory to the path so we can import from animate_netcdf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from animate_netcdf.core.app_controller import AppController


def main():
    """Main entry point for the application."""
    try:
        # Create and run the application controller
        controller = AppController()
        success = controller.run()
        
        if success:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
