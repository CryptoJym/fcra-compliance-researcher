from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional
from filelock import FileLock

from .types import ResearchTask
from .gaps import estimate_gaps


def _normalize_dt(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class ResearchQueue:
    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
        self._lock = FileLock(str(queue_file) + ".lock")
        self.tasks: List[ResearchTask] = []

    def load(self) -> None:
        if not self.queue_file.exists():
            self.tasks = []
            return
        with self._lock:
            raw = self.queue_file.read_text()
            # Strip potential leftover conflict markers to avoid JSON decode errors
            cleaned = []
            for line in raw.splitlines():
                if line.strip().startswith(("<<<<<<<", "=======", ">>>>>>>")):
                    continue
                cleaned.append(line)
            data = json.loads("\n".join(cleaned))
        tasks: List[ResearchTask] = []
        for item in data:
            inserted_str = item.get("inserted_at")
            if inserted_str:
                dt = datetime.fromisoformat(inserted_str)
            else:
                dt = datetime.now(UTC)
            tasks.append(
                ResearchTask(
                    jurisdiction_path=item["jurisdiction_path"],
                    priority=item.get("priority", 0),
                    inserted_at=_normalize_dt(dt),
                    status=item.get("status", "pending"),
                    error=item.get("error"),
                )
            )
        self.tasks = tasks

    def save(self) -> None:
        serialized = [
            {**asdict(t), "inserted_at": t.inserted_at.isoformat()} for t in self.tasks
        ]
        with self._lock:
            self.queue_file.write_text(json.dumps(serialized, indent=2))

    def add_task(self, task: ResearchTask) -> None:
        # Normalize inserted_at to be timezone-aware UTC to avoid naive/aware comparison issues
        task.inserted_at = _normalize_dt(task.inserted_at)
        self.tasks.append(task)
        self.save()

    def sort_by_priority(self, base_dir: Path | None = None) -> None:
        # Sort by dynamic score using gaps without mutating stored priority
        def gaps_for(t: ResearchTask) -> int:
            if not base_dir:
                return 0
            try:
                return estimate_gaps(base_dir, t.jurisdiction_path)
            except Exception:
                return 0
        # Key order: higher of (explicit priority vs gaps), then gaps, then earlier insert
        self.tasks.sort(key=lambda t: (-(max(t.priority, gaps_for(t))), -gaps_for(t), t.inserted_at))
        self.save()

    def next_task(self, base_dir: Path | None = None) -> Optional[ResearchTask]:
        self.sort_by_priority(base_dir=base_dir)
        for task in self.tasks:
            if task.status == "pending":
                task.status = "in_progress"
                self.save()
                return task
        return None

    def mark_completed(self, jurisdiction_path: str) -> None:
        for task in self.tasks:
            if task.jurisdiction_path == jurisdiction_path:
                task.status = "completed"
        self.save()

    def mark_error(self, jurisdiction_path: str, error: str) -> None:
        for task in self.tasks:
            if task.jurisdiction_path == jurisdiction_path:
                task.status = "error"
                task.error = error
        self.save()
