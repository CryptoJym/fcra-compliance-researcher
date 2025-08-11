from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", env_file_encoding="utf-8")

    app_env: str = "development"
    log_level: str = "INFO"

    vector_db_path: str = ".vector/faiss_index"
    database_url: str = "sqlite:///./researcher.db"

    redis_url: str | None = None

    github_token: str | None = None
    github_repo: str | None = None
    github_default_branch: str = "main"

    google_cse_id: str | None = None
    google_api_key: str | None = None
    perplexity_api_key: str | None = None

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-oss-128b"

    dashboard_port: int = 8000

    # Throttling
    requests_per_second: int | None = 2

    # Vector store retention (days). If set, purge documents older than N days based on metadata.ingested_at
    vector_retention_days: int | None = None


settings = Settings()
