"""Global provider orchestration with explicit data-quality states."""
import json
from pathlib import Path
from .dem import DEMError, derive_slopes, fetch_elevations
from .features import build_features
from .grid import make_grid
from .osm import OSMError, fetch_osm
from .worldcover import WorldCoverError, fetch_worldcover, WORLD_COVER_TILE_URL
from .osm import extract_facts as _attach_osm_features

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"

class GlobalDataError(RuntimeError): pass

def _key(lat, lon): return f"{float(lat):.4f}_{float(lon):.4f}"

def _cached(name, key, loader):
    folder = CACHE / name; folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}.json"
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError): path.unlink(missing_ok=True)
    value = loader()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value), encoding="utf-8")
    tmp.replace(path)
    return value

def get_global_grid(lat, lon):
    cells = make_grid(lat, lon)
    min_lat = min(c["bounds"][0][0] for c in cells); max_lat = max(c["bounds"][1][0] for c in cells)
    min_lon = min(c["bounds"][0][1] for c in cells); max_lon = max(c["bounds"][1][1] for c in cells)
    key = _key(lat, lon)
    quality = {}

    try:
        dem = _cached("dem", key, lambda: fetch_elevations(cells))
        elevations = dem["values"]
        quality["dem"] = {"status": "available", "source": dem["source"]}
    except (DEMError, KeyError, ValueError) as error:
        elevations = [None] * len(cells)
        quality["dem"] = {"status": "failed", "source": "Open-Meteo Elevation / Copernicus DEM", "reason": str(error)}

    try:
        cover = _cached("worldcover-v2", key, lambda: fetch_worldcover(cells))
        cover_cells = [dict(c, worldcover_status="available") for c in cover["cells"]]
        quality["worldcover"] = {"status": "available", "source": cover["source"]}
    except (WorldCoverError, KeyError, ValueError) as error:
        names = ("tree_cover","shrubland","grassland","cropland","built_up","bare_sparse","snow_ice","water","wetland","mangroves","moss_lichen")
        cover_cells = []
        for _ in cells:
            item = {f"{name}_fraction": None for name in names}
            item.update({"land_cover_classes": {}, "raw_class_codes": {}, "land_cover_class": None,
                         "worldcover_status": "failed", "worldcover_reason": str(error)})
            cover_cells.append(item)
        quality["worldcover"] = {"status": "failed", "source": "ESA WorldCover 2021 via ArcGIS REST metadata and LERC tiles", "reason": str(error)}

    try:
        osm = _cached("osm", key, lambda: {"payload": fetch_osm(min_lat, min_lon, max_lat, max_lon),
                                            "source": "OpenStreetMap via Overpass", "status": "available"})
        osm_payload = osm["payload"]
        quality["osm"] = {"status": "available", "source": osm["source"]}
    except (OSMError, KeyError, ValueError) as error:
        osm_payload = None
        quality["osm"] = {"status": "failed", "source": "OpenStreetMap via Overpass", "reason": str(error)}

    cells = build_features(cells, elevations, cover_cells, osm_payload, derive_slopes)
    if osm_payload is None:
        for cell in cells:
            cell.update({"waterway_present": None, "building_count": None, "water_distance_m": None, "landuse_tags": None})
    sources = {"elevation": "Open-Meteo Elevation / Copernicus DEM",
               "land_cover": "ESA WorldCover 2021 via ArcGIS REST metadata and LERC tiles",
               "osm": "OpenStreetMap via Overpass"}
    return cells, sources, quality
