"""Location API service."""

from pathlib import Path
from typing import Any

from geo.repository import GeoRepository
from geo.spatial import get_nearest_cell

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "rain2risk.db"


def get_location(lat: float, lon: float) -> dict[str, Any]:
    cell = get_nearest_cell(GeoRepository(DATABASE_PATH), lat, lon)
    return {
        "location": {"lat": lat, "lon": lon},
        "cell": cell.to_dict(),
    }
