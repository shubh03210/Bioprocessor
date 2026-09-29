from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "bbp-backend"
    assert "version" in body
