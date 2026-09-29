"""Load long-format run CSVs into aligned minute series."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES, MINUTE_H


def load_run_series(path: Path | str) -> dict[str, np.ndarray]:
    path = Path(path)
    by_time: dict[float, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            t = float(row["time_h"])
            by_time.setdefault(t, {})[row["signal_name"]] = float(row["value"])

    times = sorted(by_time)
    do = np.array([by_time[t]["DO"] for t in times], dtype=float)
    feed = np.array([by_time[t]["feed_rate"] for t in times], dtype=float)
    return {
        "time_h": np.array(times, dtype=float),
        "DO": do,
        "feed_rate": feed,
    }


def build_windows(
    do: np.ndarray,
    feed: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return X (n, 120) = [DO_60 | feed_60], y (n, 10) next DO values."""
    n = len(do)
    need = HISTORY_MINUTES + HORIZON_MINUTES
    if n < need:
        return np.empty((0, HISTORY_MINUTES * 2)), np.empty((0, HORIZON_MINUTES))

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for i in range(HISTORY_MINUTES - 1, n - HORIZON_MINUTES):
        hist_do = do[i - HISTORY_MINUTES + 1 : i + 1]
        hist_feed = feed[i - HISTORY_MINUTES + 1 : i + 1]
        fut_do = do[i + 1 : i + 1 + HORIZON_MINUTES]
        xs.append(np.concatenate([hist_do, hist_feed]))
        ys.append(fut_do)
    return np.vstack(xs), np.vstack(ys)


def series_from_minute_maps(
    do_by_minute: dict[int, float],
    feed_by_minute: dict[int, float],
) -> tuple[list[float], list[float]] | None:
    """Build contiguous last-60 histories ending at the latest shared minute index."""
    if not do_by_minute or not feed_by_minute:
        return None
    end = min(max(do_by_minute), max(feed_by_minute))
    start = end - HISTORY_MINUTES + 1
    if start < 0:
        return None
    do_hist: list[float] = []
    feed_hist: list[float] = []
    for m in range(start, end + 1):
        if m not in do_by_minute or m not in feed_by_minute:
            return None
        do_hist.append(do_by_minute[m])
        feed_hist.append(feed_by_minute[m])
    return do_hist, feed_hist


def minute_index(time_h: float) -> int:
    return int(round(time_h / MINUTE_H))
