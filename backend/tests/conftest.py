"""Shared pytest fixtures for backend API tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app.api.deps import get_db
from app.db.seed import seed_schedule
from app.main import app

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fresh migrated SQLite DB + TestClient (no schedule seed)."""
    db_path = tmp_path / "api.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)

    def _override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def seeded_api_client(api_client):
    """API client with demo schedule seed (deliberate DR-002/DR-003)."""
    client, engine = api_client
    with Session(engine) as session:
        seed_schedule(session)
    return client, engine
