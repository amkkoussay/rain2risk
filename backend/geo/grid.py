"""Small geographic grid helpers for any valid world coordinate."""

import math

ROWS, COLS = 8, 10
RADIUS_DEG = 0.010
MAX_LATITUDE = 85.0


def normalize_longitude(lon: float) -> float:
    return ((float(lon) + 180.0) % 360.0) - 180.0


def make_grid(lat: float, lon: float, rows: int = ROWS, cols: int = COLS, radius_deg: float = RADIUS_DEG) -> list[dict]:
    lat = float(lat); lon = normalize_longitude(lon)
    if abs(lat) > MAX_LATITUDE:
        raise ValueError("latitude must be between -85 and 85 for the MVP")
    min_lat, max_lat = lat - radius_deg, lat + radius_deg
    lon_radius = radius_deg / max(0.2, math.cos(math.radians(lat)))
    min_lon, max_lon = lon - lon_radius, lon + lon_radius
    lat_step, lon_step = (max_lat - min_lat) / rows, (max_lon - min_lon) / cols
    cells = []
    for r in range(rows):
        for c in range(cols):
            south, north = min_lat + r * lat_step, min_lat + (r + 1) * lat_step
            west = normalize_longitude(min_lon + c * lon_step)
            east = normalize_longitude(min_lon + (c + 1) * lon_step)
            cells.append({"cell_id": f"r{r}c{c}", "row": r, "col": c,
                          "lat": min_lat + (r + .5) * lat_step,
                          "lon": normalize_longitude(min_lon + (c + .5) * lon_step),
                          "bounds": [[south, west], [north, east]],
                          "geometry": {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}})
    return cells


def cell_dimensions_m(cell: dict) -> tuple[float, float]:
    south, west = cell["bounds"][0]
    north, east = cell["bounds"][1]
    lat_m = 111320.0 * abs(north - south)
    lon_m = 111320.0 * max(0.05, math.cos(math.radians((south + north) / 2))) * abs(east - west)
    return lat_m, lon_m
