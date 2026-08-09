import json

import httpx
import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.main import create_app
from app.schemas.trip import (
    ItineraryDay,
    Place,
    TRIP_PLAN_REQUIRED_FIELDS,
    TripRequest,
    TransportOption,
    TripPlan,
    trip_plan_groq_schema,
)
from app.services.groq_service import GroqService


class FakeGroqService:
    async def generate_plan(self, request):
        return TripPlan(
            source=request.source,
            destination=request.destination,
            duration=request.duration,
            travelers=request.travelers,
            budget=request.budget,
            places=[
                Place(name="Old Fort", category="History", description="A well-preserved historic site."),
                Place(name="Central Market", category="Food", description="Popular local food stalls."),
                Place(name="City Museum", category="Culture", description="An introduction to local culture."),
            ],
            transport_options=[
                TransportOption(mode="Flight", estimated_cost="Estimated ₹5,000", duration="2h", recommendation="Fastest option"),
                TransportOption(mode="Train", estimated_cost="Estimated ₹1,500", duration="15h", recommendation="Budget-friendly option"),
            ],
            itinerary=[
                ItineraryDay(day=day, activities=[f"Day {day} highlights", "Local food"])
                for day in range(1, request.duration + 1)
            ],
            travel_tips=["Book ahead.", "Use public transport.", "Carry water.", "Check local opening hours."],
        )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def api_client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


@pytest.mark.anyio
async def test_health():
    async with api_client(create_app()) as client:
        response = await client.get("/health")
    assert response.json() == {"status": "healthy"}


@pytest.mark.anyio
async def test_trip_request_validation():
    async with api_client(create_app()) as client:
        response = await client.post("/api/trips/plan", json={"source": "", "destination": "Delhi", "duration": 0, "travelers": 0, "budget": 0})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_plan_trip_with_mocked_service():
    app = create_app()
    app.state.groq_service = FakeGroqService()
    payload = {"source": "Bangalore", "destination": "Delhi", "duration": 3, "travelers": 2, "budget": 20000, "interests": ["food"]}
    async with api_client(app) as client:
        response = await client.post("/api/trips/plan", json=payload)

    assert response.status_code == 200
    plan = response.json()
    assert plan["source"] == payload["source"]
    assert plan["destination"] == payload["destination"]
    assert plan["duration"] == payload["duration"]
    assert plan["travelers"] == payload["travelers"]
    assert plan["budget"] == payload["budget"]
    assert plan["places"]
    assert plan["transport_options"]
    assert plan["travel_tips"]
    assert len(plan["itinerary"]) == payload["duration"]
    assert [item["day"] for item in plan["itinerary"]] == [1, 2, 3]


def test_groq_schema_is_flat_closed_and_complete():
    schema = trip_plan_groq_schema()

    assert schema["required"] == list(TRIP_PLAN_REQUIRED_FIELDS)
    assert schema["additionalProperties"] is False
    assert "$defs" not in schema
    assert "$ref" not in json.dumps(schema)
    for field in ("places", "transport_options", "itinerary"):
        assert schema["properties"][field]["items"]["additionalProperties"] is False


@pytest.mark.anyio
async def test_groq_service_preserves_request_facts_and_complete_plan(monkeypatch):
    generated_plan = {
        "source": "Incorrect source",
        "destination": "Incorrect destination",
        "duration": 2,
        "travelers": 99,
        "budget": 1,
        "places": [
            {"name": "Old Fort", "category": "History", "description": "A historic landmark."},
            {"name": "Museum", "category": "Culture", "description": "A local cultural museum."},
            {"name": "Market", "category": "Food", "description": "A popular food market."},
        ],
        "transport_options": [
            {"mode": "Flight", "estimated_cost": "Estimated ₹5,000", "duration": "1h 30m", "recommendation": "A fast option."},
            {"mode": "Train", "estimated_cost": "Estimated ₹2,000", "duration": "6 hours", "recommendation": "A practical option."},
            {"mode": "Bus", "estimated_cost": "Estimated ₹1,500", "duration": "12 hours", "recommendation": "A budget option."},
        ],
        "itinerary": [
            {"day": 1, "activities": ["Old Fort", "Market"]},
            {"day": 2, "activities": ["Museum", "Local food"]},
        ],
        "travel_tips": ["Book transport ahead.", "Carry water.", "Use local transport.", "Check opening hours."],
    }

    class SuccessfulClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, *args, **kwargs):
            request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
            return httpx.Response(200, request=request, json={"choices": [{"message": {"content": json.dumps(generated_plan)}}]})

    monkeypatch.setattr("app.services.groq_service.httpx.AsyncClient", lambda **kwargs: SuccessfulClient())
    request = TripRequest(source="Bangalore", destination="Delhi", duration=2, travelers=2, budget=20_000)
    plan = await GroqService(Settings(groq_api_key="test-secret", groq_model="openai/gpt-oss-20b")).generate_plan(request)

    assert plan.source == request.source
    assert plan.destination == request.destination
    assert plan.duration == request.duration
    assert plan.travelers == request.travelers
    assert plan.budget == request.budget
    assert plan.places
    assert plan.transport_options
    assert plan.travel_tips
    assert len(plan.itinerary) == request.duration
    assert [option.duration for option in plan.transport_options] == ["Estimated 5h", "Estimated 35h", "Estimated 42h"]


@pytest.mark.anyio
async def test_groq_http_error_is_logged_without_api_key(monkeypatch, caplog):
    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, *args, **kwargs):
            request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
            return httpx.Response(400, request=request, json={"error": {"message": "unsupported response format"}})

    monkeypatch.setattr("app.services.groq_service.httpx.AsyncClient", lambda **kwargs: FailingClient())
    service = GroqService(Settings(groq_api_key="test-secret", groq_model="openai/gpt-oss-20b"))

    with pytest.raises(HTTPException) as error:
        await service.generate_plan(
            TripRequest(source="Bangalore", destination="Delhi", duration=1, travelers=1, budget=20_000)
        )

    assert error.value.status_code == 502
    assert "status=400" in caplog.text
    assert "unsupported response format" in caplog.text
    assert "test-secret" not in caplog.text
