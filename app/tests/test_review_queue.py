from __future__ import annotations

from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient

from app.dashboard.server import app
from app.core.db import get_engine, Base, JurisdictionRun
from app.config.settings import settings
from sqlalchemy.orm import Session


def test_review_queue_renders(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    engine = get_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Insert a run needing review
    with Session(engine) as session:
        run = JurisdictionRun(
            jurisdiction_path="unified/city/sample.json",
            status="completed",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) + timedelta(seconds=1),
            review_status="needs_review",
        )
        session.add(run)
        session.commit()

    client = TestClient(app)
    monkeypatch.setenv("DASH_AUTH_DISABLED", "1")
    r = client.get("/review")
    assert r.status_code == 200
    assert "Human Review Queue" in r.text
    assert "sample.json" in r.text
