#!/usr/bin/env python3
"""
NetCDF Explorer Script
Demonstrates how to explore NetCDF file structure including groups and subgroups
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to import animate_netcdf
sys.path.insert(0, str(Path(__file__).parent.parent))

from animate_netcdf.utils import explore_netcdf_file, get_netcdf_groups, NetCDFExplorer


def main():
    """Main function to explore NetCDF files."""
    
    if len(sys.argv) < 2:
        print("Usage: python explore_netcdf.py <netcdf_file> [options]")
        print("\nOptions:")
        print("  --no-print    Don't print summary to stdout")
        print("  --compare     Compare multiple files (provide multiple file paths)")
        print("  --groups-only Show only group names")
        print("\nExamples:")
        print("  python explore_netcdf.py data/20250816.nc")
        print("  python explore_netcdf.py data/20250816.nc --groups-only")
        print("  python explore_netcdf.py data/*.nc --compare")
        return
    
    file_paths = []
    options = {
        'print_summary': True,
        'compare': False,
        'groups_only': False
    }
    
    # Parse arguments
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            if arg == '--no-print':
                options['print_summary'] = False
            elif arg == '--compare':
                options['compare'] = True
            elif arg == '--groups-only':
                options['groups_only'] = True
        else:
            file_paths.append(arg)
    
    if not file_paths:
        print("❌ No NetCDF files specified")
        return
    
    # Handle single file exploration
    if len(file_paths) == 1 and not options['compare']:
        file_path = file_paths[0]
        
        if options['groups_only']:
            print(f"📂 Groups in {file_path}:")
            groups = get_netcdf_groups(file_path)
            if groups:
                for group in groups:
                    print(f"  - {group}")
            else:
                print("  No groups found (flat structure)")
        else:
            try:
                structure = explore_netcdf_file(file_path, options['print_summary'])
                if not options['print_summary']:
                    print(f"✅ Successfully explored {file_path}")
                    print(f"📊 Total variables found: {len(NetCDFExplorer.get_variable_paths(structure))}")
            except Exception as e:
                print(f"❌ Error exploring {file_path}: {e}")
    
    # Handle multiple file comparison
    elif options['compare']:
        if len(file_paths) < 2:
            print("❌ Need at least 2 files for comparison")
            return
        
        print(f"🔍 Comparing {len(file_paths)} NetCDF files...")
        try:
            comparison = NetCDFExplorer.compare_netcdf_files(file_paths)
            
            print(f"\n📊 Comparison Results:")
            print(f"  Total files: {comparison['total_files']}")
            print(f"  Successfully read: {comparison['successful_reads']}")
            print(f"  Common variables: {len(comparison['common_variables'])}")
            
            if comparison['common_variables']:
                print(f"\n🔗 Common variables across all files:")
                for var in sorted(comparison['common_variables']):
                    print(f"  - {var}")
            
            print(f"\n📁 File details:")
            for file_path, structure in comparison['files'].items():
                if 'error' not in structure:
                    var_count = len(NetCDFExplorer.get_variable_paths(structure))
                    size_mb = structure.get('file_size_mb', 0)
                    print(f"  {file_path}: {var_count} variables, {size_mb:.2f} MB")
                else:
                    print(f"  {file_path}: ❌ {structure['error']}")
                    
        except Exception as e:
            print(f"❌ Error during comparison: {e}")
    
    else:
        print("❌ Invalid option combination")


if __name__ == "__main__":
    main()
