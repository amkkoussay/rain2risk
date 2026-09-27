"""Lightweight geographic validation and distance helpers."""

from math import asin, cos, radians, sin, sqrt

from .models import GeoCell
from .repository import GeoRepository

STUDY_AREA = {
    "name": "Tunis urban MVP area",
    "min_lat": 36.79,
    "max_lat": 36.82,
    "min_lon": 10.16,
    "max_lon": 10.20,
}


def validate_coordinates(lat: float, lon: float) -> None:
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")


def is_inside_study_area(lat: float, lon: float) -> bool:
    return (
        STUDY_AREA["min_lat"] <= lat <= STUDY_AREA["max_lat"]
        and STUDY_AREA["min_lon"] <= lon <= STUDY_AREA["max_lon"]
    )


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two geographic points."""
    earth_radius_m = 6_371_000
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    value = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_m * asin(sqrt(value))


def get_nearest_cell(repository: GeoRepository, lat: float, lon: float) -> GeoCell:
    validate_coordinates(lat, lon)
    if not is_inside_study_area(lat, lon):
        raise LookupError("location_outside_study_area")
    cell = repository.nearest_cell(lat, lon)
    if cell is None:
        raise LookupError("geospatial dataset is empty")
    return cell
