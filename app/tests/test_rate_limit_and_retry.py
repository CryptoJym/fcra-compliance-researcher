from __future__ import annotations

import os
from app.agents.sourcing_agent import SourcingAgent, SourceDocument
from app.core.vector_store import VectorStore


def test_sourcing_agent_retry_rate_limit(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, timeout):
        calls["n"] += 1
        class R:
            status_code = 200 if calls["n"] >= 2 else 500
            text = "<html><title>ok</title><body>ok</body></html>"
        return R()

    import httpx
    monkeypatch.setattr(httpx, "get", fake_get)

    vs = VectorStore(index_path="/tmp/ignore-faiss")
    agent = SourcingAgent(vs)
    docs = agent.search_and_collect("unified/city/sf.json", ["http://example.com"])
    assert len(docs) == 1
    assert calls["n"] >= 2
