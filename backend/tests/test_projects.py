from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.user import UserModel

VALID_PROJECT = {
    "name": "Project Alpha",
    "description": "A valid project description",
    "status": "draft",
}


def create_project(
    client: TestClient,
    auth_headers: dict[str, str],
    payload: dict[str, str],
) -> dict[str, object]:
    response = client.post("/api/projects", json=payload, headers=auth_headers)

    assert response.status_code == 201

    return response.json()


def register_and_login(
    client: TestClient,
    email: str,
    full_name: str,
) -> tuple[dict[str, str], dict[str, object]]:
    registration_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": "password12345",
        },
    )
    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "password12345"},
    )
    assert login_response.status_code == 200

    return (
        {"Authorization": f"Bearer {login_response.json()['access_token']}"},
        registration_response.json(),
    )


def promote_to_admin(test_engine: object, email: str) -> None:
    with Session(test_engine) as session:
        user = session.exec(select(UserModel).where(UserModel.email == email)).one()
        user.role = "admin"
        session.add(user)
        session.commit()


def test_create_valid_project_returns_201(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post("/api/projects", json=VALID_PROJECT, headers=auth_headers)

    assert response.status_code == 201

    project = response.json()
    assert project["name"] == VALID_PROJECT["name"]
    assert project["description"] == VALID_PROJECT["description"]
    assert project["owner_id"] == project["owner"]["id"]
    assert project["owner"]["full_name"] == "Test User"
    assert project["owner"]["email"] == "user@example.com"
    assert "password_hash" not in project["owner"]
    assert project["status"] == VALID_PROJECT["status"]
    assert UUID(project["id"])
    assert UUID(project["owner_id"])
    assert datetime.fromisoformat(project["created_at"].replace("Z", "+00:00"))


def test_create_invalid_project_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/projects",
        json={
            **VALID_PROJECT,
            "name": "AB",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_list_projects_returns_two_created_projects(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    first_project = create_project(client, auth_headers, VALID_PROJECT)
    second_project = create_project(
        client,
        auth_headers,
        {
            **VALID_PROJECT,
            "name": "Project Beta",
        },
    )

    response = client.get("/api/projects", headers=auth_headers)

    assert response.status_code == 200

    response_body = response.json()
    assert response_body["count"] == 2
    assert {project["id"] for project in response_body["items"]} == {
        first_project["id"],
        second_project["id"],
    }


def test_list_projects_starts_with_clean_database(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/projects", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0}


def test_get_existing_project_returns_200(
    client: TestClient,
    auth_headers: dict[str, str],
    sample_project: dict[str, object],
) -> None:
    response = client.get(
        f"/api/projects/{sample_project['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == sample_project


def test_get_missing_project_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(f"/api/projects/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_patch_updates_only_supplied_fields(
    client: TestClient,
    auth_headers: dict[str, str],
    sample_project: dict[str, object],
) -> None:
    response = client.patch(
        f"/api/projects/{sample_project['id']}",
        json={
            "status": "active",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    updated_project = response.json()
    assert updated_project["name"] == sample_project["name"]
    assert updated_project["description"] == sample_project["description"]
    assert updated_project["owner"] == sample_project["owner"]
    assert updated_project["status"] == "active"


def test_patch_rejects_pending_status(
    client: TestClient,
    auth_headers: dict[str, str],
    sample_project: dict[str, object],
) -> None:
    response = client.patch(
        f"/api/projects/{sample_project['id']}",
        json={"status": "pending"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_patch_missing_project_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.patch(
        f"/api/projects/{uuid4()}",
        json={"status": "active"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_delete_project_returns_204_and_removes_project(
    client: TestClient,
    auth_headers: dict[str, str],
    sample_project: dict[str, object],
) -> None:
    delete_response = client.delete(
        f"/api/projects/{sample_project['id']}",
        headers=auth_headers,
    )
    get_response = client.get(
        f"/api/projects/{sample_project['id']}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Project not found"