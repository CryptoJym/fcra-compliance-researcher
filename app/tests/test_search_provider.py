from __future__ import annotations

from app.core.search import get_default_search_provider, NullSearchProvider


def test_null_search_provider(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    provider = get_default_search_provider()
    assert isinstance(provider, NullSearchProvider)
    assert provider.search("anything") == []
