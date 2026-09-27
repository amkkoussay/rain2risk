"""Small environment-based configuration for Rain2Risk."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    """Load simple KEY=VALUE lines from .env without adding a dependency."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_TIMEOUT = float(os.getenv("OPENWEATHER_TIMEOUT", "10"))
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "300"))
