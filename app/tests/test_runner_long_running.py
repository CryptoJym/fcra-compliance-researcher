from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.runner import app
from typer.testing import CliRunner


def test_long_running_alert(tmp_path: Path, monkeypatch):
    # Minimal queue with one task
    qpath = tmp_path / "tools" / "research_queue.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(json.dumps([{"jurisdiction_path": "unified/city/sample.json", "priority": 0}]))

    # Slow down sourcing to simulate long-running
    import app.agents.sourcing_agent as sa
    original = sa.SourcingAgent._fetch

    def slow_fetch(self, url: str):
        time.sleep(0.05)
        return "<html><title>ok</title><body>ok</body></html>"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("VECTOR_RETENTION_DAYS", "0")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")  # disabled
    monkeypatch.setenv("LONG_RUNNING_SECONDS", "0")
    monkeypatch.setattr(sa.SourcingAgent, "_fetch", slow_fetch)

    runner = CliRunner()
    result = runner.invoke(app, ["--workers", "1", "--idle-sleep", "0.01", "--max-cycles", "1", "--queue-path", str(qpath), "--skip-validation", "--skip-merge"])
    assert result.exit_code == 0


