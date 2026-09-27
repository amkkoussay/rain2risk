"""Offline tests for the Phase 2 weather service."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.weather import get_weather, validate_coordinates
from weather.parser import parse_forecast


MOCK_RESPONSE = {
    "list": [
        {"main": {"temp": 28.4}, "weather": [{"main": "Clouds"}], "rain": {"1h": 1.2, "3h": 4.2}},
        {"main": {"temp": 27.8}, "weather": [{"main": "Rain"}], "rain": {"3h": 7.5}},
        {"main": {"temp": 26.9}, "weather": [{"main": "Rain"}]},
    ]
}


class WeatherTests(unittest.TestCase):
    def test_valid_coordinates_are_accepted(self) -> None:
        validate_coordinates(36.8065, 10.1815)

    def test_invalid_coordinates_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_coordinates(91, 0)
        with self.assertRaises(ValueError):
            validate_coordinates(0, 181)

    def test_parser_normalizes_and_sums_rain(self) -> None:
        result = parse_forecast(MOCK_RESPONSE, 36.8065, 10.1815).to_dict()
        self.assertEqual(result["current"]["temperature_c"], 28.4)
        self.assertEqual(result["rainfall"]["next_1h_mm"], 1.2)
        self.assertEqual(result["rainfall"]["next_3h_mm"], 4.2)
        self.assertEqual(result["rainfall"]["next_6h_mm"], 11.7)
        self.assertEqual(result["rainfall"]["next_24h_mm"], 11.7)

    def test_parser_handles_missing_precipitation(self) -> None:
        result = parse_forecast({"list": [{"main": {"temp": 20}}]}, 0, 0).to_dict()
        self.assertEqual(result["rainfall"]["next_1h_mm"], 0.0)
        self.assertEqual(result["rainfall"]["next_3h_mm"], 0.0)

    @patch("api.weather.OPENWEATHER_API_KEY", "")
    def test_missing_api_key(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "OPENWEATHER_API_KEY is not configured"):
            get_weather(0, 0)

    @patch("api.weather.OPENWEATHER_API_KEY", "test-key")
    @patch("api.weather.OpenWeatherClient.get_forecast", side_effect=RuntimeError("network failure"))
    def test_provider_failure_is_raised(self, _mock_get_forecast) -> None:
        with self.assertRaises(RuntimeError):
            get_weather(0, 0)


if __name__ == "__main__":
    unittest.main()
