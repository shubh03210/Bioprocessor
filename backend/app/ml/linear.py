"""Ridge multi-output linear DO forecaster."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES

MODEL_VERSION = "ridge-linear-v1"


class LinearForecaster:
    def __init__(self, model: Pipeline | None = None, version: str = MODEL_VERSION):
        self.model = model
        self.version = version

    @staticmethod
    def _features(do_history: Sequence[float], feed_history: Sequence[float]) -> np.ndarray:
        if len(do_history) != HISTORY_MINUTES or len(feed_history) != HISTORY_MINUTES:
            raise ValueError(
                f"histories must be length {HISTORY_MINUTES}, "
                f"got DO={len(do_history)} feed={len(feed_history)}"
            )
        return np.concatenate([np.asarray(do_history, dtype=float), np.asarray(feed_history, dtype=float)]).reshape(
            1, -1
        )

    def predict(
        self,
        do_history: Sequence[float],
        feed_history: Sequence[float],
    ) -> list[float]:
        if self.model is None:
            raise RuntimeError("model not loaded")
        x = self._features(do_history, feed_history)
        y = self.model.predict(x)[0]
        return [float(v) for v in y]

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        pipe: Pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "ridge",
                    MultiOutputRegressor(Ridge(alpha=1.0, random_state=42)),
                ),
            ]
        )
        pipe.fit(x, y)
        self.model = pipe

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"version": self.version, "model": self.model}, path)

    @classmethod
    def load(cls, path: Path | str) -> LinearForecaster:
        payload = joblib.load(path)
        return cls(model=payload["model"], version=payload.get("version", MODEL_VERSION))


def train_linear_forecaster(x: np.ndarray, y: np.ndarray) -> LinearForecaster:
    assert y.shape[1] == HORIZON_MINUTES
    forecaster = LinearForecaster()
    forecaster.fit(x, y)
    return forecaster
