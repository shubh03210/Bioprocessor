"""Forecast model and API tests."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from app.ml.baseline import PersistenceBaselineForecaster
from app.ml.data import build_windows, load_run_series
from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES, MINUTE_H
from app.ml.linear import train_linear_forecaster
from app.models import Prediction, Reading

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_KIT = BACKEND_ROOT.parent / "data_kit"


def test_persistence_baseline_repeats_last_do():
    do = [float(i) for i in range(HISTORY_MINUTES)]
    feed = [0.0] * HISTORY_MINUTES
    pred = PersistenceBaselineForecaster().predict(do, feed)
    assert pred == [do[-1]] * HORIZON_MINUTES


def test_linear_forecaster_fits_and_predicts():
    series = load_run_series(DATA_KIT / "run_A.csv")
    x, y = build_windows(series["DO"], series["feed_rate"])
    assert x.shape[0] > 100
    model = train_linear_forecaster(x[:500], y[:500])
    out = model.predict(x[0][:HISTORY_MINUTES], x[0][HISTORY_MINUTES:])
    assert len(out) == HORIZON_MINUTES
    assert all(isinstance(v, float) for v in out)


def _seed_history(session: Session, n_minutes: int = 60) -> None:
    for m in range(n_minutes):
        t = m * MINUTE_H
        session.add(Reading(time_h=t, signal_name="DO", value=90.0 - 0.01 * m, unit="%"))
        session.add(Reading(time_h=t, signal_name="feed_rate", value=1.0, unit="mL/h"))
        session.add(Reading(time_h=t, signal_name="pH", value=6.5, unit="-"))
        session.add(Reading(time_h=t, signal_name="temp", value=30.0, unit="degC"))
    session.commit()


def test_forecast_endpoint_appends_predictions(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_history(session)

    response = client.post("/api/forecast")
    assert response.status_code == 200
    body = response.json()
    assert len(body["points"]) == 10
    assert body["model_version"]

    with Session(engine) as session:
        rows = session.exec(select(Prediction)).all()
        assert len(rows) == 10

    latest = client.get("/api/forecast/latest")
    assert latest.status_code == 200
    assert len(latest.json()["points"]) == 10


def test_forecast_requires_history(api_client):
    client, _engine = api_client
    response = client.post("/api/forecast")
    assert response.status_code == 422


def test_forecast_append_only_second_call(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_history(session)

    assert client.post("/api/forecast").status_code == 200
    assert client.post("/api/forecast").status_code == 200
    with Session(engine) as session:
        assert len(session.exec(select(Prediction)).all()) == 20
