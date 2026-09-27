"""Fetch historical hourly precipitation for the event dates.

Source: Open-Meteo Historical Weather API using ERA5 reanalysis. The data is
stored locally so replay does not call a live weather API.
"""

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "historical" / "raw_events.csv"
OUTPUT = ROOT / "data" / "historical" / "historical_weather.csv"
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"


def rolling_max(values: list[float], width: int) -> float:
    return max((sum(values[i:i + width]) for i in range(max(1, len(values) - width + 1))), default=0.0)


def fetch_day(lat: float, lon: float, day: str) -> tuple[float, float, float, float]:
    query = urlencode({"latitude": lat, "longitude": lon, "start_date": day, "end_date": day, "hourly": "precipitation", "timezone": "Africa/Tunis"})
    with urlopen(f"{BASE_URL}?{query}", timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    values = [float(value or 0) for value in payload.get("hourly", {}).get("precipitation", [])]
    return rolling_max(values, 1), rolling_max(values, 3), rolling_max(values, 6), sum(values)


def main() -> None:
    rows = []
    with EVENTS.open(newline="", encoding="utf-8") as source:
        for event in csv.DictReader(source):
            if not event["date"]:
                continue
            rain = fetch_day(float(event["latitude"]), float(event["longitude"]), event["date"])
            rows.append({"event_id": event["event_id"], "date": event["date"], "latitude": event["latitude"], "longitude": event["longitude"], "rain_1h": round(rain[0], 2), "rain_3h": round(rain[1], 2), "rain_6h": round(rain[2], 2), "rain_24h": round(rain[3], 2), "source": "https://open-meteo.com/en/docs/historical-weather-api", "model": "ERA5", "time_note": "event-day hourly reanalysis; exact event hour was not available"})
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Historical weather rows: {len(rows)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Weather download failed: {error}", file=sys.stderr)
        raise
