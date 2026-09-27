"""Convert raw weather and geographic values to 0..100 contributions."""

from .thresholds import MAX_SLOPE_DEG, MAX_WATER_DISTANCE_M, RAINFALL_POINTS


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _interpolate(value: float, points: tuple[tuple[float, float], ...]) -> float:
    value = max(points[0][0], min(points[-1][0], value))
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if value <= x2:
            ratio = (value - x1) / (x2 - x1)
            return clamp(y1 + ratio * (y2 - y1))
    return points[-1][1]


def rainfall_score(rainfall_mm: float) -> float:
    return _interpolate(max(0.0, rainfall_mm), RAINFALL_POINTS)


def slope_score(slope_deg: float) -> float:
    # Flat land contributes more to ponding risk, but slope 0 is not flood proof.
    return clamp(100.0 - (max(0.0, slope_deg) / MAX_SLOPE_DEG * 100.0))


def elevation_score(elevation_m: float, min_elevation_m: float, max_elevation_m: float) -> float:
    if max_elevation_m <= min_elevation_m:
        return 50.0
    relative = (elevation_m - min_elevation_m) / (max_elevation_m - min_elevation_m)
    return clamp((1.0 - relative) * 100.0)


def built_up_score(built_up: float) -> float:
    return clamp(max(0.0, built_up) * 100.0)


def water_distance_score(distance_m: float) -> float:
    return clamp((1.0 - max(0.0, distance_m) / MAX_WATER_DISTANCE_M) * 100.0)
