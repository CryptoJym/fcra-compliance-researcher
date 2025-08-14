from __future__ import annotations

from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dashboard.server import app
from app.core.db import get_engine, Base, JurisdictionRun
from app.config.settings import settings


def test_dashboard_filters_status_and_type(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    engine = get_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        now = datetime.now(UTC)
        session.add_all([
            JurisdictionRun(jurisdiction_path="unified/state/alpha.json", status="completed", started_at=now, completed_at=now + timedelta(seconds=1)),
            JurisdictionRun(jurisdiction_path="unified/city/beta.json", status="error", started_at=now),
        ])
        session.commit()

    client = TestClient(app)
    monkeypatch.setenv("DASH_AUTH_DISABLED", "1")
    r = client.get("/?status=completed&type=state")
    assert r.status_code == 200
    text = r.text
    assert "alpha.json" in text
    assert "beta.json" not in text



