"""Tests for the Phase 1 health endpoint."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.health import health_payload


class HealthPayloadTests(unittest.TestCase):
    def test_health_payload(self) -> None:
        response = json.loads(health_payload().decode("utf-8"))
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["service"], "rain2risk")


if __name__ == "__main__":
    unittest.main()
