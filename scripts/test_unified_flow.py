#!/usr/bin/env python3
"""
Test script for the unified NetCDF animation flow.
This demonstrates how the consolidated logic works.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to import animate_netcdf
sys.path.insert(0, str(Path(__file__).parent.parent))

from animate_netcdf.core.app_controller import AppController
from animate_netcdf.core.cli_parser import CLIParser


def test_unified_flow():
    """Test the unified flow."""
    print("🧪 Testing Unified NetCDF Animation Flow")
    print("=" * 60)
    
    # Test with a sample file
    test_file = "data/sample_data/IDALIA_2km.nc"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure the sample data is available")
        return False
    
    print(f"📁 Test file: {test_file}")
    print("\n🎯 The unified flow will:")
    print("1. Read file's architecture and show groups")
    print("2. Let user select group")
    print("3. Let user select variable")
    print("4. Let user choose plot type (timeseries PNG, animation MP4, batch)")
    print("5. Set output filename")
    print("6. Set FPS (for animations)")
    print("7. Set zoom factor")
    print("\n🚀 Launching unified flow...")
    
    try:
        # Create mock args for testing
        class MockArgs:
            def __init__(self):
                self.input_pattern = test_file
                self.variable = None
                self.type = 'efficient'
                self.fps = 10
                self.output = None
                self.batch = False
                self.plot = False
                self.time_step = 0
                self.percentile = 5
                self.animate_dim = 'time'
                self.level = None
                self.zoom = 1.0
                self.config = None
                self.save_config = None
                self.overwrite = False
                self.no_interactive = False
                self.explore = False
                self.pre_scan = True
                self.global_colorbar = True
        
        args = MockArgs()
        
        # Run the controller
        controller = AppController()
        success = controller.run(args)
        
        if success:
            print("\n✅ Unified flow test completed successfully!")
        else:
            print("\n❌ Unified flow test failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during unified flow test: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_unified_flow_info():
    """Show information about the unified flow."""
    print("🎬 NetCDF Animation Creator - Unified Flow")
    print("=" * 60)
    
    print("✨ UNIFIED FLOW FEATURES:")
    print("   • Single entry point: 'anc filename.nc'")
    print("   • Consistent user experience")
    print("   • Logical step-by-step flow")
    print("   • Better error handling and validation")
    print("   • Clean, maintainable codebase")
    
    print("\n🎯 UNIFIED FLOW STEPS:")
    print("   1. File architecture exploration")
    print("   2. Group selection")
    print("   3. Variable selection")
    print("   4. Plot type selection")
    print("   5. Output filename configuration")
    print("   6. Animation settings (FPS, zoom)")


if __name__ == "__main__":
    # Show unified flow information
    show_unified_flow_info()
    
    # Test the unified flow
    print("\n" + "=" * 60)
    success = test_unified_flow()
    
    if success:
        print("\n🎉 All tests passed! The unified flow is working correctly.")
        print("\n💡 To use the unified flow:")
        print("   anc your_file.nc")
        print("\n   This will guide you through the complete process:")
        print("   1. File architecture → 2. Group selection → 3. Variable selection")
        print("   4. Plot type → 5. Output filename → 6. FPS → 7. Zoom factor")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
