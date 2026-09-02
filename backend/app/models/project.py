from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import UserModel


class ProjectModel(SQLModel, table=True):
    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str
    owner: str
    owner_id: UUID = Field(foreign_key="users.id", nullable=False)
    status: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    owner_user: "UserModel" = Relationship(back_populates="projects")


class ProjectCreate(SQLModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=10)
    status: Literal["draft", "active", "archived"] = "draft"
    owner_id: UUID | None = None


class ProjectUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=3)
    description: str | None = Field(default=None, min_length=10)
    status: Literal["draft", "active", "archived"] | None = None
    owner_id: UUID | None = None


class Project(SQLModel):
    id: UUID
    name: str
    description: str
    owner: str
    owner_id: UUID
    status: str
    created_at: datetime
