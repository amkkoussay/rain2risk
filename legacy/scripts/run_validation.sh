#!/data/data/com.termux/files/usr/bin/bash
set -e
python scripts/prepare_historical_data.py
python scripts/collect_historical_weather.py
python scripts/replay_historical_events.py
python scripts/compute_validation.py
if command -v Rscript >/dev/null 2>&1; then
  Rscript analysis/R/spatial_validation.R
  Rscript analysis/R/statistics.R
  Rscript analysis/R/plots.R
else
  echo "Rscript not found: Python validation outputs are ready; R analysis is optional and offline."
fi
