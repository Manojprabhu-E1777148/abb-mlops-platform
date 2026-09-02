from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.auth import CurrentUserDependency
from app.database import get_session
from app.models.project import Project, ProjectCreate, ProjectModel, ProjectUpdate
from app.models.user import UserModel

router = APIRouter(prefix="/api/projects", tags=["Projects"])

SessionDependency = Annotated[Session, Depends(get_session)]


def get_owned_project(
    project_id: UUID,
    session: Session,
    current_user: UserModel,
) -> ProjectModel:
    project = session.exec(
        select(ProjectModel).where(
            ProjectModel.id == project_id,
            ProjectModel.owner_id == current_user.id,
        )
    ).first()

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project


@router.get("")
def get_projects(
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> dict[str, object]:
    statement = (
        select(ProjectModel)
        .where(ProjectModel.owner_id == current_user.id)
        .order_by(ProjectModel.created_at)
    )
    projects = list(session.exec(statement).all())

    return {
        "items": projects,
        "count": len(projects),
    }


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> ProjectModel:
    new_project = ProjectModel(**project.model_dump(), owner_id=current_user.id)

    session.add(new_project)
    session.commit()
    session.refresh(new_project)

    return new_project


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: UUID,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> ProjectModel:
    return get_owned_project(project_id, session, current_user)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> ProjectModel:
    project = get_owned_project(project_id, session, current_user)

    project.sqlmodel_update(project_update.model_dump(exclude_unset=True))
    session.add(project)
    session.commit()
    session.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> Response:
    project = get_owned_project(project_id, session, current_user)

    session.delete(project)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
