"""Configurable heuristic thresholds for the first MVP baseline."""

WEIGHTS = {
    "rainfall": 0.40,
    "slope": 0.20,
    "elevation": 0.15,
    "built_up": 0.15,
    "water_distance": 0.10,
}

RISK_LEVELS = ((25, "LOW"), (50, "MODERATE"), (75, "HIGH"), (101, "VERY_HIGH"))
RAINFALL_POINTS = ((0.0, 0.0), (10.0, 15.0), (25.0, 35.0), (50.0, 65.0), (75.0, 85.0), (100.0, 100.0))
MAX_SLOPE_DEG = 10.0
MAX_WATER_DISTANCE_M = 2000.0
