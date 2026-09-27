"""Convert OpenWeather forecast periods into coverage-aware data."""
from datetime import datetime, timezone
from typing import Any
from .models import WeatherForecast

def _number(value: Any, default: float | None = 0.0) -> float | None:
    try: return float(value)
    except (TypeError, ValueError): return default

def _timestamp(period: dict[str, Any], fallback: float) -> float:
    if period.get("dt") is not None: return float(_number(period.get("dt"), fallback))
    text = period.get("dt_txt")
    if text:
        try: return datetime.fromisoformat(str(text).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()
        except ValueError: pass
    return fallback

def parse_forecast(payload: dict[str, Any], latitude: float, longitude: float) -> WeatherForecast:
    periods = payload.get("list") or []
    if not periods:
        return WeatherForecast(latitude, longitude, None, "Unknown", None, None, None, None, 0, 0, 0, 0, "unavailable")
    first = periods[0]
    first_ts = _timestamp(first, datetime.now(timezone.utc).timestamp())
    records = []
    for index, period in enumerate(periods):
        start = _timestamp(period, first_ts + index * 10800)
        next_start = _timestamp(periods[index + 1], start + 10800) if index + 1 < len(periods) else start + _number(payload.get("interval"), 10800)
        duration_h = max(0.0, min(3.0, (next_start - start) / 3600.0))
        rain = period.get("rain") or {}
        # In OpenWeather forecast records, an omitted rain field means no precipitation
        # was reported for that period; this is distinct from an unavailable forecast.
        records.append((start, duration_h, _number(rain.get("3h"), 0.0)))
    def window(hours):
        end = first_ts + hours * 3600
        selected = [(duration, rain) for start, duration, rain in records if start < end and start + duration * 3600 > first_ts]
        coverage = min(float(hours), sum(d for d, _ in selected))
        if coverage <= 0: return None, 0.0
        return round(sum(r for _, r in selected), 2), round(coverage, 2)
    rain_3h, cov3 = window(3); rain_6h, cov6 = window(6); rain_24h, cov24 = window(24)
    first_rain = first.get("rain") or {}
    rain_1h = _number(first_rain.get("1h"), 0.0)
    weather_items = first.get("weather") or []; main = first.get("main") or {}
    weather_name = str(weather_items[0].get("main", "Unknown")) if weather_items else "Unknown"
    return WeatherForecast(latitude, longitude, _number(main.get("temp"), None), weather_name,
                           rain_1h, rain_3h, rain_6h, rain_24h, min(1.0, cov3), cov3, cov6, cov24, "available")
