from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session

from app.config import (
    JWT_ALGORITHM,
    get_jwt_access_token_expire_minutes,
    get_jwt_secret_key,
)
from app.database import get_session
from app.models.user import UserModel

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SessionDependency = Annotated[Session, Depends(get_session)]


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=get_jwt_access_token_expire_minutes()
    )
    payload = {"sub": str(user_id), "exp": expires_at}

    return jwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDependency,
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
        )
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise credentials_exception

    user = session.get(UserModel, user_id)
    if user is None:
        raise credentials_exception

    return user


CurrentUserDependency = Annotated[UserModel, Depends(get_current_user)]
