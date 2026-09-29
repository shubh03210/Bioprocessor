"""Control-loop query endpoints (implementation extensions)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.deps import get_db
from app.api.errors import json_error
from app.schemas.control import (
    CommandOut,
    ControlStateOut,
    ControllerStepOut,
    ReadingOut,
    ReplayStartIn,
    ReplayStatusOut,
)
from app.services.command import CommandService
from app.services.controller import ControllerService
from app.services.ingest import IngestService
from app.services.replay import get_replay_worker

router = APIRouter(prefix="/control", tags=["control"])


def _replay_out(st) -> ReplayStatusOut:
    return ReplayStatusOut(
        running=st.running,
        run_id=st.run_id,
        process_time_h=st.process_time_h,
        ticks_done=st.ticks_done,
        message=st.message,
        interval_s=st.interval_s,
    )


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


@router.post("/commands/cancel-pending", response_model=list[CommandOut])
def cancel_pending_commands(
    session: Session = Depends(get_db),
) -> list[CommandOut]:
    """Reject all pending feed commands so a new setpoint can be sent."""
    rows = CommandService(session).cancel_pending()
    return [CommandOut.model_validate(r) for r in rows]


@router.post("/commands/{command_id}/ack", response_model=CommandOut)
def ack_command(
    command_id: int,
    session: Session = Depends(get_db),
) -> CommandOut | JSONResponse:
    """Device acknowledges a pending command was applied locally."""
    row = CommandService(session).ack_applied(command_id)
    if row is None:
        return json_error(404, "not_found", "command not found")
    return CommandOut.model_validate(row)


@router.post("/step", response_model=ControllerStepOut)
def controller_step(session: Session = Depends(get_db)) -> ControllerStepOut:
    """Run one reactive controller evaluation (bounds, lag, dwell via command path)."""
    decision = ControllerService(session).step()
    command = None
    if decision.result is not None:
        command = CommandOut.model_validate(decision.result.command)
    return ControllerStepOut(acted=decision.acted, reason=decision.reason, command=command)


@router.get("/replay", response_model=ReplayStatusOut)
def get_replay_status() -> ReplayStatusOut:
    """Hosted run-replay status (Play A/B/C)."""
    return _replay_out(get_replay_worker().status())


@router.post("/replay/start", response_model=ReplayStatusOut)
def start_replay(body: ReplayStartIn) -> ReplayStatusOut | JSONResponse:
    """Stream run_A/B/C minute-by-minute into ingest (charts move without external sim)."""
    worker = get_replay_worker()
    try:
        st = worker.start(body.run_id, interval_s=body.interval_s)
    except RuntimeError as exc:
        return json_error(409, "conflict", str(exc))
    except (ValueError, FileNotFoundError) as exc:
        return json_error(400, "invalid_request", str(exc))
    return _replay_out(st)


@router.post("/replay/stop", response_model=ReplayStatusOut)
def stop_replay() -> ReplayStatusOut:
    return _replay_out(get_replay_worker().stop())
