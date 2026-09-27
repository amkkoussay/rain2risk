"""Health endpoint for the Rain2Risk service."""

import json


HEALTH_RESPONSE = {
    "status": "ok",
    "service": "rain2risk",
}


def health_payload() -> bytes:
    """Return the health response as UTF-8 encoded JSON."""
    return json.dumps(HEALTH_RESPONSE).encode("utf-8")
