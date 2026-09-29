"""Prediction persistence (append-only)."""

from __future__ import annotations

from sqlmodel import Session, col, func, select

from app.models import Prediction


def insert_predictions(
    session: Session,
    rows: list[Prediction],
    *,
    commit: bool = True,
) -> list[Prediction]:
    for row in rows:
        session.add(row)
    if commit:
        session.commit()
        for row in rows:
            session.refresh(row)
    else:
        session.flush()
    return rows


def get_latest_do_forecast(session: Session) -> list[Prediction]:
    made_at = session.exec(
        select(func.max(Prediction.made_at_time_h)).where(Prediction.signal_name == "DO")
    ).one()
    if made_at is None:
        return []
    return list(
        session.exec(
            select(Prediction)
            .where(Prediction.signal_name == "DO")
            .where(Prediction.made_at_time_h == made_at)
            .order_by(col(Prediction.target_time_h))
        ).all()
    )
