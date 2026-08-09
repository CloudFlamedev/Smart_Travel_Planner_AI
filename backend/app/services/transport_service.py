"""Deterministic transport-duration estimates for travel plans.

Coordinates intentionally live in this small local mapping rather than an
external geocoding dependency. A maps/geocoding provider can replace
``coordinates_for_city`` later without changing the planning service.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
import re

from app.schemas.trip import TransportOption

Coordinate = tuple[float, float]

# Latitude/longitude for commonly requested Indian destinations. The normalized
# city name is the key so aliases can be kept separate and easy to extend.
CITY_COORDINATES: dict[str, Coordinate] = {
    "ahmedabad": (23.0225, 72.5714),
    "amritsar": (31.6340, 74.8723),
    "bangalore": (12.9716, 77.5946),
    "bhopal": (23.2599, 77.4126),
    "bhubaneswar": (20.2961, 85.8245),
    "chandigarh": (30.7333, 76.7794),
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "delhi": (28.6139, 77.2090),
    "goa": (15.4909, 73.8278),
    "guwahati": (26.1445, 91.7362),
    "hyderabad": (17.3850, 78.4867),
    "indore": (22.7196, 75.8577),
    "jaipur": (26.9124, 75.7873),
    "kochi": (9.9312, 76.2673),
    "kolkata": (22.5726, 88.3639),
    "lucknow": (26.8467, 80.9462),
    "madurai": (9.9252, 78.1198),
    "mumbai": (19.0760, 72.8777),
    "mysore": (12.2958, 76.6394),
    "nagpur": (21.1458, 79.0882),
    "patna": (25.5941, 85.1376),
    "pune": (18.5204, 73.8567),
    "srinagar": (34.0837, 74.7973),
    "thiruvananthapuram": (8.5241, 76.9366),
    "udaipur": (24.5854, 73.7125),
    "varanasi": (25.3176, 82.9739),
    "visakhapatnam": (17.6868, 83.2185),
}

CITY_ALIASES = {
    "bengaluru": "bangalore",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "cochin": "kochi",
    "new delhi": "delhi",
    "panaji": "goa",
    "trivandrum": "thiruvananthapuram",
    "mysuru": "mysore",
    "vizag": "visakhapatnam",
}

EARTH_RADIUS_KM = 6_371.0
FALLBACK_STRAIGHT_LINE_DISTANCE_KM = 500.0


@dataclass(frozen=True)
class ModeEstimate:
    speed_kmph: float
    route_multiplier: float = 1.0
    fixed_overhead_hours: float = 0.0


MODE_ESTIMATES = {
    "flight": ModeEstimate(speed_kmph=700, fixed_overhead_hours=2.5),
    "train": ModeEstimate(speed_kmph=55, route_multiplier=1.10),
    "bus": ModeEstimate(speed_kmph=50, route_multiplier=1.20),
}


def _normalise_city_name(city: str) -> str:
    primary_name = city.split(",", maxsplit=1)[0].strip().lower()
    return re.sub(r"[^a-z0-9 ]+", "", primary_name).replace(" city", "").strip()


def coordinates_for_city(city: str) -> Coordinate | None:
    """Return known city coordinates, or None when a geocoder is needed."""
    normalized = _normalise_city_name(city)
    return CITY_COORDINATES.get(CITY_ALIASES.get(normalized, normalized))


def haversine_distance_km(source: Coordinate, destination: Coordinate) -> float:
    """Calculate straight-line distance between two latitude/longitude points."""
    source_lat, source_lon = map(radians, source)
    destination_lat, destination_lon = map(radians, destination)
    latitude_delta = destination_lat - source_lat
    longitude_delta = destination_lon - source_lon
    arc = sin(latitude_delta / 2) ** 2 + cos(source_lat) * cos(destination_lat) * sin(longitude_delta / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(arc))


def estimated_distance_km(source: str, destination: str) -> float:
    """Use known city coordinates, with a safe deterministic fallback otherwise."""
    source_coordinates = coordinates_for_city(source)
    destination_coordinates = coordinates_for_city(destination)
    if source_coordinates and destination_coordinates:
        return haversine_distance_km(source_coordinates, destination_coordinates)
    return FALLBACK_STRAIGHT_LINE_DISTANCE_KM


def _mode_key(mode: str) -> str | None:
    normalized = mode.lower()
    if "flight" in normalized or "air" in normalized:
        return "flight"
    if "train" in normalized or "rail" in normalized:
        return "train"
    if "bus" in normalized or "coach" in normalized:
        return "bus"
    return None


def _format_duration(hours: float) -> str:
    rounded_minutes = max(30, round(hours * 2) * 30)
    whole_hours, minutes = divmod(rounded_minutes, 60)
    if minutes:
        return f"Estimated {whole_hours}h {minutes}m"
    return f"Estimated {whole_hours}h"


def estimate_transport_duration(source: str, destination: str, mode: str) -> str:
    """Return a backend-owned estimated duration; never use an LLM duration."""
    mode_key = _mode_key(mode)
    if mode_key is None:
        return "Estimated duration unavailable for this transport mode"

    estimate = MODE_ESTIMATES[mode_key]
    travel_hours = estimated_distance_km(source, destination) * estimate.route_multiplier / estimate.speed_kmph
    return _format_duration(travel_hours + estimate.fixed_overhead_hours)


def apply_transport_duration_estimates(
    source: str,
    destination: str,
    options: list[TransportOption],
) -> list[TransportOption]:
    """Replace every model-generated transport duration with a backend estimate."""
    return [
        option.model_copy(update={"duration": estimate_transport_duration(source, destination, option.mode)})
        for option in options
    ]
