from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.user import UserModel


def register_and_login(
    client: TestClient,
    email: str,
    password: str = "test-password-123",
) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": email.split("@")[0], "password": password},
    )
    assert response.status_code == 201
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_admin_headers(client: TestClient, test_engine: object) -> dict[str, str]:
    email = "admin@example.com"
    register_and_login(client, email)
    with Session(test_engine) as session:
        user = session.exec(select(UserModel).where(UserModel.email == email)).one()
        user.role = "admin"
        session.add(user)
        session.commit()
    response = client.post(
        "/api/auth/login", data={"username": email, "password": "test-password-123"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_model_and_version(client: TestClient, headers: dict[str, str]) -> tuple[dict[str, object], dict[str, object]]:
    model_response = client.post(
        "/api/models",
        json={"name": "Turbine Quality Model", "description": "Predicts turbine quality."},
        headers=headers,
    )
    assert model_response.status_code == 201
    model = model_response.json()
    version_response = client.post(
        f"/api/models/{model['id']}/versions",
        json={
            "version": "1.0.0",
            "framework": "scikit-learn",
            "algorithm": "RandomForestClassifier",
            "artifact_uri": "s3://models/turbine/1.0.0",
            "training_data_reference": "s3://datasets/turbine/2026-03",
        },
        headers=headers,
    )
    assert version_response.status_code == 201
    return model, version_response.json()


def test_member_has_read_only_mlops_access(client: TestClient) -> None:
    member_headers = register_and_login(client, "member@example.com")

    response = client.post(
        "/api/models",
        json={"name": "Unauthorized Model", "description": "Should not be created."},
        headers=member_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert client.get("/api/models", headers=member_headers).status_code == 200


def test_versions_start_pending_and_only_approved_versions_deploy_to_production(
    client: TestClient, test_engine: object
) -> None:
    admin_headers = create_admin_headers(client, test_engine)
    model, version = create_model_and_version(client, admin_headers)

    assert version["approval_status"] == "PENDING"
    assert version["lifecycle_stage"] == "DRAFT"

    rejected_response = client.post(
        "/api/deployments",
        json={"model_version_id": version["id"], "environment": "production"},
        headers={**admin_headers, "Idempotency-Key": "pending-production"},
    )
    assert rejected_response.status_code == 409

    approval_response = client.patch(
        f"/api/models/{model['id']}/versions/{version['id']}/approval",
        json={"approval_status": "APPROVED", "lifecycle_stage": "PRODUCTION"},
        headers=admin_headers,
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["lifecycle_stage"] == "PRODUCTION"


def test_deployment_is_idempotent_and_records_every_status_event(
    client: TestClient, test_engine: object
) -> None:
    admin_headers = create_admin_headers(client, test_engine)
    model, version = create_model_and_version(client, admin_headers)
    client.patch(
        f"/api/models/{model['id']}/versions/{version['id']}/approval",
        json={"approval_status": "APPROVED"},
        headers=admin_headers,
    )
    request_headers = {**admin_headers, "Idempotency-Key": "production-deployment"}
    payload = {"model_version_id": version["id"], "environment": "PRODUCTION"}

    first_response = client.post("/api/deployments", json=payload, headers=request_headers)
    duplicate_response = client.post("/api/deployments", json=payload, headers=request_headers)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == first_response.json()["id"]
    assert [event["status"] for event in first_response.json()["events"]] == [
        "REQUESTED", "VALIDATING", "DEPLOYING", "SUCCEEDED"
    ]
    assert UUID(first_response.json()["id"])


def test_failed_deployment_can_retry_and_successful_production_deployment_can_roll_back(
    client: TestClient, test_engine: object
) -> None:
    admin_headers = create_admin_headers(client, test_engine)
    model, version = create_model_and_version(client, admin_headers)
    client.patch(
        f"/api/models/{model['id']}/versions/{version['id']}/approval",
        json={"approval_status": "APPROVED"},
        headers=admin_headers,
    )
    failed_response = client.post(
        "/api/deployments",
        json={
            "model_version_id": version["id"],
            "environment": "STAGING",
            "simulate_failure": True,
        },
        headers={**admin_headers, "Idempotency-Key": "failed-staging"},
    )
    assert failed_response.status_code == 201
    assert failed_response.json()["status"] == "FAILED"

    retry_response = client.post(
        f"/api/deployments/{failed_response.json()['id']}/retry", headers=admin_headers
    )
    assert retry_response.status_code == 201
    assert retry_response.json()["status"] == "SUCCEEDED"
    assert retry_response.json()["retry_of_deployment_id"] == failed_response.json()["id"]

    production_response = client.post(
        "/api/deployments",
        json={"model_version_id": version["id"], "environment": "PRODUCTION"},
        headers={**admin_headers, "Idempotency-Key": "rollback-production"},
    )
    assert production_response.status_code == 201

    rollback_response = client.post(
        f"/api/deployments/{production_response.json()['id']}/rollback", headers=admin_headers
    )
    assert rollback_response.status_code == 200
    assert rollback_response.json()["status"] == "ROLLED_BACK"
    assert rollback_response.json()["events"][-1]["status"] == "ROLLED_BACK"


def test_metrics_are_created_deterministically_for_a_model(
    client: TestClient, test_engine: object
) -> None:
    admin_headers = create_admin_headers(client, test_engine)
    model, _ = create_model_and_version(client, admin_headers)

    response = client.get(f"/api/models/{model['id']}/metrics", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["prediction_latency_ms"] == 42.0
    assert response.json()["monitoring_status"] == "HEALTHY"


def test_model_versions_can_be_compared(client: TestClient, test_engine: object) -> None:
    admin_headers = create_admin_headers(client, test_engine)
    model, first_version = create_model_and_version(client, admin_headers)
    second_version_response = client.post(
        f"/api/models/{model['id']}/versions",
        json={
            "version": "2.0.0",
            "framework": "pytorch",
            "algorithm": "NeuralNetworkClassifier",
            "artifact_uri": "s3://models/turbine/2.0.0",
            "training_data_reference": "s3://datasets/turbine/2026-04",
            "tags": ["candidate"],
            "metadata": {"feature_count": 32},
        },
        headers=admin_headers,
    )
    assert second_version_response.status_code == 201
    second_version = second_version_response.json()

    response = client.get(
        f"/api/models/{model['id']}/versions/compare",
        params={
            "left_version_id": first_version["id"],
            "right_version_id": second_version["id"],
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    comparison = response.json()
    assert comparison["left_version"]["id"] == first_version["id"]
    assert comparison["right_version"]["id"] == second_version["id"]
    assert comparison["differences"]["framework"] == {
        "left": "scikit-learn",
        "right": "pytorch",
    }
    assert comparison["differences"]["metadata"] == {
        "left": {},
        "right": {"feature_count": 32},
    }
