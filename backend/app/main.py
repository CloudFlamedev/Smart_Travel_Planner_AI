from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.trip import router as trip_router
from app.core.config import get_settings
from app.services.groq_service import GroqService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Smart Travel Planner API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.state.groq_service = GroqService(settings)
    app.include_router(trip_router)

    @app.get("/health")
    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()

