# Rain2Risk repaired delivery

This package contains the repaired Rain2Risk MVP, updated architecture diagrams, and runtime screenshots.

## Repair included

The risk aggregation bug was fixed. The previous implementation multiplied already weighted factor contributions by 100 a second time, causing many results to clamp at 100. The corrected implementation divides the weighted contribution sum by the sum of available weights once. A regression test verifies that zero rainfall does not produce a very-high score.

## Runtime evidence

The application was run locally through the browser. A second live analysis was performed for Tokyo (`35.67620, 139.65030`) with the configured OpenWeather key. The rendered result showed 41.8 mm of rainfall over six hours, a 76/100 score, VERY HIGH level, and Good data quality.

See:

- `docs/screenshots/live-ui-home.webp`
- `docs/screenshots/live-tokyo-result.webp`
- `docs/architecture-clean.png` and `docs/architecture-clean.mmd`
- `docs/analysis-workflow.png` and `docs/analysis-workflow.mmd`
- `docs/OPERATIONS.md`

## Verification

The final offline verification suite completed successfully:

- Python compilation: PASS
- Offline unit tests: PASS, 20 tests
- JavaScript syntax check: PASS

The private `.env` file is intentionally excluded from the delivery archive. Configure `OPENWEATHER_API_KEY` locally before running provider-backed analysis.
