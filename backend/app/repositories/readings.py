"""Reading persistence helpers."""

from __future__ import annotations

from sqlmodel import Session, col, func, select

from app.models import Reading


def insert_readings(
    session: Session,
    rows: list[Reading],
    *,
    commit: bool = True,
) -> list[Reading]:
    for row in rows:
        session.add(row)
    if commit:
        session.commit()
        for row in rows:
            session.refresh(row)
    else:
        session.flush()
    return rows


def max_process_time_h(session: Session) -> float | None:
    value = session.exec(select(func.max(Reading.time_h))).one()
    return float(value) if value is not None else None


def list_recent_readings(
    session: Session,
    *,
    limit: int = 500,
    signal_name: str | None = None,
) -> list[Reading]:
    stmt = select(Reading).order_by(col(Reading.time_h).desc(), col(Reading.id).desc())
    if signal_name is not None:
        stmt = stmt.where(Reading.signal_name == signal_name)
    stmt = stmt.limit(limit)
    rows = list(session.exec(stmt).all())
    rows.reverse()
    return rows


def list_recent_signal_values(
    session: Session,
    signal_name: str,
    *,
    limit: int = 200,
) -> list[Reading]:
    """Latest rows for one signal (handles duplicate timestamps from re-ingest)."""
    return list_recent_readings(session, limit=limit, signal_name=signal_name)


def count_readings(session: Session) -> int:
    return int(session.exec(select(func.count()).select_from(Reading)).one())
