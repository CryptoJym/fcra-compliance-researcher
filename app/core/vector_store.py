from __future__ import annotations

from pathlib import Path
from typing import List, Optional

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
        if api_key and OpenAIEmbeddings is not None:
            self.embeddings = OpenAIEmbeddings(
                api_key=api_key if hasattr(OpenAIEmbeddings, "api_key") else api_key,  # type: ignore
                openai_api_key=api_key if hasattr(OpenAIEmbeddings, "openai_api_key") else None,  # type: ignore
                model="text-embedding-3-large",
                base_url=base_url if hasattr(OpenAIEmbeddings, "base_url") else None,  # type: ignore
                openai_api_base=base_url if hasattr(OpenAIEmbeddings, "openai_api_base") else None,  # type: ignore
            )
        else:
            # Offline deterministic embeddings for tests/dev
            self.embeddings = LocalHashEmbeddings()
        self._store = None

    def load(self) -> None:
        if not self._use_faiss:
            self._store = SimpleVectorStore()
            return
        # FAISS path
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
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(self.index_path))  # type: ignore

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        if self._store is None:
            self.load()
        assert self._store is not None
        if self._use_faiss:
            self._store.add_texts(texts=texts, metadatas=metadatas)  # type: ignore
        else:
            self._store.add_texts(texts=texts, metadatas=metadatas)
        self.save()

    def similarity_search(self, query: str, k: int = 5, filter: Optional[dict] = None):
        if self._store is None:
            self.load()
        assert self._store is not None
        return self._store.similarity_search(query, k=k, filter=filter)
