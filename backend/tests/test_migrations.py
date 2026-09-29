"""Migration and equipment-seed smoke tests (Phase 1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import Session, select

from app.db.seed import seed_equipment
from app.models import Equipment
from app.models.constants import EQUIPMENT_SEED_NAMES

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

EXPECTED_TABLES = {
    "equipment",
    "batch",
    "unit_operation",
    "unit_operation_dependency",
    "reading",
    "prediction",
    "control_command",
    "alembic_version",
}


def _alembic_config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


@pytest.fixture()
def migrated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "phase1.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    engine = create_engine(db_url)
    yield engine, cfg
    engine.dispose()


def test_migration_creates_expected_tables(migrated_db):
    engine, _cfg = migrated_db
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)


def test_seed_equipment_inserts_five_rows(migrated_db):
    engine, _cfg = migrated_db
    with Session(engine) as session:
        rows = seed_equipment(session)
        names = [r.name for r in rows]
    assert names == list(EQUIPMENT_SEED_NAMES)

    with Session(engine) as session:
        again = seed_equipment(session)
        assert [r.name for r in again] == list(EQUIPMENT_SEED_NAMES)
        count = len(session.exec(select(Equipment)).all())
        assert count == 5


def test_migration_upgrade_and_downgrade(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "updown.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_config()

    command.upgrade(cfg, "head")
    engine = create_engine(db_url)
    assert "equipment" in inspect(engine).get_table_names()
    engine.dispose()

    command.downgrade(cfg, "base")
    engine = create_engine(db_url)
    remaining = set(inspect(engine).get_table_names())
    assert not (EXPECTED_TABLES - {"alembic_version"}) & remaining
    engine.dispose()


def test_equipment_name_unique(migrated_db):
    engine, _cfg = migrated_db
    with Session(engine) as session:
        seed_equipment(session)
        session.add(Equipment(name="1.5L"))
        with pytest.raises(Exception):
            session.commit()
        session.rollback()
