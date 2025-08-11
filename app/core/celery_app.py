from __future__ import annotations

from celery import Celery
from .logger import setup_logger
from ..config.settings import settings


logger = setup_logger("celery")


def create_celery_app() -> Celery:
    broker = settings.redis_url or "memory://"
    backend = settings.redis_url or None
    app = Celery(
        "fcra_researcher",
        broker=broker,
        backend=backend,
        include=["app.agents.tasks"],
    )
    app.conf.update(
        task_default_queue="research",
        task_routes={"app.agents.tasks.*": {"queue": "research"}},
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = create_celery_app()
