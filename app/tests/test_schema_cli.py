from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from app.scripts.schema_cli import app


def test_schema_cli_version():
    runner = CliRunner()
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert r.stdout.strip().startswith("v")


def test_schema_cli_validate_and_migrate(tmp_path: Path):
    p = tmp_path / "patch.json"
    p.write_text(json.dumps({"lastUpdated": "2024-01-01", "jurisdiction_path": "unified/city/x.json"}))
    runner = CliRunner()
    r1 = runner.invoke(app, ["validate", str(p)])
    assert r1.exit_code == 0
    data = json.loads(r1.stdout)
    assert data["ok"] is False

    r2 = runner.invoke(app, ["migrate", str(p)])
    assert r2.exit_code == 0
    out = json.loads(r2.stdout)
    assert out["migrated"] is True
    # Valid after migration
    r3 = runner.invoke(app, ["validate", str(p)])
    assert r3.exit_code == 0
    data2 = json.loads(r3.stdout)
    assert data2["ok"] is True


