from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'projects.db'}"


class Settings(BaseSettings):
    database_url: str = DEFAULT_DATABASE_URL
    jwt_secret_key: str | None = None
    jwt_access_token_expire_minutes: str = "30"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()