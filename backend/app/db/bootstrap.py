"""CLI: apply migrations and seed equipment + demo schedule.

Usage (from backend/):
  python -m app.db.bootstrap
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlmodel import Session

from app.db.seed import describe_seed_schedule, seed_equipment, seed_schedule
from app.db.session import engine
from app.models.constants import EQUIPMENT_SEED_NAMES


def run_alembic_upgrade() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_root,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    run_alembic_upgrade()
    with Session(engine) as session:
        equipment = seed_equipment(session)
        names = [r.name for r in equipment]
        schedule = seed_schedule(session)
        # Capture summary while session is open (avoid DetachedInstanceError)
        schedule_summary = {
            "created": schedule["created"],
            "batches": schedule["batches"],
            "unit_operations": schedule["unit_operations"],
            "dependencies": schedule["dependencies"],
        }

    print(f"Database ready. Equipment ({len(names)}): {', '.join(names)}")
    missing = [n for n in EQUIPMENT_SEED_NAMES if n not in names]
    if missing:
        raise SystemExit(f"Missing equipment seed rows: {missing}")

    created_label = "created" if schedule_summary["created"] else "already present"
    print(
        f"Schedule seed ({created_label}): "
        f"{schedule_summary['batches']} batches, "
        f"{schedule_summary['unit_operations']} unit operations, "
        f"{schedule_summary['dependencies']} dependencies"
    )
    print(describe_seed_schedule())


if __name__ == "__main__":
    main()
