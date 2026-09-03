from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.user import UserModel


def create_admin_headers(client: TestClient, test_engine: object) -> dict[str, str]:
    email = "model-admin@example.com"
    password = "test-password-123"
    registration = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Model Admin", "password": password},
    )
    assert registration.status_code == 201

    with Session(test_engine) as session:
        user = session.exec(select(UserModel).where(UserModel.email == email)).one()
        user.role = "admin"
        session.add(user)
        session.commit()

    login = client.post("/api/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def model_payload(name: str = "Pump Failure Predictor") -> dict[str, object]:
    return {
        "name": name,
        "description": "Predicts centrifugal-pump failures.",
        "tags": ["plant-a", "critical"],
        "metadata": {"owner_team": "Reliability"},
    }


def test_create_model_returns_audited_model(client: TestClient, test_engine: object) -> None:
    response = client.post(
        "/api/models",
        json=model_payload(),
        headers=create_admin_headers(client, test_engine),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Pump Failure Predictor"
    assert payload["tags"] == ["plant-a", "critical"]
    assert payload["metadata"] == {"owner_team": "Reliability"}
    assert datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00")).tzinfo is not None
    assert datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00")).tzinfo is not None


def test_list_models_returns_models(client: TestClient, test_engine: object) -> None:
    headers = create_admin_headers(client, test_engine)
    assert client.post("/api/models", json=model_payload(), headers=headers).status_code == 201

    response = client.get("/api/models", headers=headers)

    assert response.status_code == 200
    assert [model["name"] for model in response.json()] == ["Pump Failure Predictor"]


def test_get_model_by_id_returns_model(client: TestClient, test_engine: object) -> None:
    headers = create_admin_headers(client, test_engine)
    created = client.post("/api/models", json=model_payload(), headers=headers).json()

    response = client.get(f"/api/models/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_model_returns_structured_not_found(
    client: TestClient,
    test_engine: object,
) -> None:
    response = client.get(
        "/api/models/00000000-0000-0000-0000-000000000000",
        headers=create_admin_headers(client, test_engine),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["trace_id"]


def test_create_model_rejects_invalid_input(client: TestClient, test_engine: object) -> None:
    response = client.post(
        "/api/models",
        json={"name": "", "description": ""},
        headers=create_admin_headers(client, test_engine),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_model_rejects_duplicate_name(client: TestClient, test_engine: object) -> None:
    headers = create_admin_headers(client, test_engine)
    assert client.post("/api/models", json=model_payload(), headers=headers).status_code == 201

    response = client.post("/api/models", json=model_payload(), headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"