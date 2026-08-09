import re

from app.schemas.trip import TransportOption
from app.services.transport_service import (
    apply_transport_duration_estimates,
    estimate_transport_duration,
    estimated_distance_km,
)


def duration_hours(value: str) -> float:
    match = re.fullmatch(r"Estimated (\d+)h(?: (\d+)m)?", value)
    assert match, f"Expected an estimated duration, received: {value}"
    return int(match.group(1)) + int(match.group(2) or 0) / 60


def test_bangalore_to_delhi_duration_estimates_are_realistic():
    assert estimated_distance_km("Bangalore", "Delhi") > 1_700

    flight = duration_hours(estimate_transport_duration("Bangalore", "Delhi", "Flight"))
    train = duration_hours(estimate_transport_duration("Bangalore", "Delhi", "Train"))
    bus = duration_hours(estimate_transport_duration("Bangalore", "Delhi", "Bus"))

    assert 4 <= flight <= 6
    assert 30 <= train <= 36
    assert 35 <= bus <= 45
    assert flight > 2
    assert train > 10
    assert bus > 10


def test_mumbai_to_delhi_duration_estimates_are_mode_appropriate():
    flight = duration_hours(estimate_transport_duration("Mumbai", "Delhi", "Flight"))
    train = duration_hours(estimate_transport_duration("Mumbai", "Delhi", "Train"))
    bus = duration_hours(estimate_transport_duration("Mumbai", "Delhi", "Bus"))

    assert 3 <= flight <= 5
    assert train >= 20
    assert bus > train > flight


def test_llm_transport_durations_are_always_replaced():
    options = [
        TransportOption(mode="Flight", estimated_cost="Estimated ₹5,000", duration="1h 30m", recommendation="Fastest"),
        TransportOption(mode="Train", estimated_cost="Estimated ₹2,000", duration="6h", recommendation="Comfortable"),
        TransportOption(mode="Bus", estimated_cost="Estimated ₹1,200", duration="12h", recommendation="Affordable"),
    ]

    normalized = apply_transport_duration_estimates("Bangalore", "Delhi", options)

    assert [option.duration for option in normalized] == ["Estimated 5h", "Estimated 35h", "Estimated 42h"]
    assert [option.estimated_cost for option in normalized] == [option.estimated_cost for option in options]
    assert [option.recommendation for option in normalized] == [option.recommendation for option in options]


def test_unknown_city_uses_a_safe_duration_fallback():
    assert duration_hours(estimate_transport_duration("Unknown Town", "Delhi", "Flight")) == 3
    assert duration_hours(estimate_transport_duration("Unknown Town", "Delhi", "Train")) == 10
