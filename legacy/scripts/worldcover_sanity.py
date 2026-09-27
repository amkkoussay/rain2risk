"""Live spatial sanity check for WorldCover fractions."""
import sys, json
sys.path.insert(0, "/home/ubuntu/rain2risk/backend")
from geo.grid import make_grid
from geo.worldcover import fetch_worldcover

points = {"urban": (35.6762, 139.6503), "rural": (46.5, 6.7), "coastal": (52.3676, 4.9041)}
for name, (lat, lon) in points.items():
    cell = make_grid(lat, lon, rows=1, cols=1, radius_deg=0.004)[0]
    result = fetch_worldcover([cell])["cells"][0]
    print(json.dumps({"location": name, "land_cover_class": result["land_cover_class"], "fractions": {k: v for k, v in result.items() if k.endswith("_fraction")}, "raw_class_codes": result["raw_class_codes"]}, sort_keys=True))
