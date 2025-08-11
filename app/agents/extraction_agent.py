from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from langchain.prompts import ChatPromptTemplate

try:
    from langchain_openai import ChatOpenAI  # Newer package
except Exception:
    try:
        from langchain.chat_models import ChatOpenAI  # Backward compat
    except Exception:
        ChatOpenAI = None  # type: ignore

from .base import Agent
from ..config.settings import settings
from ..core.vector_store import VectorStore
from ..core.schema_enums import get_allowed_enums


EXTRACTION_PROMPT = """
You are an expert FCRA compliance researcher. Using the provided context passages, extract values for each field in the FCRA Compliance Matrix schema v1.
- Use only allowed enum values. If unknown or not found, set null.
- Do not change jurisdiction_code or jurisdiction_type.
- Include citations with URLs and page anchors for each populated field.
Return a JSON object following the schema strictly.

Jurisdiction: {jurisdiction}
Allowed enums: {allowed_enums}

Context:
{context}
"""


class ExtractionAgent(Agent):
    def __init__(self, vector_store: VectorStore):
        super().__init__("extraction_agent")
        self.vector_store = vector_store
        self.llm = None
        if settings.openai_api_key and ChatOpenAI is not None:
            # Only initialize live LLM when API is configured
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key if hasattr(ChatOpenAI, "api_key") else None,  # type: ignore
                    base_url=settings.openai_base_url if hasattr(ChatOpenAI, "base_url") else None,  # type: ignore
                    model=settings.openai_model,
                    temperature=0.0,
                )
            except Exception:
                self.llm = None

    def _retrieve_context(self, jurisdiction: str) -> str:
        docs = self.vector_store.similarity_search(jurisdiction, k=6, filter={"jurisdiction_tags": jurisdiction})
        chunks: List[str] = []
        for d in docs:
            meta = d.metadata or {}
            chunks.append(f"Source: {meta.get('url')}\nTitle: {meta.get('title')}\n---\n{d.page_content[:1500]}")
        return "\n\n".join(chunks)

    def _allowed_enums(self) -> Dict[str, List[str]]:
        return get_allowed_enums()

    def run(self, jurisdiction: str, schema_skeleton: Dict[str, Any]):
        context = self._retrieve_context(jurisdiction)
        prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
        message = prompt.format_messages(
            jurisdiction=jurisdiction,
            allowed_enums=json.dumps(self._allowed_enums()),
            context=context,
        )
        if self.llm is None:
            # Offline mode: return skeleton only
            data = dict(schema_skeleton)
            data["last_updated"] = datetime.now(UTC).date().isoformat()
            return data

        response = self.llm.invoke(message)
        try:
            data = json.loads(response.content)
        except Exception:
            data = dict(schema_skeleton)
        data["last_updated"] = datetime.now(UTC).date().isoformat()
        return data
