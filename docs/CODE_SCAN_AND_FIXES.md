# Rain2Risk — Code Scan and Fix Report

**Scope:** Static review and local regression testing of the current `rain2risk-fixed` source tree. This report records code-level findings and checks run locally; it does not claim a live-provider or production deployment verification.

## Summary

The scan found and fixed four correctness/reliability issues in the current code, then added regression coverage. The existing relative-risk heuristic, weights, thresholds, and data sources were not replaced.

## Findings fixed

### 1. Risk score was scaled twice

**File:** `backend/risk/scoring.py`

Each normalized factor score is already on a `0–100` scale. The weighted contributions are therefore also in score points. The final aggregation multiplied their weighted average by `100` again before clamping. For example, a weighted average of `7.5` became `750`, then was clamped to `100` — making a low-scoring case appear `VERY_HIGH`.

**Fix:** The final score is now the weighted average of available factor contributions divided by the sum of their weights, with no second multiplication by `100`.

**Regression test:** `test_weighted_score_stays_on_0_to_100_scale` verifies a controlled low-score case returns `7.5`, not `100`.

### 2. All factors unavailable could be presented as zero risk

**Files:** `backend/risk/scoring.py`, `backend/risk/models.py`, `frontend/app.js`

When no factor was available, the old calculation returned `0.0`, which looked like a valid low-risk score rather than an unavailable analysis.

**Fix:** A result with no available factors now has `score: null` and `level: "UNAVAILABLE"`. The frontend displays “Unavailable” instead of showing a numeric score. The existing `unavailable_factors` list remains available to explain the missing inputs.

**Regression test:** `test_all_factors_unavailable_does_not_become_zero_risk` verifies that the result is not converted to zero.

### 3. NaN coordinates could bypass range validation

**Files:** `backend/main.py`, `backend/api/weather.py`, `backend/geo/grid.py`

Comparisons such as `-90 <= lat <= 90` do not reject IEEE `NaN` reliably because comparisons with NaN are false. This allowed malformed numeric coordinates to get past ordinary range checks in some paths.

**Fix:** The HTTP endpoint and weather coordinate validation now require finite values. `make_grid` also rejects non-finite coordinates when called directly.

**Regression test:** `test_non_finite_coordinates_are_rejected` verifies the API returns HTTP 400 for a NaN latitude.

### 4. Selected-cell distance used a degree-based approximation

**File:** `backend/api/analyze.py`

The selected cell's displayed distance was computed from Euclidean latitude/longitude differences multiplied by a fixed metres-per-degree value. Longitude degrees vary with latitude, so this can misstate the distance.

**Fix:** Replaced the approximation with a great-circle (haversine) calculation in metres. This affects the reported distance only, not cell selection or the risk score.

### 5. Concurrent GIS cache writes shared one temporary filename

**File:** `backend/geo/global_data.py`

Concurrent requests for the same cache key could write to the same `.tmp` path before replacing the cache file, creating a race between writers.

**Fix:** Each write now uses a uniquely named temporary file in the cache directory, then atomically replaces the target file. A failed write attempts to clean up its temporary file.

## Verification performed

Commands run from the project root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q backend tests
node --check frontend/app.js
```

**Results:**

- Unit/API tests: **22 passed**
- Python compile check: **passed**
- JavaScript syntax check: **passed**

The suite includes regression checks for the corrected score scale, unavailable-factor behavior, selected-cell consistency, and non-finite API coordinates.

## Not claimed as verified

- No live external-provider end-to-end run is asserted by this report.
- The complete GIS behavior at the antimeridian (dateline) still needs a dedicated geometry/provider test; wrapped longitude bounds can require splitting requests and polygons across the dateline.
- GIS cache entries still have no time-based expiry or explicit provider/schema versioning. Unique temporary files address write collisions, not cache freshness.
- The heuristic thresholds and weights have not been scientifically calibrated. The output remains a **relative flood-risk screening score**, not a flood prediction or a calibrated probability.
- `python -m pytest -q` exceeded the available command time limit in this environment; the project's `unittest` suite was run directly and completed successfully.

## Files changed

- `backend/risk/scoring.py`
- `backend/risk/models.py`
- `backend/main.py`
- `backend/api/weather.py`
- `backend/api/analyze.py`
- `backend/geo/grid.py`
- `backend/geo/global_data.py`
- `frontend/app.js`
- `tests/test_risk_fixes.py`
- `tests/test_api.py`
