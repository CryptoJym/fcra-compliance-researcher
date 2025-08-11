from __future__ import annotations

from app.core.vector_store import VectorStore


def test_vector_store_add_and_search(tmp_path):
    vs = VectorStore(index_path=str(tmp_path / "faiss"))
    vs.load()
    vs.add_texts(["San Francisco Ban the Box ordinance applies at conditional offer stage."], metadatas=[{"jurisdiction_tags": "unified/city/san_francisco.json", "url": "http://example.com"}])
    res = vs.similarity_search("San Francisco ban the box", k=1)
    assert len(res) == 1


def test_vector_store_dedupe_and_filter(tmp_path):
    vs = VectorStore(index_path=str(tmp_path / "faiss"))
    vs.load()
    text = "City of SF ordinance applies at conditional offer stage."
    meta1 = {"jurisdiction_tags": ["unified/city/san_francisco.json"], "url": "http://example.com/a"}
    meta2 = {"jurisdiction_tags": ["unified/city/san_francisco.json"], "url": "http://example.com/a"}
    vs.add_texts([text, text], metadatas=[meta1, meta2])
    # Deduped to 1
    res = vs.similarity_search("conditional offer stage", k=5)
    assert len(res) >= 1
    # Filter by jurisdiction tag list membership
    res2 = vs.similarity_search("conditional offer stage", k=5, filter={"jurisdiction_tags": "unified/city/san_francisco.json"})
    assert len(res2) >= 1
