from __future__ import annotations

<<<<<<< HEAD
import os
from pathlib import Path

from app.core.notifications import notify_slack
from app.core.dlq import push_to_dlq, DLQ_FILE
=======
from pathlib import Path

from app.core.notifications import notify_slack
from app.core.dlq import push_to_dlq
>>>>>>> origin/main


def test_notify_slack_disabled(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    assert notify_slack("hello") is False


def test_dlq_append(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.core.dlq.DLQ_FILE", tmp_path / "dead_letter_queue.json")
    push_to_dlq({"k": 1})
    push_to_dlq({"k": 2})
    data = (tmp_path / "dead_letter_queue.json").read_text()
    assert "\"k\": 1" in data and "\"k\": 2" in data
