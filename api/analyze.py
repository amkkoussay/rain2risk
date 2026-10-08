"""Vercel serverless analyze endpoint for Rain2Risk.

Wraps the existing backend analysis pipeline. Vercel's filesystem is
read-only outside /tmp, so the on-disk GIS cache is redirected there.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

import geo.global_data as _global_data

_global_data.CACHE = Path("/tmp/rain2risk-cache")

from api.analyze import analyze
from geo.global_data import GlobalDataError
from weather.client import WeatherClientError


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw.decode("utf-8"))
            lat, lon = float(body["lat"]), float(body["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("latitude or longitude is outside valid range")
            self._send_json(200, analyze(lat, lon))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(400, {"error": str(error)})
        except (GlobalDataError, WeatherClientError) as error:
            self._send_json(503, {"error": str(error), "available": False})
        except Exception:
            self._send_json(500, {"error": "analysis failed"})

    def do_GET(self) -> None:
        self._send_json(405, {"error": "method_not_allowed"})
