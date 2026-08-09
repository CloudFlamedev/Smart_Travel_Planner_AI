import json
import logging
import re

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.trip import TripPlan, TripRequest, trip_plan_groq_schema
from app.services.transport_service import apply_transport_duration_estimates


SYSTEM_PROMPT = """You are a practical travel planning assistant. Create realistic and useful recommendations from the supplied trip details. Do not claim real-time ticket prices, live availability, or booking availability. Transportation prices must be approximate estimates.

Return exactly one JSON object with no markdown, commentary, or extra keys. The object must include every one of these required top-level fields: source, destination, duration, travelers, budget, places, transport_options, itinerary, travel_tips.

Field contract:
- source and destination: strings that exactly echo the supplied cities.
- duration, travelers, and budget: integers that exactly echo the supplied values.
- places: an array of 3 to 8 objects. Every object has non-empty string name, category, and description fields.
- transport_options: an array of 2 to 4 objects. Every object has non-empty string mode, estimated_cost, duration, and recommendation fields. estimated_cost must say Estimated or Approximate. Prefer Flight, Train, or Bus modes when practical. The backend independently calculates duration, so do not present its duration as live data.
- itinerary: an array with exactly one object for each trip day, numbered consecutively from 1 through duration. Every object has integer day and a non-empty array of string activities.
- travel_tips: an array of 4 to 6 useful non-empty strings.

Never omit a required field. If a detail is uncertain, use a practical approximate recommendation rather than null, an empty object, or a missing field. All values must use the specified JSON types."""

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _safe_response_detail(self, response: httpx.Response) -> str:
        """Keep the useful upstream error while never writing the API key to logs."""
        detail = response.text.replace("\n", " ")[:1_000]
        detail = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[REDACTED]", detail)
        if self.settings.groq_api_key:
            detail = detail.replace(self.settings.groq_api_key, "[REDACTED]")
        return detail

    async def generate_plan(self, request: TripRequest) -> TripPlan:
        if not self.settings.groq_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trip planning is not configured. Add GROQ_API_KEY to the backend environment.",
            )

        schema = trip_plan_groq_schema()
        payload = {
            "model": self.settings.groq_model,
            "temperature": 0.1,
            "reasoning_effort": "low",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "source": request.source,
                            "destination": request.destination,
                            "duration": request.duration,
                            "travelers": request.travelers,
                            "budget": request.budget,
                            "interests": request.interests,
                            "instructions": "Return every required field: source, destination, duration, travelers, budget, places, transport_options, itinerary, travel_tips. Do not omit any field, including travel_tips, places, transport_options, or itinerary, even when information is uncertain. Use approximate practical recommendations instead. Keep all values in their required JSON types. Include exactly one itinerary object for every requested trip day, numbered consecutively from 1 through duration. Costs are per person unless clearly stated otherwise.",
                        }
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "trip_plan", "strict": True, "schema": schema},
            },
        }
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(35.0)) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
            generated = TripPlan.model_validate_json(content)
            transport_options = apply_transport_duration_estimates(
                request.source,
                request.destination,
                generated.transport_options,
            )
            # Preserve request facts and validate again so the final API response
            # still has one itinerary day for each requested trip day and uses
            # backend-calculated transport durations.
            return TripPlan.model_validate(
                generated.model_dump()
                | {
                    "source": request.source,
                    "destination": request.destination,
                    "duration": request.duration,
                    "travelers": request.travelers,
                    "budget": request.budget,
                    "transport_options": transport_options,
                }
            )
        except httpx.TimeoutException as exc:
            logger.warning("Groq request timed out (model=%s)", self.settings.groq_model)
            raise HTTPException(status_code=504, detail="The travel planner timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Groq API rejected the request (status=%s, model=%s): %s",
                exc.response.status_code,
                self.settings.groq_model,
                self._safe_response_detail(exc.response),
            )
            raise HTTPException(status_code=502, detail="The travel planning service is unavailable. Please try again.") from exc
        except httpx.RequestError as exc:
            logger.error(
                "Groq network request failed (type=%s, model=%s): %s",
                type(exc).__name__,
                self.settings.groq_model,
                str(exc),
            )
            raise HTTPException(status_code=502, detail="The travel planning service is unavailable. Please try again.") from exc
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            logger.error("Groq returned an invalid structured response (model=%s, type=%s)", self.settings.groq_model, type(exc).__name__)
            raise HTTPException(status_code=502, detail="The travel planner returned an invalid response. Please try again.") from exc
