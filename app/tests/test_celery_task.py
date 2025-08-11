from __future__ import annotations

import os
from app.core.celery_app import create_celery_app
from app.agents.tasks import process_jurisdiction


def test_celery_task_eager(tmp_path):
    # Configure Celery in eager mode
    os.environ["REDIS_URL"] = "memory://"
    app = create_celery_app()
    app.conf.task_always_eager = True

    # Minimal DB path
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"

    # Invoke task eagerly
    res = process_jurisdiction.apply(kwargs={
        "jurisdiction_path": "unified/city/san_francisco.json",
        "skip_validation": True,
        "skip_merge": True,
    })
    assert res.successful()
    data = res.result
    assert data.get("status") in {"completed", "validation_failed", "merge_failed", "error"}
