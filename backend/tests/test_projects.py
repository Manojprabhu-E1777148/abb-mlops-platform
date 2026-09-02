from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

VALID_PROJECT = {
    "name": "Project Alpha",
    "description": "A valid project description",
    "owner": "ABB Team",
    "status": "draft",
}


def create_project(client: TestClient, payload: dict[str, str]) -> dict[str, object]:
    response = client.post("/api/projects", json=payload)

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
    assert UUID(project["id"])
    assert datetime.fromisoformat(project["created_at"].replace("Z", "+00:00"))


def test_create_invalid_project_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={
            **VALID_PROJECT,
            "name": "AB",
        },
    )

    assert response.status_code == 422


def test_list_projects_returns_two_created_projects(client: TestClient) -> None:
    first_project = create_project(client, VALID_PROJECT)
    second_project = create_project(
        client,
        {
            **VALID_PROJECT,
            "name": "Project Beta",
        },
    )

    response = client.get("/api/projects")

    assert response.status_code == 200

    response_body = response.json()
    assert response_body["count"] == 2
    assert {project["id"] for project in response_body["items"]} == {
        first_project["id"],
        second_project["id"],
    }


def test_list_projects_starts_with_clean_database(client: TestClient) -> None:
    response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0}


def test_get_existing_project_returns_200(
    client: TestClient,
    sample_project: dict[str, object],
) -> None:
    response = client.get(f"/api/projects/{sample_project['id']}")

    assert response.status_code == 200
    assert response.json() == sample_project


def test_get_missing_project_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/projects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_patch_updates_only_supplied_fields(
    client: TestClient,
    sample_project: dict[str, object],
) -> None:
    response = client.patch(
        f"/api/projects/{sample_project['id']}",
        json={
            "status": "active",
            "owner": "Platform Team",
        },
    )

    assert response.status_code == 200

    updated_project = response.json()
    assert updated_project["name"] == sample_project["name"]
    assert updated_project["description"] == sample_project["description"]
    assert updated_project["owner"] == "Platform Team"
    assert updated_project["status"] == "active"


def test_patch_rejects_pending_status(
    client: TestClient,
    sample_project: dict[str, object],
) -> None:
    response = client.patch(
        f"/api/projects/{sample_project['id']}",
        json={"status": "pending"},
    )

    assert response.status_code == 422


def test_patch_missing_project_returns_404(client: TestClient) -> None:
    response = client.patch(
        f"/api/projects/{uuid4()}",
        json={"status": "active"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_delete_project_returns_204_and_removes_project(
    client: TestClient,
    sample_project: dict[str, object],
) -> None:
    delete_response = client.delete(f"/api/projects/{sample_project['id']}")
    get_response = client.get(f"/api/projects/{sample_project['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Project not found"