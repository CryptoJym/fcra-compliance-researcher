from __future__ import annotations

from pathlib import Path
import os


def project_root() -> Path:
    # Allow tests to override via env without importing settings (avoid circular deps during import time)
    override = os.getenv("PROJECT_ROOT_OVERRIDE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2]


def ensure_directories() -> None:
    for p in [
        project_root() / ".vector",
        project_root() / "research_inputs",
        project_root() / "logs",
    ]:
        p.mkdir(parents=True, exist_ok=True)
