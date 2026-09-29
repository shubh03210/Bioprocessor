from fastapi import APIRouter

from app import __version__
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness/readiness stub for Phase 0. No business logic."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }
