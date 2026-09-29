"""Database engine and session helpers."""

from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.config import settings

connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    # Required for FastAPI + SQLite across threads
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ARG001
    """Enforce foreign keys on SQLite connections."""
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_engine():
    return engine
