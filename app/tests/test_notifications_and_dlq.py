from __future__ import annotations

import json
from pathlib import Path

import app.core.dlq as dlq
from app.core.notifications import notify_slack


def test_dlq_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.core.dlq.DLQ_FILE", tmp_path / "dead_letter_queue.json")
    dlq.push_to_dlq({"jurisdiction": "x", "stage": "validation", "error": "oops"})
    assert dlq.DLQ_FILE.exists()
    items = json.loads(dlq.DLQ_FILE.read_text())
    assert items and items[0]["jurisdiction"] == "x"


def test_notify_slack_disabled(monkeypatch):
    # No webhook set
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    ok = notify_slack("hello")
    assert ok is False


def test_dlq_append(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.core.dlq.DLQ_FILE", tmp_path / "dead_letter_queue.json")
    dlq.push_to_dlq({"k": 1})
    dlq.push_to_dlq({"k": 2})
    data = (tmp_path / "dead_letter_queue.json").read_text()
    assert "\"k\": 1" in data and "\"k\": 2" in data
