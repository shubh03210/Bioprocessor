"""API integration tests for Part A scheduling endpoints."""

from __future__ import annotations

from sqlmodel import Session

from app.services.scheduling import SchedulingService


def test_get_schedule_returns_seed_violations(seeded_api_client):
    client, _engine = seeded_api_client
    response = client.get(
        "/api/schedule",
        params={"start_date": "2025-10-01", "end_date": "2025-11-30"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["equipment"]) == 5
    assert len(body["batches"]) >= 3
    assert len(body["unit_operations"]) >= 6
    rule_ids = {v["rule_id"] for v in body["violations"]}
    assert "DR-002" in rule_ids
    assert "DR-003" in rule_ids


def test_get_schedule_rejects_bad_range(seeded_api_client):
    client, _engine = seeded_api_client
    response = client.get(
        "/api/schedule",
        params={"start_date": "2025-11-01", "end_date": "2025-10-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_unit_operation_save_and_return(seeded_api_client):
    client, engine = seeded_api_client
    with Session(engine) as session:
        svc = SchedulingService(session)
        batch = next(b for b in svc.list_batches() if b.name == "Batch Alpha")
        eq = next(e for e in svc.list_equipment() if e.name == "75L")
        batch_id, eq_id = batch.id, eq.id

    response = client.post(
        "/api/unit_operations",
        json={
            "name": "Alpha TFF 75L",
            "type": "TFF",
            "color": "#888888",
            "status": "draft",
            "start_date": "2025-10-31",
            "end_date": "2025-11-01",
            "batch_id": batch_id,
            "equipment_id": eq_id,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["unit_operation"]["name"] == "Alpha TFF 75L"
    assert "violations" in body


def test_create_unknown_batch_404(seeded_api_client):
    client, engine = seeded_api_client
    with Session(engine) as session:
        eq_id = SchedulingService(session).list_equipment()[0].id
    response = client.post(
        "/api/unit_operations",
        json={
            "name": "X",
            "type": "Seed",
            "color": "#000",
            "status": "draft",
            "start_date": "2025-10-01",
            "end_date": "2025-10-02",
            "batch_id": 99999,
            "equipment_id": eq_id,
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_put_updates_and_returns_violations(seeded_api_client):
    client, engine = seeded_api_client
    with Session(engine) as session:
        op = next(
            o
            for o in SchedulingService(session).list_unit_operations()
            if o.name == "Charlie Bioreactor 1500L"
        )
        payload = {
            "name": op.name,
            "type": op.type,
            "color": op.color,
            "status": op.status,
            "start_date": "2025-10-24",
            "end_date": op.end_date.isoformat(),
            "batch_id": op.batch_id,
            "equipment_id": op.equipment_id,
        }
        op_id = op.id

    response = client.put(f"/api/unit_operations/{op_id}", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["unit_operation"]["start_date"] == "2025-10-24"
    messages = [v["message"] for v in body["violations"] if v["rule_id"] == "DR-002"]
    assert not any("Charlie Seed 75L" in m and "Charlie Bioreactor 1500L" in m for m in messages)


def test_delete_unit_operation(seeded_api_client):
    client, engine = seeded_api_client
    with Session(engine) as session:
        op = next(
            o
            for o in SchedulingService(session).list_unit_operations()
            if o.name == "Bravo Seed 20L"
        )
        op_id = op.id

    response = client.delete(f"/api/unit_operations/{op_id}")
    assert response.status_code == 204

    missing = client.delete(f"/api/unit_operations/{op_id}")
    assert missing.status_code == 404


def test_delete_completed_conflicts(seeded_api_client):
    client, engine = seeded_api_client
    with Session(engine) as session:
        svc = SchedulingService(session)
        op = next(o for o in svc.list_unit_operations() if o.name == "Alpha Seed 1.5L")
        svc.update_unit_operation(op.id, status="completed")
        op_id = op.id

    response = client.delete(f"/api/unit_operations/{op_id}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert response.json()["error"]["details"][0]["rule_id"] == "DR-005"
