from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from time import sleep

from ..config.settings import settings

from .base import Agent
from ..config.settings import settings
from ..core.logger import setup_logger
from ..core.vector_store import VectorStore
from ..core.search import get_default_search_provider


@dataclass
class SourceDocument:
    url: str
    title: str
    published_at: Optional[str]
    content: str
    jurisdiction_tags: List[str]
    snippet: Optional[str] = None


class SourcingAgent(Agent):
    def __init__(self, vector_store: VectorStore):
        super().__init__("sourcing_agent")
        self.vector_store = vector_store
        self.logger = setup_logger("sourcing_agent")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=6))
    def _fetch(self, url: str) -> Optional[str]:
        try:
            # Simple rate limit
            if settings.requests_per_second:
                sleep(1.0 / max(1, settings.requests_per_second))
            resp = httpx.get(url, timeout=20)
            if resp.status_code == 200:
                return resp.text
            raise RuntimeError(f"status={resp.status_code}")
        except Exception as e:
            self.logger.error(f"fetch error {url}: {e}")
            raise

    def _parse_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text("\n", strip=True)

    def _metadoc(self, doc: SourceDocument) -> Dict:
        return {
            "url": doc.url,
            "title": doc.title,
            "published_at": doc.published_at,
            "jurisdiction_tags": doc.jurisdiction_tags,
            "ingested_at": datetime.now(UTC).isoformat(),
        }

    def add_to_vector(self, docs: List[SourceDocument]) -> None:
        texts = [d.content for d in docs]
        metadatas = [self._metadoc(d) for d in docs]
        self.vector_store.add_texts(texts, metadatas)

    def search_and_collect(self, jurisdiction: str, queries: List[str]) -> List[SourceDocument]:
        results: List[SourceDocument] = []
        provider = get_default_search_provider()
        # Expand: for non-URL queries, use provider to find candidate URLs
        expanded_urls: List[str] = []
        for q in queries:
            if q.startswith("http"):
                expanded_urls.append(q)
            else:
                hits = provider.search(q, num_results=5)
                expanded_urls.extend([h.url for h in hits if h.url])
        # Deduplicate
        seen = set()
        for url in expanded_urls:
            if url in seen:
                continue
            seen.add(url)
            html = self._fetch(url)
            if not html:
                continue
            text = self._parse_html(html)
            title = url.split("//")[-1]
            snippet = text[:500]
            results.append(
                SourceDocument(
                    url=url,
                    title=title,
                    published_at=None,
                    content=text,
                    jurisdiction_tags=[jurisdiction],
                    snippet=snippet,
                )
            )
        if results:
            self.add_to_vector(results)
        return results

    def run(self, jurisdiction: str, queries: List[str]):
        docs = self.search_and_collect(jurisdiction, queries)
        return {"num_docs": len(docs)}
