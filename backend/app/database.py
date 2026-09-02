from collections.abc import Generator
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

DATABASE_FILE = Path(__file__).resolve().parent.parent / "projects.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    from app.models.project import ProjectModel

    SQLModel.metadata.create_all(engine)
