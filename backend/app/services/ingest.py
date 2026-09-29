"""Ingest application service."""

from __future__ import annotations

from sqlmodel import Session

from app.models import Reading
from app.repositories import readings as readings_repo
from app.schemas.control import ReadingIn


class IngestService:
    def __init__(self, session: Session):
        self.session = session

    def ingest(self, readings: list[ReadingIn]) -> tuple[int, float]:
        rows = [
            Reading(
                time_h=r.time_h,
                signal_name=r.signal_name,
                value=r.value,
                unit=r.unit,
            )
            for r in readings
        ]
        readings_repo.insert_readings(self.session, rows)
        current = max(r.time_h for r in readings)
        stored_max = readings_repo.max_process_time_h(self.session)
        if stored_max is not None:
            current = max(current, stored_max)
        return len(rows), current

    def current_process_time_h(self) -> float | None:
        return readings_repo.max_process_time_h(self.session)

    def recent_readings(self, *, limit: int = 500, signal_name: str | None = None):
        return readings_repo.list_recent_readings(
            self.session, limit=limit, signal_name=signal_name
        )

    def reading_count(self) -> int:
        return readings_repo.count_readings(self.session)
