"""Unit tests for simulator response model and device ticks."""

from __future__ import annotations

from pathlib import Path

import pytest

from bbp_simulator.csv_loader import MinuteSample, load_run_csv
from bbp_simulator.device import DeviceSimulator, FeedCommand
from bbp_simulator.response_model import (
    DO_MAX,
    DO_MIN,
    apply_do_response,
    clamp_do,
    step_dDO,
    target_dDO,
)

DATA_KIT = Path(__file__).resolve().parents[2] / "data_kit"


def test_clamp_do():
    assert clamp_do(-5) == DO_MIN
    assert clamp_do(150) == DO_MAX
    assert clamp_do(42.5) == 42.5


def test_target_dDO_when_feed_above_run():
    # feed 10 above run 0 → target dDO = -20
    assert target_dDO(10.0, 0.0) == pytest.approx(-20.0)


def test_step_dDO_moves_toward_target():
    d0 = 0.0
    d1 = step_dDO(d0, feed_rate=10.0, feed_run=0.0, dt_proc_minutes=5.0)
    # one full tau → moves fully to target in first-order discrete form:
    # dDO + (5/5)*(target-dDO) = target
    assert d1 == pytest.approx(-20.0)


def test_apply_do_response_clamps():
    assert apply_do_response(98.0, 10.0) == DO_MAX
    assert apply_do_response(5.0, -10.0) == DO_MIN


def test_load_run_a_has_four_signals():
    samples = load_run_csv(DATA_KIT / "run_A.csv")
    assert len(samples) > 100
    assert samples[0].time_h == pytest.approx(0.0)
    assert samples[0].DO > 0


def test_device_emits_four_signals_and_honors_command():
    samples = [
        MinuteSample(time_h=0.0, DO=90.0, pH=6.5, temp=30.0, feed_rate=0.0),
        MinuteSample(time_h=0.0167, DO=89.0, pH=6.5, temp=30.0, feed_rate=0.0),
        MinuteSample(time_h=0.0333, DO=88.0, pH=6.5, temp=30.0, feed_rate=0.0),
    ]
    emitted: list[dict] = []
    sim = DeviceSimulator(
        samples=samples,
        process_minutes_per_wall_second=1.0,
        dry_run=True,
        commands=[FeedCommand(value=8.0, apply_at_time_h=0.0)],
        on_emit=emitted.append,
        sleep_fn=lambda _s: None,
    )
    ticks = sim.run(max_ticks=2, realtime=False)
    assert ticks == 2
    assert emitted[0]["feed_rate"] == 8.0
    assert emitted[0]["DO"] <= emitted[0]["DO_run"]
    assert emitted[1]["dDO"] < emitted[0]["dDO"] or emitted[1]["dDO"] < 0


def test_device_polls_and_applies_api_command(monkeypatch: pytest.MonkeyPatch):
    samples = [
        MinuteSample(time_h=0.0, DO=90.0, pH=6.5, temp=30.0, feed_rate=0.0),
        MinuteSample(time_h=0.0167, DO=89.0, pH=6.5, temp=30.0, feed_rate=0.0),
        MinuteSample(time_h=0.0333, DO=88.0, pH=6.5, temp=30.0, feed_rate=0.0),
    ]
    acked: list[int] = []

    class FakeClient:
        def fetch_pending_commands(self):
            return [
                {
                    "id": 42,
                    "setpoint_name": "feed_rate",
                    "value": 12.0,
                    "unit": "mL/h",
                    "apply_at_time_h": 0.0,
                    "status": "pending",
                }
            ]

        def ack_command(self, command_id: int):
            acked.append(command_id)
            return {"id": command_id, "status": "applied"}

        def post_readings(self, _readings):
            return {"accepted": 4}

    emitted: list[dict] = []
    sim = DeviceSimulator(
        samples=samples,
        dry_run=False,
        poll_commands=True,
        on_emit=emitted.append,
        sleep_fn=lambda _s: None,
    )
    sim._client = FakeClient()  # type: ignore[assignment]
    ticks = sim.run(max_ticks=1, realtime=False)
    assert ticks == 1
    assert emitted[0]["feed_rate"] == 12.0
    assert acked == [42]