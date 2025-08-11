from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core.queue import ResearchQueue
from app.core.types import ResearchTask


def test_priority_by_gaps(tmp_path: Path):
    # Create two jurisdiction files, one missing fields
    base = tmp_path
    (base / "unified").mkdir(parents=True, exist_ok=True)
    low = base / "unified" / "low.json"
    high = base / "unified" / "high.json"
    low.write_text('{"jurisdiction": "unified/low.json", "last_updated": "2024-01-01"}')
    high.write_text('{"jurisdiction": "unified/high.json"}')

    qpath = tmp_path / "tools" / "research_queue.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text("[]")

    q = ResearchQueue(qpath)
    q.load()
    q.add_task(ResearchTask("unified/low.json", priority=1, inserted_at=datetime.utcnow()))
    q.add_task(ResearchTask("unified/high.json", priority=1, inserted_at=datetime.utcnow()))

    # high is missing last_updated so should come first
    t = q.next_task(base_dir=base)
    assert t is not None and t.jurisdiction_path == "unified/high.json"
