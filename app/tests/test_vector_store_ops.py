from __future__ import annotations

from datetime import datetime, UTC, timedelta

from app.core.vector_store import VectorStore
from app.config.settings import settings


def test_vector_store_retention_and_reindex(tmp_path, monkeypatch):
    # Set retention to 1 day
    monkeypatch.setenv("VECTOR_RETENTION_DAYS", "1")
    settings.model_rebuild()

    vs = VectorStore(index_path=str(tmp_path / "faiss"))
    vs.load()

    old_time = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    new_time = datetime.now(UTC).isoformat()
    docs = [
        ("old doc", {"url": "http://a", "ingested_at": old_time, "jurisdiction_tags": ["unified/x"]}),
        ("new doc", {"url": "http://b", "ingested_at": new_time, "jurisdiction_tags": ["unified/y"]}),
        ("dup doc", {"url": "http://b", "ingested_at": new_time, "jurisdiction_tags": ["unified/y"]}),
    ]
    vs.add_texts([d[0] for d in docs], [d[1] for d in docs])

    # Reindex should drop the expired and the duplicate
    vs.reindex()

    res_all = vs.similarity_search("doc", k=10)
    # Only the new unique doc should remain
    assert any("new doc" in r.page_content for r in res_all)
    assert not any("old doc" in r.page_content for r in res_all)

    # Tag filter still works
    res_tag = vs.similarity_search("doc", k=10, filter={"jurisdiction_tags": "unified/y"})
    assert len(res_tag) >= 1


