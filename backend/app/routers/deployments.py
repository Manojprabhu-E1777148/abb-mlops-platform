from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlmodel import Session

from app.auth import CurrentActiveUserDependency, RequireAdminDependency
from app.database import get_session
from app.models.mlops import DeploymentCreate, DeploymentRead
from app.services.deployment_service import DeploymentService

router = APIRouter(prefix="/api/deployments", tags=["Deployments"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def create_deployment(
    payload: DeploymentCreate,
    session: SessionDependency,
    _: RequireAdminDependency,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> DeploymentRead:
    return DeploymentService(session).create_deployment(payload, idempotency_key)


@router.get("", response_model=list[DeploymentRead])
def list_deployments(
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> list[DeploymentRead]:
    return DeploymentService(session).list_deployments()


@router.get("/{deployment_id}", response_model=DeploymentRead)
def get_deployment(
    deployment_id: UUID,
    session: SessionDependency,
    _: CurrentActiveUserDependency,
) -> DeploymentRead:
    return DeploymentService(session).get_deployment(deployment_id)


@router.post("/{deployment_id}/retry", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def retry_deployment(
    deployment_id: UUID,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> DeploymentRead:
    return DeploymentService(session).retry_deployment(deployment_id)


@router.post("/{deployment_id}/rollback", response_model=DeploymentRead)
def rollback_deployment(
    deployment_id: UUID,
    session: SessionDependency,
    _: RequireAdminDependency,
) -> DeploymentRead:
    return DeploymentService(session).rollback_deployment(deployment_id)
