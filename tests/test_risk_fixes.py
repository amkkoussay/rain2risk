"""Regression tests for the Rain2Risk repair map."""
import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from api.analyze import analyze
from risk.scoring import calculate_risk

class RiskRepairTests(unittest.TestCase):
    def test_risk_explanation_contains_real_values(self):
        result = calculate_risk(
            {"rainfall": {"next_6h_mm": 42, "coverage_hours": {"6h": 6}}},
            {"elevation_m": 10, "slope_deg": 2.4, "built_up": .68, "water_distance_m": 210,
             "min_elevation_m": 5, "max_elevation_m": 20},
        )
        text = " ".join(result.explanation)
        self.assertIn("42.0 mm", text)
        self.assertTrue(any("2.4°" in x for x in result.explanation) or result.factors["slope"].score < 50)

    def test_unavailable_factor_is_not_zero(self):
        result = calculate_risk(
            {"rainfall": {"next_6h_mm": None, "coverage_hours": {"6h": 0}}},
            {"elevation_m": None, "slope_deg": None, "built_up": None, "water_distance_m": None,
             "min_elevation_m": None, "max_elevation_m": None},
        )
        self.assertIsNone(result.factors["rainfall"].to_dict()["value"])
        self.assertEqual(result.factors["rainfall"].to_dict()["status"], "unavailable")
        self.assertEqual(result.factors["rainfall"].to_dict()["contribution"], None)

    @patch("api.analyze.get_weather", return_value={"rainfall": {"next_6h_mm": 42, "coverage_hours": {"6h": 6}, "status": "available"}})
    @patch("api.analyze.get_global_grid")
    def test_selected_cell_is_explicit_and_not_first_cell(self, grid_mock, weather_mock):
        grid_mock.return_value = ([
            {"cell_id":"r0c0","lat":0.0,"lon":0.0,"bounds":[[-.1,-.1],[.1,.1]],"elevation_m":10,"slope_deg":2,"built_up_fraction":.2,"water_fraction":.1,"water_distance_m":1000,"building_count":1,"land_cover_class":"grassland"},
            {"cell_id":"r0c1","lat":1.0,"lon":1.0,"bounds":[[.9,.9],[1.1,1.1]],"elevation_m":5,"slope_deg":1,"built_up_fraction":.8,"water_fraction":.1,"water_distance_m":100,"building_count":2,"land_cover_class":"built_up"},
        ], {"elevation":"DEM","land_cover":"WC","osm":"OSM"}, {"dem":{"status":"available"},"worldcover":{"status":"available"},"osm":{"status":"available"}})
        result = analyze(1.0, 1.0)
        self.assertEqual(result["selected_cell"]["cell_id"], "r0c1")
        self.assertEqual(result["risk"]["cell_id"], "r0c1")
        selected = next(f for f in result["grid"]["features"] if f["properties"]["cell_id"] == "r0c1")
        self.assertEqual(result["risk"]["score"], selected["properties"]["risk_score"])

if __name__ == "__main__":
    unittest.main()
