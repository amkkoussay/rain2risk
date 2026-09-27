# Rain2Risk

## A simple flood-risk map

Rain2Risk is a small web app. It gives a quick flood-risk score for a place on the map.

The user clicks a place. The app gets weather and map data. It then shows a score from **0 to 100** and colors the map cells.

> **Important:** Rain2Risk is only a screening tool. It is not an official flood warning system. Do not use it for safety or emergency decisions.

## See the app

### Desktop

![Rain2Risk desktop screen](docs/screenshots/rain2risk-desktop.png)

### Mobile

![Rain2Risk mobile screen](docs/screenshots/rain2risk-mobile.png)

### Live result

![Rain2Risk live Tokyo result](docs/screenshots/live-tokyo-result.webp)

## Proof: tested with real data

The app was tested with live weather and map services. This is not only a local demo.

- **5 cities passed the live smoke test:** Tunis, Tokyo, New York, Dhaka, and Amsterdam.
- Each city returned **80 map cells**.
- Weather, height, land cover, and OpenStreetMap data were available in the recorded run.
- A separate browser run for Tokyo showed **41.8 mm of rain in 6 hours** and a **76/100** score.

Read the proof files:

- [Delivery notes and Tokyo live result](docs/DELIVERY.md)
- [Runtime proof: server, UI, and offline checks](docs/runtime-proof.json)
- [Live smoke results for 5 cities](docs/global-smoke-results.jsonl)
- [Live smoke test script](scripts/global_smoke_test.py)
- [WorldCover data check](docs/worldcover-sanity-results.jsonl)

### Live smoke test result

| City | Result | Map cells | Main data sources |
|---|---:|---:|---|
| Tunis | PASS | 80 | Weather, height, land cover, OSM |
| Tokyo | PASS | 80 | Weather, height, land cover, OSM |
| New York | PASS | 80 | Weather, height, land cover, OSM |
| Dhaka | PASS | 80 | Weather, height, land cover, OSM |
| Amsterdam | PASS | 80 | Weather, height, land cover, OSM |

## How it works

```text
Choose a place on the map
          ↓
Send the place to the API
          ↓
Get weather and map data
          ↓
Make a simple risk score
          ↓
Show the score and map cells
```

![Rain2Risk architecture](docs/architecture-clean.png)

See the full flow in the [analysis flow diagram](docs/analysis-workflow.png).

## Data used

| Source | What it gives |
|---|---|
| [OpenWeather](https://openweathermap.org/api) | Rain and weather forecast |
| [Open-Meteo](https://open-meteo.com/) | Height above sea level |
| [ESA WorldCover](https://esa-worldcover.org/) | Land cover data |
| [OpenStreetMap / Overpass](https://overpass-api.de/) | Buildings, water, and land use |

If a source is not available, the app says so. It does not make up data.

## Main parts

```text
backend/       Python server and risk code
frontend/      Map page, JavaScript, and CSS
data/          Small sample data files
docs/           Images, diagrams, and project notes
scripts/       Test and helper scripts
tests/         Offline tests
legacy/        Old code kept for reference
```

The live app uses the code in `backend/` and `frontend/`. The `legacy/` folder is not used by the live app.

## Run it on your computer

You need Python 3. You also need Node.js for one JavaScript check.

### 1. Download the project

```bash
git clone https://github.com/amkkoussay/rain2risk.git
cd rain2risk
```

### 2. Create a Python environment

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 3. Add your weather key

Copy `.env.example` to `.env` and add your OpenWeather key:

```dotenv
OPENWEATHER_API_KEY=your-key-here
APP_HOST=127.0.0.1
APP_PORT=8000
OPENWEATHER_TIMEOUT=10
WEATHER_CACHE_TTL=300
```

Never put a real key in GitHub.

### 4. Start the app

```bash
python backend/main.py
```

Open this address in your browser:

```text
http://127.0.0.1:8000/
```

## API

### Check the server

```text
GET /api/health
```

### Analyze a place

```text
POST /api/analyze
```

Example body:

```json
{"lat": 36.8065, "lon": 10.1815}
```

The answer includes the place, weather, map cells, risk score, data sources, and data quality.

## Test the project

Run all normal checks from the project folder:

```bash
python scripts/verify_project.py
```

The current check has:

- Python compile check: **PASS**
- Offline Python tests: **19 tests, PASS**
- JavaScript syntax check: **PASS**

The live test needs an OpenWeather key and network access:

```bash
python scripts/global_smoke_test.py
```

The recorded live results are in [global-smoke-results.jsonl](docs/global-smoke-results.jsonl).

## Validation notes

The old event data does not have exact points for each flood event. Because of this, the project does not claim an accuracy score from the old data.

This is kept clear in the validation files:

- [Validation report](legacy/validation/report/validation_report.md)
- [Validation metrics](legacy/validation/results/metrics.json)
- [Validation source notes](legacy/validation_source_notes.md)

The data is ready for a later test with exact points or station data.

## Project notes and images

The `docs/` folder has the full project record:

- [Delivery notes](docs/DELIVERY.md)
- [Runtime proof](docs/runtime-proof.json)
- [Operations guide](docs/OPERATIONS.md)
- [Architecture diagram](docs/architecture-clean.png)
- [Analysis flow](docs/analysis-workflow.png)
- [Project roadmap](docs/project-roadmap.png)
- [All screen images](docs/screenshots/)
- [Data source notes](docs/global-data-sources.md)
- [Visual review](docs/visual-review.md)

## Limits

- The score is a simple estimate.
- It is not a water-depth model.
- It is not a flood warning.
- Rain data comes from a forecast for the chosen place. It is not measured for every map cell.
- Results can change when a data source is slow, missing, or has low coverage.

## License

This project is released under the [MIT License](LICENSE).

Copyright (c) 2026 Koussay Mehdouani.
