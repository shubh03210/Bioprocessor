"""Control-loop query endpoints (implementation extensions)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_db
from app.schemas.control import (
    CommandOut,
    ControlStateOut,
    ControllerStepOut,
    ReadingOut,
)
from app.services.command import CommandService
from app.services.controller import ControllerService
from app.services.ingest import IngestService

router = APIRouter(prefix="/control", tags=["control"])


@router.get("/state", response_model=ControlStateOut)
def get_control_state(
    limit: int = Query(200, ge=1, le=5000),
    session: Session = Depends(get_db),
) -> ControlStateOut:
    """Recent readings + commands + current process time for live UI / debugging."""
    svc = IngestService(session)
    cmd = CommandService(session)
    rows = svc.recent_readings(limit=limit)
    return ControlStateOut(
        current_process_time_h=svc.current_process_time_h(),
        readings=[ReadingOut.model_validate(r) for r in rows],
        reading_count=svc.reading_count(),
        recent_commands=[CommandOut.model_validate(c) for c in cmd.recent(limit=50)],
    )


@router.get("/commands/pending", response_model=list[CommandOut])
def get_pending_commands(
    session: Session = Depends(get_db),
) -> list[CommandOut]:
    """Pending setpoints for the device simulator (does not auto-expire)."""
    rows = CommandService(session).list_pending(expire_due=False)
    return [CommandOut.model_validate(r) for r in rows]


@router.post("/commands/{command_id}/ack", response_model=CommandOut)
def ack_command(
    command_id: int,
    session: Session = Depends(get_db),
) -> CommandOut:
    """Device acknowledges a pending command was applied locally."""
    row = CommandService(session).ack_applied(command_id)
    if row is None:
        raise HTTPException(status_code=404, detail="command not found")
    return CommandOut.model_validate(row)


@router.post("/step", response_model=ControllerStepOut)
def controller_step(session: Session = Depends(get_db)) -> ControllerStepOut:
    """Run one reactive controller evaluation (bounds, lag, dwell via command path)."""
    decision = ControllerService(session).step()
    command = None
    if decision.result is not None:
        command = CommandOut.model_validate(decision.result.command)
    return ControllerStepOut(acted=decision.acted, reason=decision.reason, command=command)
