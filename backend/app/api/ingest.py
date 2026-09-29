"""POST /ingest — device reading ingestion (assignment path, not under /api)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db
from app.schemas.control import IngestRequest, IngestResponse
from app.services.ingest import IngestService

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_readings(
    body: IngestRequest,
    session: Session = Depends(get_db),
) -> IngestResponse:
    svc = IngestService(session)
    accepted, current = svc.ingest(body.readings)
    return IngestResponse(accepted=accepted, current_process_time_h=current)
