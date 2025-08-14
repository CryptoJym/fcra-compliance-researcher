from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List

import typer

from ..config.settings import settings
from ..core.db import init_db, record_run
from ..core.paths import project_root
from ..core.vector_store import VectorStore
from ..core.queue import ResearchQueue
from ..core.logger import setup_logger, set_trace_id
from ..agents.task_manager import TaskManagerAgent
from ..agents.sourcing_agent import SourcingAgent
from ..core.sourcing_templates import generate_queries
from ..agents.extraction_agent import ExtractionAgent
from ..agents.validation_agent import ValidationAgent
from ..agents.merge_agent import MergeAgent


app = typer.Typer(add_completion=False)


@app.command()
def workers(
    workers: int = 2,
    idle_sleep: float = 3.0,
    max_cycles: int = 0,
    queue_path: str | None = None,
    use_celery: bool = False,
    skip_validation: bool = False,
    skip_merge: bool = False,
    deep_research: bool = False,
):
    logger = setup_logger("runner")

    init_db(settings.database_url)

    queue_file = Path(queue_path) if queue_path else (project_root() / "tools" / "research_queue.json")
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    if not queue_file.exists():
        queue_file.write_text("[]")
    task_manager = TaskManagerAgent(queue_file)
    base_dir = project_root()

    if use_celery:
        from ..agents.tasks import process_jurisdiction  # Lazy import to avoid Celery overhead when not used
    else:
        vector = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        sourcing = SourcingAgent(vector)
        extraction = ExtractionAgent(vector)
        validation = ValidationAgent()
        merge = MergeAgent()
        research_agent = None
        if deep_research:
            try:
                from ..core.research_agent import build_agent  # Lazy import to avoid optional deps when unused

                research_agent = build_agent()
            except Exception:
                research_agent = None

    cycles = 0
    while True:
        if max_cycles and cycles >= max_cycles:
            logger.info("Reached max cycles. Exiting.")
            break
        cycles += 1
        task = task_manager.next(base_dir=base_dir)
        if task is None:
            logger.info("No pending tasks. Sleeping...")
            time.sleep(idle_sleep)
            continue

        jurisdiction = task.jurisdiction_path
        # Generate a trace ID for this run
        trace_id = f"run-{int(time.time()*1000)}-{jurisdiction.replace('/', '_')}"
        set_trace_id(trace_id)
        logger.info(f"Starting task: {jurisdiction} | trace_id={trace_id}")
        started_monotonic = time.monotonic()
        record_run(settings.database_url, jurisdiction, status="in_progress", trace_id=trace_id)

        try:
            if use_celery:
                res = process_jurisdiction.delay(jurisdiction, skip_validation=skip_validation, skip_merge=skip_merge, trace_id=trace_id)
                logger.info(f"Queued Celery task id={res.id} for {jurisdiction} | trace_id={trace_id}")
                from ..core.notifications import notify_slack
                notify_slack(f"Queued task: {jurisdiction} (id={res.id})")
            else:
                # 1) Sourcing
                if deep_research and research_agent is not None:
                    try:
                        _ = research_agent.invoke({"query": f"FCRA compliance {jurisdiction}"})  # type: ignore[operator]
                        logger.info(f"Deep research pre-run completed for {jurisdiction}")
                    except Exception:
                        logger.info("Deep research not available or failed; continuing with standard pipeline")
                queries = generate_queries(
                    jurisdiction,
                    topics=[
                        "fair chance ordinance",
                        "ban the box employment",
                        "criminal history in employment",
                    ],
                )
                # Fallback canonical URL probe
                queries.append(f"https://law.justia.com/codes/{jurisdiction}")
                src_res = sourcing.run(jurisdiction, queries)
                try:
                    if src_res.get("num_docs", 0) == 0:
                        from ..core.notifications import notify_slack  # type: ignore
                        notify_slack(f"No sources found for {jurisdiction}")
                except Exception:
                    pass

                # 2) Extraction
                schema_skeleton = {"jurisdiction": jurisdiction}
                patch = extraction.run(jurisdiction, schema_skeleton)

                # 3) Write patch temp file
                patch_path = project_root() / "research_inputs" / f"{Path(jurisdiction).stem}.json"
                patch_path.write_text(json.dumps(patch, indent=2))

                # 4) Validation
                jurisdiction_file = project_root() / jurisdiction
                if not skip_validation:
                    ok, details = validation.run(jurisdiction_file, patch_path)
                    if not ok:
                        logger.error(f"Validation failed for {jurisdiction}: {details}")
                        task_manager.mark_error(jurisdiction, "validation_failed")
                        record_run(settings.database_url, jurisdiction, status="error", metrics=details, trace_id=trace_id)
                        continue

                # 5) Merge
                if not skip_merge:
                    ok, details = merge.run(jurisdiction_file, patch_path)
                    if not ok:
                        logger.error(f"Merge failed for {jurisdiction}: {details}")
                        task_manager.mark_error(jurisdiction, "merge_failed")
                        record_run(settings.database_url, jurisdiction, status="error", metrics=details, trace_id=trace_id)
                        continue

                task_manager.mark_completed(jurisdiction)
                record_run(settings.database_url, jurisdiction, status="completed", trace_id=trace_id)
                logger.info(f"Completed task: {jurisdiction} | trace_id={trace_id}")
                # Long-running alert
                try:
                    threshold = getattr(settings, "long_running_seconds", None)
                    if threshold is not None:
                        elapsed = time.monotonic() - started_monotonic
                        if elapsed >= float(threshold):
                            from ..core.notifications import notify_slack  # type: ignore
                            notify_slack(
                                f"Long-running task completed: {jurisdiction} in {elapsed:.1f}s (threshold {threshold}s)"
                            )
                except Exception:
                    pass
        except Exception as e:
            logger.exception(f"Task failed: {jurisdiction}: {e}")
            task_manager.mark_error(jurisdiction, str(e))
            record_run(settings.database_url, jurisdiction, status="error", metrics={"error": str(e)}, trace_id=trace_id)


if __name__ == "__main__":
    app()
