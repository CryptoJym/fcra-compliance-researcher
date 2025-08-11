from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from ..core.queue import ResearchQueue
from ..core.types import ResearchTask
from ..core.paths import project_root
from datetime import datetime

router = APIRouter(prefix="/api")


class EnqueueRequest(BaseModel):
    jurisdiction_path: str
    priority: int | None = None


@router.post("/enqueue")
async def enqueue(req: EnqueueRequest):
    qpath = project_root() / "tools" / "research_queue.json"
    queue = ResearchQueue(qpath)
    queue.load()
    priority = req.priority if req.priority is not None else 0
    queue.add_task(ResearchTask(jurisdiction_path=req.jurisdiction_path, priority=priority, inserted_at=datetime.utcnow()))
    return {"status": "queued", "jurisdiction_path": req.jurisdiction_path, "priority": priority}
