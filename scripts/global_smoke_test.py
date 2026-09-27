"""Live smoke check for the same global analysis path at five locations."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from api.analyze import analyze

LOCATIONS = {"Tunis": (36.8065, 10.1815), "Tokyo": (35.6762, 139.6503), "New York": (40.7128, -74.0060), "Dhaka": (23.8103, 90.4125), "Amsterdam": (52.3676, 4.9041)}

for name, (lat, lon) in LOCATIONS.items():
    try:
        result = analyze(lat, lon)
        features = result["grid"]["features"]
        props = [f["properties"] for f in features]
        elevations = [p["elevation_m"] for p in props]
        classes = sorted({p.get("land_cover_class") for p in props})
        osm_water = sum(bool(p.get("water_distance_m") is not None) for p in props)
        print(json.dumps({"location": name, "status": "PASS", "grid_cells": len(features), "risk_score": result["risk"].get("score"), "elevation_range_m": [min(elevations), max(elevations)], "land_cover_classes": classes, "cells_with_near_water": osm_water, "quality": result.get("data_quality", {})}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"location": name, "status": "FAIL", "error": str(error)}, ensure_ascii=False))
