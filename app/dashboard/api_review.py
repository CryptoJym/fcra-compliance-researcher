from __future__ import annotations

from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.db import get_engine, JurisdictionRun
from sqlalchemy.orm import Session
from ..config.settings import settings

router = APIRouter(prefix="/review")


class ReviewRequest(BaseModel):
    run_id: int
    status: str  # needs_review|approved|rejected
    notes: str | None = None
    reviewer: str | None = None


@router.post("/set")
async def set_review(req: ReviewRequest):
    if req.status not in {"needs_review", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="invalid status")
    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        run = session.get(JurisdictionRun, req.run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        run.review_status = req.status
        run.review_notes = req.notes
        run.reviewed_by = req.reviewer
        run.reviewed_at = datetime.now(UTC)
        session.commit()
    return {"ok": True}
