from __future__ import annotations

import json
import time
from pathlib import Path
from typer.testing import CliRunner

from app.core.runner import app
from app.core.db import get_engine, JurisdictionRun, Base
from app.config.settings import settings
from sqlalchemy.orm import Session


def test_runner_completes_one_cycle(tmp_path: Path, monkeypatch):
    # Prepare queue
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    qpath = tools_dir / "research_queue.json"
    qpath.write_text(json.dumps([{"jurisdiction_path": "unified/city/sample.json", "priority": 1}]))

    # Patch network fetch to be fast
    import app.agents.sourcing_agent as sa

    def quick_fetch(self, url: str):
        return "<html><body>ok</body></html>"

    monkeypatch.setattr(sa.SourcingAgent, "_fetch", quick_fetch)

    # DB
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    engine = get_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Run one cycle
    runner = CliRunner()
    res = runner.invoke(app, [
        "--workers", "1", "--idle-sleep", "0.01", "--max-cycles", "1",
        "--queue-path", str(qpath), "--skip-validation", "--skip-merge",
    ])
    assert res.exit_code == 0

    # Verify completion
    with Session(engine) as session:
        rows = session.query(JurisdictionRun).all()
        assert any(r.status == "completed" for r in rows)


