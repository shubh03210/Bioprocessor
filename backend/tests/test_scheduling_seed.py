"""Phase 2: repository / scheduling service / schedule seed tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.db.seed import (
    BATCH_ALPHA,
    BATCH_BRAVO,
    BATCH_CHARLIE,
    DELIBERATE_VIOLATIONS,
    seed_equipment,
    seed_schedule,
)
from app.models import Batch, UnitOperation
from app.models.constants import EQUIPMENT_SEED_NAMES
from app.repositories import scheduling as repo
from app.services.scheduling import NotFoundError, SchedulingService

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


def _alembic_config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


@pytest.fixture()
def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "phase2.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    command.upgrade(_alembic_config(), "head")
    engine = create_engine(db_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_equipment_and_batch_crud(db_session: Session):
    equipment = seed_equipment(db_session)
    assert [e.name for e in equipment] == list(EQUIPMENT_SEED_NAMES)

    svc = SchedulingService(db_session)
    batch = svc.create_batch(
        name="Test Batch",
        start_date=date(2025, 10, 1),
        end_date=date(2025, 10, 20),
    )
    assert batch.id is not None

    op = svc.create_unit_operation(
        name="Test Seed",
        type="Seed",
        color="#111111",
        status="draft",
        start_date=date(2025, 10, 2),
        end_date=date(2025, 10, 5),
        batch_id=batch.id,
        equipment_id=equipment[0].id,
    )
    assert op.id is not None
    assert svc.get_unit_operation(op.id).name == "Test Seed"

    updated = svc.update_unit_operation(op.id, status="confirmed")
    assert updated.status == "confirmed"

    svc.delete_unit_operation(op.id)
    with pytest.raises(NotFoundError):
        svc.get_unit_operation(op.id)


def test_create_unit_operation_unknown_batch_raises(db_session: Session):
    seed_equipment(db_session)
    svc = SchedulingService(db_session)
    eq = repo.list_equipment(db_session)[0]
    with pytest.raises(NotFoundError):
        svc.create_unit_operation(
            name="X",
            type="Seed",
            color="#000",
            status="draft",
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 2),
            batch_id=9999,
            equipment_id=eq.id,
        )


def test_seed_schedule_loads_three_batches_and_violations(db_session: Session):
    summary = seed_schedule(db_session)
    assert summary["created"] is True
    assert summary["batches"] >= 3
    assert summary["unit_operations"] >= 6
    assert summary["dependencies"] >= 1
    assert len(summary["deliberate_violations"]) >= 2

    names = {b.name for b in db_session.exec(select(Batch)).all()}
    assert {BATCH_ALPHA, BATCH_BRAVO, BATCH_CHARLIE}.issubset(names)

    ops = {op.name: op for op in db_session.exec(select(UnitOperation)).all()}
    # DR-003 pair
    bravo_br = ops["Bravo Bioreactor 1.5L"]
    charlie_seed = ops["Charlie Seed 1.5L"]
    assert bravo_br.equipment_id == charlie_seed.equipment_id
    assert bravo_br.start_date < charlie_seed.end_date
    assert charlie_seed.start_date < bravo_br.end_date

    # DR-002 pair in Charlie
    c_seed = ops["Charlie Seed 75L"]
    c_br = ops["Charlie Bioreactor 1500L"]
    assert c_br.start_date < c_seed.end_date

    # Idempotent
    again = seed_schedule(db_session)
    assert again["created"] is False
    assert again["batches"] == summary["batches"]


def test_deliberate_violations_catalog():
    assert any(v["rule_id"] == "DR-002" for v in DELIBERATE_VIOLATIONS)
    assert any(v["rule_id"] == "DR-003" for v in DELIBERATE_VIOLATIONS)


def test_schedule_window_query(db_session: Session):
    seed_schedule(db_session)
    svc = SchedulingService(db_session)
    equipment, batches, ops, deps = svc.list_schedule_window(
        start_date=date(2025, 10, 1),
        end_date=date(2025, 11, 15),
    )
    assert len(equipment) == 5
    assert len(batches) >= 3
    assert len(ops) >= 6
    assert len(deps) >= 1
