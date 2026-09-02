from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import (
    CurrentUserDependency,
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import get_session
from app.models.user import Token, User, UserLogin, UserModel, UserRegister

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user_register: UserRegister, session: SessionDependency) -> UserModel:
    existing_user = session.exec(
        select(UserModel).where(UserModel.email == user_register.email)
    ).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = UserModel(
        email=user_register.email,
        full_name=user_register.full_name,
        hashed_password=hash_password(user_register.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login_user(user_login: UserLogin, session: SessionDependency) -> Token:
    user = session.exec(
        select(UserModel).where(UserModel.email == user_login.email)
    ).first()
    if user is None or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.id), token_type="bearer")


@router.get("/me", response_model=User)
def get_me(current_user: CurrentUserDependency) -> UserModel:
    return current_user
