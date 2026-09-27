"""Offline tests for the Phase 5 risk grid API service."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.risk_grid import get_risk_grid


MOCK_WEATHER = {"rainfall": {"next_1h_mm": 2.0, "next_3h_mm": 10.0, "next_6h_mm": 54.7, "next_24h_mm": 54.7}}


class RiskGridTests(unittest.TestCase):
    def setUp(self) -> None:
        import api.risk_grid as module
        module._GRID_CACHE = None

    @patch("api.risk_grid.get_weather", return_value=MOCK_WEATHER)
    def test_grid_response_schema_and_range(self, _weather) -> None:
        result = get_risk_grid()
        self.assertIn("cells", result)
        self.assertGreater(len(result["cells"]), 0)
        for cell in result["cells"]:
            self.assertEqual(set(cell), {"id", "lat", "lon", "bounds", "risk_score", "risk_level"})
            self.assertEqual(len(cell["bounds"]), 2)
            self.assertGreaterEqual(cell["risk_score"], 0)
            self.assertLessEqual(cell["risk_score"], 100)
            self.assertIn(cell["risk_level"], {"LOW", "MODERATE", "HIGH", "VERY_HIGH"})

    @patch("api.risk_grid.get_weather", return_value=MOCK_WEATHER)
    def test_grid_cache_avoids_second_weather_request(self, weather_mock) -> None:
        first = get_risk_grid()
        second = get_risk_grid()
        self.assertEqual(first, second)
        weather_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
