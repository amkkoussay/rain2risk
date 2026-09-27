# Rain2Risk — Global flood-risk screening MVP

Rain2Risk is a lightweight, location-driven web application for **heuristic flood-risk screening**. A user selects a location, the backend builds a local geographic grid, retrieves the configured weather and GIS layers, applies the existing transparent risk methodology, and returns GeoJSON for the Leaflet interface.

> This is a heuristic flood-risk screening MVP. It is **not** an official flood-warning system, does not use machine learning, and should not be treated as a scientifically validated prediction service.

## MVP flow

```text
frontend
   ↓
POST /api/analyze
   ↓
OpenWeather · Open-Meteo · ESA WorldCover · OpenStreetMap/Overpass
   ↓
risk engine
   ↓
GeoJSON
   ↓
Leaflet
```

The production-facing API consists only of `POST /api/analyze` and `GET /api/health`. The active application does not use the historical SQLite grid or Tunisia-specific prototype endpoints.

## Data sources

| Provider | Contribution |
|---|---|
| [OpenWeather](https://openweathermap.org/api) | Rainfall forecast and current weather fields. Rainfall is not independently observed for every grid cell. |
| [Open-Meteo](https://open-meteo.com/) | Elevation data used by the DEM layer. |
| [ESA WorldCover](https://esa-worldcover.org/) | Land-cover composition for grid cells. |
| [OpenStreetMap / Overpass](https://overpass-api.de/) | Buildings, waterways, and land-use context. |

Provider failures are reported as unavailable rather than silently replaced with invented measurements. Results are cached locally in `data/cache/` when the running application has permission to write there.

## Project structure

```text
backend/
├── main.py                 # HTTP server and the two production routes
├── config.py               # environment-based configuration
├── api/
│   ├── analyze.py          # canonical analysis orchestration
│   └── health.py           # health response
├── geo/                    # grid and live GIS provider layers
├── risk/                   # existing risk calculation and normalization
└── weather/                # OpenWeather client, parser, and model
frontend/                   # Leaflet HTML, JavaScript, and CSS
scripts/global_smoke_test.py # optional live end-to-end smoke test
tests/                     # offline unit tests for the active MVP
legacy/                    # isolated SQLite/Tunis prototype and research files
data/cache/                 # local runtime cache (ignored by Git)
docs/                      # diagrams and review notes
```

The `legacy/` directory is retained for historical reference. It is not imported by the active runtime or discovered by the normal test command.

## Installation and running

The application uses Python's standard library plus the small `lerc` runtime dependency required by the WorldCover layer.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

For Termux, install Python with `pkg`, then use the same lightweight Python workflow. No Docker, database server, heavy GIS stack, or native GDAL dependency is required.

Create a local `.env` file when needed:

```dotenv
OPENWEATHER_API_KEY=replace-with-your-key
APP_HOST=127.0.0.1
APP_PORT=8000
OPENWEATHER_TIMEOUT=10
WEATHER_CACHE_TTL=300
```

Never commit real API keys. Start the server from the repository root:

```bash
python backend/main.py
```

Then open `http://127.0.0.1:8000/` in a browser.

## API

### `POST /api/analyze`

Request body:

```json
{"lat": 36.8065, "lon": 10.1815}
```

A successful response contains the requested `location`, normalized `weather`, a GeoJSON `grid`, the selected-cell `risk`, provider `sources`, and `data_quality` metadata. Invalid coordinates or missing request fields return a clear client error; external provider failures are returned as unavailable service responses without exposing stack traces or secrets.

### `GET /api/health`

Returns a small JSON health payload for checking that the server is running.

## Frontend experience and visual identity

The interface uses a focused Rain2Risk visual system: deep marine surfaces, aqua data accents, amber warnings, a compact brand mark, clear hierarchy, responsive cards, explicit loading and error states, and a persistent risk legend. The redesign keeps the existing Leaflet interaction and API contract while making the workflow easier to understand at a glance.

A runtime proof package is documented in [`docs/OPERATIONS.md`](docs/OPERATIONS.md). It includes the exact endpoint checks, orchestration commands, architecture diagrams, and screenshots captured from the locally running server:

- [`docs/screenshots/rain2risk-desktop.png`](docs/screenshots/rain2risk-desktop.png)
- [`docs/screenshots/rain2risk-mobile.png`](docs/screenshots/rain2risk-mobile.png)
- [`docs/architecture-clean.png`](docs/architecture-clean.png)
- [`docs/analysis-workflow.png`](docs/analysis-workflow.png)

## Testing

Normal tests are offline and do not call OpenWeather, Open-Meteo, Overpass, or WorldCover. Run the required checks from the repository root:

```bash
python -m compileall -q backend
python -m unittest discover -s tests -p "test_*.py"
node --check frontend/app.js
```

The optional live smoke test calls the real pipeline for Tunis, Tokyo, New York, Dhaka, and Amsterdam. It requires network access and a configured OpenWeather key. It prints a separate pass/fail result for each location and must not be interpreted as successful when providers are unavailable:

```bash
python scripts/global_smoke_test.py
```

This smoke test does not assert hardcoded risk scores; it checks HTTP success, JSON shape, grid presence, risk values, GeoJSON, and geographic coordinate consistency.

## Limitations

Risk scores are heuristic screening estimates. They are not official warnings, hydraulic simulations, or globally validated forecasts. Provider coverage, cache state, weather forecast availability, and OSM completeness can affect individual results. The application does not model water depth or hydraulic flow, and it does not claim that rainfall is independently measured for every grid cell.

## Historical material

Historical validation notes, the former Tunisia-specific SQLite implementation, old routes, and prototype scripts are under `legacy/` and are intentionally separate from the active MVP. No production secrets are included in this repository.

## References

[1]: https://openweathermap.org/api "OpenWeather API"
[2]: https://open-meteo.com/en/docs/elevation-api "Open-Meteo Elevation API"
[3]: https://esa-worldcover.org/en/data-access "ESA WorldCover data access"
[4]: https://wiki.openstreetmap.org/wiki/Overpass_API "OpenStreetMap Overpass API"
