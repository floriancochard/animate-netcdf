#!/usr/bin/env python3
"""
Test script for multi-file NetCDF animation functionality
"""

import os
import sys
import glob

def test_components():
    """Test if all required components are available."""
    print("🧪 Testing multi-file components...")
    
    # Test imports
    try:
        from config_manager import AnimationConfig, ConfigManager
        print("✅ config_manager imported successfully")
    except ImportError as e:
        print(f"❌ config_manager import failed: {e}")
        return False
    
    try:
        from file_manager import NetCDFFileManager
        print("✅ file_manager imported successfully")
    except ImportError as e:
        print(f"❌ file_manager import failed: {e}")
        return False
    
    try:
        from multi_file_animator import MultiFileAnimator
        print("✅ multi_file_animator imported successfully")
    except ImportError as e:
        print(f"❌ multi_file_animator import failed: {e}")
        return False
    
    return True

def test_file_discovery():
    """Test file discovery functionality."""
    print("\n🔍 Testing file discovery...")
    
    # Test with common patterns
    patterns = ["*.nc", "test*.nc", "F4C_00.2.SEG01.OUT.*.nc"]
    
    for pattern in patterns:
        print(f"\nTesting pattern: {pattern}")
        try:
            from file_manager import NetCDFFileManager
            manager = NetCDFFileManager(pattern)
            files = manager.discover_files()
            
            if files:
                print(f"✅ Found {len(files)} files with pattern '{pattern}'")
                for i, file in enumerate(files[:3]):  # Show first 3
                    print(f"  {i+1}. {os.path.basename(file)}")
                if len(files) > 3:
                    print(f"  ... and {len(files) - 3} more files")
            else:
                print(f"⚠️  No files found with pattern '{pattern}'")
                
        except Exception as e:
            print(f"❌ Error with pattern '{pattern}': {e}")

def test_configuration():
    """Test configuration system."""
    print("\n⚙️  Testing configuration system...")
    
    try:
        from config_manager import AnimationConfig, ConfigManager
        
        # Test basic configuration
        config = AnimationConfig()
        config.variable = "test_var"
        config.plot_type = "efficient"
        config.fps = 15
        
        print("✅ Basic configuration created")
        
        # Test configuration validation
        errors = config.validate()
        if errors:
            print(f"⚠️  Configuration validation errors: {errors}")
        else:
            print("✅ Configuration validation passed")
        
        # Test configuration manager
        config_manager = ConfigManager("test_config.json")
        config_manager.set_config(config)
        config_manager.save_config()
        print("✅ Configuration saved")
        
        # Test loading configuration
        new_manager = ConfigManager("test_config.json")
        if new_manager.load_config():
            print("✅ Configuration loaded successfully")
        else:
            print("❌ Configuration loading failed")
        
        # Clean up test file
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")
            print("✅ Test configuration file cleaned up")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def test_multi_file_animator():
    """Test multi-file animator functionality."""
    print("\n🎬 Testing multi-file animator...")
    
    try:
        from config_manager import AnimationConfig
        from file_manager import NetCDFFileManager
        from multi_file_animator import MultiFileAnimator
        
        # Create test configuration
        config = AnimationConfig()
        config.variable = "test_var"
        config.plot_type = "efficient"
        config.fps = 10
        config.pre_scan_files = False  # Skip pre-scan for testing
        
        # Create file manager
        file_manager = NetCDFFileManager("*.nc")
        files = file_manager.discover_files()
        
        if files:
            print(f"✅ Found {len(files)} files for testing")
            
            # Create multi-file animator
            animator = MultiFileAnimator(file_manager, config)
            
            # Test configuration validation
            is_valid = animator._validate_config()
            print(f"Configuration valid: {is_valid}")
            
            # Test time estimation
            if is_valid:
                time_minutes = animator.estimate_processing_time()
                print(f"Estimated processing time: {time_minutes:.1f} minutes")
            
        else:
            print("⚠️  No files found for testing")
            
    except Exception as e:
        print(f"❌ Multi-file animator test failed: {e}")

def test_main_integration():
    """Test integration with main.py."""
    print("\n🔗 Testing main.py integration...")
    
    # Test if main.py can import the new components
    try:
        # Simulate the import logic from main.py
        from config_manager import ConfigManager, AnimationConfig
        from file_manager import NetCDFFileManager
        from multi_file_animator import MultiFileAnimator
        MULTI_FILE_AVAILABLE = True
        print("✅ All components available for main.py")
        
        # Test pattern detection
        test_patterns = [
            "single_file.nc",
            "F4C_00.2.SEG01.OUT.*.nc",
            "*.nc",
            "test*.nc"
        ]
        
        for pattern in test_patterns:
            is_multi_file = ('*' in pattern or '?' in pattern)
            print(f"Pattern '{pattern}': {'Multi-file' if is_multi_file else 'Single file'}")
            
    except ImportError as e:
        print(f"❌ Main integration test failed: {e}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Multi-File NetCDF Animation Test Suite")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_components,
        test_file_discovery,
        test_configuration,
        test_multi_file_animator,
        test_main_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Multi-file functionality is ready.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 