"""Vercel serverless entrypoint for Rain2Risk.

Single-function router: Vercel's Python runtime picks up api/index.py as the
entrypoint. vercel.json rewrites /api/health and /api/analyze here; the
rewrite changes the visible path to /api/index, so dispatch is on HTTP
method (GET -> health, POST -> analyze). Static frontend files are served
directly by this handler.

The backend lives in backend/ with its own `api` package (backend/api/),
which collides with this file's location. backend/ is placed first on
sys.path and any pre-existing `api` bindings are dropped so backend imports
resolve correctly. The on-disk GIS cache is redirected to /tmp (Vercel's
filesystem is read-only elsewhere).
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = str(_ROOT / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Drop any `api` bindings (e.g. this file's parent package as seen by the
# runtime) so `from api... import ...` resolves to backend/api/*.
for _name in ("api.index", "api"):
    sys.modules.pop(_name, None)

import geo.global_data as _global_data

_global_data.CACHE = Path("/tmp/rain2risk-cache")

from api.analyze import analyze
from api.health import HEALTH_RESPONSE
from geo.global_data import GlobalDataError
from weather.client import WeatherClientError

FRONTEND_DIR = _ROOT / "frontend"
_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, rel: str) -> None:
        target = (FRONTEND_DIR / rel).resolve()
        # Prevent path traversal outside frontend/
        if FRONTEND_DIR not in target.parents and target != FRONTEND_DIR:
            self._send_json(403, {"error": "forbidden"})
            return
        if not target.is_file():
            self._send_json(404, {"error": "not_found"})
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _MIME.get(target.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def _route(self) -> str:
        return urlparse(self.path).path.rstrip("/") or "/"

    def do_GET(self) -> None:
        # NOTE: Vercel rewrites /api/health -> /api/index, so the function sees
        # the rewritten path. Dispatch on method: only /api/health rewrites GET here.
        path = self._route()
        if path == "/":
            self._send_file("index.html")
        elif path in ("/app.js", "/style.css"):
            self._send_file(path.lstrip("/"))
        elif path.startswith("/api/"):
            self._send_json(200, HEALTH_RESPONSE)
        else:
            self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        # Only /api/analyze rewrites POST here.
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
