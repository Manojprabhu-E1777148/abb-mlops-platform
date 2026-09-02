from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

engine_options: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    from app.models.project import ProjectModel
    from app.models.user import UserModel

    if engine.url.get_backend_name() == "sqlite":
        SQLModel.metadata.create_all(engine)
