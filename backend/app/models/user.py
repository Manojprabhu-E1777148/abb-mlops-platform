from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, String
from sqlmodel import Field, SQLModel


class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'member')", name="ck_users_role"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False),
    )
    full_name: str
    password_hash: str
    role: Literal["admin", "member"] = Field(
        default="member",
        sa_column=Column(String, nullable=False, server_default="member"),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="1"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserRegister(SQLModel):
    email: EmailStr
    full_name: str = Field(min_length=1)
    password: str = Field(min_length=12)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: EmailStr) -> str:
        return str(email).lower()


class User(SQLModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["admin", "member"]
    is_active: bool
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str
