from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SATCO Platform"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "satco_runtime"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "satco"
    MIGRATION_DATABASE_ROLE: str = "satco"
    TECHNICAL_REPORT_PERSISTENCE_ENABLED: bool = False
    COPILOT_ENABLED: bool = False
    COPILOT_PROVIDER_ENDPOINT: str = ""
    COPILOT_PROVIDER_API_KEY: str = ""
    COPILOT_PROVIDER_TIMEOUT_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
