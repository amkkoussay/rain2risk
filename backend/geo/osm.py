"""OpenStreetMap Overpass provider with lightweight per-cell association."""

import json
import math
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class OSMError(RuntimeError):
    pass


def fetch_osm(min_lat, min_lon, max_lat, max_lon):
    query = f'[out:json][timeout:90];(nwr["building"]({min_lat},{min_lon},{max_lat},{max_lon});nwr["waterway"]({min_lat},{min_lon},{max_lat},{max_lon});nwr["natural"~"water|wetland"]({min_lat},{min_lon},{max_lat},{max_lon});nwr["landuse"]({min_lat},{min_lon},{max_lat},{max_lon}););out center geom;'
    request = Request("https://overpass-api.de/api/interpreter", data=urlencode({"data": query}).encode(), headers={"User-Agent": "Rain2Risk/1.0"})
    try:
        with urlopen(request, timeout=90) as response: return json.loads(response.read().decode())
    except Exception as error:
        raise OSMError("OpenStreetMap data is unavailable") from error


def _distance_m(lat1, lon1, lat2, lon2):
    radius = 6371000.0; p1, p2 = math.radians(lat1), math.radians(lat2); dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _points(element):
    points = []
    if element.get("center"): points.append(element["center"])
    points.extend(element.get("geometry") or [])
    return [(float(p["lat"]), float(p["lon"])) for p in points if p and p.get("lat") is not None and p.get("lon") is not None]


def extract_facts(cells, payload):
    elements = payload.get("elements", [])
    buildings = [e for e in elements if e.get("tags", {}).get("building")]
    water = [e for e in elements if e.get("tags", {}).get("waterway") or e.get("tags", {}).get("natural") in {"water", "wetland"}]
    landuse = [e for e in elements if e.get("tags", {}).get("landuse")]
    for cell in cells:
        if cell.get("bounds"):
            south, west = cell["bounds"][0]; north, east = cell["bounds"][1]
        else:
            south, west, north, east = cell["lat"] - 0.001, cell["lon"] - 0.001, cell["lat"] + 0.001, cell["lon"] + 0.001
        cell_radius = max(_distance_m(south, west, north, east), 30.0) / 2
        nearby_water = [(e, p) for e in water for p in _points(e) if _distance_m(cell["lat"], cell["lon"], *p) <= cell_radius]
        nearby_buildings = [e for e in buildings if any(south <= lat <= north and west <= lon <= east for lat, lon in _points(e)) or any(_distance_m(cell["lat"], cell["lon"], lat, lon) <= cell_radius for lat, lon in _points(e))]
        nearby_landuse = [e for e in landuse if any(south <= lat <= north and west <= lon <= east for lat, lon in _points(e)) or any(_distance_m(cell["lat"], cell["lon"], lat, lon) <= cell_radius for lat, lon in _points(e))]
        if len(cells) == 1:
            nearby_landuse.extend(e for e in landuse if not _points(e))
        distances = [_distance_m(cell["lat"], cell["lon"], *point) for element, point in nearby_water for point in [point]]
        cell["waterway_present"] = bool(nearby_water)
        cell["building_count"] = len(nearby_buildings)
        cell["water_distance_m"] = round(min(distances), 1) if distances else None
        cell["landuse_tags"] = sorted({e.get("tags", {}).get("landuse") for e in nearby_landuse if e.get("tags", {}).get("landuse")})
    return cells
