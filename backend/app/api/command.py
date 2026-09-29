"""POST /command — feed setpoint submission (assignment path, not under /api)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.deps import get_db
from app.api.errors import error_body
from app.schemas.control import CommandIn, CommandOut
from app.services.command import CommandService

router = APIRouter(tags=["command"])


@router.post("/command", response_model=CommandOut)
def post_command(
    body: CommandIn,
    response: Response,
    session: Session = Depends(get_db),
) -> CommandOut | JSONResponse:
    """Validate and persist a setpoint command. Rejects are stored with reason."""
    result = CommandService(session).submit(
        setpoint_name=body.setpoint_name,
        value=body.value,
        unit=body.unit,
        apply_at_time_h=body.apply_at_time_h,
        source=body.source or "manual",
    )
    out = CommandOut.model_validate(result.command)
    if result.accepted:
        return out

    return JSONResponse(
        status_code=400,
        content=error_body(
            "invalid_command",
            result.command.reject_reason or "command rejected",
            details=[
                {
                    "command_id": result.command.id,
                    "status": result.command.status,
                    "reject_reason": result.command.reject_reason,
                }
            ],
        ),
    )
