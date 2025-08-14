from __future__ import annotations

import os


def test_retrieval_fallback_add_and_search(tmp_path, monkeypatch):
    # Ensure Qdrant is considered unavailable by unsetting URL and preventing import
    monkeypatch.delenv("QDRANT_URL", raising=False)

    # Force vector path to temp for isolation
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "index"))

    from app.core.retrieval import upsert_docs, retrieve

    docs = [
        {"text": "Anytown ordinance 123 about hiring", "source": "http://example.com/1", "jurisdiction": "city:Anytown", "citation": "Ord. 123"},
        {"text": "State preemption statute 456", "source": "http://example.com/2", "jurisdiction": "state:XY", "citation": "Stat. 456"},
    ]

    upsert_docs(docs)
    results = retrieve("hiring ordinance", k=2)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("Anytown" in (r.get("text") or "") for r in results)


def test_retrieval_filters_local(monkeypatch):
    # Use local store; ensure Qdrant paths do not interfere
    monkeypatch.delenv("QDRANT_URL", raising=False)
    from app.core.retrieval import upsert_docs, retrieve

    upsert_docs([
        {"text": "City data", "source": "s1", "jurisdiction": "city:X", "citation": "c1"},
        {"text": "State data", "source": "s2", "jurisdiction": "state:Y", "citation": "c2"},
    ])
    res_city = retrieve("data", k=5, filters={"jurisdiction": "city:X"})
    assert all(r.get("meta", {}).get("jurisdiction") == "city:X" for r in res_city)


