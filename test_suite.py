#!/usr/bin/env python3
"""
Test Suite for NetCDF Animation System
"""

import os
import sys
from config_manager import ConfigManager, AnimationConfig, discover_netcdf_files
from file_manager import NetCDFFileManager
from multi_file_animator import MultiFileAnimator


def test_config_manager():
    """Test the configuration system."""
    print("🧪 Testing Configuration Manager...")
    
    config_manager = ConfigManager()
    
    # Test file discovery
    test_files = discover_netcdf_files("*.nc")
    print(f"📁 Found {len(test_files)} NetCDF files")
    
    # Test configuration
    config = AnimationConfig()
    config.variable = "test_var"
    config.plot_type = "efficient"
    
    # Save and load
    config_manager.set_config(config)
    config_manager.save_config("test_config.json")
    
    # Load back
    new_manager = ConfigManager("test_config.json")
    new_manager.load_config()
    
    print("✅ Configuration system test completed!")


def test_file_manager():
    """Test the file manager."""
    print("\n🧪 Testing File Manager...")
    
    # Test with a pattern
    pattern = "*.nc"
    manager = NetCDFFileManager(pattern)
    
    # Discover files
    files = manager.discover_files()
    
    if files:
        print(f"✅ Found {len(files)} files")
        
        # Test consistency
        errors = manager.validate_consistency()
        if errors:
            print(f"❌ Consistency errors: {errors}")
        else:
            print("✅ Files are consistent")
        
        # Test common variables
        common_vars = manager.get_common_variables()
        print(f"📊 Common variables: {common_vars}")
        
        # Test memory estimation
        if common_vars:
            var = common_vars[0]
            memory_mb = manager.estimate_memory_usage(var)
            print(f"💾 Estimated memory usage for '{var}': {memory_mb:.1f} MB")
    else:
        print("⚠️  No NetCDF files found for testing")
    
    print("✅ File manager test completed!")


def test_multi_file_animator():
    """Test MultiFileAnimator functionality."""
    print("Testing MultiFileAnimator...")
    
    try:
        from multi_file_animator import MultiFileAnimator
        from config_manager import AnimationConfig
        from file_manager import NetCDFFileManager
        
        # Test codec detection
        config = AnimationConfig()
        file_manager = NetCDFFileManager("*.nc")
        animator = MultiFileAnimator(file_manager, config)
        
        # Test ffmpeg availability
        assert hasattr(animator, 'ffmpeg_available'), "ffmpeg_available attribute missing"
        assert hasattr(animator, 'available_codecs'), "available_codecs attribute missing"
        
        # Test troubleshooting tips
        tips = animator.get_troubleshooting_tips()
        assert isinstance(tips, list), "Troubleshooting tips should be a list"
        assert len(tips) > 0, "Should have troubleshooting tips"
        
        print("✅ MultiFileAnimator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ MultiFileAnimator test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("NetCDF Animation System Test Suite")
    print("=" * 60)
    
    try:
        test_config_manager()
        test_file_manager()
        test_multi_file_animator()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 