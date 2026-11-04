import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "finflow-processor")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL Database Connection String
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finflow_db",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
