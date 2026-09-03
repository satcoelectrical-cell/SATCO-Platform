from functools import lru_cache
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SATCO Platform"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PLATFORM_BOOTSTRAP_KEY: str = ""
    ACCOUNT_ACTIVATION_EXPIRE_HOURS: int = 24
    ACCOUNT_RESET_EXPIRE_MINUTES: int = 30

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "satco_runtime"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "satco"
    MIGRATION_DATABASE_ROLE: str = "satco"
    TECHNICAL_REPORT_PERSISTENCE_ENABLED: bool = False
    DISCIPLINE_PACKAGE_PERSISTENCE_ENABLED: bool = False
    COPILOT_ENABLED: bool = False
    COPILOT_PROVIDER_ENDPOINT: str = ""
    COPILOT_PROVIDER_API_KEY: str = ""
    COPILOT_PROVIDER_TIMEOUT_SECONDS: float = 30.0

    SATCO_ENVIRONMENT: str = "development"
    SATCO_RELEASE_MANIFEST_PATH: str = ""
    SATCO_PUBLIC_URL: str = ""
    SATCO_TRUSTED_HOSTS: str = ""
    SATCO_ALLOWED_ORIGINS: str = ""
    SATCO_EXPECTED_ALEMBIC_HEAD: str = ""
    SATCO_PERSISTENCE_GUARD_VERSION: str = ""
    SATCO_OBJECT_HEALTH_URL: str = ""
    SATCO_OBJECT_HEALTH_CA_FILE: str = ""
    SUPPORTING_FILE_OBJECT_ENDPOINT: str = ""
    SUPPORTING_FILE_OBJECT_BUCKET: str = ""
    SUPPORTING_FILE_OBJECT_REGION: str = ""
    SUPPORTING_FILE_OBJECT_ACCESS_KEY_FILE: str = ""
    SUPPORTING_FILE_OBJECT_SECRET_KEY_FILE: str = ""
    SUPPORTING_FILE_SCANNER_ENDPOINT: str = ""
    SUPPORTING_FILE_SCANNER_TOKEN_FILE: str = ""
    SATCO_BACKUP_POLICY_ID: str = ""
    SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE: str = ""
    SATCO_MONITORING_TOKEN: str = ""
    SATCO_MONITORING_TOKEN_FILE: str = ""
    SATCO_BOOTSTRAP_ENABLED: bool = False
    SATCO_BOOTSTRAP_WINDOW_END: str = ""
    SATCO_OPS_MODE_FILE: str = ""
    SATCO_OPS_MODE_HMAC_KEY_FILE: str = ""
    SECRET_KEY_FILE: str = ""
    PLATFORM_BOOTSTRAP_KEY_FILE: str = ""
    DATABASE_PASSWORD_FILE: str = ""

    @model_validator(mode="after")
    def load_application_secret_files(self) -> "Settings":
        """Resolve application-consumed secrets once without exposing paths."""

        if self.SECRET_KEY_FILE:
            self.SECRET_KEY = self._secret_from_file(
                self.SECRET_KEY_FILE, self.SECRET_KEY
            )
        if self.PLATFORM_BOOTSTRAP_KEY_FILE:
            self.PLATFORM_BOOTSTRAP_KEY = self._secret_from_file(
                self.PLATFORM_BOOTSTRAP_KEY_FILE,
                self.PLATFORM_BOOTSTRAP_KEY,
            )
        return self

    @staticmethod
    def _secret_from_file(path: str, fallback: str) -> str:
        if not path:
            return fallback
        value = Path(path).read_text(encoding="utf-8").strip()
        return value

    def resolved_secret_key(self) -> str:
        return self._secret_from_file(self.SECRET_KEY_FILE, self.SECRET_KEY)

    def resolved_bootstrap_key(self) -> str:
        return self._secret_from_file(
            self.PLATFORM_BOOTSTRAP_KEY_FILE, self.PLATFORM_BOOTSTRAP_KEY
        )

    def resolved_monitoring_token(self) -> str:
        return self._secret_from_file(
            self.SATCO_MONITORING_TOKEN_FILE,
            self.SATCO_MONITORING_TOKEN,
        )

    def resolved_supporting_file_scanner_token(self) -> str:
        return self._secret_from_file(self.SUPPORTING_FILE_SCANNER_TOKEN_FILE, "")

    def resolved_supporting_file_object_access_key(self) -> str:
        return self._secret_from_file(self.SUPPORTING_FILE_OBJECT_ACCESS_KEY_FILE, "")

    def resolved_supporting_file_object_secret_key(self) -> str:
        return self._secret_from_file(self.SUPPORTING_FILE_OBJECT_SECRET_KEY_FILE, "")

    def production_validation_errors(self) -> list[str]:
        """Return safe categories only; callers must not expose raw configuration."""

        if self.SATCO_ENVIRONMENT != "production":
            return []
        errors: list[str] = []
        secret_key = self.resolved_secret_key()
        if len(secret_key) < 32 or secret_key == "CHANGE_THIS_SECRET_KEY":
            errors.append("signing_secret")
        if not self.SATCO_RELEASE_MANIFEST_PATH:
            errors.append("release_manifest")
        if not self.SATCO_PUBLIC_URL.startswith("https://"):
            errors.append("public_url")
        for value, name in (
            (self.SATCO_TRUSTED_HOSTS, "trusted_hosts"),
            (self.SATCO_ALLOWED_ORIGINS, "allowed_origins"),
        ):
            if not value or "*" in value:
                errors.append(name)
        if not self.SATCO_EXPECTED_ALEMBIC_HEAD:
            errors.append("expected_head")
        if not self.SATCO_PERSISTENCE_GUARD_VERSION:
            errors.append("persistence_guards")
        if (
            not self.SATCO_OBJECT_HEALTH_URL.startswith("https://")
            or not self.SATCO_OBJECT_HEALTH_CA_FILE
        ):
            errors.append("object_health")
        if not self.SATCO_BACKUP_POLICY_ID or not self.SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE:
            errors.append("backup_policy")
        if not self.SATCO_OPS_MODE_FILE or not self.SATCO_OPS_MODE_HMAC_KEY_FILE:
            errors.append("ops_mode")
        if len(self.resolved_monitoring_token()) < 32:
            errors.append("monitoring_principal")
        try:
            scanner_token = self.resolved_supporting_file_scanner_token()
        except OSError:
            scanner_token = ""
        if (
            not self.SUPPORTING_FILE_SCANNER_ENDPOINT.startswith("https://")
            or len(scanner_token) < 32
        ):
            errors.append("supporting_file_scanner")
        try:
            object_access_key = self.resolved_supporting_file_object_access_key()
            object_secret_key = self.resolved_supporting_file_object_secret_key()
        except OSError:
            object_access_key = object_secret_key = ""
        if (
            not self.SUPPORTING_FILE_OBJECT_ENDPOINT.startswith("https://")
            or not self.SUPPORTING_FILE_OBJECT_BUCKET
            or not self.SUPPORTING_FILE_OBJECT_REGION
            or not object_access_key
            or len(object_secret_key) < 16
        ):
            errors.append("supporting_file_object_store")
        if self.SATCO_BOOTSTRAP_ENABLED:
            bootstrap = self.resolved_bootstrap_key()
            if len(bootstrap) < 32 or not self.SATCO_BOOTSTRAP_WINDOW_END:
                errors.append("bootstrap")
        if self.COPILOT_ENABLED and (
            not self.COPILOT_PROVIDER_ENDPOINT.startswith("https://")
            or not self.COPILOT_PROVIDER_API_KEY
        ):
            errors.append("copilot")
        return errors

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
