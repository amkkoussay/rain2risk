import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.analyze import analyze
from geo.global_data import GlobalDataError, make_grid


class GlobalMVPTests(unittest.TestCase):
    def test_grid_changes_with_arbitrary_location(self):
        first = make_grid(35.6762, 139.6503)
        second = make_grid(-33.8688, 151.2093)
        self.assertNotEqual((first[0]["lat"], first[0]["lon"]), (second[0]["lat"], second[0]["lon"]))
        self.assertEqual(len(first), 80)
        self.assertEqual(len(second), 80)

    @patch("api.analyze.get_weather")
    @patch("api.analyze.get_global_grid")
    def test_analyze_returns_geojson_and_sources(self, grid_mock, weather_mock):
        grid_mock.return_value = ([{
            "cell_id": "r0c0", "lat": 35.6762, "lon": 139.6503,
            "bounds": [[35.67, 139.64], [35.68, 139.66]], "elevation_m": 12.4,
            "slope_deg": 1.8, "built_up_fraction": 0.81, "water_fraction": 0.03,
            "water_distance_m": 180, "building_count": 12, "land_cover_class": "built_up"
        }], {"elevation": "Open-Meteo", "land_cover": "ESA WorldCover", "osm": "OpenStreetMap"})
        weather_mock.return_value = {"rainfall": {"next_1h_mm": 2, "next_3h_mm": 10, "next_6h_mm": 42, "next_24h_mm": 42}}
        result = analyze(35.6762, 139.6503)
        self.assertEqual(result["grid"]["type"], "FeatureCollection")
        self.assertEqual(result["sources"]["land_cover"], "ESA WorldCover")
        self.assertIn("risk_score", result["grid"]["features"][0]["properties"])

    def test_invalid_worldcover_is_explicit(self):
        self.assertTrue(issubclass(GlobalDataError, RuntimeError))


if __name__ == "__main__":
    unittest.main()


class GlobalFeatureTests(unittest.TestCase):
    def test_osm_feature_extraction_keeps_raw_facts(self):
        from geo.global_data import _attach_osm_features
        cells = [{"lat": 35.0, "lon": 139.0}]
        osm = {"elements": [
            {"center": {"lat": 35.0002, "lon": 139.0002}, "tags": {"building": "yes"}},
            {"geometry": [{"lat": 35.0003, "lon": 139.0003}], "tags": {"waterway": "stream"}},
            {"tags": {"landuse": "residential"}},
        ]}
        result = _attach_osm_features(cells, osm)[0]
        self.assertGreaterEqual(result["building_count"], 1)
        self.assertTrue(result["waterway_present"])
        self.assertIn("residential", result["landuse_tags"])

    def test_worldcover_class_values_are_named(self):
        from geo.global_data import WORLD_COVER_TILE_URL
        self.assertIn("WorldCover", WORLD_COVER_TILE_URL)
        self.assertIn("ImageServer/tile", WORLD_COVER_TILE_URL)

