from __future__ import annotations

from app.core.sourcing_templates import generate_queries


def test_generate_queries_city():
    qs = generate_queries("unified/city/san_francisco.json", topics=["ban the box application"])
    assert any("san francisco" in q.lower() for q in qs)
    assert any("fair chance" in q.lower() for q in qs)
