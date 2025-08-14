from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

from .vector_store import VectorStore
from ..config.settings import settings


class QdrantUnavailable(Exception):
    pass


def _get_qdrant_client():
    try:
        from qdrant_client import QdrantClient  # type: ignore
    except Exception as e:
        raise QdrantUnavailable(f"qdrant-client not installed: {e}")
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url)


def _get_qdrant_store(client):
    try:
        from langchain_qdrant import QdrantVectorStore  # type: ignore
    except Exception as e:
        raise QdrantUnavailable(f"langchain-qdrant not installed: {e}")
    embedding = _get_embeddings()
    collection = os.getenv("QDRANT_COLLECTION", "fcra_compliance_db")
    return QdrantVectorStore(client=client, collection_name=collection, embedding=embedding)


def _get_embeddings():
    # Prefer Ollama embeddings when available; otherwise fall back to deterministic local hash embeddings
    try:
        from langchain_ollama import OllamaEmbeddings  # type: ignore

        model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        return OllamaEmbeddings(model=model)
    except Exception:
        # Fallback: reuse LocalHashEmbeddings from existing code
        from .embeddings import LocalHashEmbeddings

        return LocalHashEmbeddings()


def _fallback_store() -> VectorStore:
    return VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def upsert_docs(docs: List[Dict[str, Any]]) -> None:
    """Upsert documents into Qdrant with metadata. Falls back to local VectorStore when unavailable."""
    # First try Qdrant
    use_qdrant = True
    try:
        client = _get_qdrant_client()
        store = _get_qdrant_store(client)
    except QdrantUnavailable:
        use_qdrant = False

    texts: List[str] = []
    metas: List[dict] = []
    for d in docs:
        text = d.get("text", "")
        meta = {
            "source": d.get("source"),
            "jurisdiction": d.get("jurisdiction"),
            "citation": d.get("citation"),
        }
        texts.append(text)
        metas.append(meta)

    if use_qdrant:
        try:
            lang_docs = [{"page_content": t, "metadata": m} for t, m in zip(texts, metas)]
            store.add_documents(lang_docs)  # type: ignore[attr-defined]
            return
        except Exception:
            # Fall through to local store
            pass

    # Fallback: local VectorStore (FAISS or in-memory)
    try:
        vs = _fallback_store()
        vs.add_texts(texts, metas)
    except Exception:
        # Best-effort; avoid raising in main pipeline
        pass


def _to_qdrant_filter(filters: Optional[Dict[str, Any]]):
    if not filters:
        return None
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore

        return Filter(
            must=[FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
        )
    except Exception:
        return None


def retrieve(query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Similarity search. Prefers Qdrant; falls back to local VectorStore when unavailable."""
    # Try Qdrant first
    try:
        client = _get_qdrant_client()
        store = _get_qdrant_store(client)
        q_filter = _to_qdrant_filter(filters)
        try:
            results = store.similarity_search(query, k=k, filter=q_filter)  # type: ignore[arg-type]
        except Exception:
            results = []
        normalized: List[Dict[str, Any]] = []
        for r in results:
            normalized.append({"text": getattr(r, "page_content", ""), "meta": getattr(r, "metadata", {})})
        return normalized
    except QdrantUnavailable:
        pass

    # Fallback: local VectorStore
    try:
        vs = _fallback_store()
        docs = vs.similarity_search(query, k=k, filter=filters)
        normalized: List[Dict[str, Any]] = []
        for r in docs:
            normalized.append({"text": getattr(r, "page_content", ""), "meta": getattr(r, "metadata", {})})
        return normalized
    except Exception:
        return []


