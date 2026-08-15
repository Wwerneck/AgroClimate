import os
from functools import lru_cache
from pathlib import Path

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal local environments
    BaseSettings = object  # type: ignore[assignment]
    SettingsConfigDict = None  # type: ignore[assignment]

    def Field(default):  # type: ignore[no-redef]
        return default


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and .env."""

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agroclimate"
    postgres_user: str = "agroclimate"
    postgres_password: str = "agroclimate"

    api_timeout: float = 20
    api_retries: int = 3
    api_retry_backoff_seconds: float = 2
    initial_ingestion_date: str = "2026-08-01"
    data_dir: Path = Field(default=Path("data"))
    log_level: str = "INFO"

    def __init__(self) -> None:
        if SettingsConfigDict is not None:
            super().__init__()
            return
        self.postgres_host = os.getenv("POSTGRES_HOST", self.postgres_host)
        self.postgres_port = int(os.getenv("POSTGRES_PORT", str(self.postgres_port)))
        self.postgres_db = os.getenv("POSTGRES_DB", self.postgres_db)
        self.postgres_user = os.getenv("POSTGRES_USER", self.postgres_user)
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", self.postgres_password)
        self.api_timeout = float(os.getenv("API_TIMEOUT", str(self.api_timeout)))
        self.api_retries = int(os.getenv("API_RETRIES", str(self.api_retries)))
        self.api_retry_backoff_seconds = float(
            os.getenv("API_RETRY_BACKOFF_SECONDS", str(self.api_retry_backoff_seconds))
        )
        self.initial_ingestion_date = os.getenv("INITIAL_INGESTION_DATE", self.initial_ingestion_date)
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.data_dir)))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)

    @property
    def bronze_dir(self) -> Path:
        return self.data_dir / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.data_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.data_dir / "gold"

    @property
    def quarantine_dir(self) -> Path:
        return self.data_dir / "quarantine"

    @property
    def metadata_dir(self) -> Path:
        return self.data_dir / "metadata"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} dbname={self.postgres_db} "
            f"user={self.postgres_user} password={self.postgres_password}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
