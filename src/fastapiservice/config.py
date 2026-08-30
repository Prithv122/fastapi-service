"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Minimum acceptable reward/risk ratio for a trade setup to be accepted.
    min_risk_reward_ratio: float = 1.5

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Neon (and most providers) hand out a bare `postgres(ql)://` URL, which
        SQLAlchemy defaults to the psycopg2 dialect. Normalize to the psycopg 3 driver
        this project actually installs, so a stock Neon connection string just works.
        """
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
