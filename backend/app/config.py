"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://cancer360:localdev@localhost:5432/cancer360"
    database_url_sync: str = "postgresql://cancer360:localdev@localhost:5432/cancer360"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Application
    app_name: str = "Cancer 360"
    app_version: str = "0.1.0"
    trust_code: str = "RYJ"
    trust_name: str = "Imperial College Healthcare NHS Trust"
    debug: bool = True

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
