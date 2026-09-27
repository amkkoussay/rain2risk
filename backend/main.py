"""Lightweight HTTP server for the Rain2Risk Phase 3 foundation."""

import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from api.health import health_payload
from api.analyze import analyze
from geo.global_data import GlobalDataError
from config import APP_HOST, APP_PORT
from weather.client import WeatherClientError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def json_bytes(data: dict) -> bytes:
    return json.dumps(data).encode("utf-8")


class Rain2RiskHandler(SimpleHTTPRequestHandler):
    def send_json(self, status: int, data: dict) -> None:
        payload = json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self.send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            lat, lon = float(body["lat"]), float(body["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("latitude or longitude is outside valid range")
            self.send_json(200, analyze(lat, lon))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})
        except GlobalDataError as error:
            LOGGER.error("Global GIS request failed: %s", error)
            self.send_json(503, {"error": str(error), "available": False})
        except WeatherClientError as error:
            LOGGER.error("Global weather request failed: %s", error)
            self.send_json(502, {"error": str(error), "available": False})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(200, json.loads(health_payload()))
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def log_message(self, format_string: str, *args: object) -> None:
        super().log_message(format_string, *args)


def create_server() -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: Rain2RiskHandler(*args, directory=str(FRONTEND_ROOT), **kwargs)
    return ThreadingHTTPServer((APP_HOST, APP_PORT), handler)


def main() -> None:
    server = create_server()
    print(f"Rain2Risk is running at http://{APP_HOST}:{APP_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nRain2Risk server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
