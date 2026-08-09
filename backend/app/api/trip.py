from fastapi import APIRouter, Request

from app.schemas.trip import TripPlan, TripRequest
from app.services.groq_service import GroqService

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("/plan", response_model=TripPlan)
async def plan_trip(payload: TripRequest, request: Request) -> TripPlan:
    service: GroqService = request.app.state.groq_service
    return await service.generate_plan(payload)

