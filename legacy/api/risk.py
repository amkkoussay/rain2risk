"""Risk API orchestration layer."""

import sqlite3
from pathlib import Path
from typing import Any

from api.location import get_location
from api.weather import get_weather
from geo.repository import GeoRepository
from risk.scoring import calculate_risk

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "rain2risk.db"


def get_risk(lat: float, lon: float) -> dict[str, Any]:
    location = get_location(lat, lon)
    weather = get_weather(lat, lon)
    with sqlite3.connect(DATABASE_PATH) as connection:
        minimum, maximum = connection.execute("SELECT MIN(elevation_m), MAX(elevation_m) FROM cells").fetchone()
    geo = dict(location["cell"]["features"])
    geo["min_elevation_m"] = minimum
    geo["max_elevation_m"] = maximum
    risk = calculate_risk(weather, geo).to_dict()
    return {
        "location": location["location"],
        "weather": {
            "rain_1h_mm": weather["rainfall"]["next_1h_mm"],
            "rain_6h_mm": weather["rainfall"]["next_6h_mm"],
            "rain_24h_mm": weather["rainfall"]["next_24h_mm"],
        },
        "geospatial": location["cell"]["features"],
        "risk": risk,
        "disclaimer": "Estimated flood risk, not an official flood warning.",
    }
