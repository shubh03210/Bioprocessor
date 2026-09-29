"""Command validation rules (assignment Part C — four reject reasons)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings

FEED_SETPOINT = "feed_rate"
FEED_UNIT = "mL/h"


@dataclass(frozen=True)
class CommandCandidate:
    setpoint_name: str
    value: float
    unit: str
    apply_at_time_h: float


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reject_reason: str | None = None


def validate_command(
    candidate: CommandCandidate,
    *,
    current_process_time_h: float | None,
    has_pending_same_setpoint: bool,
    feed_min: float | None = None,
    feed_max: float | None = None,
) -> ValidationResult:
    """Return ok/reject for a command. Does not persist."""
    lo = settings.feed_rate_min if feed_min is None else feed_min
    hi = settings.feed_rate_max if feed_max is None else feed_max

    if candidate.setpoint_name != FEED_SETPOINT:
        return ValidationResult(
            False,
            f"unsupported setpoint_name '{candidate.setpoint_name}' (only '{FEED_SETPOINT}')",
        )

    if candidate.unit != FEED_UNIT:
        return ValidationResult(
            False,
            f"unit does not match: expected '{FEED_UNIT}', got '{candidate.unit}'",
        )

    if not (lo <= candidate.value <= hi):
        return ValidationResult(
            False,
            f"value {candidate.value} outside [{lo}, {hi}] {FEED_UNIT}",
        )

    if current_process_time_h is not None and candidate.apply_at_time_h < current_process_time_h:
        return ValidationResult(
            False,
            (
                f"apply_at_time_h {candidate.apply_at_time_h} earlier than "
                f"current process time {current_process_time_h}"
            ),
        )

    if has_pending_same_setpoint:
        return ValidationResult(
            False,
            f"another command for setpoint '{candidate.setpoint_name}' is still pending",
        )

    return ValidationResult(True, None)
