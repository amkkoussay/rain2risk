"""ESA WorldCover 2021 provider using the service's own georeferencing."""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import lerc
except ImportError:  # WorldCover is optional for unrelated imports/tests.
    lerc = None

WORLD_COVER_SERVICE_URL = "https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/European_Space_Agency_WorldCover_2021_Land_Cover_WGS84_7/ImageServer"
WORLD_COVER_TILE_URL = WORLD_COVER_SERVICE_URL + "/tile"
CLASS_NAMES = {10: "tree_cover", 20: "shrubland", 30: "grassland", 40: "cropland", 50: "built_up", 60: "bare_sparse", 70: "snow_ice", 80: "water", 90: "wetland", 95: "mangroves", 100: "moss_lichen"}
VALID_CODES = set(CLASS_NAMES)
_METADATA = None

class WorldCoverError(RuntimeError):
    pass


def _service_metadata():
    global _METADATA
    if _METADATA is not None: return _METADATA
    request = Request(WORLD_COVER_SERVICE_URL + "?" + urlencode({"f": "pjson"}), headers={"User-Agent": "Rain2Risk/1.0"})
    try:
        with urlopen(request, timeout=30) as response: metadata = json.loads(response.read().decode())
        tile_info = metadata["tileInfo"]
        _METADATA = {"origin": tile_info["origin"], "rows": int(tile_info["rows"]), "cols": int(tile_info["cols"]), "lods": tile_info["lods"], "extent": metadata["extent"]}
        return _METADATA
    except Exception as error:
        raise WorldCoverError("WorldCover metadata is unavailable") from error


def _level(metadata):
    # WorldCover is a 10 m product; use the finest advertised service level.
    return min(metadata["lods"], key=lambda lod: float(lod["resolution"]))


def _tile_xy(lat, lon, metadata):
    lod = _level(metadata); resolution = float(lod["resolution"]); cols = metadata["cols"]; rows = metadata["rows"]
    origin_x = float(metadata["origin"]["x"]); origin_y = float(metadata["origin"]["y"])
    tile_width = cols * resolution; tile_height = rows * resolution
    return int((lon - origin_x) // tile_width), int((origin_y - lat) // tile_height), resolution, lod["level"]


def _fetch_tile(x, y, level):
    if lerc is None: raise WorldCoverError("WorldCover dependency lerc is not installed")
    request = Request(f"{WORLD_COVER_TILE_URL}/{level}/{y}/{x}", headers={"User-Agent": "Rain2Risk/1.0"})
    try:
        with urlopen(request, timeout=60) as response: status, array, mask = lerc.decode(response.read())
    except Exception as error:
        raise WorldCoverError("WorldCover request failed") from error
    if status != 0: raise WorldCoverError("WorldCover request failed")
    return array, mask


def _cell_fraction(cell, metadata, tile_cache, samples=5):
    south, west = cell["bounds"][0]; north, east = cell["bounds"][1]
    east_unwrapped = east if east >= west else east + 360.0
    counts = {name: 0 for name in CLASS_NAMES.values()}; valid = 0
    origin_x = float(metadata["origin"]["x"]); origin_y = float(metadata["origin"]["y"]); cols = metadata["cols"]; rows = metadata["rows"]
    for rr in range(samples):
        lat = south + (rr + .5) * (north - south) / samples
        for cc in range(samples):
            lon = west + (cc + .5) * (east_unwrapped - west) / samples
            lon = ((lon + 180.0) % 360.0) - 180.0
            x, y, resolution, level = _tile_xy(lat, lon, metadata)
            if (x, y, level) not in tile_cache: tile_cache[(x, y, level)] = _fetch_tile(x, y, level)
            array, mask = tile_cache[(x, y, level)]
            px = max(0, min(cols - 1, int(((lon - origin_x) / resolution) - x * cols)))
            py = max(0, min(rows - 1, int(((origin_y - lat) / resolution) - y * rows)))
            if mask is not None and not bool(mask[py, px]): continue
            code = int(array[py, px])
            if code in VALID_CODES: counts[CLASS_NAMES[code]] += 1; valid += 1
    if valid == 0: raise WorldCoverError("WorldCover request returned no valid pixels")
    result = {f"{name}_fraction": round(count / valid, 4) for name, count in counts.items()}
    result["land_cover_classes"] = {name: count for name, count in counts.items() if count}
    result["raw_class_codes"] = {str(code): CLASS_NAMES[code] for code in CLASS_NAMES if counts[CLASS_NAMES[code]]}
    result["land_cover_class"] = max(counts, key=counts.get)
    return result


def fetch_worldcover(cells):
    metadata = _service_metadata(); tile_cache = {}
    extent = metadata["extent"]
    if any(cell["bounds"][0][0] < extent["ymin"] or cell["bounds"][1][0] > extent["ymax"] for cell in cells):
        raise WorldCoverError("WorldCover is unavailable outside its published latitude extent")
    values = [_cell_fraction(cell, metadata, tile_cache) for cell in cells]
    return {"cells": values, "source": "ESA WorldCover 2021 via ArcGIS REST metadata and LERC tiles", "available": True}
