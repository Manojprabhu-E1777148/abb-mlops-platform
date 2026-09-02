from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/projects", tags=["Projects"])

projects: list["Project"] = []


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=10)
    owner: str = Field(min_length=2)
    status: Literal["draft", "active", "archived"] = "draft"


class Project(BaseModel):
    id: UUID
    name: str
    description: str
    owner: str
    status: str
    created_at: datetime


@router.get("")
async def get_projects() -> dict[str, object]:
    return {
        "items": projects,
        "count": len(projects),
    }


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate) -> Project:
    new_project = Project(
        id=uuid4(),
        name=project.name,
        description=project.description,
        owner=project.owner,
        status=project.status,
        created_at=datetime.now(timezone.utc),
    )
    projects.append(new_project)
    return new_project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID) -> Project:
    for project in projects:
        if project.id == project_id:
            return project

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID) -> Response:
    for index, project in enumerate(projects):
        if project.id == project_id:
            projects.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
