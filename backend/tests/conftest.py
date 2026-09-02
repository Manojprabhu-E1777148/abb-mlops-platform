from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

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
def sample_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "name": "Project Alpha",
            "description": "A valid project description",
            "owner": "ABB Team",
            "status": "draft",
        },
    )

    assert response.status_code == 201

    return response.json()