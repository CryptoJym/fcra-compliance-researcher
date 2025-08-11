from __future__ import annotations

from pathlib import Path

from app.core.queue import ResearchQueue
from app.core.types import ResearchTask
from datetime import datetime


def test_queue_roundtrip(tmp_path: Path):
    qpath = tmp_path / "research_queue.json"
    queue = ResearchQueue(qpath)
    queue.load()
    assert queue.tasks == []

    queue.add_task(ResearchTask("unified/state/ca.json", 5, datetime.utcnow()))
    queue.add_task(ResearchTask("unified/city/sf.json", 2, datetime.utcnow()))

    queue.sort_by_priority()
    t = queue.next_task()
    assert t is not None and t.status == "in_progress"

    queue.mark_completed(t.jurisdiction_path)
    assert any(x.status == "completed" for x in queue.tasks)
