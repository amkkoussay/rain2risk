"""SQLite repository for geospatial cells."""

import sqlite3
from pathlib import Path

from .models import GeoCell


class GeoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def nearest_cell(self, lat: float, lon: float) -> GeoCell | None:
        """Return the nearest candidate cell; distance is finalized in spatial.py."""
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, lat, lon, elevation_m, slope_deg, built_up, water_distance_m
                FROM cells
                ORDER BY ABS(lat - ?) + ABS(lon - ?)
                LIMIT 1
                """,
                (lat, lon),
            ).fetchone()
        if row is None:
            return None
        return GeoCell(*row)

    def count(self) -> int:
        with sqlite3.connect(self.database_path) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM cells").fetchone()[0])
