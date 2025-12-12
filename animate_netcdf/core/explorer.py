#!/usr/bin/env python3
"""
NetCDF Explorer
Interactive exploration interface for NetCDF files
"""

import os
import glob
from typing import Dict, Any, List, Optional
from animate_netcdf.utils.netcdf_explorer import NetCDFExplorer


class Explorer:
    """Interactive explorer for NetCDF files."""
    
    def __init__(self):
        """Initialize explorer."""
        self.explorer = NetCDFExplorer()
    
    def explore_file(self, file_path: str) -> bool:
        """Explore a single NetCDF file interactively.
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            bool: True if exploration completed successfully
        """
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print("=" * 80)
        print("NetCDF File Explorer")
        print("=" * 80)
        
        try:
            # Explore file structure
            structure = self.explorer.explore_netcdf_structure(file_path)
            self.explorer.print_structure_summary(structure)
            
            # Interactive navigation
            return self._navigate_structure(structure)
            
        except Exception as e:
            print(f"❌ Error exploring file: {e}")
            return False
    
    def explore_files(self, file_pattern: str) -> bool:
        """Compare multiple NetCDF files.
        
        Args:
            file_pattern: Glob pattern for files to compare
            
        Returns:
            bool: True if exploration completed successfully
        """
        # Expand glob pattern
        files = glob.glob(file_pattern)
        if not files:
            print(f"❌ No files found matching pattern: {file_pattern}")
            return False
        
        print("=" * 80)
        print(f"NetCDF File Comparison ({len(files)} files)")
        print("=" * 80)
        
        try:
            # Compare files
            comparison = self.explorer.compare_netcdf_files(files)
            
            # Print comparison results
            print(f"\n📊 Comparison Results:")
            print(f"  Total files: {comparison['total_files']}")
            print(f"  Successfully read: {comparison['successful_reads']}")
            print(f"  Common variables: {len(comparison['common_variables'])}")
            
            if comparison['common_variables']:
                print(f"\n🔗 Common variables across all files:")
                for var in sorted(comparison['common_variables']):
                    print(f"  - {var}")
            
            print(f"\n📁 File details:")
            for file_path, file_structure in comparison['files'].items():
                if 'error' not in file_structure:
                    var_count = len(self.explorer.get_variable_paths(file_structure))
                    size_mb = file_structure.get('file_size_mb', 0)
                    print(f"  {os.path.basename(file_path)}: {var_count} variables, {size_mb:.2f} MB")
                else:
                    print(f"  {os.path.basename(file_path)}: ❌ {file_structure['error']}")
            
            print("=" * 80)
            return True
            
        except Exception as e:
            print(f"❌ Error comparing files: {e}")
            return False
    
    def _navigate_structure(self, structure: Dict[str, Any]) -> bool:
        """Interactive navigation through file structure.
        
        Args:
            structure: File structure dictionary
            
        Returns:
            bool: True if navigation completed successfully
        """
        if 'root' not in structure:
            print("❌ No structure information available")
            return False
        
        current_path = []
        current_group = structure['root']
        
        while True:
            print("\n" + "=" * 80)
            print(f"Current location: {'/' + '/'.join(current_path) if current_path else '/ (root)'}")
            print("=" * 80)
            
            # Show current group information
            self._print_group_info(current_group, current_path)
            
            # Show navigation options
            print("\n📂 Navigation:")
            options = []
            
            # Add subgroups
            groups = current_group.get('groups', {})
            if groups:
                print("  Groups:")
                for i, (group_name, group_info) in enumerate(groups.items(), 1):
                    var_count = len(group_info.get('variables', {}))
                    sub_groups = len(group_info.get('groups', {}))
                    print(f"    {i}. {group_name} ({var_count} variables, {sub_groups} subgroups)")
                    options.append(('group', group_name, group_info))
            
            # Add variables
            variables = current_group.get('variables', {})
            if variables:
                print("  Variables:")
                for i, (var_name, var_info) in enumerate(variables.items(), 1):
                    shape = var_info.get('shape', 'N/A')
                    dtype = var_info.get('dtype', 'N/A')
                    size_mb = var_info.get('size_mb', 0)
                    print(f"    {i + len(options)}. {var_name}: {shape} ({dtype}) - {size_mb:.1f} MB")
                    options.append(('variable', var_name, var_info))
            
            # Add navigation commands
            print("\n  Commands:")
            print("    'up' - Go up one level")
            print("    'root' - Go to root")
            print("    'info <name>' - Show detailed info for variable/group")
            print("    'quit' or 'q' - Exit explorer")
            
            # Get user input
            try:
                choice = input("\nEnter choice: ").strip()
                
                if choice.lower() in ['quit', 'q', 'exit']:
                    print("👋 Exiting explorer")
                    return True
                
                elif choice.lower() == 'up':
                    if current_path:
                        current_path.pop()
                        # Navigate back to parent
                        current_group = structure['root']
                        for path_part in current_path:
                            current_group = current_group['groups'][path_part]
                
                elif choice.lower() == 'root':
                    current_path = []
                    current_group = structure['root']
                
                elif choice.lower().startswith('info '):
                    name = choice[5:].strip()
                    self._show_detailed_info(current_group, name)
                
                else:
                    # Try to parse as number
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(options):
                            option_type, option_name, option_info = options[idx]
                            
                            if option_type == 'group':
                                # Navigate into group
                                current_path.append(option_name)
                                current_group = option_info
                            elif option_type == 'variable':
                                # Show variable details
                                self._show_variable_details(option_name, option_info)
                        else:
                            print(f"❌ Invalid choice. Please enter a number between 1 and {len(options)}")
                    except ValueError:
                        print("❌ Invalid input. Please enter a number or command.")
                
            except KeyboardInterrupt:
                print("\n👋 Exiting explorer")
                return True
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _print_group_info(self, group: Dict[str, Any], path: List[str]) -> None:
        """Print information about current group."""
        print(f"\n📂 Group Information:")
        print(f"  Dimensions: {len(group.get('dimensions', {}))}")
        print(f"  Variables: {len(group.get('variables', {}))}")
        print(f"  Subgroups: {len(group.get('groups', {}))}")
        
        if group.get('dimensions'):
            dims_str = ", ".join([f"{k}={v}" for k, v in group['dimensions'].items()])
            print(f"  Dimension details: {dims_str}")
        
        if group.get('attributes'):
            print(f"  Attributes: {len(group['attributes'])}")
            # Show first few attributes
            attrs = list(group['attributes'].items())[:5]
            for key, value in attrs:
                print(f"    {key}: {value}")
            if len(group['attributes']) > 5:
                print(f"    ... and {len(group['attributes']) - 5} more")
    
    def _show_variable_details(self, var_name: str, var_info: Dict[str, Any]) -> None:
        """Show detailed information about a variable."""
        print("\n" + "=" * 80)
        print(f"Variable: {var_name}")
        print("=" * 80)
        print(f"  Dimensions: {var_info.get('dimensions', [])}")
        print(f"  Shape: {var_info.get('shape', 'N/A')}")
        print(f"  Data type: {var_info.get('dtype', 'N/A')}")
        print(f"  Size: {var_info.get('size_mb', 0):.2f} MB")
        
        if var_info.get('attributes'):
            print(f"\n  Attributes:")
            for key, value in var_info['attributes'].items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"    {key}: {value_str}")
    
    def _show_detailed_info(self, group: Dict[str, Any], name: str) -> None:
        """Show detailed info for a variable or group by name."""
        # Check variables
        if name in group.get('variables', {}):
            self._show_variable_details(name, group['variables'][name])
            return
        
        # Check groups
        if name in group.get('groups', {}):
            group_info = group['groups'][name]
            print(f"\n📂 Group: {name}")
            self._print_group_info(group_info, [])
            return
        
        print(f"❌ '{name}' not found in current location")
