"""Control-loop ORM models (Part C persistence)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Index, String, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Reading(SQLModel, table=True):
    __tablename__ = "reading"
    __table_args__ = (
        Index("ix_reading_signal_time", "signal_name", "time_h"),
        Index("ix_reading_time_h", "time_h"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    time_h: float = Field(sa_column=Column(Float, nullable=False))
    signal_name: str = Field(sa_column=Column(String(32), nullable=False))
    value: float = Field(sa_column=Column(Float, nullable=False))
    unit: str = Field(sa_column=Column(String(16), nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Prediction(SQLModel, table=True):
    """Append-only forecast history — never overwrite rows."""

    __tablename__ = "prediction"
    __table_args__ = (
        Index("ix_prediction_made_at", "made_at_time_h"),
        Index("ix_prediction_signal_made_at", "signal_name", "made_at_time_h"),
        Index("ix_prediction_target_time", "target_time_h"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    made_at_time_h: float = Field(sa_column=Column(Float, nullable=False))
    target_time_h: float = Field(sa_column=Column(Float, nullable=False))
    signal_name: str = Field(sa_column=Column(String(32), nullable=False))
    value: float = Field(sa_column=Column(Float, nullable=False))
    unit: str = Field(sa_column=Column(String(16), nullable=False))
    model_version: Optional[str] = Field(
        default=None,
        sa_column=Column(String(64), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ControlCommand(SQLModel, table=True):
    __tablename__ = "control_command"
    __table_args__ = (
        Index("ix_control_command_setpoint_status", "setpoint_name", "status"),
        Index("ix_control_command_apply_at", "apply_at_time_h"),
        Index("ix_control_command_created_at", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    setpoint_name: str = Field(sa_column=Column(String(32), nullable=False))
    value: float = Field(sa_column=Column(Float, nullable=False))
    unit: str = Field(sa_column=Column(String(16), nullable=False))
    apply_at_time_h: float = Field(sa_column=Column(Float, nullable=False))
    status: str = Field(sa_column=Column(String(32), nullable=False))
    reject_reason: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    source: Optional[str] = Field(
        default=None,
        sa_column=Column(String(32), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
