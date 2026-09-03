from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.mlops import (
    ApprovalStatus,
    ApprovalUpdate,
    LifecycleStage,
    ModelModel,
    ModelUpdate,
    ModelVersionComparisonRead,
    ModelVersionCreate,
    ModelVersionModel,
    ModelVersionRead,
)
from app.repositories.model_repository import ModelRepository
from app.schemas.model import ModelCreateRequest, ModelDetailResponse


class MlopsNotFoundError(Exception):
    pass


class MlopsConflictError(Exception):
    pass


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def serialize_model(model: ModelModel) -> ModelDetailResponse:
    return ModelDetailResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        tags=model.tags,
        metadata=model.metadata_json,
        created_at=normalize_utc(model.created_at),
        updated_at=normalize_utc(model.updated_at),
    )


def serialize_version(version: ModelVersionModel) -> ModelVersionRead:
    return ModelVersionRead(
        id=version.id,
        model_id=version.model_id,
        version=version.version,
        framework=version.framework,
        algorithm=version.algorithm,
        artifact_uri=version.artifact_uri,
        training_data_reference=version.training_data_reference,
        tags=version.tags,
        metadata=version.metadata_json,
        approval_status=version.approval_status,
        lifecycle_stage=version.lifecycle_stage,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


class ModelService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ModelRepository(session)

    def create_model(self, payload: ModelCreateRequest) -> ModelDetailResponse:
        model = ModelModel(
            name=payload.name,
            description=payload.description,
            tags=payload.tags,
            metadata_json=payload.metadata,
        )
        self.repository.add(model)
        try:
            self.repository.commit()
        except IntegrityError as error:
            self.repository.rollback()
            raise MlopsConflictError("A model with this name already exists.") from error
        self.repository.refresh(model)
        return serialize_model(model)

    def list_models(self) -> list[ModelDetailResponse]:
        models = self.repository.list()
        return [serialize_model(model) for model in models]

    def get_model(self, model_id: UUID) -> ModelDetailResponse:
        return serialize_model(self.get_model_entity(model_id))

    def get_model_entity(self, model_id: UUID) -> ModelModel:
        model = self.repository.get(model_id)
        if model is None:
            raise MlopsNotFoundError("Model not found.")
        return model

    def update_model(self, model_id: UUID, payload: ModelUpdate) -> ModelRead:
        model = self.get_model_entity(model_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "metadata" in update_data:
            update_data["metadata_json"] = update_data.pop("metadata")
        for field, value in update_data.items():
            setattr(model, field, value)
        model.updated_at = datetime.now(timezone.utc)
        self.session.add(model)
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise MlopsConflictError("A model with this name already exists.") from error
        self.session.refresh(model)
        return serialize_model(model)

    def delete_model(self, model_id: UUID) -> None:
        model = self.get_model_entity(model_id)
        has_versions = self.session.exec(
            select(ModelVersionModel.id).where(ModelVersionModel.model_id == model_id)
        ).first()
        if has_versions is not None:
            raise MlopsConflictError("Models with registered versions cannot be deleted.")
        self.session.delete(model)
        self.session.commit()

    def create_version(self, model_id: UUID, payload: ModelVersionCreate) -> ModelVersionRead:
        self.get_model_entity(model_id)
        version = ModelVersionModel(
            model_id=model_id,
            version=payload.version,
            framework=payload.framework,
            algorithm=payload.algorithm,
            artifact_uri=payload.artifact_uri,
            training_data_reference=payload.training_data_reference,
            tags=payload.tags,
            metadata_json=payload.metadata,
        )
        self.session.add(version)
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise MlopsConflictError("This version already exists for the model.") from error
        self.session.refresh(version)
        return serialize_version(version)

    def list_versions(self, model_id: UUID) -> list[ModelVersionRead]:
        self.get_model_entity(model_id)
        versions = self.session.exec(
            select(ModelVersionModel)
            .where(ModelVersionModel.model_id == model_id)
            .order_by(ModelVersionModel.created_at.desc())
        ).all()
        return [serialize_version(version) for version in versions]

    def compare_versions(
        self,
        model_id: UUID,
        left_version_id: UUID,
        right_version_id: UUID,
    ) -> ModelVersionComparisonRead:
        self.get_model_entity(model_id)
        left_version = self.session.get(ModelVersionModel, left_version_id)
        right_version = self.session.get(ModelVersionModel, right_version_id)
        if left_version is None or left_version.model_id != model_id:
            raise MlopsNotFoundError("Left model version not found.")
        if right_version is None or right_version.model_id != model_id:
            raise MlopsNotFoundError("Right model version not found.")

        left_read = serialize_version(left_version)
        right_read = serialize_version(right_version)
        left_values = left_read.model_dump(mode="json")
        right_values = right_read.model_dump(mode="json")
        excluded_fields = {"id", "model_id", "created_at", "updated_at"}
        differences = {
            field: {"left": left_values[field], "right": right_values[field]}
            for field in left_values
            if field not in excluded_fields and left_values[field] != right_values[field]
        }

        return ModelVersionComparisonRead(
            left_version=left_read,
            right_version=right_read,
            differences=differences,
        )

    def update_approval(self, model_id: UUID, version_id: UUID, payload: ApprovalUpdate) -> ModelVersionRead:
        self.get_model_entity(model_id)
        version = self.session.get(ModelVersionModel, version_id)
        if version is None or version.model_id != model_id:
            raise MlopsNotFoundError("Model version not found.")

        if (
            payload.lifecycle_stage == LifecycleStage.PRODUCTION
            and payload.approval_status != ApprovalStatus.APPROVED
        ):
            raise MlopsConflictError("Only APPROVED model versions can be promoted to PRODUCTION.")

        version.approval_status = payload.approval_status
        if payload.lifecycle_stage is not None:
            version.lifecycle_stage = payload.lifecycle_stage
        elif payload.approval_status == ApprovalStatus.APPROVED:
            version.lifecycle_stage = LifecycleStage.APPROVED
        version.updated_at = datetime.now(timezone.utc)
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return serialize_version(version)
