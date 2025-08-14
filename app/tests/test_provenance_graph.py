from __future__ import annotations

from sqlalchemy import text
from app.core.provenance_graph import init_provenance_graph, record_provenance_edge
from app.core.db import get_engine
from app.config.settings import settings


def test_provenance_graph_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/prov.db")
    init_provenance_graph()
    record_provenance_edge("unified/city/sf.json", "claim:ban_the_box", "http://example.com/law", 0.9)
    engine = get_engine(settings.database_url)
    with engine.connect() as conn:
        rows = list(conn.execute(text("select * from provenance_edges")))
        assert len(rows) == 1


