from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'projects.db'}"


class Settings(BaseSettings):
    app_name: str = "ABB MLOps Platform API"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = DEFAULT_DATABASE_URL
    secret_key: str | None = None
    access_token_expire_minutes: str | None = None
    jwt_secret_key: str | None = None
    jwt_access_token_expire_minutes: str | None = None
    demo_admin_password: str | None = None
    demo_member_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()