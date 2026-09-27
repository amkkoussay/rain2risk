"""Weather API handler and small in-memory cache."""

import logging
import time
from typing import Any

from config import OPENWEATHER_API_KEY, OPENWEATHER_TIMEOUT, WEATHER_CACHE_TTL
from weather.client import OpenWeatherClient, WeatherClientError
from weather.parser import parse_forecast

LOGGER = logging.getLogger(__name__)
_CACHE: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}


def validate_coordinates(lat: float, lon: float) -> None:
    if not -90 <= lat <= 90:
        raise ValueError("lat must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("lon must be between -180 and 180")


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    validate_coordinates(lat, lon)
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY is not configured")

    key = (round(lat, 4), round(lon, 4))
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < WEATHER_CACHE_TTL:
        return cached[1]

    LOGGER.info("Weather request received")
    LOGGER.info("Fetching forecast")
    payload = OpenWeatherClient(OPENWEATHER_API_KEY, OPENWEATHER_TIMEOUT).get_forecast(lat, lon)
    result = parse_forecast(payload, lat, lon).to_dict()
    _CACHE[key] = (time.time(), result)
    LOGGER.info("Weather response received")
    return result
