"""Command submission service — validate, persist accept or reject."""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session

from app.domain.command_validation import CommandCandidate, validate_command
from app.models import ControlCommand
from app.models.constants import ControlCommandStatus
from app.repositories import commands as commands_repo
from app.repositories import readings as readings_repo


@dataclass
class CommandSubmitResult:
    command: ControlCommand
    accepted: bool


class CommandService:
    def __init__(self, session: Session):
        self.session = session

    def _current_process_time_h(self) -> float | None:
        return readings_repo.max_process_time_h(self.session)

    def submit(
        self,
        *,
        setpoint_name: str,
        value: float,
        unit: str,
        apply_at_time_h: float,
        source: str = "manual",
    ) -> CommandSubmitResult:
        current = self._current_process_time_h()
        if current is not None:
            commands_repo.expire_due_pending(self.session, current)

        candidate = CommandCandidate(
            setpoint_name=setpoint_name,
            value=value,
            unit=unit,
            apply_at_time_h=apply_at_time_h,
        )
        pending = commands_repo.has_pending(self.session, setpoint_name)
        result = validate_command(
            candidate,
            current_process_time_h=current,
            has_pending_same_setpoint=pending,
        )

        if result.ok:
            row = ControlCommand(
                setpoint_name=setpoint_name,
                value=value,
                unit=unit,
                apply_at_time_h=apply_at_time_h,
                status=ControlCommandStatus.PENDING.value,
                reject_reason=None,
                source=source,
            )
            commands_repo.insert_command(self.session, row)
            return CommandSubmitResult(command=row, accepted=True)

        row = ControlCommand(
            setpoint_name=setpoint_name,
            value=value,
            unit=unit,
            apply_at_time_h=apply_at_time_h,
            status=ControlCommandStatus.REJECTED.value,
            reject_reason=result.reject_reason,
            source=source,
        )
        commands_repo.insert_command(self.session, row)
        return CommandSubmitResult(command=row, accepted=False)

    def list_pending(
        self,
        setpoint_name: str | None = None,
        *,
        expire_due: bool = False,
    ) -> list[ControlCommand]:
        """List pending commands. Device poll uses expire_due=False so lag window stays visible."""
        if expire_due:
            current = self._current_process_time_h()
            if current is not None:
                commands_repo.expire_due_pending(self.session, current)
        return commands_repo.list_pending(self.session, setpoint_name=setpoint_name)

    def ack_applied(self, command_id: int) -> ControlCommand | None:
        return commands_repo.mark_applied(self.session, command_id)

    def cancel_pending(self, *, reason: str = "cancelled by operator") -> list[ControlCommand]:
        return commands_repo.cancel_all_pending(self.session, reason=reason)

    def recent(self, *, limit: int = 50) -> list[ControlCommand]:
        return commands_repo.list_recent_commands(self.session, limit=limit)
