"""API routes: health + root info."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import get_db
from app.schemas.common import HealthResponse
from app.services.llm_service import llm_service
from fastapi import Depends

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    provider = llm_service.provider_status()
    database = "connected"
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:  # noqa: BLE001
        database = "error"
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        ai_provider=provider["provider"],
        ai_configured=provider["configured"],
        ai_model=provider["model"],
        database=database,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
