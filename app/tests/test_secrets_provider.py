from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.secrets import SecretsProvider, get_default_provider
from app.config.settings import Settings


def test_secrets_provider_json_and_env_precedence(tmp_path: Path, monkeypatch):
    content = {"GITHUB_TOKEN": "from_json", "default": {"OPENAI_API_KEY": "from_ns"}}
    p = tmp_path / ".secrets.json"
    p.write_text(json.dumps(content))
    sp = SecretsProvider(json_path=p)
    assert sp.get("GITHUB_TOKEN") == "from_json"
    # env overrides
    monkeypatch.setenv("GITHUB_TOKEN", "from_env")
    assert sp.get("GITHUB_TOKEN") == "from_env"
    # namespaced lookup (ensure host env does not interfere)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    sp2 = SecretsProvider(json_path=p, namespace="default")
    assert sp2.get("OPENAI_API_KEY") == "from_ns"


def test_settings_resolves_secrets_from_json(tmp_path: Path, monkeypatch):
    content = {"GITHUB_TOKEN": "gh_token", "GOOGLE_API_KEY": "g_key", "GOOGLE_CSE_ID": "cse", "OPENAI_API_KEY": "okey", "PERPLEXITY_API_KEY": "pkey"}
    p = tmp_path / ".secrets.json"
    p.write_text(json.dumps(content))
    monkeypatch.setenv("SECRETS_JSON_PATH", str(p))
    # ensure env not set for these
    for k in ["GITHUB_TOKEN", "GOOGLE_API_KEY", "GOOGLE_CSE_ID", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"]:
        monkeypatch.delenv(k, raising=False)
    s = Settings()
    # Values should be populated from secrets provider
    assert s.github_token == "gh_token"
    assert s.google_api_key == "g_key"
    assert s.google_cse_id == "cse"
    assert s.openai_api_key == "okey"
    assert s.perplexity_api_key == "pkey"
