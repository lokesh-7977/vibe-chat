from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.schemas.health import HealthResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
    )
