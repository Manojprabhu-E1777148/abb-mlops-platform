from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

from app import database
from app.main import app

TEST_DATABASE_FILE = Path(__file__).parent / "test_projects.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_FILE}"

VALID_PROJECT = {
    "name": "Project Alpha",
    "description": "A valid project description",
    "owner": "ABB Team",
    "status": "draft",
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    TEST_DATABASE_FILE.unlink(missing_ok=True)

    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", test_engine)

    SQLModel.metadata.create_all(test_engine)

    with TestClient(app) as test_client:
        yield test_client

    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()
    TEST_DATABASE_FILE.unlink(missing_ok=True)


def create_project(client: TestClient) -> dict[str, object]:
    response = client.post("/api/projects", json=VALID_PROJECT)

    assert response.status_code == 201

    return response.json()


def test_create_valid_project_returns_201(client: TestClient) -> None:
    response = client.post("/api/projects", json=VALID_PROJECT)

    assert response.status_code == 201

    project = response.json()
    assert project["name"] == VALID_PROJECT["name"]
    assert project["description"] == VALID_PROJECT["description"]
    assert project["owner"] == VALID_PROJECT["owner"]
    assert project["status"] == VALID_PROJECT["status"]
    assert project["id"]
    assert project["created_at"]


def test_create_invalid_project_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={
            **VALID_PROJECT,
            "name": "AB",
        },
    )

    assert response.status_code == 422


def test_list_projects_contains_created_project(client: TestClient) -> None:
    project = create_project(client)

    response = client.get("/api/projects")

    assert response.status_code == 200

    response_body = response.json()
    assert response_body["count"] == 1
    assert response_body["items"] == [project]


def test_retrieve_existing_project_returns_200(client: TestClient) -> None:
    project = create_project(client)

    response = client.get(f"/api/projects/{project['id']}")

    assert response.status_code == 200
    assert response.json() == project


def test_retrieve_missing_project_returns_404(client: TestClient) -> None:
    project_id = uuid4()

    response = client.get(f"/api/projects/{project_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_partial_update_status_preserves_other_fields(client: TestClient) -> None:
    project = create_project(client)

    response = client.patch(
        f"/api/projects/{project['id']}",
        json={"status": "active"},
    )

    assert response.status_code == 200

    updated_project = response.json()
    assert updated_project["name"] == VALID_PROJECT["name"]
    assert updated_project["description"] == VALID_PROJECT["description"]
    assert updated_project["owner"] == VALID_PROJECT["owner"]
    assert updated_project["status"] == "active"


def test_partial_update_rejects_invalid_status(client: TestClient) -> None:
    project = create_project(client)

    response = client.patch(
        f"/api/projects/{project['id']}",
        json={"status": "pending"},
    )

    assert response.status_code == 422


def test_delete_project_returns_204(client: TestClient) -> None:
    project = create_project(client)

    response = client.delete(f"/api/projects/{project['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_retrieve_deleted_project_returns_404(client: TestClient) -> None:
    project = create_project(client)

    delete_response = client.delete(f"/api/projects/{project['id']}")
    response = client.get(f"/api/projects/{project['id']}")

    assert delete_response.status_code == 204
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"