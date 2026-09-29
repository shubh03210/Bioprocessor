"""Shared constants aligned with docs/04-DATABASE_DESIGN.md."""

from enum import StrEnum

EQUIPMENT_SEED_NAMES: tuple[str, ...] = (
    "1.5L",
    "15L",
    "20L",
    "75L",
    "1500L",
)


class UnitOperationType(StrEnum):
    SEED = "Seed"
    BIOREACTOR = "Bioreactor"
    TFF = "TFF"
    SPRAY = "Spray"
    SUM = "Sum"


class UnitOperationStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"


class SignalName(StrEnum):
    DO = "DO"
    PH = "pH"
    TEMP = "temp"
    FEED_RATE = "feed_rate"


class ControlCommandStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    APPLIED = "applied"
    REJECTED = "rejected"


UNIT_OPERATION_TYPES: tuple[str, ...] = tuple(t.value for t in UnitOperationType)
UNIT_OPERATION_STATUSES: tuple[str, ...] = tuple(s.value for s in UnitOperationStatus)
SIGNAL_NAMES: tuple[str, ...] = tuple(s.value for s in SignalName)
CONTROL_COMMAND_STATUSES: tuple[str, ...] = tuple(s.value for s in ControlCommandStatus)
