from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .types import ResearchTask


class ResearchQueue:
    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
        self.tasks: List[ResearchTask] = []

    def load(self) -> None:
        if not self.queue_file.exists():
            self.tasks = []
            return
        data = json.loads(self.queue_file.read_text())
        self.tasks = [
            ResearchTask(
                jurisdiction_path=item["jurisdiction_path"],
                priority=item.get("priority", 0),
                inserted_at=datetime.fromisoformat(item.get("inserted_at") if item.get("inserted_at") else datetime.utcnow().isoformat()),
                status=item.get("status", "pending"),
                error=item.get("error"),
            )
            for item in data
        ]

    def save(self) -> None:
        serialized = [
            {**asdict(t), "inserted_at": t.inserted_at.isoformat()} for t in self.tasks
        ]
        self.queue_file.write_text(json.dumps(serialized, indent=2))

    def add_task(self, task: ResearchTask) -> None:
        self.tasks.append(task)
        self.save()

    def sort_by_priority(self) -> None:
        self.tasks.sort(key=lambda t: (-t.priority, t.inserted_at))
        self.save()

    def next_task(self) -> Optional[ResearchTask]:
        self.sort_by_priority()
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
