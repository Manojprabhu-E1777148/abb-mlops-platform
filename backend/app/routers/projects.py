from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.project import Project, ProjectCreate, ProjectModel, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["Projects"])

SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("")
def get_projects(session: SessionDependency) -> dict[str, object]:
    statement = select(ProjectModel).order_by(ProjectModel.created_at)
    projects = list(session.exec(statement).all())

    return {
        "items": projects,
        "count": len(projects),
    }


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, session: SessionDependency) -> ProjectModel:
    new_project = ProjectModel(**project.model_dump())

    session.add(new_project)
    session.commit()
    session.refresh(new_project)

    return new_project


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: UUID, session: SessionDependency) -> ProjectModel:
    project = session.exec(
        select(ProjectModel).where(ProjectModel.id == project_id)
    ).first()

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    session: SessionDependency,
) -> ProjectModel:
    project = session.exec(
        select(ProjectModel).where(ProjectModel.id == project_id)
    ).first()

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.sqlmodel_update(project_update.model_dump(exclude_unset=True))
    session.add(project)
    session.commit()
    session.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, session: SessionDependency) -> Response:
    project = session.exec(
        select(ProjectModel).where(ProjectModel.id == project_id)
    ).first()

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    session.delete(project)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
