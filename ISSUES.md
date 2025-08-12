# Issues / Tasks

## Completed
- Containerized services: `dashboard`, `redis`, `worker`
- Added optional `flower` dashboard overlay via deploy files
- Healthchecks wired for services (dashboard via `/openapi.json`, redis ping, worker Celery inspect)
- Staging and production compose overlays with env files
- Deployment documentation (`DEPLOYMENT.md`, `deploy/README-deploy.md`)

## Follow-ups
- Consider re-adding `flower` to local compose if desired by default
- Optionally switch dashboard healthcheck to `/readyz` (endpoint available) and expose `/healthz`
- Replace SQLite with Postgres for multi-node deployments; update `DATABASE_URL`
- Configure non-root user for Celery worker in production
- Add alerts/notifications integration (Slack/email)
- Harden secrets: move to secret manager and remove `.env` from production
- Add CI job to run `docker compose -f ... up --detach` smoke test

