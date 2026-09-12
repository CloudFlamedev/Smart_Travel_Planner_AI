"""Deterministic minimum-budget feasibility checks for travel plans.

These are deliberately conservative "budget traveller" cost floors (shared
stays, street food, general/sleeper class or bus travel) used only to flag
requests that are unrealistic for the requested route, trip length, and
group size. They are not a real price quote, and they intentionally never
call the LLM, so the check is free and instant.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.transport_service import estimated_distance_km

# Conservative per-person, per-day floor covering budget stay, food, and
# local transport within the destination city (INR).
MIN_DAILY_COST_PER_PERSON_INR = 1_200

# Conservative per-km, per-person floor for the cheapest realistic
# long-distance mode (bus/general rail), applied to a round trip (INR/km).
MIN_TRANSPORT_COST_PER_KM_INR = 1.5

# Straight-line (haversine) distance undercounts real road/rail distance.
ROAD_DISTANCE_MULTIPLIER = 1.15

# Small buffer so we only warn when the budget is meaningfully short, not
# for rounding-level gaps.
FEASIBILITY_BUFFER = 0.9


@dataclass(frozen=True)
class BudgetFeasibility:
    minimum_recommended_budget: int
    shortfall: int

    @property
    def is_tight(self) -> bool:
        return self.shortfall > 0


def minimum_recommended_budget(source: str, destination: str, duration: int, travelers: int) -> int:
    """Return a conservative floor for what this trip would realistically cost, in INR."""
    straight_line_km = estimated_distance_km(source, destination)
    round_trip_km = straight_line_km * ROAD_DISTANCE_MULTIPLIER * 2
    transport_cost_per_person = round_trip_km * MIN_TRANSPORT_COST_PER_KM_INR
    stay_and_food_cost_per_person = MIN_DAILY_COST_PER_PERSON_INR * duration
    per_person_total = transport_cost_per_person + stay_and_food_cost_per_person
    return round(per_person_total * travelers)


def check_budget_feasibility(
    source: str,
    destination: str,
    duration: int,
    travelers: int,
    budget: int,
) -> BudgetFeasibility:
    minimum = minimum_recommended_budget(source, destination, duration, travelers)
    shortfall = max(0, round(minimum * FEASIBILITY_BUFFER) - budget)
    return BudgetFeasibility(minimum_recommended_budget=minimum, shortfall=shortfall)


def budget_warning_message(
    source: str,
    destination: str,
    duration: int,
    travelers: int,
    budget: int,
    feasibility: BudgetFeasibility,
) -> str | None:
    if not feasibility.is_tight:
        return None
    traveler_word = "traveler" if travelers == 1 else "travelers"
    day_word = "day" if duration == 1 else "days"
    return (
        f"Your budget of ₹{budget:,} looks tight for {travelers} {traveler_word} traveling "
        f"{duration} {day_word} from {source} to {destination}. A realistic minimum for this trip is "
        f"around ₹{feasibility.minimum_recommended_budget:,} (covers basic transport, stay, and food). "
        "Consider raising your budget, shortening the trip, or reducing the number of travelers — the "
        "plan below is still generated, but expect it to be a stretch at this budget."
    )
