from __future__ import annotations

import json
from pathlib import Path

from app.core.schema_versioning import (
    validate_version,
    migrate_to_latest,
    migrate_patch_dict,
    migrate_patch_file,
)


def test_validate_version_missing():
    ok, msg = validate_version({})
    assert not ok and "schema_version" in msg


def test_validate_version_supported():
    ok, msg = validate_version({"schema_version": "v1"})
    assert ok


def test_migrate_sets_default_when_missing():
    out, note = migrate_to_latest({"jurisdiction": "unified/x.json"})
    assert out.get("schema_version") == "v1"


def test_migrate_missing_version_to_v1(tmp_path: Path):
    patch = {"jurisdiction_path": "unified/city/x.json", "lastUpdated": "2024-01-01"}
    m, notes = migrate_patch_dict(patch)
    assert m.get("schema_version") == "v1"
    assert m.get("last_updated") == "2024-01-01"
    assert m.get("jurisdiction") == "unified/city/x.json"
    assert any("Stamped schema_version" in n for n in notes)


def test_migrate_patch_file(tmp_path: Path):
    p = tmp_path / "patch.json"
    p.write_text(json.dumps({"lastUpdated": "2024-02-02"}))
    notes = migrate_patch_file(p)
    data = json.loads(p.read_text())
    assert data["schema_version"] == "v1"
    assert data["last_updated"] == "2024-02-02"
    assert len(notes) >= 1
