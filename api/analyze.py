"""Vercel serverless analyze endpoint for Rain2Risk.

Wraps the existing backend analysis pipeline. Vercel's filesystem is
read-only outside /tmp, so the on-disk GIS cache is redirected there.

NOTE on imports: this file lives at api/analyze.py, which collides with the
backend's own `api` package (backend/api/). To make `from api... import ...`
resolve to the backend copy regardless of how the runtime imports this file,
backend/ is placed first on sys.path and any pre-existing `api` bindings are
dropped from sys.modules before importing.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = str(_ROOT / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Drop any `api` module bindings (e.g. this very file if the runtime imported
# it as api.analyze) so the imports below resolve to backend/api/*.
for _name in ("api.analyze", "api.health", "api"):
    sys.modules.pop(_name, None)

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
