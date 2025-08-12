from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import List, Optional

import httpx

from .logger import setup_logger

logger = setup_logger("search")


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


class SearchProvider:
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError


class GoogleCSEProvider(SearchProvider):
    def __init__(self, api_key: Optional[str], cse_id: Optional[str]):
        self.api_key = api_key
        self.cse_id = cse_id

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        if not self.api_key or not self.cse_id:
            return []
        try:
            resp = httpx.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": self.api_key, "cx": self.cse_id, "q": query, "num": min(num_results, 10)},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or []
            results: List[SearchResult] = []
            for it in items:
                results.append(
                    SearchResult(
                        url=it.get("link"),
                        title=it.get("title", ""),
                        snippet=it.get("snippet", ""),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Google CSE error: {e}")
            return []


class PerplexityProvider(SearchProvider):
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        if not self.api_key:
            return []
        try:
            # Perplexity API: simple search-like endpoint (mocked usage)
            # Using hypothetical endpoint for offline-friendly tests
            resp = httpx.post(
                "https://api.perplexity.ai/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"q": query, "k": num_results},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("results") or []
            results: List[SearchResult] = []
            for it in items:
                results.append(
                    SearchResult(
                        url=it.get("url"),
                        title=it.get("title", ""),
                        snippet=it.get("snippet", ""),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Perplexity error: {e}")
            return []


class CombinedSearchProvider(SearchProvider):
    def __init__(self, providers: List[SearchProvider]):
        self.providers = providers

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        merged: List[SearchResult] = []
        seen = set()
        for p in self.providers:
            for r in p.search(query, num_results):
                if not r.url or r.url in seen:
                    continue
                seen.add(r.url)
                merged.append(r)
                if len(merged) >= num_results:
                    return merged
        return merged

class NullSearchProvider(SearchProvider):
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        return []


def get_default_search_provider() -> SearchProvider:
    google_key = os.getenv("GOOGLE_API_KEY")
    google_cse = os.getenv("GOOGLE_CSE_ID")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    providers: List[SearchProvider] = []
    if google_key and google_cse:
        providers.append(GoogleCSEProvider(google_key, google_cse))
    if perplexity_key:
        providers.append(PerplexityProvider(perplexity_key))
    if not providers:
        return NullSearchProvider()
    if len(providers) == 1:
        return providers[0]
    return CombinedSearchProvider(providers)
