from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.auth import CurrentActiveUserDependency
from app.database import get_session
from app.models.project import Project, ProjectCreate, ProjectModel, ProjectUpdate
from app.models.user import UserModel

router = APIRouter(prefix="/api/projects", tags=["Projects"])

SessionDependency = Annotated[Session, Depends(get_session)]


def get_project_or_404(
    project_id: UUID,
    session: Session,
) -> ProjectModel:
    project = session.get(ProjectModel, project_id)

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project


def get_authorized_project(
    project_id: UUID,
    session: Session,
    current_user: UserModel,
) -> ProjectModel:
    project = get_project_or_404(project_id, session)

    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project",
        )

    return project


def get_owner_or_422(owner_id: UUID, session: Session) -> UserModel:
    owner = session.get(UserModel, owner_id)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Owner not found",
        )

    return owner


@router.get("")
def get_projects(
    session: SessionDependency,
    current_user: CurrentActiveUserDependency,
) -> dict[str, object]:
    statement = select(ProjectModel).order_by(ProjectModel.created_at)
    if current_user.role != "admin":
        statement = statement.where(ProjectModel.owner_id == current_user.id)
    projects = list(session.exec(statement).all())

    return {
        "items": projects,
        "count": len(projects),
    }


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    session: SessionDependency,
    current_user: CurrentActiveUserDependency,
) -> ProjectModel:
    if current_user.role != "admin" and project.owner_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to assign project ownership",
        )

    owner_id = project.owner_id or current_user.id
    owner = get_owner_or_422(owner_id, session)
    new_project = ProjectModel(
        name=project.name,
        description=project.description,
        owner=owner.full_name,
        owner_id=owner.id,
        status=project.status,
    )

    session.add(new_project)
    session.commit()
    session.refresh(new_project)

    return new_project


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: UUID,
    session: SessionDependency,
    current_user: CurrentActiveUserDependency,
) -> ProjectModel:
    return get_authorized_project(project_id, session, current_user)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    session: SessionDependency,
    current_user: CurrentActiveUserDependency,
) -> ProjectModel:
    project = get_authorized_project(project_id, session, current_user)
    update_data = project_update.model_dump(exclude_unset=True)

    if "owner_id" in update_data:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign project ownership",
            )

        owner_id = update_data.pop("owner_id")
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Owner not found",
            )

        owner = get_owner_or_422(owner_id, session)
        project.owner_id = owner.id
        project.owner = owner.full_name

    project.sqlmodel_update(update_data)
    session.add(project)
    session.commit()
    session.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    session: SessionDependency,
    current_user: CurrentActiveUserDependency,
) -> Response:
    project = get_authorized_project(project_id, session, current_user)

    session.delete(project)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
