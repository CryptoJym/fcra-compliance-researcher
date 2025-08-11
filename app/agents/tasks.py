from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from celery import shared_task
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config.settings import settings
from ..core.paths import project_root
from ..core.logger import setup_logger
from ..core.vector_store import VectorStore
from ..core.db import record_run
from .sourcing_agent import SourcingAgent
from .extraction_agent import ExtractionAgent
from .validation_agent import ValidationAgent
from .merge_agent import MergeAgent


logger = setup_logger("tasks")


@shared_task(name="app.agents.tasks.process_jurisdiction", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=8), reraise=True)
def process_jurisdiction(jurisdiction_path: str, skip_validation: bool = False, skip_merge: bool = False) -> dict:
    logger.info(f"Processing task via Celery: {jurisdiction_path}")

    record_run(settings.database_url, jurisdiction_path, status="in_progress")

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
                record_run(settings.database_url, jurisdiction_path, status="error", metrics=details)
                return {"status": "validation_failed", "details": details}

        # Merge
        if not skip_merge:
            ok, details = merge.run(jurisdiction_file, patch_path)
            if not ok:
                record_run(settings.database_url, jurisdiction_path, status="error", metrics=details)
                return {"status": "merge_failed", "details": details}

        record_run(settings.database_url, jurisdiction_path, status="completed")
        return {"status": "completed", "jurisdiction": jurisdiction_path}
    except Exception as e:
        logger.exception(f"Celery task failed: {jurisdiction_path}: {e}")
        record_run(settings.database_url, jurisdiction_path, status="error", metrics={"error": str(e)})
        return {"status": "error", "error": str(e)}
