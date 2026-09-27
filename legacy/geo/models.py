"""Normalized geospatial cell model."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GeoCell:
    id: int
    lat: float
    lon: float
    elevation_m: float
    slope_deg: float
    built_up: float
    water_distance_m: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lat": self.lat,
            "lon": self.lon,
            "features": {
                "elevation_m": self.elevation_m,
                "slope_deg": self.slope_deg,
                "built_up": self.built_up,
                "water_distance_m": self.water_distance_m,
            },
        }
