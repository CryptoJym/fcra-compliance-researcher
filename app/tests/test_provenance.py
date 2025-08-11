from __future__ import annotations

from sqlalchemy import text

from app.core.provenance import init_provenance, record_provenance
from app.core.db import get_engine
from app.config.settings import settings


def test_provenance_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    init_provenance()
    record_provenance("unified/city/sf.json", "ban_the_box.applies", "http://example.com", "quoted snippet")
    engine = get_engine(settings.database_url)
    with engine.connect() as conn:
        rows = list(conn.execute(text("select * from provenance")))
        assert len(rows) == 1
