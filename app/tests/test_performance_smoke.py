from __future__ import annotations

import time
from pathlib import Path

from app.core.vector_store import VectorStore


def test_vector_add_and_search_smoke(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VECTOR_RETENTION_DAYS", "0")
    vs = VectorStore(index_path=str(tmp_path / "vec"))
    vs.load()
    start = time.perf_counter()
    vs.add_texts(["alpha", "beta", "gamma"])
    res = vs.similarity_search("alp", k=1)
    elapsed = time.perf_counter() - start
    assert len(res) >= 1
    # Under 1s in CI/dev
    assert elapsed < 1.0


