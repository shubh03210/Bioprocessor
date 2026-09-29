"""Ingest and control-loop API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SignalName = Literal["DO", "pH", "temp", "feed_rate"]

EXPECTED_UNITS = {
    "DO": "%",
    "pH": "-",
    "temp": "degC",
    "feed_rate": "mL/h",
}


class ReadingIn(BaseModel):
    time_h: float = Field(ge=0)
    signal_name: SignalName
    value: float
    unit: str

    @model_validator(mode="after")
    def unit_matches_signal(self) -> ReadingIn:
        expected = EXPECTED_UNITS[self.signal_name]
        if self.unit != expected:
            raise ValueError(
                f"unit for {self.signal_name} must be '{expected}', got '{self.unit}'"
            )
        return self


class IngestRequest(BaseModel):
    readings: list[ReadingIn] = Field(min_length=1)


class IngestResponse(BaseModel):
    accepted: int
    current_process_time_h: float


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time_h: float
    signal_name: str
    value: float
    unit: str
    created_at: datetime


class CommandIn(BaseModel):
    setpoint_name: str
    value: float
    unit: str
    apply_at_time_h: float = Field(ge=0)
    source: Literal["manual", "controller"] | None = "manual"


class CommandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    setpoint_name: str
    value: float
    unit: str
    apply_at_time_h: float
    status: str
    reject_reason: str | None = None
    source: str | None = None
    created_at: datetime


class ControllerStepOut(BaseModel):
    acted: bool
    reason: str
    command: CommandOut | None = None


class ControlStateOut(BaseModel):
    """Implementation extension for live UI / debugging."""

    current_process_time_h: float | None
    readings: list[ReadingOut]
    reading_count: int
    recent_commands: list[CommandOut] = Field(default_factory=list)
