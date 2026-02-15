#!/usr/bin/env python3
"""
Test script: render a map (land/sea, coastlines, gridlines) at the same extent
as your data would use, but without plotting any data. Use this to verify
that Cartopy land/sea and coastlines render correctly.

Usage (from repo root):
  python scripts/test_map_only.py "data/5af/ext_t2m/gfs/2t_*.nc" --zoom-factor 100 --zoom-center-lat 27.82 --zoom-center-lon -82.58
  python scripts/test_map_only.py "data/5af/ext_t2m/gfs/*.nc" --zoom-factor 10 --output my_map_test.png
"""

import argparse
import glob
import sys
import os

# Run from repo root so package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xarray as xr
import matplotlib.pyplot as plt

from animate_netcdf.utils.data_processing import DataProcessor
from animate_netcdf.utils.plot_utils import PlotUtils


def main():
    parser = argparse.ArgumentParser(
        description="Render map only (land/sea, coastlines) at data extent — no data layer."
    )
    parser.add_argument(
        "pattern",
        help="NetCDF file pattern (e.g. data/5af/ext_t2m/gfs/2t_*.nc)",
    )
    parser.add_argument(
        "--zoom-factor",
        type=float,
        default=1.0,
        help="Zoom factor (default: 1.0). Use e.g. 100 for your test.",
    )
    parser.add_argument(
        "--zoom-center-lat",
        type=float,
        default=None,
        help="Zoom center latitude (e.g. 27.82)",
    )
    parser.add_argument(
        "--zoom-center-lon",
        type=float,
        default=None,
        help="Zoom center longitude (e.g. -82.58)",
    )
    parser.add_argument(
        "--variable",
        type=str,
        default=None,
        help="Variable name (default: first data variable)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_land_sea.png",
        help="Output PNG path (default: test_land_sea.png)",
    )
    parser.add_argument(
        "--no-place-names",
        action="store_true",
        help="Disable place names on the map",
    )
    parser.add_argument("--map-land-color", type=str, default=None, help="Land fill color (e.g. #b0b0b0)")
    parser.add_argument("--map-ocean-color", type=str, default=None, help="Ocean fill color (e.g. #7eb8da)")
    parser.add_argument("--map-land-alpha", type=float, default=None, help="Land fill opacity 0–1 (e.g. 0.5)")
    parser.add_argument("--map-ocean-alpha", type=float, default=None, help="Ocean fill opacity 0–1 (e.g. 0.45)")
    parser.add_argument("--map-land-hatch", type=str, default=None, help="Land hatch pattern (e.g. ///)")
    parser.add_argument("--map-ocean-hatch", type=str, default=None, help="Ocean hatch pattern (e.g. ---)")
    parser.add_argument(
        "--map-land-sea-scale",
        type=str,
        default=None,
        choices=["110m", "50m", "10m"],
        help="Land/sea resolution: 110m (coarse), 50m (default), 10m (fine)",
    )
    args = parser.parse_args()

    # Resolve first file
    files = sorted(glob.glob(args.pattern))
    if not files:
        print(f"❌ No files matched pattern: {args.pattern}")
        sys.exit(1)
    first_file = files[0]
    print(f"📁 Using file: {first_file}")
    print(f"🔍 Zoom: factor={args.zoom_factor}, center=({args.zoom_center_lat}, {args.zoom_center_lon})")

    # Load and get extent from data (same logic as animation)
    PlotUtils.setup_cartopy_logging()
    with xr.open_dataset(first_file) as ds:
        data_vars = [v for v in ds.data_vars if ds[v].ndim >= 2]
        if not data_vars:
            print("❌ No 2D+ data variables found in the file.")
            sys.exit(1)
        var_name = args.variable or data_vars[0]
        if var_name not in ds.data_vars:
            print(f"❌ Variable '{var_name}' not found. Available: {list(ds.data_vars)}")
            sys.exit(1)
        data_array = ds[var_name]

    data, lats, lons = DataProcessor.prepare_data_for_plotting(
        data_array,
        time_step=0,
        animate_dim="time",
        zoom_factor=args.zoom_factor,
        zoom_center_lat=args.zoom_center_lat,
        zoom_center_lon=args.zoom_center_lon,
        verbose=False,
    )
    print(f"📐 Extent: lon [{lons.min():.4f}, {lons.max():.4f}], lat [{lats.min():.4f}, {lats.max():.4f}]")
    print(f"   Grid shape: {lats.shape}")

    # Map only: same projection and setup, no data layer
    fig, ax = PlotUtils.create_geographic_plot("efficient")
    PlotUtils.setup_geographic_plot(
        ax, lats, lons,
        show_land_sea=True,
        show_place_names=not args.no_place_names,
        map_land_color=args.map_land_color,
        map_ocean_color=args.map_ocean_color,
        map_land_alpha=args.map_land_alpha,
        map_ocean_alpha=args.map_ocean_alpha,
        map_land_hatch=args.map_land_hatch,
        map_ocean_hatch=args.map_ocean_hatch,
        map_land_sea_scale=args.map_land_sea_scale,
    )
    ax.set_title("Map only (no data) — land/sea, coastlines, gridlines")

    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {args.output}")


if __name__ == "__main__":
    main()
