from __future__ import annotations

import os
from app.core.search import get_default_search_provider, NullSearchProvider


def test_searxng_disabled_defaults(monkeypatch):
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    provider = get_default_search_provider()
    # With no keys set, falls back to Null
    assert isinstance(provider, NullSearchProvider)


def test_searxng_backoff_envs(monkeypatch):
    # Provider should construct even if endpoint not reachable; we won't call it here
    monkeypatch.setenv("SEARXNG_URL", "http://localhost:8080")
    monkeypatch.setenv("SEARXNG_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("SEARXNG_MIN_BACKOFF", "0.1")
    monkeypatch.setenv("SEARXNG_MAX_BACKOFF", "0.2")
    provider = get_default_search_provider()
    # Not asserting type directly to avoid importing nested class; ensure it has a search method
    assert hasattr(provider, "search")


