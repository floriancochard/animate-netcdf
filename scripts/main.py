#!/usr/bin/env python3
"""
Animation Creator for NetCDF Data
Refactored main entry point using the new modular architecture with subcommand support
"""

import sys
import os
import importlib
from typing import Dict, Callable, List, Optional, Tuple

# Handle path issues for both development and installed environments
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to the path so we can import from animate_netcdf
sys.path.insert(0, parent_dir)

# Also add the current directory to handle imports from scripts
sys.path.insert(0, current_dir)

from animate_netcdf.core.app_controller import AppController


class SubcommandManager:
    """Manages subcommand execution with consistent error handling."""
    
    def __init__(self):
        self.subcommands: Dict[str, Callable] = {}
        self._register_subcommands()
    
    def _register_subcommands(self):
        """Register all available subcommands."""
        self.subcommands = {
            'config': self._run_config_command,
            'validate': self._run_validate_command,
            'test': self._run_test_command,
        }
    
    def _run_subcommand(self, command: str, args: List[str]) -> int:
        """Execute a subcommand with proper error handling.
        
        Args:
            command: The subcommand name
            args: Arguments to pass to the subcommand
            
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if command not in self.subcommands:
            print(f"❌ Unknown subcommand: {command}")
            return 1
        
        try:
            return self.subcommands[command](args)
        except ImportError as e:
            print(f"❌ Subcommand module not available: {e}")
            return 1
        except Exception as e:
            print(f"❌ Subcommand error: {e}")
            return 1
    
    def _run_config_command(self, args: List[str]) -> int:
        """Run the configuration creation command."""
        from scripts.create_config import main as config_main
        return self._execute_with_args(config_main, args)
    
    def _run_validate_command(self, args: List[str]) -> int:
        """Run the validation command."""
        from scripts.validate_setup import main as validate_main
        return self._execute_with_args(validate_main, args)
    
    def _run_test_command(self, args: List[str]) -> int:
        """Run the test command."""
        from scripts.run_tests import main as test_main
        return self._execute_with_args(test_main, args)
    
    def _execute_with_args(self, func: Callable, args: List[str]) -> int:
        """Execute a function with modified sys.argv.
        
        Args:
            func: The function to execute
            args: Arguments to pass
            
        Returns:
            int: Exit code from the function
        """
        original_argv = sys.argv.copy()
        try:
            sys.argv = [original_argv[0]] + args
            return func()
        finally:
            sys.argv = original_argv


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
    anc                                    # Interactive mode
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
        from animate_netcdf.core.cli_parser import CLIParser
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
    """Main entry point for the application with subcommand support."""
    try:
        # Get command line arguments
        args = sys.argv[1:]
        
        # Check for help commands first
        if args and args[0].lower() in ["help", "--help", "-h"]:
            show_help()
            return 0
        
        # Initialize subcommand manager
        subcommand_manager = SubcommandManager()
        
        # Handle subcommands
        if not args:
            # No arguments - run interactive mode
            return run_interactive_mode()
        
        command = args[0].lower()
        
        # Check if this is a known subcommand
        if command in subcommand_manager.subcommands:
            return subcommand_manager._run_subcommand(command, args[1:])
        else:
            # Check if this looks like a subcommand (not a file path)
            if not os.path.exists(command) and not command.endswith('.nc') and not '*' in command and not '?' in command:
                print(f"❌ Unknown subcommand: {command}")
                print("Available subcommands: config, validate, test")
                print("Use 'python scripts/main.py help' for more information")
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
