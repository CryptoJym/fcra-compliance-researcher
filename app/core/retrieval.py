from __future__ import annotations

from typing import Any, Dict, List, Optional
import os


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


def upsert_docs(docs: List[Dict[str, Any]]) -> None:
    """Upsert documents into Qdrant with metadata. Safe no-op if Qdrant unavailable."""
    try:
        client = _get_qdrant_client()
        store = _get_qdrant_store(client)
    except QdrantUnavailable:
        # Graceful noop in environments without Qdrant
        return

    lang_docs = []
    for d in docs:
        text = d.get("text", "")
        meta = {
            "source": d.get("source"),
            "jurisdiction": d.get("jurisdiction"),
            "citation": d.get("citation"),
        }
        lang_docs.append({"page_content": text, "metadata": meta})
    try:
        store.add_documents(lang_docs)
    except Exception:
        # Best-effort; avoid raising in main pipeline
        pass


def retrieve(query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Similarity search from Qdrant. Returns [] when unavailable."""
    try:
        client = _get_qdrant_client()
        store = _get_qdrant_store(client)
    except QdrantUnavailable:
        return []

    try:
        results = store.similarity_search(query, k=k, filter=filters)
    except Exception:
        return []
    normalized: List[Dict[str, Any]] = []
    for r in results:
        normalized.append({"text": getattr(r, "page_content", ""), "meta": getattr(r, "metadata", {})})
    return normalized


