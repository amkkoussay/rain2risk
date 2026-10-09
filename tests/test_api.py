"""Offline tests for the canonical HTTP API contract."""
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import main


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = main.ThreadingHTTPServer(("127.0.0.1", 0), main.Rain2RiskHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(self, payload: object) -> tuple[int, dict]:
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_missing_fields_return_client_error(self) -> None:
        status, body = self.post({"lat": 10})
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_invalid_coordinates_return_client_error(self) -> None:
        status, body = self.post({"lat": 91, "lon": 0})
        self.assertEqual(status, 400)
        self.assertIn("error", body)


    def test_non_finite_coordinates_are_rejected(self) -> None:
        status, body = self.post({"lat": float("nan"), "lon": 20})
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    @patch.object(main, "analyze", return_value={
        "location": {"lat": 10.0, "lon": 20.0},
        "weather": {},
        "grid": {"type": "FeatureCollection", "features": []},
        "risk": {"score": 12},
        "sources": {},
        "data_quality": {},
    })
    def test_success_preserves_response_contract(self, analyze_mock) -> None:
        status, body = self.post({"lat": 10, "lon": 20})
        self.assertEqual(status, 200)
        self.assertEqual(body["location"], {"lat": 10.0, "lon": 20.0})
        self.assertEqual(body["grid"]["type"], "FeatureCollection")
        self.assertIn("risk", body)
        analyze_mock.assert_called_once_with(10.0, 20.0)


    @patch.object(main, "analyze", side_effect=main.WeatherClientError("provider unavailable"))
    def test_provider_failure_is_not_a_traceback(self, _analyze_mock) -> None:
        status, body = self.post({"lat": 10, "lon": 20})
        self.assertEqual(status, 502)
        self.assertEqual(body["available"], False)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
