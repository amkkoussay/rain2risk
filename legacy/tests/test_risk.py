"""Offline tests for the Phase 4 rule-based risk engine."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.risk import get_risk
from risk.scoring import calculate_risk


def weather(rain_6h: float) -> dict:
    return {"rainfall": {"next_1h_mm": 2.0, "next_3h_mm": 10.0, "next_6h_mm": rain_6h, "next_24h_mm": rain_6h}}


def geo(slope=2.0, elevation=8.0, built_up=0.7, water=400.0) -> dict:
    return {"slope_deg": slope, "elevation_m": elevation, "built_up": built_up, "water_distance_m": water, "min_elevation_m": 5.0, "max_elevation_m": 20.0}


class RiskTests(unittest.TestCase):
    def test_score_boundaries_and_classes(self) -> None:
        self.assertEqual(calculate_risk(weather(0), {**geo(), "slope_deg": 10, "elevation_m": 20, "built_up": 0, "water_distance_m": 2000}).level, "LOW")
        self.assertTrue(0 <= calculate_risk(weather(1000), geo()).score <= 100)

    def test_rainfall_increases_score(self) -> None:
        self.assertGreaterEqual(calculate_risk(weather(70), geo()).score, calculate_risk(weather(10), geo()).score)

    def test_slope_elevation_built_up_and_water_are_monotonic(self) -> None:
        self.assertGreaterEqual(calculate_risk(weather(30), geo(slope=1)).score, calculate_risk(weather(30), geo(slope=8)).score)
        self.assertGreaterEqual(calculate_risk(weather(30), geo(elevation=6)).score, calculate_risk(weather(30), geo(elevation=18)).score)
        self.assertGreaterEqual(calculate_risk(weather(30), geo(built_up=0.9)).score, calculate_risk(weather(30), geo(built_up=0.1)).score)
        self.assertGreaterEqual(calculate_risk(weather(30), geo(water=100)).score, calculate_risk(weather(30), geo(water=1800)).score)

    def test_rainfall_window_fallback(self) -> None:
        result = calculate_risk({"rainfall": {"next_3h_mm": 12}}, geo())
        self.assertEqual(result.rainfall_window, "3h")

    @patch("api.risk.get_weather", return_value=weather(54.7))
    @patch("api.risk.get_location", return_value={"location": {"lat": 36.8065, "lon": 10.1815}, "cell": {"features": geo()}})
    def test_api_integration_with_mocks(self, _location, _weather) -> None:
        result = get_risk(36.8065, 10.1815)
        self.assertIn("risk", result)
        self.assertIn("top_contributors", result["risk"])
        self.assertEqual(result["risk"]["rainfall_window"], "6h")
        self.assertIn("not an official flood warning", result["disclaimer"])


if __name__ == "__main__":
    unittest.main()
