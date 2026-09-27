"""Build a real-data SQLite grid for the Tunis study area.

Sources:
- Open-Meteo Elevation API: 90 m digital elevation model.
- OpenStreetMap Overpass: mapped landuse and waterways.

This preprocessing script may use the network. The production app only reads
SQLite and needs no GIS dependency.
"""

import json
import math
import sqlite3
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "rain2risk.db"
GIS_DIR = ROOT / "data" / "gis"
MIN_LAT, MAX_LAT, MIN_LON, MAX_LON = 36.79, 36.82, 10.16, 10.20
ROWS, COLS = 8, 10


def get_json(url, data=None):
    request = Request(url, data=data, headers={"User-Agent": "Rain2Risk/0.1 research MVP"})
    with urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def points():
    return [(MIN_LAT + (r + 0.5) * (MAX_LAT - MIN_LAT) / ROWS, MIN_LON + (c + 0.5) * (MAX_LON - MIN_LON) / COLS) for r in range(ROWS) for c in range(COLS)]


def elevation_data(coords):
    query = urlencode({"latitude": ",".join(str(x[0]) for x in coords), "longitude": ",".join(str(x[1]) for x in coords)})
    return get_json(f"https://api.open-meteo.com/v1/elevation?{query}")


def osm_data():
    query = f'[out:json][timeout:90];(way["waterway"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});way["landuse"~"residential|commercial|industrial"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}););out geom;'
    return get_json("https://overpass-api.de/api/interpreter", data=urlencode({"data": query}).encode())


def distance_m(lat1, lon1, lat2, lon2):
    dy, dx = (lat2 - lat1) * 111320, (lon2 - lon1) * 111320 * math.cos(math.radians(lat1))
    return math.hypot(dx, dy)


def point_in_polygon(lat, lon, ring):
    inside = False
    for i in range(len(ring)):
        y1, x1 = ring[i].get("lat"), ring[i].get("lon")
        y2, x2 = ring[i - 1].get("lat"), ring[i - 1].get("lon")
        if ((x1 > lon) != (x2 > lon)) and lat < (y2 - y1) * (lon - x1) / ((x2 - x1) or 1e-12) + y1:
            inside = not inside
    return inside


def build_grid():
    coords = points()
    elevations = elevation_data(coords)
    osm = osm_data()
    GIS_DIR.mkdir(parents=True, exist_ok=True)
    (GIS_DIR / "elevation_points.json").write_text(json.dumps(elevations, indent=2), encoding="utf-8")
    (GIS_DIR / "osm_features.json").write_text(json.dumps(osm, indent=2), encoding="utf-8")
    values = elevations.get("elevation", [])
    ways = osm.get("elements", [])
    water_nodes = [(p.get("lat"), p.get("lon")) for way in ways if way.get("tags", {}).get("waterway") for p in way.get("geometry", [])]
    landuse = [way.get("geometry", []) for way in ways if way.get("tags", {}).get("landuse")]
    rows = []
    for index, (lat, lon) in enumerate(coords):
        elev = float(values[index])
        water = min((distance_m(lat, lon, x, y) for x, y in water_nodes), default=2000.0)
        built = 1.0 if any(point_in_polygon(lat, lon, ring) for ring in landuse if len(ring) >= 3) else 0.0
        rows.append([index + 1, round(lat, 6), round(lon, 6), round(elev, 2), 0.0, built, round(min(water, 5000.0), 1)])
    by_point = {(r, c): rows[r * COLS + c][3] for r in range(ROWS) for c in range(COLS)}
    for r in range(ROWS):
        for c in range(COLS):
            north = by_point.get((max(0, r - 1), c), by_point[(r, c)])
            south = by_point.get((min(ROWS - 1, r + 1), c), by_point[(r, c)])
            east = by_point.get((r, min(COLS - 1, c + 1)), by_point[(r, c)])
            west = by_point.get((r, max(0, c - 1)), by_point[(r, c)])
            rise = math.hypot(south - north, east - west)
            rows[r * COLS + c][4] = round(math.degrees(math.atan2(rise, 2 * 250)), 2)
    DATABASE.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        connection.executescript("DROP TABLE IF EXISTS cells; CREATE TABLE cells (id INTEGER PRIMARY KEY, lat REAL NOT NULL, lon REAL NOT NULL, elevation_m REAL NOT NULL, slope_deg REAL NOT NULL, built_up REAL NOT NULL CHECK (built_up BETWEEN 0.0 AND 1.0), water_distance_m REAL NOT NULL CHECK (water_distance_m >= 0.0)); CREATE INDEX idx_cells_lat_lon ON cells (lat, lon);")
        connection.executemany("INSERT INTO cells VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        connection.commit()
    print(f"Built {len(rows)} real-data cells at {DATABASE}")
    print(f"Elevation source: Open-Meteo; OSM ways: {len(ways)}; landuse polygons: {len(landuse)}; waterways: {len(water_nodes)} nodes")
    return len(rows)


if __name__ == "__main__":
    build_grid()
