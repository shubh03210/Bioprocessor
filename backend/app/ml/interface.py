"""Forecaster interface and shared constants."""

from __future__ import annotations

from typing import Protocol, Sequence

HISTORY_MINUTES = 60
HORIZON_MINUTES = 10
MINUTE_H = 1.0 / 60.0


class Forecaster(Protocol):
    """Predict next 10 minutes of DO from last 60 minutes of DO + feed_rate."""

    version: str

    def predict(
        self,
        do_history: Sequence[float],
        feed_history: Sequence[float],
    ) -> list[float]:
        """Return length-10 DO forecast. Histories must be length 60 (oldest→newest)."""
        ...
