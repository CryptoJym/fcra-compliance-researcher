from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.vector_store import VectorStore


def test_vector_store_thread_safety(tmp_path):
    vs = VectorStore(index_path=str(tmp_path / "faiss"))

    def add_chunk(i: int):
        vs.add_texts([f"doc {i}"], metadatas=[{"i": i}])
        return i

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(add_chunk, i) for i in range(50)]
        results = [f.result() for f in as_completed(futs)]
    # If no exceptions and we can search, consider it ok
    res = vs.similarity_search("doc 10", k=1)
    assert len(res) == 1
