from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TripRequest(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    duration: int = Field(ge=1, le=30)
    travelers: int = Field(ge=1, le=20)
    budget: int = Field(gt=0, le=10_000_000)
    interests: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("source", "destination")
    @classmethod
    def clean_city(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("interests")
    @classmethod
    def clean_interests(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()][:8]


class StrictSchemaModel(BaseModel):
    """Produces a Groq strict-mode-compatible JSON schema."""

    model_config = ConfigDict(extra="forbid")


class Place(StrictSchemaModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=320)


class TransportOption(StrictSchemaModel):
    mode: str = Field(min_length=1, max_length=40)
    estimated_cost: str = Field(min_length=1, max_length=120)
    duration: str = Field(min_length=1, max_length=80)
    recommendation: str = Field(min_length=1, max_length=160)


class ItineraryDay(StrictSchemaModel):
    day: int = Field(ge=1, le=30)
    activities: list[str] = Field(min_length=1, max_length=5)


class TripPlan(StrictSchemaModel):
    source: str
    destination: str
    duration: int
    travelers: int
    budget: int
    places: list[Place] = Field(min_length=3, max_length=8)
    transport_options: list[TransportOption] = Field(min_length=2, max_length=4)
    itinerary: list[ItineraryDay] = Field(min_length=1, max_length=30)
    travel_tips: list[str] = Field(min_length=4, max_length=6)

    @model_validator(mode="after")
    def validate_itinerary_matches_duration(self) -> "TripPlan":
        if len(self.itinerary) != self.duration:
            raise ValueError("itinerary must contain exactly one item per trip day")
        if [item.day for item in self.itinerary] != list(range(1, self.duration + 1)):
            raise ValueError("itinerary days must be consecutive from 1 through duration")
        return self


TRIP_PLAN_REQUIRED_FIELDS = (
    "source",
    "destination",
    "duration",
    "travelers",
    "budget",
    "places",
    "transport_options",
    "itinerary",
    "travel_tips",
)


def trip_plan_groq_schema() -> dict[str, Any]:
    """Return the flat JSON Schema subset accepted by Groq strict mode.

    Pydantic remains the source of runtime validation. This deliberately avoids
    generated ``$defs``/``$ref`` and constraint keywords while keeping every
    required API field, its type, and every object closed to extra properties.
    """

    place = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "category", "description"],
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string"},
            "description": {"type": "string"},
        },
    }
    transport_option = {
        "type": "object",
        "additionalProperties": False,
        "required": ["mode", "estimated_cost", "duration", "recommendation"],
        "properties": {
            "mode": {"type": "string"},
            "estimated_cost": {"type": "string"},
            "duration": {"type": "string"},
            "recommendation": {"type": "string"},
        },
    }
    itinerary_day = {
        "type": "object",
        "additionalProperties": False,
        "required": ["day", "activities"],
        "properties": {
            "day": {"type": "integer"},
            "activities": {"type": "array", "items": {"type": "string"}},
        },
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(TRIP_PLAN_REQUIRED_FIELDS),
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string"},
            "duration": {"type": "integer"},
            "travelers": {"type": "integer"},
            "budget": {"type": "integer"},
            "places": {"type": "array", "items": place},
            "transport_options": {"type": "array", "items": transport_option},
            "itinerary": {"type": "array", "items": itinerary_day},
            "travel_tips": {"type": "array", "items": {"type": "string"}},
        },
    }
