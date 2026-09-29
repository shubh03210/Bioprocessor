"""Device simulator: replay + response model + 1 Hz emit + optional API command poll."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from bbp_simulator.client import IngestClient, reading_dicts
from bbp_simulator.csv_loader import MinuteSample
from bbp_simulator.response_model import apply_do_response, step_dDO


@dataclass
class FeedCommand:
    """Local/pending feed setpoint."""

    value: float
    apply_at_time_h: float
    unit: str = "mL/h"
    command_id: int | None = None


@dataclass
class DeviceState:
    process_time_h: float = 0.0
    dDO: float = 0.0
    active_feed_setpoint: float | None = None
    tick_count: int = 0


@dataclass
class DeviceSimulator:
    samples: list[MinuteSample]
    process_minutes_per_wall_second: float = 1.0
    start_time_h: float = 0.0
    dry_run: bool = True
    api_base: str = "http://127.0.0.1:8000"
    commands: list[FeedCommand] = field(default_factory=list)
    poll_commands: bool = False
    on_emit: Callable[[dict], None] | None = None
    sleep_fn: Callable[[float], None] = time.sleep

    def __post_init__(self) -> None:
        self._by_time = {round(s.time_h, 4): s for s in self.samples}
        self._times = sorted(self._by_time)
        self.state = DeviceState(process_time_h=self.start_time_h)
        self._client = IngestClient(self.api_base)
        self._commands = sorted(self.commands, key=lambda c: c.apply_at_time_h)
        self._seen_command_ids: set[int] = {
            c.command_id for c in self._commands if c.command_id is not None
        }

    def _sample_at(self, time_h: float) -> MinuteSample | None:
        key = round(time_h, 4)
        if key in self._by_time:
            return self._by_time[key]
        candidates = [t for t in self._times if t <= time_h + 1e-9]
        if not candidates:
            return None
        return self._by_time[candidates[-1]]

    def _poll_api_commands(self) -> None:
        if self.dry_run or not self.poll_commands:
            return
        try:
            rows = self._client.fetch_pending_commands()
        except Exception as exc:  # noqa: BLE001 — keep sim alive on transient API errors
            if self.on_emit:
                self.on_emit({"_warn": f"command poll failed: {exc}"})
            return
        for row in rows:
            if row.get("setpoint_name") != "feed_rate":
                continue
            cid = int(row["id"])
            if cid in self._seen_command_ids:
                continue
            self._seen_command_ids.add(cid)
            self._commands.append(
                FeedCommand(
                    value=float(row["value"]),
                    apply_at_time_h=float(row["apply_at_time_h"]),
                    unit=str(row.get("unit") or "mL/h"),
                    command_id=cid,
                )
            )
        self._commands.sort(key=lambda c: c.apply_at_time_h)

    def _apply_due_commands(self) -> None:
        due = [
            c
            for c in self._commands
            if c.apply_at_time_h <= self.state.process_time_h + 1e-12
        ]
        if not due:
            return
        latest = due[-1]
        self.state.active_feed_setpoint = latest.value
        applied_ids = [c.command_id for c in due if c.command_id is not None]
        self._commands = [
            c
            for c in self._commands
            if c.apply_at_time_h > self.state.process_time_h + 1e-12
        ]
        if not self.dry_run and self.poll_commands:
            for cid in applied_ids:
                try:
                    self._client.ack_command(cid)
                except Exception:
                    pass

    def tick(self) -> dict | None:
        """Advance one wall-clock second of process time and emit four signals."""
        sample = self._sample_at(self.state.process_time_h)
        if sample is None:
            return None

        self._poll_api_commands()
        self._apply_due_commands()

        feed_run = sample.feed_rate
        feed_rate = (
            self.state.active_feed_setpoint
            if self.state.active_feed_setpoint is not None
            else feed_run
        )

        dt_min = self.process_minutes_per_wall_second
        self.state.dDO = step_dDO(
            self.state.dDO,
            feed_rate=feed_rate,
            feed_run=feed_run,
            dt_proc_minutes=dt_min,
        )
        do_value = apply_do_response(sample.DO, self.state.dDO)

        payload = {
            "time_h": self.state.process_time_h,
            "DO": do_value,
            "pH": sample.pH,
            "temp": sample.temp,
            "feed_rate": feed_rate,
            "DO_run": sample.DO,
            "feed_run": feed_run,
            "dDO": self.state.dDO,
        }

        readings = reading_dicts(
            time_h=payload["time_h"],
            DO=payload["DO"],
            pH=payload["pH"],
            temp=payload["temp"],
            feed_rate=payload["feed_rate"],
        )

        if self.on_emit:
            self.on_emit(payload)

        if not self.dry_run:
            self._client.post_readings(readings)

        self.state.tick_count += 1
        self.state.process_time_h += dt_min / 60.0
        return payload

    def run(self, max_ticks: int | None = None, realtime: bool = True) -> int:
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if self.state.process_time_h > self._times[-1] + 1e-9:
                break
            emitted = self.tick()
            if emitted is None:
                break
            ticks += 1
            if realtime:
                self.sleep_fn(1.0)
        return ticks
