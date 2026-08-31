"""Application settings loaded from the environment."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ASYNC_SAFE_PREFIX = "postgresql+psycopg://"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "gym-tracker"
    debug: bool = False
    default_language: str = "en"
    database_url: str = "postgresql+psycopg://gym:gym@localhost:5432/gym"

    @field_validator("database_url")
    @classmethod
    def _normalize_driver(cls, value: str) -> str:
        """Force the psycopg (v3) driver.

        Managed providers such as Render hand out plain ``postgresql://`` (or the
        legacy ``postgres://``) URLs; SQLAlchemy would otherwise pick psycopg2.
        """
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return _ASYNC_SAFE_PREFIX + value[len(prefix) :]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
