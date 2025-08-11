from __future__ import annotations

from pathlib import Path
import hashlib
from typing import List, Optional, Callable
from datetime import datetime, UTC, timedelta
from filelock import FileLock

try:
    from langchain_community.vectorstores import FAISS  # type: ignore
except Exception:
    FAISS = None  # type: ignore

try:
    import faiss as _faiss  # type: ignore
    HAS_FAISS_NATIVE = True
except Exception:
    HAS_FAISS_NATIVE = False

from .paths import ensure_directories
from .embeddings import LocalHashEmbeddings
from .simple_vector_store import SimpleVectorStore
from ..config.settings import settings
try:
    from langchain_openai import OpenAIEmbeddings  # Preferred in newer LangChain
except Exception:  # Fallback for langchain_community
    try:
        from langchain_community.embeddings import OpenAIEmbeddings  # type: ignore
    except Exception:
        OpenAIEmbeddings = None  # type: ignore


class VectorStore:
    def __init__(self, index_path: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        ensure_directories()
        self.index_path = Path(index_path)
        # Only use FAISS when the native library is available AND wrapper import exists
        self._use_faiss = bool(FAISS is not None and HAS_FAISS_NATIVE)
        self._lock = FileLock(str(self.index_path) + ".lock")
        if api_key and OpenAIEmbeddings is not None:
            # Build kwargs compatible with the installed embeddings package
            kwargs: dict = {"model": "text-embedding-3-large"}
            module_name = getattr(OpenAIEmbeddings, "__module__", "")
            if module_name.startswith("langchain_openai"):
                # Newer package
                # Newer package expects only api_key/base_url when provided
                if api_key is not None:
                    kwargs["api_key"] = api_key
                if base_url is not None:
                    kwargs["base_url"] = base_url
            else:
                # Older community wrapper
                if api_key is not None:
                    kwargs["openai_api_key"] = api_key
                if base_url is not None:
                    kwargs["openai_api_base"] = base_url
            self.embeddings = OpenAIEmbeddings(**kwargs)  # type: ignore
        else:
            # Offline deterministic embeddings for tests/dev
            self.embeddings = LocalHashEmbeddings()
        self._store = None

    def load(self) -> None:
        if not self._use_faiss:
            self._store = SimpleVectorStore()
            return
        # FAISS path
        with self._lock:
            if self.index_path.exists():
                self._store = FAISS.load_local(str(self.index_path), self.embeddings, allow_dangerous_deserialization=True)  # type: ignore
            else:
                self._store = FAISS.from_texts([""], self.embeddings)  # type: ignore
                self.save()

    def save(self) -> None:
        if not self._use_faiss:
            return
        if self._store is None:
            return
        with self._lock:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self._store.save_local(str(self.index_path))  # type: ignore

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        if self._store is None:
            self.load()
        assert self._store is not None
        # Deduplicate by URL or content hash when available
        dedup_texts: List[str] = []
        dedup_metas: List[dict] = []
        metadatas = metadatas or [{} for _ in texts]
        seen_keys = set()
        for text, meta in zip(texts, metadatas):
            url = (meta or {}).get("url")
            key = url or hashlib.sha1(text.encode("utf-8")).hexdigest()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            # Persist the dedupe key for later tooling
            meta = dict(meta or {})
            meta.setdefault("dedupe_key", key)
            dedup_texts.append(text)
            dedup_metas.append(meta)
        if self._use_faiss:
            with self._lock:
                self._store.add_texts(texts=dedup_texts, metadatas=dedup_metas)  # type: ignore
        else:
            self._store.add_texts(texts=dedup_texts, metadatas=dedup_metas)
        self.save()

    def similarity_search(self, query: str, k: int = 5, filter: Optional[dict] = None):
        if self._store is None:
            self.load()
        assert self._store is not None
        return self._store.similarity_search(query, k=k, filter=filter)

    # Retention and maintenance
    def _is_expired(self, meta: dict, now: datetime) -> bool:
        # Read from settings, but allow env override at runtime for tests
        import os
        days_env = os.getenv("VECTOR_RETENTION_DAYS")
        days = None
        if days_env:
            try:
                days = int(days_env)
            except Exception:
                days = None
        if days is None:
            days = settings.vector_retention_days
        if not days:
            return False
        ts = meta.get("ingested_at") or meta.get("timestamp")
        if not ts:
            return False
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return (now - dt) > timedelta(days=days)
        except Exception:
            return False

    def reindex(self, progress_cb: Optional[Callable[[int, int], None]] = None) -> None:
        """Rebuild the underlying index from stored texts/metadata, applying dedupe and retention.

        For FAISS, we reload from scratch to apply pruning; for SimpleVectorStore we rebuild vectors.
        """
        if self._store is None:
            self.load()
        assert self._store is not None
        # Extract current corpus
        # SimpleVectorStore: has internal lists; FAISS path: we don't have direct docs; keep as no-op
        if isinstance(self._store, SimpleVectorStore):
            texts = list(self._store._texts)  # type: ignore[attr-defined]
            metas = list(self._store._metas)  # type: ignore[attr-defined]
            now = datetime.now(UTC)
            filtered_texts: List[str] = []
            filtered_metas: List[dict] = []
            seen = set()
            total = len(texts)
            for idx, (t, m) in enumerate(zip(texts, metas)):
                key = (m or {}).get("url") or hashlib.sha1((t or "").encode("utf-8")).hexdigest()
                if key in seen:
                    continue
                if self._is_expired(m or {}, now):
                    continue
                seen.add(key)
                filtered_texts.append(t)
                filtered_metas.append(m)
                if progress_cb:
                    progress_cb(idx + 1, total)
            # Reset and rebuild
            self._store._texts = []  # type: ignore[attr-defined]
            self._store._metas = []  # type: ignore[attr-defined]
            self._store._vectors = []  # type: ignore[attr-defined]
            self._store.add_texts(filtered_texts, filtered_metas)
            self.save()
        else:
            # For FAISS: best-effort no-op for now; external persisted index lacks doc store
            self.save()
