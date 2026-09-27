"""Deterministic, transparent relative-risk scoring."""
from typing import Any
from .models import FactorResult, RiskResult
from .normalization import built_up_score, elevation_score, rainfall_score, slope_score, water_distance_score
from .thresholds import RISK_LEVELS, WEIGHTS

def _level(score: float) -> str:
    for limit, label in RISK_LEVELS:
        if score < limit:
            return label
    return "VERY_HIGH"

def _rainfall_input(weather: dict[str, Any]) -> tuple[float | None, str, str]:
    rainfall = weather.get("rainfall", weather) or {}
    for key, window in (("next_6h_mm", "6h"), ("rain_6h", "6h"), ("next_3h_mm", "3h"), ("rain_3h", "3h"), ("next_1h_mm", "1h"), ("rain_1h", "1h")):
        if rainfall.get(key) is not None:
            coverage = (rainfall.get("coverage_hours") or {}).get(window, float(window.rstrip("h")))
            if coverage is not None and float(coverage) <= 0:
                return None, window, "unavailable"
            return float(rainfall[key]), window, "available"
    return None, "none", "unavailable"

def _explanations(geo: dict[str, Any], rain_mm: float | None, rainfall_window: str, raw: dict[str, float | None]) -> dict[str, str]:
    result = {}
    if rain_mm is not None:
        result["rainfall"] = f"Rainfall: {rain_mm:.1f} mm expected over the next {rainfall_window}."
    else:
        result["rainfall"] = "Rainfall: unavailable."
    if geo.get("slope_deg") is not None:
        result["slope"] = f"Slope: {float(geo['slope_deg']):.1f}° — relatively flat terrain." if raw["slope"] >= 50 else f"Slope: {float(geo['slope_deg']):.1f}°."
    else:
        result["slope"] = "Slope: unavailable."
    if geo.get("elevation_m") is not None:
        result["elevation"] = f"Elevation: {float(geo['elevation_m']):.1f} m — relatively low within this grid." if raw["elevation"] >= 50 else f"Elevation: {float(geo['elevation_m']):.1f} m."
    else:
        result["elevation"] = "Elevation: unavailable."
    if geo.get("built_up") is not None:
        result["built_up"] = f"Built-up coverage: {float(geo['built_up'])*100:.0f}%."
    else:
        result["built_up"] = "Built-up coverage: unavailable."
    if geo.get("water_distance_m") is not None:
        result["water_distance"] = f"Nearest mapped water context: {float(geo['water_distance_m']):.0f} m."
    else:
        result["water_distance"] = "Water proximity: unavailable."
    return result

def calculate_risk(weather: dict[str, Any], geo_features: dict[str, Any]) -> RiskResult:
    """Calculate a 0–100 relative screening score from available factors only."""
    rain_mm, rainfall_window, rain_status = _rainfall_input(weather)
    min_elevation = geo_features.get("min_elevation_m")
    max_elevation = geo_features.get("max_elevation_m")
    raw = {
        "rainfall": rainfall_score(rain_mm) if rain_mm is not None else None,
        "slope": slope_score(float(geo_features["slope_deg"])) if geo_features.get("slope_deg") is not None else None,
        "elevation": elevation_score(float(geo_features["elevation_m"]), float(min_elevation), float(max_elevation))
            if None not in (geo_features.get("elevation_m"), min_elevation, max_elevation) else None,
        "built_up": built_up_score(float(geo_features["built_up"])) if geo_features.get("built_up") is not None else None,
        "water_distance": water_distance_score(float(geo_features["water_distance_m"]))
            if geo_features.get("water_distance_m") is not None and geo_features.get("water_distance_m") == geo_features.get("water_distance_m") else None,
    }
    explanations = _explanations(geo_features, rain_mm, rainfall_window, raw)
    units = {"rainfall": "mm", "slope": "°", "elevation": "m", "built_up": "fraction", "water_distance": "m"}
    raw_values = {"rainfall": rain_mm, "slope": geo_features.get("slope_deg"), "elevation": geo_features.get("elevation_m"),
                  "built_up": geo_features.get("built_up"), "water_distance": geo_features.get("water_distance_m")}
    factors = {}
    for name, score in raw.items():
        available = score is not None
        status = "available" if available else "unavailable"
        value = float(score) if available else 0.0
        factors[name] = FactorResult(value, WEIGHTS[name], value * WEIGHTS[name],
                                     explanations[name], available, status, raw_values[name], units[name])
    available_names = [name for name, factor in factors.items() if factor.available]
    weight_sum = sum(WEIGHTS[name] for name in available_names)
    total = max(0.0, min(100.0, sum(factors[n].contribution for n in available_names) * 100.0 / weight_sum)) if weight_sum else 0.0
    ordered = sorted(available_names, key=lambda name: factors[name].contribution, reverse=True)
    explanation = [explanations[n] for n in ordered if factors[n].score >= 50][:3]
    if not explanation and ordered:
        explanation = [explanations[ordered[0]]]
    unavailable = [name for name, factor in factors.items() if not factor.available]
    return RiskResult(total, _level(total), factors, ordered[:3], explanation, rainfall_window, unavailable)
