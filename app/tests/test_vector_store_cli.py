from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from app.scripts.vector_maint import app
from app.core.vector_store import VectorStore


def test_vector_reindex_and_stats(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VECTOR_RETENTION_DAYS", "0")
    db = tmp_path / "vec"
    vs = VectorStore(index_path=str(db))
    vs.load()
    vs.add_texts(["a", "b", "a"], metadatas=[{"url": "u1"}, {"url": "u2"}, {"url": "u1"}])

    runner = CliRunner()
    r1 = runner.invoke(app, ["reindex", "--index-path", str(db)])
    assert r1.exit_code == 0

    r2 = runner.invoke(app, ["stats", "--index-path", str(db)])
    assert r2.exit_code == 0
    data = json.loads(r2.stdout)
    assert data.get("docs", 0) >= 2


