"""Validate the Phase 3 SQLite dataset."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "rain2risk.db"


def validate() -> tuple[int, int]:
    if not DATABASE.exists():
        raise SystemExit("Dataset validation: FAIL\nDatabase not found")
    with sqlite3.connect(DATABASE) as connection:
        table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cells'").fetchone()
        if not table:
            raise SystemExit("Dataset validation: FAIL\nTable cells not found")
        rows = connection.execute("SELECT id, lat, lon, elevation_m, slope_deg, built_up, water_distance_m FROM cells").fetchall()
    invalid = 0
    ids = set()
    for cell_id, lat, lon, elevation, slope, built_up, water_distance in rows:
        valid = (
            cell_id not in ids and -90 <= lat <= 90 and -180 <= lon <= 180
            and -500 <= elevation <= 9000 and slope >= 0 and 0 <= built_up <= 1 and water_distance >= 0
        )
        ids.add(cell_id)
        invalid += not valid
    if not rows:
        invalid = 1
    return len(rows), invalid


if __name__ == "__main__":
    count, invalid = validate()
    status = "PASS" if invalid == 0 else "FAIL"
    print(f"Dataset validation: {status}")
    print(f"Cells: {count}")
    print(f"Invalid records: {invalid}")
    if invalid:
        raise SystemExit(1)
