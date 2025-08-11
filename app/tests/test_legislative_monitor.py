from __future__ import annotations

import json
from pathlib import Path

from app.core.legislative_monitor import ingest_json_feed, enqueue_from_feed


def test_ingest_and_enqueue(tmp_path: Path):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps([
        {"jurisdiction_path": "unified/city/a.json", "priority": 3},
        {"jurisdiction_path": "unified/city/b.json"}
    ]))
    items = ingest_json_feed(feed)
    assert len(items) == 2

    # Wire into a temp queue
    tools = tmp_path / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    (tools / "research_queue.json").write_text("[]")

    # Monkeypatch project_root by temporarily chdir
    enqueue_from_feed(items)
