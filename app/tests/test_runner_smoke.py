from __future__ import annotations

from pathlib import Path

from app.core.runner import app
from typer.testing import CliRunner


def test_runner_cli_smoke(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    # Ensure tools/research_queue.json exists and is empty
    qpath = tmp_path / "tools" / "research_queue.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text("[]")

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")

    # Single-command app: call without the command name
    result = runner.invoke(app, [
        "--workers", "1", "--idle-sleep", "0.05", "--max-cycles", "1", "--queue-path", str(qpath)
    ])
    assert result.exit_code == 0
