Containerization and Orchestration

Services
- dashboard: FastAPI UI (port 8000)
- redis: message broker and result backend
- worker: Celery worker
- flower: Celery monitoring dashboard (port 5555)

Local
```bash
docker compose up -d
docker compose ps
docker compose logs -f --tail=200
```

Health checks
- Dashboard: responds on `/openapi.json` (used for healthcheck)
- Redis: `redis-cli ping`
- Worker: Celery `inspect ping`
- Flower: HTTP 200 on root

Staging
```bash
cp env/staging.env.example env/staging.env
# edit values
docker compose -f docker-compose.yml -f deploy/docker-compose.staging.yml up -d
```

Production
```bash
cp env/prod.env.example env/prod.env
# edit values (set DASH_USER/DASH_PASS and secrets)
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

Secrets
- Provided via environment or `.secrets.json`/keyring through `app/core/secrets.py`.
- Prefer a cloud secret manager in production.

Graceful shutdown
- `docker compose down` sends SIGTERM; Uvicorn and Celery exit cleanly.

