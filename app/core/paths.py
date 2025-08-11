from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_directories() -> None:
    for p in [
        project_root() / ".vector",
        project_root() / "research_inputs",
        project_root() / "logs",
    ]:
        p.mkdir(parents=True, exist_ok=True)
