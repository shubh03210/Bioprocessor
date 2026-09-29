"""API tests for POST /ingest and GET /api/control/state."""

from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models import Reading


def test_ingest_persists_readings_and_returns_process_time(api_client):
    client, engine = api_client
    payload = {
        "readings": [
            {"time_h": 0.0, "signal_name": "DO", "value": 98.0, "unit": "%"},
            {"time_h": 0.0, "signal_name": "pH", "value": 6.5, "unit": "-"},
            {"time_h": 0.0, "signal_name": "temp", "value": 30.0, "unit": "degC"},
            {"time_h": 0.0, "signal_name": "feed_rate", "value": 0.0, "unit": "mL/h"},
            {"time_h": 0.0167, "signal_name": "DO", "value": 97.0, "unit": "%"},
            {"time_h": 0.0167, "signal_name": "feed_rate", "value": 5.0, "unit": "mL/h"},
            {"time_h": 0.0167, "signal_name": "pH", "value": 6.5, "unit": "-"},
            {"time_h": 0.0167, "signal_name": "temp", "value": 30.0, "unit": "degC"},
        ]
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] == 8
    assert body["current_process_time_h"] == pytest.approx(0.0167)

    with Session(engine) as session:
        rows = session.exec(select(Reading)).all()
        assert len(rows) == 8


def test_ingest_rejects_bad_unit(api_client):
    client, _engine = api_client
    response = client.post(
        "/ingest",
        json={
            "readings": [
                {"time_h": 1.0, "signal_name": "DO", "value": 50.0, "unit": "mL/h"},
            ]
        },
    )
    assert response.status_code == 422


def test_control_state_returns_stored_readings(api_client):
    client, _engine = api_client
    client.post(
        "/ingest",
        json={
            "readings": [
                {"time_h": 1.0, "signal_name": "DO", "value": 40.0, "unit": "%"},
                {"time_h": 1.0, "signal_name": "feed_rate", "value": 2.0, "unit": "mL/h"},
                {"time_h": 1.0, "signal_name": "pH", "value": 6.4, "unit": "-"},
                {"time_h": 1.0, "signal_name": "temp", "value": 30.1, "unit": "degC"},
            ]
        },
    )
    response = client.get("/api/control/state")
    assert response.status_code == 200
    body = response.json()
    assert body["current_process_time_h"] == pytest.approx(1.0)
    assert body["reading_count"] == 4
    assert len(body["readings"]) == 4
    assert "recent_commands" in body
