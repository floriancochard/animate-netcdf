#!/usr/bin/env python3
"""
Setup Validation for NetCDF Animation App
Checks if all required components are available and ready for testing.
"""

import sys
import os
import importlib
import subprocess
from typing import List, Dict, Any, Tuple

# Add the parent directory to the path so we can import from animate_netcdf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def check_python_version() -> Tuple[bool, str]:
    """Check Python version compatibility.
    
    Returns:
        Tuple[bool, str]: (is_compatible, version_info)
    """
    version = sys.version_info
    is_compatible = version.major >= 3 and version.minor >= 7
    version_info = f"Python {version.major}.{version.minor}.{version.micro}"
    return is_compatible, version_info


def check_required_packages() -> List[Tuple[str, bool, str]]:
    """Check if required packages are available.
    
    Returns:
        List[Tuple[str, bool, str]]: List of (package_name, is_available, version_info)
    """
    required_packages = [
        'numpy',
        'xarray', 
        'matplotlib',
        'cartopy',
        'psutil'
    ]
    
    results = []
    for package in required_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            results.append((package, True, version))
        except ImportError:
            results.append((package, False, 'not installed'))
    
    return results


def check_app_components() -> List[Tuple[str, bool, str]]:
    """Check if app components are available.
    
    Returns:
        List[Tuple[str, bool, str]]: List of (component_name, is_available, status)
    """
    components = [
        'animate_netcdf.core.config_manager',
        'animate_netcdf.core.file_manager', 
        'animate_netcdf.animators.multi_file_animator',
        'animate_netcdf.core.app_controller',
        'animate_netcdf.core.cli_parser',
        'animate_netcdf.utils.data_processing',
        'animate_netcdf.utils.plot_utils',
        'animate_netcdf.utils.ffmpeg_utils',
        'animate_netcdf.utils.logging_utils'
    ]
    
    results = []
    for component in components:
        try:
            importlib.import_module(component)
            results.append((component, True, 'available'))
        except ImportError as e:
            results.append((component, False, str(e)))
    
    return results


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if FFmpeg is available.
    
    Returns:
        Tuple[bool, str]: (is_available, version_info)
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version from output
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else 'unknown'
            return True, version_line
        else:
            return False, 'command failed'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, 'not found'


def check_file_permissions() -> Tuple[bool, str]:
    """Check file system permissions.
    
    Returns:
        Tuple[bool, str]: (has_permissions, status)
    """
    try:
        # Try to create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
            f.write('test')
        return True, 'write permissions OK'
    except Exception as e:
        return False, f'permission error: {e}'


def check_memory_availability() -> Tuple[bool, str]:
    """Check memory availability.
    
    Returns:
        Tuple[bool, str]: (has_sufficient_memory, status)
    """
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb >= 0.1:  # At least 100MB
            return True, f'{available_gb:.1f} GB available'
        else:
            return False, f'only {available_gb:.1f} GB available'
    except ImportError:
        return False, 'psutil not available'


def check_disk_space() -> Tuple[bool, str]:
    """Check disk space availability.
    
    Returns:
        Tuple[bool, str]: (has_sufficient_space, status)
    """
    try:
        import psutil
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb >= 0.1:  # At least 100MB
            return True, f'{free_gb:.1f} GB free'
        else:
            return False, f'only {free_gb:.1f} GB free'
    except ImportError:
        return False, 'psutil not available'


def print_validation_report():
    """Print comprehensive validation report."""
    print("=" * 80)
    print("🔍 NETCDF ANIMATION APP SETUP VALIDATION")
    print("=" * 80)
    print()
    
    # Check Python version
    py_compatible, py_version = check_python_version()
    print(f"🐍 Python Version: {py_version}")
    if py_compatible:
        print("   ✅ Compatible")
    else:
        print("   ❌ Incompatible (requires Python 3.7+)")
    print()
    
    # Check required packages
    print("📦 Required Packages:")
    package_results = check_required_packages()
    all_packages_ok = True
    for package, available, version in package_results:
        status = "✅" if available else "❌"
        print(f"   {status} {package}: {version}")
        if not available:
            all_packages_ok = False
    print()
    
    # Check app components
    print("🔧 App Components:")
    component_results = check_app_components()
    all_components_ok = True
    for component, available, status in component_results:
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {component}: {status}")
        if not available:
            all_components_ok = False
    print()
    
    # Check FFmpeg
    print("🎬 FFmpeg:")
    ffmpeg_available, ffmpeg_version = check_ffmpeg()
    ffmpeg_icon = "✅" if ffmpeg_available else "⚠️"
    print(f"   {ffmpeg_icon} {ffmpeg_version}")
    print()
    
    # Check system resources
    print("💻 System Resources:")
    
    # File permissions
    file_ok, file_status = check_file_permissions()
    file_icon = "✅" if file_ok else "❌"
    print(f"   {file_icon} File permissions: {file_status}")
    
    # Memory
    memory_ok, memory_status = check_memory_availability()
    memory_icon = "✅" if memory_ok else "❌"
    print(f"   {memory_icon} Memory: {memory_status}")
    
    # Disk space
    disk_ok, disk_status = check_disk_space()
    disk_icon = "✅" if disk_ok else "❌"
    print(f"   {disk_icon} Disk space: {disk_status}")
    print()
    
    # Overall assessment
    print("=" * 80)
    print("📊 OVERALL ASSESSMENT")
    print("=" * 80)
    
    critical_issues = []
    warnings = []
    
    if not py_compatible:
        critical_issues.append("Python version incompatible")
    
    if not all_packages_ok:
        critical_issues.append("Missing required packages")
    
    if not all_components_ok:
        critical_issues.append("Missing app components")
    
    if not file_ok:
        critical_issues.append("File permission issues")
    
    if not memory_ok:
        critical_issues.append("Insufficient memory")
    
    if not disk_ok:
        critical_issues.append("Insufficient disk space")
    
    if not ffmpeg_available:
        warnings.append("FFmpeg not available (will use fallback methods)")
    
    if critical_issues:
        print("❌ CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"   - {issue}")
        print()
        print("🔧 Please fix these issues before running tests.")
        return False
    else:
        print("✅ All critical requirements met!")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   - {warning}")
            print("\n💡 The app should work but may have limited functionality.")
        else:
            print("\n🎉 Setup is perfect! Ready for testing.")
        
        return True


def main():
    """Main validation function."""
    print_validation_report()
    
    # Ask user if they want to run tests
    print("\n" + "=" * 80)
    print("🧪 TEST EXECUTION")
    print("=" * 80)
    
    try:
        response = input("Would you like to run the test suite now? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            print("\n🚀 Starting test suite...")
            os.system(f"{sys.executable} run_tests.py --full")
        else:
            print("\n💡 To run tests later, use:")
            print("   python run_tests.py --full")
            print("   python run_tests.py --categories config files animation")
    except KeyboardInterrupt:
        print("\n\n👋 Validation completed. Run tests when ready!")


if __name__ == "__main__":
    main() 