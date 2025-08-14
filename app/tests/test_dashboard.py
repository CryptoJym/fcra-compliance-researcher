from __future__ import annotations

from datetime import datetime, UTC, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.dashboard.server import app
from app.core.db import Base, JurisdictionRun, get_engine
from app.config.settings import settings
from sqlalchemy.orm import Session


def test_dashboard_index_renders_with_duration(tmp_path: Path, monkeypatch):
    # Use a temp database
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    engine = get_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Insert a completed run
    started = datetime.now(UTC)
    completed = started + timedelta(seconds=1.5)
    with Session(engine) as session:
        run = JurisdictionRun(
            jurisdiction_path="unified/city/sample.json",
            status="completed",
            started_at=started,
            completed_at=completed,
            metrics={"ok": True},
        )
        session.add(run)
        session.commit()

    monkeypatch.setenv("DASH_AUTH_DISABLED", "1")
    client = TestClient(app)
    # disable auth for test
    monkeypatch.setenv("DASH_AUTH_DISABLED", "1")
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "Recent Runs" in html
    assert "Duration" in html
    assert "1.5s" in html


def test_eval_endpoint_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    engine = get_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(JurisdictionRun(jurisdiction_path="unified/city/sample.json", status="completed"))
        session.commit()
    monkeypatch.setenv("DASH_AUTH_DISABLED", "1")
    client = TestClient(app)
    resp = client.get("/api/eval")
    assert resp.status_code == 200
    data = resp.json()
    assert set(["total_recent", "completed", "errors", "avg_duration_sec"]).issubset(data.keys())

