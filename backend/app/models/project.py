from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class ProjectModel(SQLModel, table=True):
    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str
    owner: str
    status: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectCreate(SQLModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=10)
    owner: str = Field(min_length=2)
    status: Literal["draft", "active", "archived"] = "draft"


class ProjectUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=3)
    description: str | None = Field(default=None, min_length=10)
    owner: str | None = Field(default=None, min_length=2)
    status: Literal["draft", "active", "archived"] | None = None


class Project(SQLModel):
    id: UUID
    name: str
    description: str
    owner: str
    status: str
    created_at: datetime
