from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from .api import router as api_router
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config.settings import settings
from ..core.db import get_engine, JurisdictionRun
from sqlalchemy.orm import Session

app = FastAPI()
app.include_router(api_router)

TEMPLATES = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parent / "templates")),
    autoescape=select_autoescape(["html"]),
)


@app.get("/")
async def index():
    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        runs = session.query(JurisdictionRun).order_by(JurisdictionRun.started_at.desc()).limit(200).all()
    template = TEMPLATES.get_template("index.html")
    html = template.render(runs=runs)
    return HTMLResponse(html)
