from __future__ import annotations

import os
from pathlib import Path

from app.core.secrets import SecretsProvider
from app.core.logger import redact_secrets


def test_secrets_provider_env_and_json(tmp_path: Path, monkeypatch):
    # Env wins
    monkeypatch.setenv("MY_TOKEN", "envval")
    sp = SecretsProvider(json_path=tmp_path / ".secrets.json", namespace="ns")
    assert sp.get("MY_TOKEN") == "envval"
    # JSON fallback
    data = {"ns": {"API_KEY": "abc123"}}
    (tmp_path / ".secrets.json").write_text(__import__("json").dumps(data))
    sp2 = SecretsProvider(json_path=tmp_path / ".secrets.json", namespace="ns")
    assert sp2.get("API_KEY") == "abc123"


def test_redact_secrets():
    msg = "user logged in api_key=secret123 token=abcd"
    red = redact_secrets(msg)
    assert "api_key=***" in red and "token=***" in red



