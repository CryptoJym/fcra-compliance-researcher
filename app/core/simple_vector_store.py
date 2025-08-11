from __future__ import annotations

from typing import List, Optional

from .embeddings import LocalHashEmbeddings


class SimpleVectorStore:
    def __init__(self):
        self.embeddings = LocalHashEmbeddings()
        self._texts: List[str] = []
        self._metas: List[dict] = []
        self._vectors: List[List[float]] = []

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        metadatas = metadatas or [{} for _ in texts]
        self._texts.extend(texts)
        self._metas.extend(metadatas)
        self._vectors.extend(self.embeddings.embed_documents(texts))

    def similarity_search(self, query: str, k: int = 5, filter: Optional[dict] = None):
        qvec = self.embeddings.embed_query(query)
        scored = []
        for idx, vec in enumerate(self._vectors):
            # cosine (dot because normalized)
            score = sum(a * b for a, b in zip(qvec, vec))
            meta = self._metas[idx]
            if filter:
                ok = True
                for key, val in filter.items():
                    if meta.get(key) != val:
                        ok = False
                        break
                if not ok:
                    continue
            scored.append((score, idx))
        scored.sort(reverse=True)
        results = []
        for _, i in scored[:k]:
            # unify interface with langchain Document
            doc = type("Doc", (), {})()
            doc.page_content = self._texts[i]
            doc.metadata = self._metas[i]
            results.append(doc)
        return results
