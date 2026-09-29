"""Integration: seed schedule yields expected deliberate violations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlmodel import Session

from app.db.seed import seed_schedule
from app.domain.scheduling_rules import RULE_DR002, RULE_DR003, RULE_DR005
from app.services.scheduling import DomainViolationError, SchedulingService

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "phase3.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(cfg, "head")
    engine = create_engine(db_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_seed_schedule_has_deliberate_dr002_and_dr003(db_session: Session):
    seed_schedule(db_session)
    svc = SchedulingService(db_session)
    violations = svc.evaluate_violations()
    by_rule = {}
    for v in violations:
        by_rule.setdefault(v.rule_id, []).append(v)

    assert RULE_DR002 in by_rule
    assert RULE_DR003 in by_rule

    # DR-003 names from seed
    dr003_text = " ".join(v.message for v in by_rule[RULE_DR003])
    assert "Bravo Bioreactor 1.5L" in dr003_text
    assert "Charlie Seed 1.5L" in dr003_text

    # DR-002 includes Charlie Seed 75L vs Bioreactor
    dr002_text = " ".join(v.message for v in by_rule[RULE_DR002])
    assert "Charlie Seed 75L" in dr002_text
    assert "Charlie Bioreactor 1500L" in dr002_text


def test_completed_op_cannot_be_deleted(db_session: Session):
    seed_schedule(db_session)
    svc = SchedulingService(db_session)
    op = next(o for o in svc.list_unit_operations() if o.name == "Alpha Seed 1.5L")
    svc.update_unit_operation(op.id, status="completed")
    with pytest.raises(DomainViolationError) as exc:
        svc.delete_unit_operation(op.id)
    assert exc.value.violations[0].rule_id == RULE_DR005


def test_completed_op_cannot_be_moved(db_session: Session):
    seed_schedule(db_session)
    svc = SchedulingService(db_session)
    op = next(o for o in svc.list_unit_operations() if o.name == "Alpha Seed 1.5L")
    svc.update_unit_operation(op.id, status="completed")
    with pytest.raises(DomainViolationError):
        svc.update_unit_operation(op.id, start_date=date(2025, 10, 22))
