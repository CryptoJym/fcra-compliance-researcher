from __future__ import annotations

import hashlib
from typing import List


class LocalHashEmbeddings:
    """
    Lightweight, deterministic embedding for tests and offline use.
    Generates a fixed-size vector by hashing whitespace-separated tokens.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        tokens = text.split()
        for token in tokens:
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t or "") for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text or "")
