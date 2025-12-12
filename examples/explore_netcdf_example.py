#!/usr/bin/env python3
"""
Example script showing how to use the NetCDF Explorer utilities
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path to import animate_netcdf
sys.path.insert(0, str(Path(__file__).parent.parent))

from animate_netcdf.utils import (
    NetCDFExplorer, 
    explore_netcdf_file, 
    get_netcdf_groups
)


def main():
    """Demonstrate different ways to explore NetCDF files."""
    
    # Example file path - update this to match your file
    file_path = "data/20250816.nc"
    
    print("🔍 NetCDF Explorer Examples")
    print("=" * 50)
    
    # Method 1: Simple group listing
    print("\n1️⃣ Simple group listing:")
    groups = get_netcdf_groups(file_path)
    if groups:
        for group in groups:
            print(f"   📁 {group}")
    else:
        print("   No groups found")
    
    # Method 2: Full structure exploration
    print("\n2️⃣ Full structure exploration:")
    try:
        structure = NetCDFExplorer.explore_netcdf_structure(file_path)
        print(f"   ✅ File explored successfully")
        print(f"   📊 File size: {structure['file_size_mb']:.2f} MB")
        print(f"   🔧 Format: {structure['format']}")
        
        # Get all variable paths
        variable_paths = NetCDFExplorer.get_variable_paths(structure)
        print(f"   🔢 Total variables: {len(variable_paths)}")
        
        # Show some variable examples
        if variable_paths:
            print(f"   📝 Variable examples:")
            for var_path in variable_paths[:5]:
                print(f"      - {var_path}")
            if len(variable_paths) > 5:
                print(f"      ... and {len(variable_paths) - 5} more")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 3: Interactive exploration with printing
    print("\n3️⃣ Interactive exploration (with output):")
    try:
        explore_netcdf_file(file_path, print_summary=True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 4: Programmatic access to specific groups
    print("\n4️⃣ Programmatic access to specific groups:")
    try:
        structure = NetCDFExplorer.explore_netcdf_structure(file_path)
        root = structure['root']
        
        # Access the Stations group
        if 'Stations' in root.get('groups', {}):
            stations_group = root['groups']['Stations']
            print(f"   📁 Stations group found")
            print(f"      📊 Subgroups: {len(stations_group.get('groups', {}))}")
            
            # Access a specific subgroup
            if 'Betsizarai' in stations_group.get('groups', {}):
                betsi_group = stations_group['groups']['Betsizarai']
                print(f"      📁 Betsizarai subgroup:")
                print(f"         🔢 Variables: {len(betsi_group.get('variables', {}))}")
                
                # Show some variables from this subgroup
                var_names = list(betsi_group.get('variables', {}).keys())[:5]
                if var_names:
                    print(f"         📝 Variables: {', '.join(var_names)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 5: Compare multiple files
    print("\n5️⃣ File comparison (if multiple files exist):")
    try:
        # Look for other NetCDF files in the data directory
        data_dir = Path(file_path).parent
        nc_files = list(data_dir.glob("*.nc"))
        
        if len(nc_files) > 1:
            print(f"   🔍 Comparing {len(nc_files)} files...")
            comparison = NetCDFExplorer.compare_netcdf_files([str(f) for f in nc_files])
            
            print(f"   📊 Comparison results:")
            print(f"      Total files: {comparison['total_files']}")
            print(f"      Successfully read: {comparison['successful_reads']}")
            print(f"      Common variables: {len(comparison['common_variables'])}")
            
            if comparison['common_variables']:
                print(f"      🔗 Common variables:")
                for var in comparison['common_variables'][:3]:
                    print(f"         - {var}")
                if len(comparison['common_variables']) > 3:
                    print(f"         ... and {len(comparison['common_variables']) - 3} more")
        else:
            print(f"   ℹ️  Only one NetCDF file found in {data_dir}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    main()
