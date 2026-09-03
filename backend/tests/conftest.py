from collections.abc import Generator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

os.environ.setdefault("SECRET_KEY", "test-jwt-secret-with-at-least-32-bytes")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app import database
from app.database import get_session
from app.main import app


@pytest.fixture
def test_engine(tmp_path: Path) -> Generator[object, None, None]:
    test_database_file = tmp_path / "projects.db"
    engine = create_engine(
        f"sqlite:///{test_database_file}",
        connect_args={"check_same_thread": False},
    )

    yield engine

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    test_engine: object,
) -> Generator[TestClient, None, None]:
    def get_test_session() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    monkeypatch.setattr(database, "engine", test_engine)
    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    registration_response = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
            "password": "password12345",
        },
    )
    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "password12345"},
    )
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}
