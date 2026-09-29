"""Device DO/feed response (assignment §3) — shared by hosted replay."""

from __future__ import annotations

TAU_PROCESS_MINUTES = 5.0
GAIN_DO_PER_ML_H = 2.0
DO_MIN = 0.0
DO_MAX = 100.0


def target_dDO(feed_rate: float, feed_run: float, gain: float = GAIN_DO_PER_ML_H) -> float:
    return -gain * (feed_rate - feed_run)


def step_dDO(
    dDO: float,
    *,
    feed_rate: float,
    feed_run: float,
    dt_proc_minutes: float,
    tau: float = TAU_PROCESS_MINUTES,
    gain: float = GAIN_DO_PER_ML_H,
) -> float:
    if dt_proc_minutes <= 0:
        return dDO
    target = target_dDO(feed_rate, feed_run, gain=gain)
    return dDO + (dt_proc_minutes / tau) * (target - dDO)


def clamp_do(do_value: float) -> float:
    return max(DO_MIN, min(DO_MAX, do_value))


def apply_do_response(do_run: float, dDO: float) -> float:
    return clamp_do(do_run + dDO)
