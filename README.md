FCRA Compliance Researcher

Project overview
- An autonomous, multi-agent pipeline that collects, extracts, validates, and merges legal data into the FCRA Compliance Matrix.
- Components: Task Manager, Sourcing Agent, Extraction Agent, Validation Agent, Merge Agent, and a web Dashboard for observability.

Architecture
- Orchestration: lightweight Typer CLI; ready to plug into CrewAI/AutoGen if needed.
- Retrieval: local vector store with FAISS or in-memory fallback for offline/dev.
 - Retrieval: local vector store with FAISS or in-memory fallback for offline/dev; optional JSONL doc-store for reindex/maintenance.
- LLM: calls are optional and disabled by default for tests; can use self-hosted OpenAI-compatible models.
- State: SQLite DB for run logs and metrics; JSON queue for task scheduling.
- Dashboard: FastAPI + Jinja template for recent runs.

Getting started
1) Setup environment
- Copy `.env.example` to `.env` and fill values as needed (GitHub token, OpenAI base URL/model, search keys).

2) Install
- Recommended: Python 3.11
- Install in editable mode:
  ```bash
  pip install -e .
  ```
- Run tests:
  ```bash
  pytest -q
  ```

3) Run services
- Dashboard and Redis (optional):
  ```bash
  docker compose up -d
  ```
- Start the worker loop (single-command app):
  ```bash
  python -m app.core.runner --workers 2 --idle-sleep 3.0
  ```
  Options:
  - `--max-cycles N` to stop after N cycles (useful in CI/tests)
  - `--queue-path PATH` to point to a custom `research_queue.json`

Directory layout
- `app/agents/`: agents for task management, sourcing, extraction, validation, and merging
- `app/core/`: shared utilities (DB, queue, vector store, logger, paths, runner CLI)
- `app/dashboard/`: FastAPI server and templates for monitoring runs
- `app/tests/`: unit tests
- `app/config/`: settings via pydantic
- `research_inputs/`: temporary extraction outputs (JSON patches)
- `tools/research_queue.json`: task queue file

Progress tracker
- Milestones
  - [x] Project scaffolding and packaging
  - [x] Queue, DB models, logger, runner CLI
  - [x] Offline-safe vector store and embeddings
  - [x] Dedupe, retention, and reindex; doc store + CLI (vector_maint)
  - [x] Basic agents (sourcing/extraction/validation/merge stubs wired)
  - [x] FastAPI dashboard (recent runs)
  - [x] Unit tests and CI-ready runner flags
  - [x] Performance and integration smoke tests (runner cycle, tools, dashboard filters)
  - [ ] Real search integrations (Google CSE, Perplexity) with query templates
  - [ ] Schema-driven extraction enums from `SCHEMA_SPECIFICATION.md`
  - [ ] Validation wiring to upstream `tools/validate_matrix.py`
 - [x] Schema evolution tooling: version, validate, and migrate patch files (CLI)
  - [ ] Patch application via `tools/apply_research_patch.py`
  - [ ] GitHub PR automation (branch/commit/PR) with CI
  - [ ] Dashboard metrics, filters, auth
  - [ ] Notifications (Slack/email)
  - [x] Security & secrets: Secrets provider (env/JSON/keyring) and log redaction helper
- [ ] Docker-compose for all services + production hardening
  - [x] Base compose with dashboard, worker, redis
  - [ ] Add env profiles (staging/prod) and healthchecks
  - [ ] Harden container users and resource limits

Deployment
- Local: `docker compose up -d` brings up `dashboard`, `redis`, and `worker`.
- Reindex vectors: `python -m app.scripts.vector_maint reindex` (uses `settings.vector_db_path`).
- Vector stats: `python -m app.scripts.vector_maint stats` (reports total and unique docs).
- Configure doc store via env:
  - `VECTOR_DOC_STORE_ENABLED=0` to disable persistence (default enabled)
  - `VECTOR_DOC_STORE_PATH=/path/to/docs.jsonl` to override location
 - Schema CLI:
   - `python -m app.scripts.schema_cli version`
   - `python -m app.scripts.schema_cli validate path/to/patch.json`
   - `python -m app.scripts.schema_cli migrate path/to/patch.json`

How to run a sample task
1) Add an item to `tools/research_queue.json`:
   ```json
   [
     {"jurisdiction_path": "unified/city/san_francisco.json", "priority": 5}
   ]
   ```
2) Start the runner:
   ```bash
   python -m app.core.runner --workers 1 --idle-sleep 2.0
   ```
3) Open dashboard at `http://localhost:8000` to see recent runs.

Operational notes
- Offline mode: When no OpenAI API key is set, extraction returns a skeleton JSON with `last_updated` and vector store uses local hash embeddings.
- Persistence: Run logs are stored in SQLite (`DATABASE_URL`).
- Safety: Validation and merge agents call external scripts expected from the upstream repo; until wired, they are placeholders.

Contributing
- Run `pytest` before pushing. Keep code readable and typed.
- Prefer small, cohesive edits and add unit tests for new behavior.

License
- TBD. Align with upstream repository’s license.
