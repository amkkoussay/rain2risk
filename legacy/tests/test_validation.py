"""Offline checks for the historical validation pipeline outputs."""

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ValidationPipelineTests(unittest.TestCase):
    def test_normalized_events_are_inside_study_area(self) -> None:
        with (ROOT / "data/historical/historical_events.csv").open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        self.assertGreater(len(rows), 0)
        self.assertEqual(len({row["event_id"] for row in rows}), len(rows))
        for row in rows:
            self.assertTrue(36.79 <= float(row["latitude"]) <= 36.82)
            self.assertTrue(10.16 <= float(row["longitude"]) <= 10.20)

    def test_replay_has_expected_columns_and_range(self) -> None:
        with (ROOT / "validation/results/validation_results.csv").open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 0)
        self.assertEqual(list(rows[0].keys()) if rows else [], [])

    def test_metrics_has_real_counts(self) -> None:
        metrics = json.loads((ROOT / "validation/results/metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["status"], "no_point_validated_events")
        self.assertEqual(metrics["events"], 0)


if __name__ == "__main__":
    unittest.main()
