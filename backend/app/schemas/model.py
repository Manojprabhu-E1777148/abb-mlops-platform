from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


class ModelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelDetailResponse(BaseModel):
    id: UUID
    name: str
    description: str
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ModelListResponse(RootModel[list[ModelDetailResponse]]):
    pass