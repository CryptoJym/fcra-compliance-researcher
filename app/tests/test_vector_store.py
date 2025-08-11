from __future__ import annotations

from app.core.vector_store import VectorStore


def test_vector_store_add_and_search(tmp_path):
    vs = VectorStore(index_path=str(tmp_path / "faiss"))
    vs.load()
    vs.add_texts(["San Francisco Ban the Box ordinance applies at conditional offer stage."], metadatas=[{"jurisdiction_tags": "unified/city/san_francisco.json", "url": "http://example.com"}])
    res = vs.similarity_search("San Francisco ban the box", k=1)
    assert len(res) == 1
