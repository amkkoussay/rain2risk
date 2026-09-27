"""Canonical analysis orchestration and API response contract."""
from typing import Any
from api.weather import get_weather
from weather.client import WeatherClientError
from geo.global_data import get_global_grid
from risk.scoring import calculate_risk

def _status_for(value):
    return "available" if value is not None else "unavailable"

def _cell_risk(cell, weather, elevations):
    geo = {
        "elevation_m": cell.get("elevation_m"),
        "slope_deg": cell.get("slope_deg"),
        "built_up": cell.get("built_up_fraction"),
        "water_distance_m": cell.get("water_distance_m"),
        "min_elevation_m": min((x for x in elevations if x is not None), default=None),
        "max_elevation_m": max((x for x in elevations if x is not None), default=None),
    }
    return calculate_risk(weather, geo)

def _quality_summary(quality):
    statuses = [item.get("status") for item in quality.values()]
    if all(s == "available" for s in statuses):
        overall = "good"
    elif any(s == "available" for s in statuses):
        overall = "partial"
    else:
        overall = "unavailable"
    return {"status": overall, "providers": quality}

def analyze(lat: float, lon: float) -> dict[str, Any]:
    grid_payload = get_global_grid(lat, lon)
    cells, gis_sources = grid_payload[:2]
    data_quality = grid_payload[2] if len(grid_payload) > 2 else {}

    try:
        weather = get_weather(lat, lon)
        weather_quality = {"status": weather.get("status", weather.get("rainfall", {}).get("status", "available")),
                           "source": "OpenWeather forecast"}
    except WeatherClientError as error:
        # Weather is optional for a partial screening result; the score will exclude rainfall.
        weather = {"location": {"lat": lat, "lon": lon},
                   "current": {"temperature_c": None, "weather": "Unavailable"},
                   "rainfall": {"next_1h_mm": None, "next_3h_mm": None, "next_6h_mm": None, "next_24h_mm": None,
                                "coverage_hours": {"1h": 0, "3h": 0, "6h": 0, "24h": 0}, "status": "unavailable"},
                   "source": "openweather", "status": "unavailable", "error": str(error)}
        weather_quality = {"status": "failed", "source": "OpenWeather forecast", "reason": str(error)}
    data_quality = {**data_quality, "weather": weather_quality}
    elevations = [c.get("elevation_m") for c in cells]

    grid_features = []
    for cell in cells:
        result = _cell_risk(cell, weather, elevations)
        grid_features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[
                [cell["bounds"][0][1], cell["bounds"][0][0]],
                [cell["bounds"][1][1], cell["bounds"][0][0]],
                [cell["bounds"][1][1], cell["bounds"][1][0]],
                [cell["bounds"][0][1], cell["bounds"][1][0]],
                [cell["bounds"][0][1], cell["bounds"][0][0]],
            ]]},
            "properties": {
                "cell_id": cell["cell_id"], "lat": cell["lat"], "lon": cell["lon"],
                "elevation_m": cell.get("elevation_m"), "slope_deg": cell.get("slope_deg"),
                "built_up_fraction": cell.get("built_up_fraction"), "water_fraction": cell.get("water_fraction"),
                "water_distance_m": cell.get("water_distance_m"), "building_count": cell.get("building_count"),
                "land_cover_class": cell.get("land_cover_class"), "raw_class_codes": cell.get("raw_class_codes"),
                "land_cover_fractions": {k: v for k, v in cell.items() if k.endswith("_fraction")},
                "feature_status": {
                    "elevation": cell.get("elevation_status", _status_for(cell.get("elevation_m"))),
                    "slope": cell.get("slope_status", _status_for(cell.get("slope_deg"))),
                    "land_cover": cell.get("worldcover_status", _status_for(cell.get("land_cover_class"))),
                    "osm": cell.get("osm_status", "available"),
                    "water_distance": _status_for(cell.get("water_distance_m")),
                },
                "rainfall_input": {
                    "value": weather.get("rainfall", {}).get("next_6h_mm"),
                    "unit": "mm",
                    "window": "6h",
                    "status": weather.get("rainfall", {}).get("status", "unavailable"),
                    "scope": "regional_reference",
                },
                "risk_score": round(result.score), "risk_level": result.level,
                "risk_reasons": result.explanation,
                "risk_factors": {k: v.to_dict() for k, v in result.factors.items()},
            }
        })

    # The selected cell is explicitly resolved from the requested point; never fall back to grid[0].
    selected = min(cells, key=lambda c: (c["lat"] - lat) ** 2 + (c["lon"] - lon) ** 2)
    selected_result = _cell_risk(selected, weather, elevations)
    risk = selected_result.to_dict()
    risk["cell_id"] = selected["cell_id"]

    selected_cell = {
        "cell_id": selected["cell_id"],
        "center": {"lat": selected["lat"], "lon": selected["lon"]},
        "distance_to_requested_point_m": round(((selected["lat"]-lat)**2 + (selected["lon"]-lon)**2) ** 0.5 * 111320, 1),
        "risk_score": round(selected_result.score),
        "risk_level": selected_result.level,
    }
    quality = _quality_summary(data_quality)
    return {
        "location": {"lat": lat, "lon": lon},
        "weather": weather,
        "risk": risk,
        "selected_cell": selected_cell,
        "grid": {"type": "FeatureCollection", "features": grid_features},
        "data_quality": quality,
        "sources": {"weather": "OpenWeather", **gis_sources},
        "scope": {
            "type": "relative_flood_risk_screening",
            "rainfall_scope": "regional_reference",
            "note": "Rainfall is sampled at the analysis location and used as a regional reference input for every grid cell; spatial differences in risk come from geographic factors."
        },
    }
