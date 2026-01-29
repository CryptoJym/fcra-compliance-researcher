from __future__ import annotations

from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from ..core.secrets import get_default_provider


class Settings(BaseSettings):
    def __init__(self, **values):
        # Load secrets first to allow defaults
        sp = get_default_provider()
        # seed env if missing
        def seed(name: str, val: str | None):
            if val and not os.environ.get(name):
                os.environ[name] = val
        seed("GITHUB_TOKEN", sp.get("GITHUB_TOKEN"))
        seed("GITHUB_REPO", sp.get("GITHUB_REPO"))
        seed("GOOGLE_API_KEY", sp.get("GOOGLE_API_KEY"))
        seed("GOOGLE_CSE_ID", sp.get("GOOGLE_CSE_ID"))
        seed("OPENAI_API_KEY", sp.get("OPENAI_API_KEY"))
        seed("OPENAI_BASE_URL", sp.get("OPENAI_BASE_URL"))
        seed("PERPLEXITY_API_KEY", sp.get("PERPLEXITY_API_KEY"))
        super().__init__(**values)
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
    enable_live_llm: bool = False

    dashboard_port: int = 8000
    research_scope: str = "CRA"  # FCRA or CRA
    # Tests and utilities may set these envs; accept them to avoid validation errors
    project_root_override: str | None = None  # maps from PROJECT_ROOT_OVERRIDE
    dash_auth_disabled: bool = False  # maps from DASH_AUTH_DISABLED

    # Throttling
    requests_per_second: int | None = 2

    # Vector store retention (days). If set, purge documents older than N days based on metadata.ingested_at
    vector_retention_days: int | None = None

    # Vector doc store persistence for maintenance/reindex (JSONL). When disabled, reindex falls back to in-memory where possible
    vector_doc_store_enabled: bool = True
    vector_doc_store_path: str | None = None


settings = Settings()
