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


class NullSearchProvider(SearchProvider):
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        return []


def get_default_search_provider() -> SearchProvider:
    key = os.getenv("GOOGLE_API_KEY")
    cse = os.getenv("GOOGLE_CSE_ID")
    if key and cse:
        return GoogleCSEProvider(key, cse)
    return NullSearchProvider()
