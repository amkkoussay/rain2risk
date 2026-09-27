# Legacy and historical material

This directory contains prototype, Tunisia-specific, historical-validation, and generated research material retained for reference. It is **not part of the production MVP runtime**.

The active application flow is:

`frontend → POST /api/analyze → OpenWeather, Open-Meteo, ESA WorldCover, Overpass → risk engine → GeoJSON → Leaflet`

The production health endpoint is `/api/health`.

The files under `legacy/api/`, `legacy/geo/`, and `legacy/tests/` belong to the former SQLite/Tunis prototype. The historical scripts and datasets are retained as reproducibility material, but they are not imported by the active application. Do not add new production dependencies or API routes here.

To inspect or run historical material, use its original project-root-relative paths only after reviewing the script and its data requirements. The production test command intentionally excludes this directory.
