"""Persistence baseline: repeat last observed DO across the horizon."""

from __future__ import annotations

from typing import Sequence

from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES


class PersistenceBaselineForecaster:
    version = "persistence-v1"

    def predict(
        self,
        do_history: Sequence[float],
        feed_history: Sequence[float],
    ) -> list[float]:
        if len(do_history) < HISTORY_MINUTES:
            raise ValueError(
                f"need {HISTORY_MINUTES} DO points, got {len(do_history)}"
            )
        last = float(do_history[-1])
        return [last] * HORIZON_MINUTES
