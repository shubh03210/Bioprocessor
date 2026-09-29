"""CLI / library: apply migrations and seed equipment + demo schedule.

Usage (from backend/):
  python -m app.db.bootstrap
"""

from __future__ import annotations

import csv
import logging
import subprocess
import sys
from pathlib import Path

from sqlmodel import Session

from app.config import settings
from app.db.seed import describe_seed_schedule, seed_equipment, seed_schedule
from app.db.session import engine
from app.models import Reading
from app.models.constants import EQUIPMENT_SEED_NAMES
from app.repositories import readings as readings_repo

logger = logging.getLogger(__name__)


def run_alembic_upgrade() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_root,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed with code {result.returncode}")


def _data_kit_dir() -> Path:
    path = Path(settings.data_kit_path)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[2] / path).resolve()
    return path


def seed_control_readings_from_run(
    session: Session,
    *,
    max_minutes: int | None = None,
) -> int:
    """Load early run_A samples into reading table if empty (hosted Control demo)."""
    if readings_repo.count_readings(session) > 0:
        return 0

    limit = max_minutes if max_minutes is not None else settings.seed_control_minutes
    csv_path = _data_kit_dir() / "run_A.csv"
    if not csv_path.exists():
        logger.warning("Control seed skipped — missing %s", csv_path)
        return 0

    rows: list[Reading] = []
    seen_minutes: set[int] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rec in reader:
            time_h = float(rec["time_h"])
            minute = int(round(time_h * 60))
            if minute >= limit:
                continue
            seen_minutes.add(minute)
            rows.append(
                Reading(
                    time_h=time_h,
                    signal_name=rec["signal_name"],
                    value=float(rec["value"]),
                    unit=rec["unit"],
                )
            )
    if not rows:
        return 0
    readings_repo.insert_readings(session, rows)
    logger.info(
        "Seeded %s control readings (%s process-minutes from run_A)",
        len(rows),
        len(seen_minutes),
    )
    return len(rows)


def bootstrap_database(*, seed_control: bool | None = None) -> dict:
    """Migrate + seed schedule (+ optional control readings). Safe to call repeatedly."""
    run_alembic_upgrade()
    do_control = (
        settings.seed_control_readings if seed_control is None else seed_control
    )
    with Session(engine) as session:
        equipment = seed_equipment(session)
        names = [r.name for r in equipment]
        schedule = seed_schedule(session)
        control_n = 0
        if do_control:
            control_n = seed_control_readings_from_run(session)
        summary = {
            "equipment": names,
            "schedule_created": schedule["created"],
            "batches": schedule["batches"],
            "unit_operations": schedule["unit_operations"],
            "dependencies": schedule["dependencies"],
            "control_readings_seeded": control_n,
        }
    missing = [n for n in EQUIPMENT_SEED_NAMES if n not in names]
    if missing:
        raise RuntimeError(f"Missing equipment seed rows: {missing}")
    return summary


def main() -> None:
    try:
        summary = bootstrap_database()
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc

    names = summary["equipment"]
    print(f"Database ready. Equipment ({len(names)}): {', '.join(names)}")
    created_label = "created" if summary["schedule_created"] else "already present"
    print(
        f"Schedule seed ({created_label}): "
        f"{summary['batches']} batches, "
        f"{summary['unit_operations']} unit operations, "
        f"{summary['dependencies']} dependencies"
    )
    if summary["control_readings_seeded"]:
        print(f"Control readings seeded: {summary['control_readings_seeded']}")
    print(describe_seed_schedule())


if __name__ == "__main__":
    main()
