"""Command validation and controller tests."""

from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.domain.command_validation import CommandCandidate, validate_command
from app.models import ControlCommand, Reading
from app.models.constants import ControlCommandStatus
from app.services.controller import propose_feed_setpoint


def _seed_readings(session: Session, time_h: float = 1.0, do: float = 95.0, feed: float = 2.0):
    session.add(Reading(time_h=time_h, signal_name="DO", value=do, unit="%"))
    session.add(Reading(time_h=time_h, signal_name="feed_rate", value=feed, unit="mL/h"))
    session.add(Reading(time_h=time_h, signal_name="pH", value=6.5, unit="-"))
    session.add(Reading(time_h=time_h, signal_name="temp", value=30.0, unit="degC"))
    session.commit()


def test_validate_bounds_unit_time_pending():
    ok = validate_command(
        CommandCandidate("feed_rate", 8.0, "mL/h", 1.0),
        current_process_time_h=0.5,
        has_pending_same_setpoint=False,
    )
    assert ok.ok

    bounds = validate_command(
        CommandCandidate("feed_rate", 35.0, "mL/h", 1.0),
        current_process_time_h=0.5,
        has_pending_same_setpoint=False,
    )
    assert not bounds.ok
    assert "outside" in (bounds.reject_reason or "")

    unit = validate_command(
        CommandCandidate("feed_rate", 8.0, "%", 1.0),
        current_process_time_h=0.5,
        has_pending_same_setpoint=False,
    )
    assert not unit.ok
    assert "unit" in (unit.reject_reason or "").lower()

    time_rej = validate_command(
        CommandCandidate("feed_rate", 8.0, "mL/h", 0.1),
        current_process_time_h=0.5,
        has_pending_same_setpoint=False,
    )
    assert not time_rej.ok
    assert "earlier" in (time_rej.reject_reason or "")

    pending = validate_command(
        CommandCandidate("feed_rate", 8.0, "mL/h", 1.0),
        current_process_time_h=0.5,
        has_pending_same_setpoint=True,
    )
    assert not pending.ok
    assert "pending" in (pending.reject_reason or "")


def test_propose_feed_decreases_when_do_low():
    new, reason = propose_feed_setpoint(do=30.0, feed=10.0)
    assert new is not None and new < 10.0
    assert "decrease" in reason


def test_propose_feed_deadband_holds():
    new, reason = propose_feed_setpoint(do=60.0, feed=5.0)
    assert new is None
    assert "deadband" in reason


def test_post_command_accepts(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=1.0)

    response = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 8.0,
            "unit": "mL/h",
            "apply_at_time_h": 1.1,
            "source": "manual",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["value"] == 8.0


def test_post_command_rejects_out_of_bounds_and_persists(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=1.0)

    response = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 35.0,
            "unit": "mL/h",
            "apply_at_time_h": 1.1,
        },
    )
    assert response.status_code == 400
    err = response.json()["error"]
    assert err["code"] == "invalid_command"
    assert err["details"][0]["status"] == "rejected"

    with Session(engine) as session:
        rows = session.exec(select(ControlCommand)).all()
        assert len(rows) == 1
        assert rows[0].status == ControlCommandStatus.REJECTED.value


def test_post_command_rejects_bad_unit(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=1.0)

    response = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 8.0,
            "unit": "%",
            "apply_at_time_h": 1.1,
        },
    )
    assert response.status_code == 400
    assert "unit" in response.json()["error"]["message"].lower()


def test_post_command_rejects_apply_before_process_time(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=2.0)

    response = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 8.0,
            "unit": "mL/h",
            "apply_at_time_h": 1.0,
        },
    )
    assert response.status_code == 400
    assert "earlier" in response.json()["error"]["message"]


def test_post_command_rejects_pending_conflict(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=1.0)

    first = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 5.0,
            "unit": "mL/h",
            "apply_at_time_h": 1.2,
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/command",
        json={
            "setpoint_name": "feed_rate",
            "value": 6.0,
            "unit": "mL/h",
            "apply_at_time_h": 1.3,
        },
    )
    assert second.status_code == 400
    assert "pending" in second.json()["error"]["message"]


def test_controller_step_emits_pending_with_lag(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=2.0, do=95.0, feed=2.0)

    response = client.post("/api/control/step")
    assert response.status_code == 200
    body = response.json()
    assert body["acted"] is True
    assert body["command"]["status"] == "pending"
    assert body["command"]["source"] == "controller"
    assert body["command"]["apply_at_time_h"] == pytest.approx(2.0 + 5.0 / 60.0)

    pending = client.get("/api/control/commands/pending")
    assert pending.status_code == 200
    assert len(pending.json()) == 1

    cmd_id = body["command"]["id"]
    ack = client.post(f"/api/control/commands/{cmd_id}/ack")
    assert ack.status_code == 200
    assert ack.json()["status"] == "applied"
    assert client.get("/api/control/commands/pending").json() == []


def test_controller_respects_pending_block(api_client):
    client, engine = api_client
    with Session(engine) as session:
        _seed_readings(session, time_h=2.0, do=95.0, feed=2.0)

    first = client.post("/api/control/step")
    assert first.json()["acted"] is True

    second = client.post("/api/control/step")
    assert second.status_code == 200
    assert second.json()["acted"] is False
    reason = second.json()["reason"].lower()
    assert "pending" in reason or "dwell" in reason
