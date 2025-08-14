from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path

from ..core.queue import ResearchQueue
from ..core.db import get_engine, JurisdictionRun
from sqlalchemy.orm import Session
from ..core.types import ResearchTask
from ..core.paths import project_root
from datetime import datetime, UTC
import json
from pathlib import Path

LOGS_DIR = Path("logs")

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
    queue.add_task(
        ResearchTask(
            jurisdiction_path=req.jurisdiction_path,
            priority=priority,
            inserted_at=datetime.now(UTC),
        )
    )
    return {"status": "queued", "jurisdiction_path": req.jurisdiction_path, "priority": priority}


@router.get("/logs/{trace_id}")
async def get_logs(trace_id: str):
    if not LOGS_DIR.exists():
        return JSONResponse({"trace_id": trace_id, "events": []})
    events = []
    for path in LOGS_DIR.glob("*.jsonl"):
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("trace_id") == trace_id:
                            events.append(obj)
                    except Exception:
                        continue
        except Exception:
            continue
    return JSONResponse({"trace_id": trace_id, "events": events})


@router.get("/eval")
async def get_eval():
    """Return a minimal evaluation aggregate from recent runs."""
    engine = get_engine()
    with Session(engine) as session:
        runs = session.query(JurisdictionRun).order_by(JurisdictionRun.started_at.desc()).limit(200).all()
    total = len(runs)
    completed = sum(1 for r in runs if r.status == "completed")
    errors = sum(1 for r in runs if r.status == "error")
    durations = []
    from datetime import datetime
    for r in runs:
        if isinstance(r.started_at, datetime) and isinstance(r.completed_at, datetime) and r.completed_at:
            durations.append((r.completed_at - r.started_at).total_seconds())
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
    return JSONResponse({
        "total_recent": total,
        "completed": completed,
        "errors": errors,
        "avg_duration_sec": avg_duration,
    })
