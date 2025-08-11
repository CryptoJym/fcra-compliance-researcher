from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from .paths import project_root
from .logger import setup_logger
from ..agents.task_manager import TaskManagerAgent

logger = setup_logger("legislative_monitor")


def ingest_json_feed(feed_path: Path | None = None) -> List[Dict]:
    path = feed_path or (project_root() / "tools" / "legislative_feed.json")
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        return data  # items with {jurisdiction_path, priority?}
    except Exception as e:
        logger.error(f"Invalid feed: {e}")
        return []


def enqueue_from_feed(feed_items: List[Dict]) -> int:
    qpath = project_root() / "tools" / "research_queue.json"
    tm = TaskManagerAgent(qpath)
    added = 0
    for item in feed_items:
        jp = item.get("jurisdiction_path")
        priority = int(item.get("priority") or 0)
        if jp:
            tm.insert_task(jp, priority)
            added += 1
    return added
