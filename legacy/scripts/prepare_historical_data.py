"""Validate and filter historical event records into a normalized CSV."""

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "historical" / "raw_events.csv"
OUTPUT = ROOT / "data" / "historical" / "historical_events.csv"
MIN_LAT, MAX_LAT, MIN_LON, MAX_LON = 36.79, 36.82, 10.16, 10.20
ALLOWED_TYPES = {"rainfall", "flood", "flash_flood", "waterlogging"}


def prepare() -> int:
    kept, seen = [], set()
    with RAW.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            key = row["event_id"]
            try:
                date.fromisoformat(row["date"])
                lat, lon = float(row["latitude"]), float(row["longitude"])
                valid = key not in seen and key and row["event_type"] in ALLOWED_TYPES and -90 <= lat <= 90 and -180 <= lon <= 180 and MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON
            except (ValueError, TypeError):
                valid = False
            if valid:
                seen.add(key)
                kept.append(row)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        fields = ["event_id", "date", "time", "location_name", "latitude", "longitude", "event_type", "severity", "observed_flood", "coordinate_precision", "validation_eligible", "source", "source_note"]
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)
    print(f"Prepared historical events: {len(kept)}")
    return len(kept)


if __name__ == "__main__":
    raise SystemExit(0 if prepare() else 1)
