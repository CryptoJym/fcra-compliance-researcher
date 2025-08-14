# Issues / Tasks

## Completed
- Containerized services: `dashboard`, `redis`, `worker`
- Added optional `flower` dashboard overlays via `deploy/` files
- Staging and production compose overlays with env files (`env/staging.env.example`, `env/prod.env.example`)
- Deployment documentation (`DEPLOYMENT.md`, `deploy/README-deploy.md`)
- Optional deep-research services included in base compose: `qdrant`, `searxng`
- Minimal Slack notifications wired (queueing/no-sources/long-running) via `app/core/notifications.py`

Note: A previous entry claimed healthchecks were wired. Compose files currently lack `healthcheck:` blocks and the dashboard does not expose `/healthz`/`/readyz` yet.

## Follow-ups
- Add health endpoints (`/healthz`, `/readyz`) in `app/dashboard/server.py` and wire Docker Compose `healthcheck:` for:
  - `dashboard` (GET `/readyz`)
  - `redis` (PING)
  - `worker` (Celery inspect ping)
- Consider re-adding `flower` to local `docker-compose.yml` (it’s available in `deploy/*` overlays)
- Replace SQLite with Postgres for multi-node deployments; update `DATABASE_URL` and docs
- Run containers as non-root (update `Dockerfile` and compose `user:`); fix file permissions
- Extend notifications:
  - Slack alerts for validation/merge failures
  - Optional email integration
- Harden secrets (prefer a secret manager); avoid `.env` in production deployments
- Add CI job to run a Docker Compose smoke test (bring up services, hit health endpoints)
- Add LICENSE (README shows TBD)

