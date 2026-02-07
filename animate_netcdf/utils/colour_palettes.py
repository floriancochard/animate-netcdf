#!/usr/bin/env python3
"""
Colour palettes for NetCDF visualization.
Provides meteorology-focused colormaps (matplotlib names) and variable suggestions.
"""

from typing import List, Tuple, Optional

# List of (id, display_name, matplotlib_cmap).
# All use built-in matplotlib colormaps (no extra deps).
PALETTES: List[Tuple[str, str, str]] = [
    # Wind speed (intensity: light → strong)
    ("wind_speed_viridis", "Wind speed (Viridis)", "viridis"),
    ("wind_speed_ylorrd", "Wind speed (Yellow-Orange-Red)", "YlOrRd"),
    ("wind_speed_plasma", "Wind speed (Plasma)", "plasma"),
    # Wind direction (cyclic; use with care on sequential data)
    ("wind_direction_twilight", "Wind direction (Twilight)", "twilight"),
    ("wind_direction_hsv", "Wind direction (HSV)", "hsv"),
    # Temperature (cold → hot)
    ("temperature_rdylbu", "Temperature (Red-Yellow-Blue)", "RdYlBu_r"),
    ("temperature_coolwarm", "Temperature (Cool-Warm)", "coolwarm"),
    ("temperature_bwr", "Temperature (Blue-White-Red)", "bwr"),
    ("temperature_rdbu", "Temperature (Red-Blue)", "RdBu_r"),
    # Rainfall / precipitation
    ("rainfall_blues", "Rainfall (Blues)", "Blues"),
    ("rainfall_ylgnbu", "Rainfall (Yellow-Green-Blue)", "YlGnBu"),
    ("rainfall_viridis", "Rainfall (Viridis)", "viridis"),
    ("rainfall_puor", "Rainfall (Purple-Orange)", "PuOr"),
    # Solar radiation
    ("solar_ylorrd", "Solar radiation (Yellow-Orange-Red)", "YlOrRd"),
    ("solar_hot", "Solar radiation (Hot)", "hot"),
    ("solar_plasma", "Solar radiation (Plasma)", "plasma"),
    ("solar_inferno", "Solar radiation (Inferno)", "inferno"),
    # Humidity
    ("humidity_blues", "Humidity (Blues)", "Blues"),
    ("humidity_gnbu", "Humidity (Green-Blue)", "GnBu"),
    ("humidity_ylgnbu", "Humidity (Yellow-Green-Blue)", "YlGnBu"),
    # Generic / multi-purpose
    ("generic_blues", "Generic (Blues)", "Blues"),
    ("generic_viridis", "Generic (Viridis)", "viridis"),
    ("generic_plasma", "Generic (Plasma)", "plasma"),
    ("generic_magma", "Generic (Magma)", "magma"),
    ("generic_cividis", "Generic (Cividis)", "cividis"),
]

# Variable name (or substring) -> list of palette ids to suggest first
SUGGESTED_PALETTES_BY_VARIABLE: dict = {
    "wind": ["wind_speed_viridis", "wind_speed_ylorrd", "wind_direction_twilight"],
    "speed": ["wind_speed_viridis", "wind_speed_ylorrd"],
    "direction": ["wind_direction_twilight", "wind_direction_hsv"],
    "temp": ["temperature_rdylbu", "temperature_coolwarm", "temperature_bwr"],
    "temperature": ["temperature_rdylbu", "temperature_coolwarm"],
    "rain": ["rainfall_blues", "rainfall_ylgnbu", "rainfall_viridis"],
    "precip": ["rainfall_blues", "rainfall_ylgnbu"],
    "solar": ["solar_ylorrd", "solar_plasma", "solar_hot"],
    "radiation": ["solar_ylorrd", "solar_plasma"],
    "humidity": ["humidity_blues", "humidity_gnbu", "humidity_ylgnbu"],
    "salinity": ["generic_viridis", "generic_plasma", "generic_blues"],
    "sst": ["temperature_rdylbu", "temperature_coolwarm", "temperature_bwr"],
}


def get_palette_id_to_cmap() -> dict:
    """Return mapping palette_id -> matplotlib cmap name."""
    return {pid: cmap for pid, _name, cmap in PALETTES}


def get_palette_by_id(palette_id: str) -> Optional[str]:
    """Return matplotlib cmap name for a palette id, or None if not found."""
    for pid, _name, cmap in PALETTES:
        if pid == palette_id:
            return cmap
    return None


def get_suggested_palette_ids_for_variable(variable: str) -> List[str]:
    """Return list of palette ids suggested for the given variable name."""
    var_lower = (variable or "").lower()
    for key, ids in SUGGESTED_PALETTES_BY_VARIABLE.items():
        if key in var_lower:
            return ids
    return ["generic_blues", "generic_viridis", "generic_plasma"]
