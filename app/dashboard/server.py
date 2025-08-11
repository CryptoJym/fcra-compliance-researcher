from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Depends, Request
from .api import router as api_router
from .api_review import router as review_router
from .auth import require_basic_auth
from fastapi.responses import HTMLResponse
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config.settings import settings
from ..core.db import get_engine, JurisdictionRun
from sqlalchemy.orm import Session

app = FastAPI()
app.include_router(api_router)
app.include_router(review_router)

TEMPLATES = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parent / "templates")),
    autoescape=select_autoescape(["html"]),
)


@app.get("/")
async def index(request: Request, _: bool = Depends(require_basic_auth)):
    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        q = session.query(JurisdictionRun)
        status_filter = request.query_params.get("status") or ""
        type_filter = request.query_params.get("type") or ""
        if status_filter:
            q = q.filter(JurisdictionRun.status == status_filter)
        if type_filter:
            like_pat = f"/%/{type_filter}/%" if type_filter in ("state", "county", "city") else None
            if like_pat:
                q = q.filter(JurisdictionRun.jurisdiction_path.like(f"%/{type_filter}/%"))
        runs = q.order_by(JurisdictionRun.started_at.desc()).limit(200).all()
    # Pre-compute display fields and duration strings for the template
    rows = []
    for r in runs:
        started_at_str = r.started_at.isoformat() if isinstance(r.started_at, datetime) else str(r.started_at)
        completed_at_str = (
            r.completed_at.isoformat() if isinstance(r.completed_at, datetime) and r.completed_at else ""
        )
        duration_str = ""
        if isinstance(r.started_at, datetime) and isinstance(r.completed_at, datetime) and r.completed_at:
            duration_seconds = (r.completed_at - r.started_at).total_seconds()
            duration_str = f"{duration_seconds:.1f}s"
        rows.append(
            {
                "jurisdiction_path": r.jurisdiction_path,
                "status": r.status,
                "started_at": started_at_str,
                "completed_at": completed_at_str,
                "metrics": r.metrics,
                "error": r.error or "",
                "duration": duration_str,
                "trace_id": getattr(r, "trace_id", "-"),
            }
        )
    counts = {"completed": 0, "in_progress": 0, "pending": 0, "error": 0}
    for r in runs:
        if r.status in counts:
            counts[r.status] += 1
    total = sum(counts.values()) or 1
    percent = int(100 * counts["completed"] / total)
    template = TEMPLATES.get_template("index.html")
    html = template.render(rows=rows, counts=counts, percent=percent, status_filter=status_filter, type_filter=type_filter)
    return HTMLResponse(html)
