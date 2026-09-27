"""Replay historical events through the production Risk Engine."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from geo.repository import GeoRepository
from geo.spatial import get_nearest_cell
from risk.normalization import rainfall_score
from risk.scoring import calculate_risk

EVENTS = ROOT / "data" / "historical" / "historical_events.csv"
WEATHER = ROOT / "data" / "historical" / "historical_weather.csv"
OUTPUT = ROOT / "validation" / "results" / "validation_results.csv"
DB = ROOT / "data" / "rain2risk.db"


def replay() -> int:
    with EVENTS.open(newline="", encoding="utf-8") as event_file, WEATHER.open(newline="", encoding="utf-8") as weather_file:
        events = {row["event_id"]: row for row in csv.DictReader(event_file)}
        weather = {row["event_id"]: row for row in csv.DictReader(weather_file)}
    repository = GeoRepository(DB)
    with __import__("sqlite3").connect(DB) as connection:
        minimum, maximum = connection.execute("SELECT MIN(elevation_m), MAX(elevation_m) FROM cells").fetchone()
    output_rows = []
    for event_id, event in events.items():
        if event.get("validation_eligible") != "1" or event.get("observed_flood") not in {"0", "1"} or event_id not in weather:
            continue
        rain = weather[event_id]
        cell = get_nearest_cell(repository, float(event["latitude"]), float(event["longitude"]))
        features = {"elevation_m": cell.elevation_m, "slope_deg": cell.slope_deg, "built_up": cell.built_up, "water_distance_m": cell.water_distance_m, "min_elevation_m": minimum, "max_elevation_m": maximum}
        result = calculate_risk({"rainfall": {"next_1h_mm": float(rain["rain_1h"]), "next_3h_mm": float(rain["rain_3h"]), "next_6h_mm": float(rain["rain_6h"]), "next_24h_mm": float(rain["rain_24h"])}}, features)
        output_rows.append({"event_id": event_id, "date": event["date"], "lat": event["latitude"], "lon": event["longitude"], "observed_event": event["event_type"], "observed_flood": event["observed_flood"], "rain_6h": rain["rain_6h"], "risk_score": round(result.score, 2), "risk_level": result.level, "rainfall_only_score": round(rainfall_score(float(rain["rain_6h"])), 2), "cell_id": cell.id})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["event_id", "date", "lat", "lon", "observed_event", "observed_flood", "rain_6h", "risk_score", "risk_level", "rainfall_only_score", "cell_id"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Replayed events: {len(output_rows)}")
    return len(output_rows)


if __name__ == "__main__":
    replay()

