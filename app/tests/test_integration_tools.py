from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from app.scripts.vector_maint import app as vector_app
from app.scripts.schema_cli import app as schema_app


def test_schema_and_vector_tools_work_together(tmp_path: Path):
    # Prepare a patch, migrate, validate
    patch = tmp_path / "patch.json"
    patch.write_text(json.dumps({"lastUpdated": "2024-01-01", "jurisdiction_path": "unified/city/x.json"}))
    runner = CliRunner()
    r1 = runner.invoke(schema_app, ["migrate", str(patch)])
    assert r1.exit_code == 0
    r2 = runner.invoke(schema_app, ["validate", str(patch)])
    assert r2.exit_code == 0
    out = json.loads(r2.stdout)
    assert out.get("ok") is True

    # Use vector maint to reindex and check stats
    vec_dir = tmp_path / "vec"
    r3 = runner.invoke(vector_app, ["reindex", "--index-path", str(vec_dir)])
    assert r3.exit_code == 0
    r4 = runner.invoke(vector_app, ["stats", "--index-path", str(vec_dir)])
    assert r4.exit_code == 0
    stats = json.loads(r4.stdout)
    assert "docs" in stats and "unique" in stats



