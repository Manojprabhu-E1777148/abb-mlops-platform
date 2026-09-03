from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.auth import CurrentActiveUserDependency, RequireAdminDependency
from app.database import get_session
from app.models.mlops import (
    ApprovalUpdate,
    ModelUpdate,
    ModelVersionComparisonRead,
    ModelVersionCreate,
    ModelVersionRead,
)
from app.schemas.model import (
    ModelCreateRequest,
    ModelDetailResponse,
    ModelDetailResponse as ModelRead,
    ModelListResponse,
)
from app.services.deployment_service import MonitoringService
from app.services.model_service import ModelService

router = APIRouter(prefix="/api/models", tags=["Models"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=ModelDetailResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    payload: ModelCreateRequest,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> ModelDetailResponse:
    return ModelService(session).create_model(payload)


@router.get("", response_model=ModelListResponse)
def list_models(
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> ModelListResponse:
    return ModelListResponse(ModelService(session).list_models())


@router.get("/{model_id}", response_model=ModelDetailResponse)
def get_model(
    model_id: UUID,
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> ModelDetailResponse:
    return ModelService(session).get_model(model_id)


@router.patch("/{model_id}", response_model=ModelRead)
def update_model(
    model_id: UUID,
    payload: ModelUpdate,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> ModelRead:
    return ModelService(session).update_model(model_id, payload)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: UUID,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> Response:
    ModelService(session).delete_model(model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{model_id}/versions", response_model=ModelVersionRead, status_code=status.HTTP_201_CREATED)
def create_version(
    model_id: UUID,
    payload: ModelVersionCreate,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> ModelVersionRead:
    return ModelService(session).create_version(model_id, payload)


@router.get("/{model_id}/versions", response_model=list[ModelVersionRead])
def list_versions(
    model_id: UUID,
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> list[ModelVersionRead]:
    return ModelService(session).list_versions(model_id)


@router.get("/{model_id}/versions/compare", response_model=ModelVersionComparisonRead)
def compare_versions(
    model_id: UUID,
    left_version_id: UUID,
    right_version_id: UUID,
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> ModelVersionComparisonRead:
    return ModelService(session).compare_versions(
        model_id,
        left_version_id,
        right_version_id,
    )


@router.patch("/{model_id}/versions/{version_id}/approval", response_model=ModelVersionRead)
def update_approval(
    model_id: UUID,
    version_id: UUID,
    payload: ApprovalUpdate,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> ModelVersionRead:
    return ModelService(session).update_approval(model_id, version_id, payload)


@router.get("/{model_id}/metrics")
def get_metrics(
    model_id: UUID,
    session: SessionDependency,
    _: CurrentActiveUserDependency,
):
    return MonitoringService(session).get_metrics(model_id)
