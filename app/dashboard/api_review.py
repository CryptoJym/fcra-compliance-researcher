from __future__ import annotations

from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
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
async def set_review(request: Request):
    content_type = request.headers.get("content-type", "").lower()
    # Parse form or JSON payload
    if content_type.startswith("application/x-www-form-urlencoded") or content_type.startswith("multipart/form-data"):
        form = await request.form()
        run_id = int(form.get("run_id")) if form.get("run_id") is not None else None
        status = form.get("status")
        notes = form.get("notes")
        reviewer = form.get("reviewer")
        wants_redirect = True
    else:
        data = await request.json()
        run_id = int(data.get("run_id")) if data.get("run_id") is not None else None
        status = data.get("status")
        notes = data.get("notes")
        reviewer = data.get("reviewer")
        wants_redirect = False

    if status not in {"needs_review", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="invalid status")
    if run_id is None:
        raise HTTPException(status_code=400, detail="missing run_id")

    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        run = session.get(JurisdictionRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        run.review_status = status
        run.review_notes = notes
        run.reviewed_by = reviewer
        run.reviewed_at = datetime.now(UTC)
        session.commit()

    if wants_redirect:
        return RedirectResponse(url="/review", status_code=303)
    return JSONResponse({"ok": True})
