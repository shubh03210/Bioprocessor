"""ControlCommand persistence helpers."""

from __future__ import annotations

from sqlmodel import Session, col, select

from app.models import ControlCommand
from app.models.constants import ControlCommandStatus


def insert_command(
    session: Session,
    row: ControlCommand,
    *,
    commit: bool = True,
) -> ControlCommand:
    session.add(row)
    if commit:
        session.commit()
        session.refresh(row)
    else:
        session.flush()
    return row


def list_pending(
    session: Session,
    *,
    setpoint_name: str | None = None,
) -> list[ControlCommand]:
    stmt = select(ControlCommand).where(
        ControlCommand.status == ControlCommandStatus.PENDING.value
    )
    if setpoint_name is not None:
        stmt = stmt.where(ControlCommand.setpoint_name == setpoint_name)
    stmt = stmt.order_by(col(ControlCommand.apply_at_time_h), col(ControlCommand.id))
    return list(session.exec(stmt).all())


def get_command(session: Session, command_id: int) -> ControlCommand | None:
    return session.get(ControlCommand, command_id)


def mark_applied(
    session: Session,
    command_id: int,
    *,
    commit: bool = True,
) -> ControlCommand | None:
    row = get_command(session, command_id)
    if row is None:
        return None
    if row.status == ControlCommandStatus.PENDING.value:
        row.status = ControlCommandStatus.APPLIED.value
        session.add(row)
        if commit:
            session.commit()
            session.refresh(row)
        else:
            session.flush()
    return row


def has_pending(session: Session, setpoint_name: str) -> bool:
    return len(list_pending(session, setpoint_name=setpoint_name)) > 0


def expire_due_pending(
    session: Session,
    current_process_time_h: float,
    *,
    commit: bool = True,
) -> int:
    """Mark pending commands with apply_at <= now as applied (device would have taken them)."""
    pending = list_pending(session)
    n = 0
    for row in pending:
        if row.apply_at_time_h <= current_process_time_h + 1e-12:
            row.status = ControlCommandStatus.APPLIED.value
            session.add(row)
            n += 1
    if commit and n:
        session.commit()
    elif n:
        session.flush()
    return n


def latest_non_rejected(
    session: Session,
    setpoint_name: str,
) -> ControlCommand | None:
    stmt = (
        select(ControlCommand)
        .where(ControlCommand.setpoint_name == setpoint_name)
        .where(ControlCommand.status != ControlCommandStatus.REJECTED.value)
        .order_by(col(ControlCommand.apply_at_time_h).desc(), col(ControlCommand.id).desc())
    )
    return session.exec(stmt).first()


def list_recent_commands(
    session: Session,
    *,
    limit: int = 50,
) -> list[ControlCommand]:
    stmt = (
        select(ControlCommand)
        .order_by(col(ControlCommand.created_at).desc(), col(ControlCommand.id).desc())
        .limit(limit)
    )
    rows = list(session.exec(stmt).all())
    rows.reverse()
    return rows
