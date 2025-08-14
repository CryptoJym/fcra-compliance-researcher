from __future__ import annotations

import json
from pathlib import Path

from app.core.validation_rules import check_citations, check_required_fields, maybe_infer_preemption, run_internal_checks, detect_contradictions


def test_required_and_citations(tmp_path: Path):
    patch = {
        "jurisdiction": "unified/city/test.json",
        "ban_the_box": {"applies": True},
        "citations": {"laws": []},
    }
    p = tmp_path / "patch.json"
    p.write_text(json.dumps(patch))
    ok, details = run_internal_checks(p, "unified/city/test.json")
    assert not ok
    assert any("citations" in e for e in details["errors"]) and any("Missing required field" in e for e in details["errors"]) 


def test_infer_preemption(tmp_path: Path):
    patch = {
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


def test_detect_contradictions():
    facts = [
        {"source": "http://a", "claim": "X"},
        {"source": "http://a", "claim": "Y"},
        {"source": "http://b", "claim": "X"},
        {"source": "http://b", "claim": "X"},
    ]
    conflicts = detect_contradictions(facts)
    assert any(isinstance(t, tuple) and len(t) == 2 for t in conflicts)
