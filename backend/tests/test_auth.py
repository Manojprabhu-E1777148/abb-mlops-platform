from fastapi.testclient import TestClient

PROJECT_PAYLOAD = {
    "name": "Project Alpha",
    "description": "A valid project description",
    "status": "draft",
}


def register_and_login(
    client: TestClient,
    email: str,
    full_name: str,
    password: str = "password12345",
) -> dict[str, str]:
    registration_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": password,
        },
    )
    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_register_user_returns_safe_profile(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "USER@EXAMPLE.COM",
            "full_name": "Test User",
            "password": "password12345",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["full_name"] == "Test User"
    assert response.json()["role"] == "member"
    assert response.json()["is_active"] is True
    assert "password_hash" not in response.json()
    assert "password" not in response.json()


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    register_and_login(client, "user@example.com", "Test User")

    response = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Another User",
            "password": "password12345",
        },
    )

    assert response.status_code == 409


def test_login_returns_bearer_access_token(client: TestClient) -> None:
    register_and_login(client, "user@example.com", "Test User")

    response = client.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "password12345"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_invalid_credentials_returns_401(client: TestClient) -> None:
    register_and_login(client, "user@example.com", "Test User")

    response = client.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_me_requires_a_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_get_me_returns_authenticated_user(client: TestClient) -> None:
    headers = register_and_login(client, "user@example.com", "Test User")

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["role"] == "member"
    assert "password_hash" not in response.json()


def test_protected_project_routes_require_a_token(client: TestClient) -> None:
    response = client.get("/api/projects")

    assert response.status_code == 401


def test_authenticated_user_can_create_project(client: TestClient) -> None:
    headers = register_and_login(client, "user@example.com", "Test User")

    response = client.post("/api/projects", json=PROJECT_PAYLOAD, headers=headers)

    assert response.status_code == 201
    assert response.json()["owner_id"]


def test_user_cannot_access_another_users_project(client: TestClient) -> None:
    first_user_headers = register_and_login(client, "first@example.com", "First User")
    second_user_headers = register_and_login(client, "second@example.com", "Second User")
    create_response = client.post(
        "/api/projects",
        json=PROJECT_PAYLOAD,
        headers=first_user_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    responses = [
        client.get(f"/api/projects/{project_id}", headers=second_user_headers),
        client.patch(
            f"/api/projects/{project_id}",
            json={"status": "active"},
            headers=second_user_headers,
        ),
        client.delete(f"/api/projects/{project_id}", headers=second_user_headers),
    ]

    for response in responses:
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to access this project"
