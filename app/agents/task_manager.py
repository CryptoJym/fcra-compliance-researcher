from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base import Agent
from ..core.queue import ResearchQueue
from ..core.types import ResearchTask
from ..core.logger import setup_logger
from ..config.settings import settings


class TaskManagerAgent(Agent):
    def __init__(self, queue_path: Path):
        super().__init__("task_manager")
        self.queue = ResearchQueue(queue_path)
        self.queue.load()
        self.logger = setup_logger("task_manager")

    def insert_task(self, jurisdiction_path: str, priority: int = 0) -> None:
        task = ResearchTask(jurisdiction_path=jurisdiction_path, priority=priority, inserted_at=datetime.utcnow())
        self.queue.add_task(task)

    def next(self, base_dir: Path | None = None) -> Optional[ResearchTask]:
        return self.queue.next_task(base_dir=base_dir)

    def mark_completed(self, jurisdiction_path: str) -> None:
        self.queue.mark_completed(jurisdiction_path)

    def mark_error(self, jurisdiction_path: str, error: str) -> None:
        self.queue.mark_error(jurisdiction_path, error)

    def run(self, **kwargs):
        return {"pending": len([t for t in self.queue.tasks if t.status == "pending"]) }
