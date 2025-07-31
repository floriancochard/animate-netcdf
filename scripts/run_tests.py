#!/usr/bin/env python3
"""
Test Runner for NetCDF Animation App
Allows running specific test categories or the full test suite.
"""

import sys
import argparse
import unittest
import sys
import os

# Add the tests directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

from test_app import TestNetCDFAnimationApp


def run_specific_tests(test_categories, verbosity=2):
    """Run specific test categories.
    
    Args:
        test_categories: List of test category names
        verbosity: Test verbosity level (1-3)
    """
    print("=" * 80)
    print("🧪 RUNNING SPECIFIC TEST CATEGORIES")
    print("=" * 80)
    
    # Create test suite with specific tests
    suite = unittest.TestSuite()
    
    # Map test categories to test methods
    test_mapping = {
        'config': [
            'test_01_configuration_management',
            'test_02_config_manager'
        ],
        'files': [
            'test_03_file_discovery_and_validation'
        ],
        'animation': [
            'test_04_multi_file_animation_setup'
        ],
        'system': [
            'test_05_system_compatibility_checks'
        ],
        'utilities': [
            'test_06_data_processing_utilities',
            'test_07_plot_utilities'
        ],
        'cli': [
            'test_08_cli_parser_functionality'
        ],
        'integration': [
            'test_09_app_controller_integration',
            'test_10_end_to_end_workflow',
            'test_13_system_integration_validation'
        ],
        'error_handling': [
            'test_11_error_handling_and_recovery'
        ],
        'performance': [
            'test_12_performance_and_memory_checks'
        ]
    }
    
    # Add tests for requested categories
    for category in test_categories:
        if category in test_mapping:
            for test_name in test_mapping[category]:
                test_method = getattr(TestNetCDFAnimationApp, test_name)
                suite.addTest(TestNetCDFAnimationApp(test_name))
                print(f"✅ Added test: {test_name}")
        else:
            print(f"⚠️  Unknown test category: {category}")
    
    if not suite.countTestCases():
        print("❌ No valid test categories specified!")
        return False
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


def run_full_suite(verbosity=2):
    """Run the full test suite.
    
    Args:
        verbosity: Test verbosity level (1-3)
    """
    from test_app import run_comprehensive_test_suite
    return run_comprehensive_test_suite()


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for NetCDF Animation App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  config      - Configuration management and validation
  files       - File discovery and validation
  animation   - Multi-file animation setup
  system      - System compatibility checks
  utilities   - Data processing and plot utilities
  cli         - Command line interface
  integration - App controller and end-to-end workflows
  error_handling - Error handling and recovery
  performance - Performance and memory management

Examples:
  # Run full test suite
  python run_tests.py --full
  
  # Run specific categories
  python run_tests.py --categories config files animation
  
  # Run with minimal output
  python run_tests.py --categories system --verbosity 1
  
  # Run integration tests only
  python run_tests.py --categories integration
        """
    )
    
    parser.add_argument('--full', action='store_true',
                       help='Run the full comprehensive test suite')
    
    parser.add_argument('--categories', nargs='+',
                       choices=['config', 'files', 'animation', 'system', 
                               'utilities', 'cli', 'integration', 
                               'error_handling', 'performance'],
                       help='Specific test categories to run')
    
    parser.add_argument('--verbosity', type=int, choices=[1, 2, 3], default=2,
                       help='Test verbosity level (default: 2)')
    
    args = parser.parse_args()
    
    if not args.full and not args.categories:
        print("❌ Please specify either --full or --categories")
        parser.print_help()
        return 1
    
    if args.full:
        print("🚀 Running full comprehensive test suite...")
        success = run_full_suite(args.verbosity)
    else:
        print(f"🚀 Running specific test categories: {', '.join(args.categories)}")
        success = run_specific_tests(args.categories, args.verbosity)
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 