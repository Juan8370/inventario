from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignorar variables extra en .env
    )

    # App
    APP_NAME: str = Field(default="Sistema de Inventario")
    APP_DESCRIPTION: str = Field(default="API para gestión de inventario")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")  # development | production | test

    # CORS
    ALLOWED_ORIGINS: List[AnyHttpUrl] | List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./inventario.db")

    # Auth
    SECRET_KEY: str = Field(default="change_this_secret_key_in_production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    # Seed
    SEED_DEV_ADMIN: bool = Field(default=False)

    # Normalize comma-separated strings into list for ALLOWED_ORIGINS
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _normalize_origins(cls, v):  # type: ignore[override]
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
