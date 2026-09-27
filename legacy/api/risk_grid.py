"""Risk grid API service.

The grid uses one weather forecast for the study area. It does not call
OpenWeather once per cell.
"""

import sqlite3
import time
from pathlib import Path
from typing import Any

from api.weather import get_weather
from config import WEATHER_CACHE_TTL
from risk.scoring import calculate_risk

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "rain2risk.db"
_GRID_CACHE: tuple[float, list[dict[str, Any]]] | None = None


def _load_cells() -> list[dict[str, Any]]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT id, lat, lon, elevation_m, slope_deg, built_up, water_distance_m FROM cells ORDER BY id"
        ).fetchall()
    return [
        {
            "id": row[0], "lat": row[1], "lon": row[2],
            "elevation_m": row[3], "slope_deg": row[4],
            "built_up": row[5], "water_distance_m": row[6],
        }
        for row in rows
    ]


def get_risk_grid() -> dict[str, list[dict[str, Any]]]:
    """Return compact cell risk data using one shared weather request/cache."""
    global _GRID_CACHE
    if _GRID_CACHE and time.time() - _GRID_CACHE[0] < WEATHER_CACHE_TTL:
        return {"cells": _GRID_CACHE[1]}

    cells = _load_cells()
    if not cells:
        raise LookupError("risk grid is unavailable")
    weather = get_weather(cells[0]["lat"], cells[0]["lon"])
    elevations = [cell["elevation_m"] for cell in cells]
    lat_step = min((abs(a["lat"] - b["lat"]) for a in cells for b in cells if a["lat"] != b["lat"]), default=0.0025)
    lon_step = min((abs(a["lon"] - b["lon"]) for a in cells for b in cells if a["lon"] != b["lon"]), default=0.004)
    result = []
    for cell in cells:
        geo = dict(cell)
        geo["min_elevation_m"] = min(elevations)
        geo["max_elevation_m"] = max(elevations)
        risk = calculate_risk(weather, geo)
        result.append({"id": cell["id"], "lat": cell["lat"], "lon": cell["lon"], "bounds": [[cell["lat"] - lat_step / 2, cell["lon"] - lon_step / 2], [cell["lat"] + lat_step / 2, cell["lon"] + lon_step / 2]], "risk_score": round(risk.score), "risk_level": risk.level})
    _GRID_CACHE = (time.time(), result)
    return {"cells": result}
