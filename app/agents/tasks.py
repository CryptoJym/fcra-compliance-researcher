from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from celery import shared_task
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config.settings import settings
from ..core.paths import project_root
from ..core.logger import setup_logger, set_trace_id
from ..core.vector_store import VectorStore
from ..core.db import record_run
from .sourcing_agent import SourcingAgent
from .extraction_agent import ExtractionAgent
from .validation_agent import ValidationAgent
from .merge_agent import MergeAgent


logger = setup_logger("tasks")


def _notify_slack_safe(message: str) -> None:
    try:
        from ..core.notifications import notify_slack  # type: ignore
        notify_slack(message)
    except Exception:
        # Optional integration. Ignore if not available.
        pass


def _push_dlq_safe(payload: dict) -> None:
    try:
        from ..core.dlq import push_to_dlq  # type: ignore
        push_to_dlq(payload)
    except Exception:
        # Optional integration. Ignore if not available.
        pass


@shared_task(name="app.agents.tasks.process_jurisdiction", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
@retry(
    stop=stop_after_attempt(getattr(settings, "retry_max_attempts", 3)),
    wait=wait_exponential(
        multiplier=getattr(settings, "retry_min_seconds", 0.5),
        min=getattr(settings, "retry_min_seconds", 0.5),
        max=getattr(settings, "retry_max_seconds", 8.0),
    ),
    reraise=True,
)
def process_jurisdiction(jurisdiction_path: str, skip_validation: bool = False, skip_merge: bool = False, trace_id: Optional[str] = None) -> dict:
    if trace_id:
        set_trace_id(trace_id)
    logger.info(f"Processing task via Celery: {jurisdiction_path}")

    record_run(settings.database_url, jurisdiction_path, status="in_progress", trace_id=trace_id)
    _notify_slack_safe(f"Started: {jurisdiction_path}")

    vector = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    sourcing = SourcingAgent(vector)
    extraction = ExtractionAgent(vector)
    validation = ValidationAgent()
    merge = MergeAgent()

    try:
        # Sourcing
        queries = [f"https://law.justia.com/codes/{jurisdiction_path}"]
        sourcing.run(jurisdiction_path, queries)

        # Extraction
        schema_skeleton = {"jurisdiction": jurisdiction_path}
        patch = extraction.run(jurisdiction_path, schema_skeleton)

        # Write patch temp file
        patch_path = project_root() / "research_inputs" / f"{Path(jurisdiction_path).stem}.json"
        patch_path.write_text(json.dumps(patch, indent=2))

        # Validation
        jurisdiction_file = project_root() / jurisdiction_path
        if not skip_validation:
            ok, details = validation.run(jurisdiction_file, patch_path)
            if not ok:
                record_run(settings.database_url, jurisdiction_path, status="error", metrics=details, trace_id=trace_id)
                _push_dlq_safe({"jurisdiction": jurisdiction_path, "stage": "validation", "details": details})
                _notify_slack_safe(f"Validation failed: {jurisdiction_path}")
                return {"status": "validation_failed", "details": details}

        # Merge
        if not skip_merge:
            ok, details = merge.run(jurisdiction_file, patch_path)
            if not ok:
                record_run(settings.database_url, jurisdiction_path, status="error", metrics=details, trace_id=trace_id)
                _push_dlq_safe({"jurisdiction": jurisdiction_path, "stage": "merge", "details": details})
                _notify_slack_safe(f"Merge failed: {jurisdiction_path}")
                return {"status": "merge_failed", "details": details}

        record_run(settings.database_url, jurisdiction_path, status="completed", trace_id=trace_id)
        _notify_slack_safe(f"Completed: {jurisdiction_path}")
        return {"status": "completed", "jurisdiction": jurisdiction_path}
    except Exception as e:
        logger.exception(f"Celery task failed: {jurisdiction_path}: {e}")
        record_run(settings.database_url, jurisdiction_path, status="error", metrics={"error": str(e)}, trace_id=trace_id)
        _push_dlq_safe({"jurisdiction": jurisdiction_path, "stage": "task", "error": str(e)})
        _notify_slack_safe(f"Error: {jurisdiction_path}")
        return {"status": "error", "error": str(e)}
