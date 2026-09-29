"""Forecast generation from stored readings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlmodel import Session

from app.ml.baseline import PersistenceBaselineForecaster
from app.ml.data import minute_index, series_from_minute_maps
from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES, MINUTE_H
from app.ml.linear import LinearForecaster, MODEL_VERSION
from app.models import Prediction
from app.repositories import predictions as predictions_repo
from app.repositories import readings as readings_repo

ARTIFACT_PATH = Path(__file__).resolve().parents[1] / "ml" / "artifacts" / f"{MODEL_VERSION}.joblib"


@lru_cache(maxsize=1)
def load_primary_forecaster() -> LinearForecaster | PersistenceBaselineForecaster:
    if ARTIFACT_PATH.exists():
        return LinearForecaster.load(ARTIFACT_PATH)
    return PersistenceBaselineForecaster()


class ForecastService:
    def __init__(self, session: Session):
        self.session = session

    def _histories_from_db(self) -> tuple[list[float], list[float], float] | None:
        # Pull enough recent rows (60 minutes * 2 signals * some slack)
        rows = readings_repo.list_recent_readings(self.session, limit=HISTORY_MINUTES * 4)
        do_by: dict[int, float] = {}
        feed_by: dict[int, float] = {}
        for r in rows:
            m = minute_index(r.time_h)
            if r.signal_name == "DO":
                do_by[m] = r.value
            elif r.signal_name == "feed_rate":
                feed_by[m] = r.value
        built = series_from_minute_maps(do_by, feed_by)
        if built is None:
            return None
        do_hist, feed_hist = built
        made_at = max(do_by) * MINUTE_H
        return do_hist, feed_hist, made_at

    def generate_and_store(self) -> dict | None:
        """Create a 10-minute DO forecast and append prediction rows. Never overwrite."""
        built = self._histories_from_db()
        if built is None:
            return None
        do_hist, feed_hist, made_at = built
        forecaster = load_primary_forecaster()
        values = forecaster.predict(do_hist, feed_hist)
        rows = [
            Prediction(
                made_at_time_h=made_at,
                target_time_h=made_at + (i + 1) * MINUTE_H,
                signal_name="DO",
                value=values[i],
                unit="%",
                model_version=forecaster.version,
            )
            for i in range(HORIZON_MINUTES)
        ]
        predictions_repo.insert_predictions(self.session, rows)
        return {
            "made_at_time_h": made_at,
            "model_version": forecaster.version,
            "points": [
                {"target_time_h": r.target_time_h, "value": r.value} for r in rows
            ],
        }

    def latest(self) -> list[Prediction]:
        return predictions_repo.get_latest_do_forecast(self.session)
