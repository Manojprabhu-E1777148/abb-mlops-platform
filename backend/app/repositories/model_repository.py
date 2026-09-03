from uuid import UUID

from sqlmodel import Session, select

from app.models.mlops import ModelModel


class ModelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, model: ModelModel) -> ModelModel:
        self._session.add(model)
        return model

    def get(self, model_id: UUID) -> ModelModel | None:
        return self._session.get(ModelModel, model_id)

    def list(self) -> list[ModelModel]:
        return list(self._session.exec(select(ModelModel).order_by(ModelModel.name)).all())

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, model: ModelModel) -> None:
        self._session.refresh(model)