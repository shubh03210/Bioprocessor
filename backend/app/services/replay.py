"""Hosted run replay — stream run_A/B/C into ingest so Control charts move."""

from __future__ import annotations

import csv
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session

from app.config import settings
from app.domain.device_response import apply_do_response, step_dDO
from app.models import Reading
from app.models.constants import ControlCommandStatus
from app.repositories import commands as commands_repo
from app.repositories import readings as readings_repo

logger = logging.getLogger(__name__)

RUN_FILES = {
    "A": "run_A.csv",
    "B": "run_B.csv",
    "C": "run_C.csv",
}


@dataclass
class MinuteSample:
    time_h: float
    DO: float
    pH: float
    temp: float
    feed_rate: float


@dataclass
class ReplayStatus:
    running: bool = False
    run_id: str | None = None
    process_time_h: float | None = None
    ticks_done: int = 0
    message: str = "idle"
    interval_s: float = 1.0


def _data_kit_dir() -> Path:
    path = Path(settings.data_kit_path)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[2] / path).resolve()
    return path


def load_run_samples(run_id: str) -> list[MinuteSample]:
    key = run_id.upper()
    if key not in RUN_FILES:
        raise ValueError(f"run_id must be A, B, or C (got {run_id})")
    path = _data_kit_dir() / RUN_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Missing run file: {path}")

    by_t: dict[float, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = float(row["time_h"])
            by_t.setdefault(t, {})[row["signal_name"]] = float(row["value"])

    samples: list[MinuteSample] = []
    for t in sorted(by_t):
        vals = by_t[t]
        samples.append(
            MinuteSample(
                time_h=t,
                DO=vals["DO"],
                pH=vals["pH"],
                temp=vals["temp"],
                feed_rate=vals["feed_rate"],
            )
        )
    return samples


class ReplayWorker:
    """Background ticker that ingests one process-minute per interval."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._status = ReplayStatus()
        self._dDO = 0.0
        self._active_feed: float | None = None

    def status(self) -> ReplayStatus:
        with self._lock:
            return ReplayStatus(
                running=self._status.running,
                run_id=self._status.run_id,
                process_time_h=self._status.process_time_h,
                ticks_done=self._status.ticks_done,
                message=self._status.message,
                interval_s=self._status.interval_s,
            )

    def start(self, run_id: str, *, interval_s: float = 1.0) -> ReplayStatus:
        samples = load_run_samples(run_id)
        with self._lock:
            if self._status.running:
                raise RuntimeError("Replay already running — stop it first")
            self._stop.clear()
            self._status = ReplayStatus(
                running=True,
                run_id=run_id.upper(),
                process_time_h=None,
                ticks_done=0,
                message="starting",
                interval_s=max(0.2, float(interval_s)),
            )
            self._dDO = 0.0
            self._active_feed = None
            self._thread = threading.Thread(
                target=self._run_loop,
                args=(samples, self._status.interval_s),
                name="bbp-replay",
                daemon=True,
            )
            self._thread.start()
        return self.status()

    def stop(self) -> ReplayStatus:
        self._stop.set()
        thread = None
        with self._lock:
            thread = self._thread
            self._status.running = False
            self._status.message = "stopped"
        if thread and thread.is_alive():
            thread.join(timeout=5)
        with self._lock:
            self._thread = None
        return self.status()

    def _run_loop(self, samples: list[MinuteSample], interval_s: float) -> None:
        from app.db.session import engine

        try:
            with Session(engine) as session:
                current = readings_repo.max_process_time_h(session)
            start_idx = 0
            if current is not None:
                for i, s in enumerate(samples):
                    if s.time_h > current + 1e-9:
                        start_idx = i
                        break
                else:
                    with self._lock:
                        self._status.running = False
                        self._status.message = (
                            f"Run finished (process time already ≥ {current:.4f} h)"
                        )
                    return

            for sample in samples[start_idx:]:
                if self._stop.is_set():
                    break
                self._tick(sample)
                if self._stop.wait(interval_s):
                    break

            with self._lock:
                self._status.running = False
                if self._stop.is_set():
                    self._status.message = "stopped"
                else:
                    self._status.message = "completed"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Replay failed")
            with self._lock:
                self._status.running = False
                self._status.message = f"error: {exc}"

    def _tick(self, sample: MinuteSample) -> None:
        from app.db.session import engine

        with Session(engine) as session:
            # Apply due pending commands (hosted closed-loop without external simulator)
            pending = commands_repo.list_pending(session, setpoint_name="feed_rate")
            due = [
                c
                for c in pending
                if c.apply_at_time_h <= sample.time_h + 1e-12
            ]
            if due:
                latest = due[-1]
                self._active_feed = latest.value
                for c in due:
                    c.status = ControlCommandStatus.APPLIED.value
                    session.add(c)
                session.commit()

            feed_run = sample.feed_rate
            feed_rate = (
                self._active_feed if self._active_feed is not None else feed_run
            )
            self._dDO = step_dDO(
                self._dDO,
                feed_rate=feed_rate,
                feed_run=feed_run,
                dt_proc_minutes=1.0,
            )
            do_value = apply_do_response(sample.DO, self._dDO)

            rows = [
                Reading(
                    time_h=sample.time_h,
                    signal_name="DO",
                    value=do_value,
                    unit="%",
                ),
                Reading(
                    time_h=sample.time_h,
                    signal_name="pH",
                    value=sample.pH,
                    unit="-",
                ),
                Reading(
                    time_h=sample.time_h,
                    signal_name="temp",
                    value=sample.temp,
                    unit="degC",
                ),
                Reading(
                    time_h=sample.time_h,
                    signal_name="feed_rate",
                    value=feed_rate,
                    unit="mL/h",
                ),
            ]
            readings_repo.insert_readings(session, rows)

        with self._lock:
            self._status.process_time_h = sample.time_h
            self._status.ticks_done += 1
            self._status.message = f"playing run_{self._status.run_id} @ {sample.time_h:.4f} h"


_worker = ReplayWorker()


def get_replay_worker() -> ReplayWorker:
    return _worker
