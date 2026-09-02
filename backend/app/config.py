from app.core.config import settings

JWT_ALGORITHM = "HS256"


def get_jwt_secret_key() -> str:
    secret_key = settings.secret_key or settings.jwt_secret_key
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable must be configured")

    return secret_key


def get_jwt_access_token_expire_minutes() -> int:
    value = (
        settings.access_token_expire_minutes
        or settings.jwt_access_token_expire_minutes
        or "30"
    )

    try:
        expire_minutes = int(value)
    except ValueError as error:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
        ) from error

    if expire_minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

    return expire_minutes
