from datetime import datetime

from fastapi.testclient import TestClient


def test_health_returns_service_status_and_utc_timestamp(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"]
    payload = response.json()
    assert payload["status"] == "Healthy"
    assert payload["service"] == "ABB MLOps Platform API"
    assert datetime.fromisoformat(payload["timestampUtc"].replace("Z", "+00:00")).tzinfo is not None