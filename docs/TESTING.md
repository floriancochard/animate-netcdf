# Testing Framework for NetCDF Animation App

This document describes the comprehensive testing framework for the NetCDF animation application.

## Overview

The testing framework provides thorough validation of all major components and system flows, ensuring the application is ready for production use.

## Test Files

- **`test_app.py`** - Main comprehensive test suite
- **`run_tests.py`** - Test runner with category selection
- **`validate_setup.py`** - Setup validation and system compatibility checks

## Quick Start

### 1. Validate Setup

```bash
python validate_setup.py
```

This will check if all required components are available and ready for testing.

### 2. Run Full Test Suite

```bash
python run_tests.py --full
```

Runs all tests with detailed output.

### 3. Run Specific Test Categories

```bash
python run_tests.py --categories config files animation
```

## Test Categories

### 🔧 Configuration Management (`config`)

- **`test_01_configuration_management`** - Tests configuration creation, validation, and serialization
- **`test_02_config_manager`** - Tests ConfigManager functionality including save/load operations

### 📁 File Discovery and Validation (`files`)

- **`test_03_file_discovery_and_validation`** - Tests file pattern matching, discovery, and consistency validation

### 🎬 Multi-File Animation Setup (`animation`)

- **`test_04_multi_file_animation_setup`** - Tests animation setup, data loading, and configuration validation

### 🔍 System Compatibility (`system`)

- **`test_05_system_compatibility_checks`** - Tests Python version, required packages, FFmpeg, and system resources

### 📊 Utilities (`utilities`)

- **`test_06_data_processing_utilities`** - Tests data processing and filtering functionality
- **`test_07_plot_utilities`** - Tests plotting utilities and animation saving

### 🖥️ Command Line Interface (`cli`)

- **`test_08_cli_parser_functionality`** - Tests argument parsing, validation, and mode detection

### 🔗 Integration (`integration`)

- **`test_09_app_controller_integration`** - Tests app controller initialization and component interaction
- **`test_10_end_to_end_workflow`** - Tests complete workflow from file discovery to animation setup
- **`test_13_system_integration_validation`** - Tests component initialization chain and data flow

### ⚠️ Error Handling (`error_handling`)

- **`test_11_error_handling_and_recovery`** - Tests error handling for invalid inputs and edge cases

### ⚡ Performance (`performance`)

- **`test_12_performance_and_memory_checks`** - Tests memory management and performance estimation

## Test Coverage

### Core Components Tested

1. **Configuration Management**

   - Configuration creation and validation
   - Serialization/deserialization
   - Error handling for invalid configurations
   - ConfigManager save/load operations

2. **File Management**

   - File pattern matching and discovery
   - NetCDF file validation and information extraction
   - Common variable detection
   - Spatial coordinate extraction
   - File consistency validation
   - Timestep-based file sorting

3. **Multi-File Animation**

   - Animation setup and configuration
   - Data loading and processing
   - Pre-scanning functionality
   - Colorbar range calculation
   - Memory and processing time estimation

4. **System Compatibility**

   - Python version compatibility (3.7+)
   - Required package availability (numpy, xarray, matplotlib, cartopy, psutil)
   - FFmpeg availability and functionality
   - File system permissions
   - Memory and disk space availability

5. **Utilities**

   - Data processing and filtering
   - Plot utilities and animation saving
   - Color map and figure size validation

6. **Command Line Interface**

   - Argument parsing and validation
   - Mode detection (interactive, non-interactive, batch, single_plot)
   - Multi-file pattern detection

7. **Application Controller**

   - Component initialization
   - Integration between components
   - End-to-end workflow validation

8. **Error Handling**

   - Invalid file patterns
   - Invalid configurations
   - Missing required fields
   - File consistency errors

9. **Performance**
   - Memory usage monitoring
   - Large data handling
   - Processing time estimation
   - Memory estimation

## Running Tests

### Full Test Suite

```bash
python run_tests.py --full
```

### Specific Categories

```bash
# Test configuration and file management
python run_tests.py --categories config files

# Test animation setup and system compatibility
python run_tests.py --categories animation system

# Test utilities and CLI
python run_tests.py --categories utilities cli

# Test integration and error handling
python run_tests.py --categories integration error_handling

# Test performance
python run_tests.py --categories performance
```

### Verbosity Levels

```bash
# Minimal output
python run_tests.py --categories system --verbosity 1

# Normal output (default)
python run_tests.py --categories config files --verbosity 2

# Maximum detail
python run_tests.py --full --verbosity 3
```

## Test Environment

### Sample Data Generation

The test suite automatically generates sample NetCDF files for testing:

- 5 time steps with realistic data
- Temperature and humidity variables
- Geographic coordinates (lat/lon)
- Proper NetCDF attributes

### Temporary Environment

- Tests run in isolated temporary directories
- Automatic cleanup after test completion
- No interference with existing files

## Validation Features

### Setup Validation (`validate_setup.py`)

Checks for:

- ✅ Python version compatibility
- ✅ Required package availability
- ✅ App component availability
- ✅ FFmpeg availability
- ✅ File system permissions
- ✅ Memory availability
- ✅ Disk space availability

### System Requirements

- **Python**: 3.7 or higher
- **Memory**: At least 100MB available
- **Disk Space**: At least 100MB free
- **Packages**: numpy, xarray, matplotlib, cartopy, psutil
- **External**: FFmpeg (optional, with fallback)

## Test Results Interpretation

### ✅ Success Indicators

- All tests pass without errors
- No critical issues in setup validation
- System resources are sufficient
- All components are available

### ⚠️ Warning Indicators

- FFmpeg not available (will use fallback methods)
- Some non-critical packages missing
- Limited system resources

### ❌ Failure Indicators

- Missing required packages
- Python version incompatible
- File permission issues
- Insufficient memory/disk space
- Missing app components

## Troubleshooting

### Common Issues

1. **Missing Packages**

   ```bash
   pip install numpy xarray matplotlib cartopy psutil
   ```

2. **FFmpeg Not Found**

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Permission Issues**

   - Ensure write permissions in current directory
   - Check disk space availability

4. **Memory Issues**
   - Close other applications
   - Increase available memory
   - Use smaller test datasets

### Test-Specific Issues

1. **Configuration Tests Failing**

   - Check config_manager.py availability
   - Verify JSON serialization support

2. **File Discovery Tests Failing**

   - Check file_manager.py availability
   - Verify xarray installation

3. **Animation Tests Failing**

   - Check multi_file_animator.py availability
   - Verify matplotlib and cartopy installation

4. **System Tests Failing**
   - Check psutil installation
   - Verify system resource availability

## Continuous Integration

The test suite is designed to work in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python validate_setup.py
    python run_tests.py --full
```

## Performance Benchmarks

The test suite includes performance validation:

- Memory usage monitoring
- Processing time estimation
- Large data handling
- Resource utilization tracking

## Contributing

When adding new features:

1. Add corresponding tests to `test_app.py`
2. Update test categories in `run_tests.py`
3. Update validation checks in `validate_setup.py`
4. Document new test requirements

## Support

For test-related issues:

1. Run `python validate_setup.py` to identify problems
2. Check the test output for specific error messages
3. Verify system requirements are met
4. Review the troubleshooting section above
