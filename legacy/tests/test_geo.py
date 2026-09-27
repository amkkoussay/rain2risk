"""Offline tests for the Phase 3 geospatial layer."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from geo.models import GeoCell
from geo.repository import GeoRepository
from geo.spatial import get_nearest_cell, haversine_distance, is_inside_study_area, validate_coordinates


class GeoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test.db"
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE cells (id INTEGER PRIMARY KEY, lat REAL, lon REAL, elevation_m REAL, slope_deg REAL, built_up REAL, water_distance_m REAL)")
            connection.execute("INSERT INTO cells VALUES (1, 36.8065, 10.1815, 8.4, 1.2, 0.87, 420)")
            connection.execute("INSERT INTO cells VALUES (2, 36.815, 10.19, 12.0, 2.0, 0.50, 700)")
            connection.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_haversine_known_distance(self) -> None:
        distance = haversine_distance(0, 0, 0, 1)
        self.assertAlmostEqual(distance, 111_195, delta=200)

    def test_coordinate_validation(self) -> None:
        validate_coordinates(0, 0)
        with self.assertRaises(ValueError): validate_coordinates(91, 0)
        with self.assertRaises(ValueError): validate_coordinates(0, 181)

    def test_nearest_cell(self) -> None:
        cell = get_nearest_cell(GeoRepository(self.database), 36.8066, 10.1816)
        self.assertIsInstance(cell, GeoCell)
        self.assertEqual(cell.id, 1)

    def test_outside_study_area(self) -> None:
        self.assertFalse(is_inside_study_area(40, 10))
        with self.assertRaisesRegex(LookupError, "location_outside_study_area"):
            get_nearest_cell(GeoRepository(self.database), 40, 10)

    def test_repository_reads_database(self) -> None:
        self.assertEqual(GeoRepository(self.database).count(), 2)


if __name__ == "__main__":
    unittest.main()
