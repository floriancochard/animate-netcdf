#!/usr/bin/env python3
"""
Main entry point for the animate_netcdf package.
This allows the package to be run as: python -m animate_netcdf
"""

import sys
import os
from typing import List

# Import the main function from the core module
from animate_netcdf.core.app_controller import AppController
from animate_netcdf.core.cli_parser import CLIParser


def show_help():
    """Show help information."""
    print("""
🎬 NetCDF Animation Creator (anc)

USAGE:
    anc [command] [options]

COMMANDS:
    (no command)     Launch interactive animation creator
    config           Create configuration files
    validate         Validate system setup
    test             Run test suite
    help             Show this help message

EXAMPLES:
    anc                                    # Interactive mode (file selection)
    anc your_file.nc                       # Single file animation
    anc *.nc --variable temperature        # Multi-file animation
    anc config                             # Create configuration
    anc validate                           # Check system setup
    anc test --full                        # Run all tests
    anc test --categories config files     # Run specific tests

For detailed help on each command:
    anc config --help
    anc validate --help
    anc test --help
""")


def run_animation_mode(args: List[str]) -> int:
    """Run the main animation mode with the given arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Save original sys.argv and modify it for parsing
        original_argv = sys.argv.copy()
        try:
            sys.argv = [original_argv[0]] + args
            args_obj = CLIParser.parse_args()
            controller = AppController()
            success = controller.run(args_obj)
            return 0 if success else 1
        finally:
            sys.argv = original_argv
    except SystemExit:
        # If argument parsing fails, show help
        show_help()
        return 1
    except Exception as e:
        print(f"❌ Animation error: {e}")
        return 1


def run_interactive_mode() -> int:
    """Run the interactive animation mode.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        controller = AppController()
        success = controller.run()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Interactive mode error: {e}")
        return 1


def main():
    """Main entry point for the application."""
    try:
        # Get command line arguments
        args = sys.argv[1:]
        
        # Check for help commands first
        if args and args[0].lower() in ["help", "--help", "-h"]:
            show_help()
            return 0
        
        # Handle subcommands
        if not args:
            # No arguments - run interactive mode
            return run_interactive_mode()
        
        command = args[0].lower()
        
        # Check if this is a known subcommand
        if command in ["config", "validate", "test"]:
            print(f"❌ Subcommand '{command}' not available in installed package.")
            print("These commands are only available during development.")
            print("Use 'anc --help' for available options.")
            return 1
        else:
            # Check if this looks like a subcommand (not a file path)
            if not os.path.exists(command) and not command.endswith('.nc') and not '*' in command and not '?' in command:
                print(f"❌ Unknown command: {command}")
                print("Use 'anc --help' for available options.")
                return 1
            else:
                # No subcommand - treat as regular animation command
                return run_animation_mode(args)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 