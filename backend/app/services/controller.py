"""Reactive feed controller (rule-based; forecast-aware is optional E2)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, col, select

from app.config import settings
from app.domain.command_validation import FEED_SETPOINT, FEED_UNIT
from app.models import Reading
from app.repositories import commands as commands_repo
from app.repositories import readings as readings_repo
from app.services.command import CommandService, CommandSubmitResult

# Design Decision — reactive thresholds (ADR-015)
DO_CRITICAL = 35.0
DO_LOW = 50.0
DO_COMFORTABLE = 75.0
DO_HIGH = 90.0
FEED_STEP_LARGE = 3.0
FEED_STEP_MED = 1.5
FEED_STEP_SMALL = 1.0

MINUTE_H = 1.0 / 60.0


@dataclass
class ControllerDecision:
    acted: bool
    reason: str
    result: CommandSubmitResult | None = None


def _latest_signal(session: Session, signal_name: str) -> Reading | None:
    stmt = (
        select(Reading)
        .where(Reading.signal_name == signal_name)
        .order_by(col(Reading.time_h).desc(), col(Reading.id).desc())
    )
    return session.exec(stmt).first()


def propose_feed_setpoint(*, do: float, feed: float) -> tuple[float | None, str]:
    """Return (new_setpoint or None, reason). Clamps to configured bounds."""
    lo = settings.feed_rate_min
    hi = settings.feed_rate_max

    if do < DO_CRITICAL:
        new = max(lo, feed - FEED_STEP_LARGE)
        if abs(new - feed) < 1e-9:
            return None, f"DO {do:.1f}% critical but feed already at min"
        return new, f"DO {do:.1f}% < {DO_CRITICAL}: decrease feed by {FEED_STEP_LARGE}"

    if do < DO_LOW:
        new = max(lo, feed - FEED_STEP_MED)
        if abs(new - feed) < 1e-9:
            return None, f"DO {do:.1f}% low but feed already at min"
        return new, f"DO {do:.1f}% < {DO_LOW}: decrease feed by {FEED_STEP_MED}"

    if do > DO_HIGH and feed < 10.0:
        new = min(hi, feed + FEED_STEP_MED)
        if abs(new - feed) < 1e-9:
            return None, "feed already high"
        return new, f"DO {do:.1f}% > {DO_HIGH}: increase feed by {FEED_STEP_MED}"

    if do > DO_COMFORTABLE and feed < 20.0:
        new = min(hi, feed + FEED_STEP_SMALL)
        if abs(new - feed) < 1e-9:
            return None, "no change needed"
        return new, f"DO {do:.1f}% > {DO_COMFORTABLE}: increase feed by {FEED_STEP_SMALL}"

    return None, f"DO {do:.1f}% in deadband; hold feed {feed:.2f}"


class ControllerService:
    def __init__(self, session: Session):
        self.session = session
        self.commands = CommandService(session)

    def step(self) -> ControllerDecision:
        """Evaluate reactive policy once; may submit a validated command."""
        current = readings_repo.max_process_time_h(self.session)
        if current is None:
            return ControllerDecision(False, "no readings yet")

        commands_repo.expire_due_pending(self.session, current)

        do_row = _latest_signal(self.session, "DO")
        feed_row = _latest_signal(self.session, "feed_rate")
        if do_row is None or feed_row is None:
            return ControllerDecision(False, "missing latest DO or feed_rate")

        lag_h = settings.actuator_lag_process_minutes * MINUTE_H
        dwell_h = settings.controller_dwell_process_minutes * MINUTE_H
        apply_at = current + lag_h

        last = commands_repo.latest_non_rejected(self.session, FEED_SETPOINT)
        if last is not None and apply_at < last.apply_at_time_h + dwell_h - 1e-12:
            return ControllerDecision(
                False,
                (
                    f"dwell: next apply_at {apply_at:.4f} < "
                    f"last {last.apply_at_time_h:.4f} + dwell {dwell_h:.4f}"
                ),
            )

        if commands_repo.has_pending(self.session, FEED_SETPOINT):
            return ControllerDecision(False, "pending command already exists")

        proposed, reason = propose_feed_setpoint(do=do_row.value, feed=feed_row.value)
        if proposed is None:
            return ControllerDecision(False, reason)

        result = self.commands.submit(
            setpoint_name=FEED_SETPOINT,
            value=proposed,
            unit=FEED_UNIT,
            apply_at_time_h=apply_at,
            source="controller",
        )
        return ControllerDecision(True, reason, result=result)
