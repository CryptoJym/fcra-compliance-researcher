from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from app.core.runner import app


def test_runner_celery_queue_path(tmp_path: Path, monkeypatch):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    qpath = tools_dir / "research_queue.json"
    qpath.write_text(json.dumps([{"jurisdiction_path": "unified/city/sample.json", "priority": 1}]))

    # Running with --use-celery should not crash (we don't wait for worker)
    runner = CliRunner()
    res = runner.invoke(app, [
        "--workers", "1", "--idle-sleep", "0.01", "--max-cycles", "1",
        "--queue-path", str(qpath), "--use-celery", "--skip-validation", "--skip-merge",
    ])
    assert res.exit_code == 0


