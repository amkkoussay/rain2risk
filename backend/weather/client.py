"""OpenWeather transport client. Parsing stays in parser.py."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class WeatherClientError(RuntimeError):
    """Safe error raised when OpenWeather cannot be reached or rejects a request."""


class OpenWeatherClient:
    """Small client that only builds and sends OpenWeather requests."""

    def __init__(self, api_key: str, timeout: float = 10) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def get_forecast(self, lat: float, lon: float) -> dict:
        """Fetch the OpenWeather 3-hour forecast response."""
        query = urlencode(
            {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            }
        )
        request = Request(
            f"https://api.openweathermap.org/data/2.5/forecast?{query}",
            headers={"Accept": "application/json"},
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8")).get("message", "request rejected")
            except (ValueError, UnicodeDecodeError):
                detail = "request rejected"
            raise WeatherClientError(f"OpenWeather error: {detail}") from error
        except (URLError, TimeoutError, OSError) as error:
            raise WeatherClientError("OpenWeather request failed or timed out") from error
        except (ValueError, UnicodeDecodeError) as error:
            raise WeatherClientError("OpenWeather returned invalid JSON") from error
