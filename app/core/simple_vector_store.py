from __future__ import annotations

from typing import List, Optional, Dict, Any, Iterator, Tuple

from .embeddings import LocalHashEmbeddings


class SimpleVectorStore:
    def __init__(self):
        self.embeddings = LocalHashEmbeddings()
        self._texts: List[str] = []
        self._metas: List[dict] = []
        self._vectors: List[List[float]] = []

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        metadatas = metadatas or [{} for _ in texts]
        # Dedupe by URL if provided, else by content hash surrogate
        seen_keys = set()
        new_texts: List[str] = []
        new_metas: List[dict] = []
        for text, meta in zip(texts, metadatas):
            key = meta.get("url") or f"content::{hash(text)}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            new_texts.append(text)
            new_metas.append(meta)
        self._texts.extend(new_texts)
        self._metas.extend(new_metas)
        self._vectors.extend(self.embeddings.embed_documents(new_texts))

    def list_documents(self) -> Iterator[Tuple[int, str, dict]]:
        for i, (text, meta) in enumerate(zip(self._texts, self._metas)):
            yield i, text, meta

    def delete_indices(self, indices: List[int]) -> None:
        index_set = set(indices)
        new_texts: List[str] = []
        new_metas: List[dict] = []
        new_vectors: List[List[float]] = []
        for i, (t, m, v) in enumerate(zip(self._texts, self._metas, self._vectors)):
            if i in index_set:
                continue
            new_texts.append(t)
            new_metas.append(m)
            new_vectors.append(v)
        self._texts = new_texts
        self._metas = new_metas
        self._vectors = new_vectors

    def _metadata_matches(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        for key, val in filter.items():
            meta_val = metadata.get(key)
            if isinstance(meta_val, list):
                if val not in meta_val:
                    return False
            else:
                if meta_val != val:
                    return False
        return True

    def similarity_search(self, query: str, k: int = 5, filter: Optional[dict] = None):
        qvec = self.embeddings.embed_query(query)
        scored = []
        for idx, vec in enumerate(self._vectors):
            # cosine (dot because normalized)
            score = sum(a * b for a, b in zip(qvec, vec))
            meta = self._metas[idx]
            if filter and not self._metadata_matches(meta, filter):
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
