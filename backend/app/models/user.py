from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False),
    )
    full_name: str
    hashed_password: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserRegister(SQLModel):
    email: EmailStr
    full_name: str = Field(min_length=1)
    password: str = Field(min_length=8)


class UserLogin(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)


class User(SQLModel):
    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str
