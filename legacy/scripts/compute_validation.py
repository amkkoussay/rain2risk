"""Compute validation metrics and plots without pandas or heavy GIS packages."""

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "validation" / "results" / "validation_results.csv"
METRICS = ROOT / "validation" / "results" / "metrics.json"
PLOTS = ROOT / "validation" / "plots"
REPORT = ROOT / "validation" / "report" / "validation_report.md"


def rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0] * len(values)
    for rank_number, index in enumerate(order, 1): ranks[index] = rank_number
    return ranks


def corr(x, y):
    if len(x) < 2: return None
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    numerator = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return round(numerator / denominator, 4) if denominator else None


def classification(rows, threshold=50):
    predicted = [float(r["risk_score"]) >= threshold for r in rows]
    observed = [r["observed_flood"] == "1" for r in rows]
    tp = sum(p and o for p, o in zip(predicted, observed)); fp = sum(p and not o for p, o in zip(predicted, observed))
    tn = sum(not p and not o for p, o in zip(predicted, observed)); fn = sum(not p and o for p, o in zip(predicted, observed))
    precision = tp / (tp + fp) if tp + fp else 0.0; recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def main():
    with RESULTS.open(newline="", encoding="utf-8") as source: rows = list(csv.DictReader(source))
    if not rows:
        metrics = {"status": "no_point_validated_events", "events": 0, "reason": "All source events have regional descriptions rather than defensible point coordinates; no binary performance metrics were computed."}
        METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        REPORT.write_text("# Rain2Risk Phase 6.5 Data Integrity Report\n\nNo point-level validation was computed. The source events name regions such as Tunis, Ariana, Manouba, or North Tunis, but do not provide exact event coordinates. The old hand-made coordinates were removed from point validation. Unknown flood status is kept as `NA`, not as no flood.\n\nThe historical event and rainfall files remain available for later polygon-level or station-level validation. The production Risk Engine was not changed.\n", encoding="utf-8")
        print(json.dumps(metrics, indent=2))
        return
    scores = [float(r["risk_score"]) for r in rows]; observed = [int(r["observed_flood"]) for r in rows]
    levels = Counter(r["risk_level"] for r in rows)
    event_rate = {level: round(sum(int(r["observed_flood"]) for r in rows if r["risk_level"] == level) / count, 4) for level, count in levels.items()}
    metrics = {"events": len(rows), "flood_events": sum(observed), "non_flood_events": len(rows) - sum(observed), "date_start": min(r["date"] for r in rows), "date_end": max(r["date"] for r in rows), "spearman_risk_vs_observed": corr(scores, observed), "event_count_by_risk_level": dict(levels), "observed_event_rate_by_risk_level": event_rate, "risk_engine_threshold_50": classification(rows), "rainfall_only_threshold_50": classification([{**r, "risk_score": r["rainfall_only_score"]} for r in rows]), "mean_risk_flood": round(sum(float(r["risk_score"]) for r in rows if r["observed_flood"] == "1") / max(1, sum(observed)), 2), "mean_risk_non_flood": round(sum(float(r["risk_score"]) for r in rows if r["observed_flood"] == "0") / max(1, len(rows) - sum(observed)), 2)}
    METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    PLOTS.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4)); plt.scatter([int(r["observed_flood"]) for r in rows], scores, c=["#c94343" if int(r["observed_flood"]) else "#64748b" for r in rows]); plt.xticks([0, 1], ["No flood", "Flood observed"]); plt.ylabel("Risk score"); plt.title("Risk score vs observed flood"); plt.tight_layout(); plt.savefig(PLOTS / "risk_vs_events.png", dpi=140); plt.close()
    plt.figure(figsize=(6, 4)); plt.bar(list(levels), [levels[k] for k in levels], color=["#2eae62", "#e2bf3f", "#e07a20", "#c94343"][:len(levels)]); plt.ylabel("Events"); plt.title("Risk level distribution"); plt.tight_layout(); plt.savefig(PLOTS / "risk_distribution.png", dpi=140); plt.close()
    plt.figure(figsize=(6, 4)); plt.scatter([float(r["lon"]) for r in rows], [float(r["lat"]) for r in rows], c=scores, cmap="RdYlGn_r", vmin=0, vmax=100); plt.colorbar(label="Risk score"); plt.xlabel("Longitude"); plt.ylabel("Latitude"); plt.title("Historical events and risk scores"); plt.tight_layout(); plt.savefig(PLOTS / "spatial_validation_map.png", dpi=140); plt.close()
    report = f"""# Rain2Risk Phase 6 Validation Report\n\n## Dataset\n\nThis replay used {metrics['events']} historical records from {metrics['date_start']} to {metrics['date_end']}. {metrics['flood_events']} records have an explicitly reported flood or waterlogging observation, and {metrics['non_flood_events']} record is rainfall-only. All records are inside the Phase 3-5 Tunis study area.\n\nEvent source: [Frontiers in Earth Science historic flood table](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2023.1332589/full). Historical rainfall source: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), using ERA5 reanalysis and event-day hourly precipitation.\n\n## Method\n\nEach event was matched to the nearest SQLite GIS cell. The stored historical rainfall was passed to the existing `backend/risk/` module. No second risk formula was created. The engine used its existing 6-hour rainfall window and geographic features. The rainfall-only baseline used the existing rainfall normalization without the geographic factors.\n\n## Results\n\n| Metric | Risk Engine | Rainfall-only baseline |\n|---|---:|---:|\n| Precision at score 50 | {metrics['risk_engine_threshold_50']['precision']} | {metrics['rainfall_only_threshold_50']['precision']} |\n| Recall at score 50 | {metrics['risk_engine_threshold_50']['recall']} | {metrics['rainfall_only_threshold_50']['recall']} |\n| F1 at score 50 | {metrics['risk_engine_threshold_50']['f1']} | {metrics['rainfall_only_threshold_50']['f1']} |\n\nSpearman correlation between score and observed flood flag: **{metrics['spearman_risk_vs_observed']}**. Mean score for flood records: **{metrics['mean_risk_flood']}**. Mean score for non-flood records: **{metrics['mean_risk_non_flood']}**.\n\n## Spatial Results\n\nThe spatial plot shows the event coordinates colored by the replayed score. This is a small point sample, not a statistically strong spatial test. The grid cell ID is retained in `validation_results.csv` for later GIS work.\n\n![Risk versus events](../plots/risk_vs_events.png)\n\n![Spatial validation](../plots/spatial_validation_map.png)\n\n## Limitations\n\nThe sample is small and comes from a published historic-event summary. Exact event hours were not available for most records, so event-day hourly reanalysis windows were used. Reanalysis is not a local rain gauge. Some events describe rainfall or road disruption without confirmed flood ground truth. The Phase 3 starter GIS values are not official elevation, land-cover, or waterway measurements. The risk model uses heuristic weights, has no historical calibration, and does not model hydraulic flow or water depth.\n\n## Reproducibility\n\n```bash\npython scripts/prepare_historical_data.py\npython scripts/collect_historical_weather.py\npython scripts/replay_historical_events.py\npython scripts/compute_validation.py\nRscript analysis/R/spatial_validation.R\n```\n\nThe R step is an offline analysis companion and is not needed by the production app.\n"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__": main()
