"""Forecast HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_db
from app.services.forecast import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])


class ForecastPointOut(BaseModel):
    target_time_h: float
    value: float


class ForecastOut(BaseModel):
    made_at_time_h: float
    model_version: str
    points: list[ForecastPointOut]


@router.post("", response_model=ForecastOut)
def create_forecast(session: Session = Depends(get_db)) -> ForecastOut:
    """Generate and persist a DO forecast from the last 60 minutes of readings."""
    result = ForecastService(session).generate_and_store()
    if result is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "validation_error",
                    "message": "Need 60 contiguous process-minutes of DO and feed_rate",
                    "details": [],
                }
            },
        )
    return ForecastOut(
        made_at_time_h=result["made_at_time_h"],
        model_version=result["model_version"],
        points=[ForecastPointOut(**p) for p in result["points"]],
    )


@router.get("/latest", response_model=ForecastOut | None)
def get_latest_forecast(session: Session = Depends(get_db)) -> ForecastOut | None:
    rows = ForecastService(session).latest()
    if not rows:
        return None
    return ForecastOut(
        made_at_time_h=rows[0].made_at_time_h,
        model_version=rows[0].model_version or "unknown",
        points=[
            ForecastPointOut(target_time_h=r.target_time_h, value=r.value) for r in rows
        ],
    )
