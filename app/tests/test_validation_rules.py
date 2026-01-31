from __future__ import annotations

import json
from pathlib import Path

from app.core.validation_rules import (
    check_citations,
    check_required_fields,
    maybe_infer_preemption,
    run_internal_checks,
)


def test_required_and_citations(tmp_path: Path):
    patch = {
        "schema_version": "v1",
        "jurisdiction": "unified/city/test.json",
        "ban_the_box": {"applies": True},
        "citations": {"laws": []},
    }
    p = tmp_path / "patch.json"
    p.write_text(json.dumps(patch))
    ok, details = run_internal_checks(p, "unified/city/test.json")
    assert not ok
    assert any("citations" in e for e in details["errors"]) and any("Missing required field" in e for e in details["errors"]) 


def test_infer_preemption(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RESEARCH_SCOPE", "FCRA")
    patch = {
        "schema_version": "v1",
        "jurisdiction": "unified/city/test.json",
        "ban_the_box": {"applies": False},
        "citations": {"laws": ["https://example.state.codes/abc"]},
        "last_updated": "2024-01-01",
    }
    p = tmp_path / "patch.json"
    p.write_text(json.dumps(patch))
    ok, details = run_internal_checks(p, "unified/city/test.json")
    assert ok
    updated = json.loads(p.read_text())
    assert updated.get("preemptions", {}).get("preempted_by") == ["state"]


def test_criminal_history_requires_citations(tmp_path: Path):
    patch = {
        "schema_version": "v1",
        "jurisdiction": "unified/state/test.json",
        "last_updated": "2024-01-01",
        "criminal_history": {"restrictions": {"convictions": {"lookback_years": 7}}},
    }
    p = tmp_path / "patch.json"
    p.write_text(json.dumps(patch))
    ok, details = run_internal_checks(p, "unified/state/test.json")
    assert not ok
    assert any("criminal_history.restrictions" in e for e in details["errors"])


def test_cra_scope_requires_criminal_history(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RESEARCH_SCOPE", "CRA")
    patch = {
        "schema_version": "v1",
        "jurisdiction": "unified/state/test.json",
        "last_updated": "2024-01-01",
        "citations": {"laws": ["https://example.gov/abc"]},
    }
    p = tmp_path / "patch.json"
    p.write_text(json.dumps(patch))
    ok, details = run_internal_checks(p, "unified/state/test.json")
    assert not ok
    assert any("CRA scope requires criminal_history.restrictions" in e for e in details["errors"])
