from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ApiError(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ApiError
    trace_id: str