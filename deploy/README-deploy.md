Deployment and Orchestration

Overview
- This repo includes Docker images and Compose orchestration for local, staging, and production.
- Services: `dashboard` (FastAPI), `redis`, `worker` (Celery), and `flower` (Celery dashboard).

Prerequisites
- Docker and Docker Compose v2
- For staging/production, provide environment files under `env/` (see samples below) or a secret manager.

Local development
```bash
# Bring up all services
docker compose up -d

# View logs
docker compose logs -f --tail=200

# Health checks
curl -fsS http://localhost:8000/healthz
curl -fsS http://localhost:8000/readyz
```

Environment variables
- Application reads env vars and/or `.secrets.json` via `app/core/secrets.py`.
- For Compose, you can use a `.env` at repo root or the provided `env/*.env` files.

Staging
```bash
# Prepare env
mkdir -p env
cat > env/staging.env <<'EOF'
APP_ENV=staging
DASH_USER=admin
DASH_PASS=change-me
DASHBOARD_PORT=8000
DATABASE_URL=sqlite:///./researcher.db
REDIS_URL=redis://redis:6379/0
WORKER_CONCURRENCY=2
EOF

# Launch
docker compose -f docker-compose.yml -f deploy/docker-compose.staging.yml up -d
```

Production
```bash
# Prepare env
mkdir -p env
cat > env/prod.env <<'EOF'
APP_ENV=production
DASH_USER=${DASH_USER}
DASH_PASS=${DASH_PASS}
DASHBOARD_PORT=8000
DATABASE_URL=sqlite:///./researcher.db
REDIS_URL=redis://redis:6379/0
WORKER_CONCURRENCY=4
EOF

# Launch
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

Graceful shutdown
- `docker compose down` sends SIGTERM; processes exit cleanly. Celery finishes current tasks by default.

Observability
- Dashboard: http://localhost:${DASHBOARD_PORT:-8000}
- Flower: http://localhost:5555
- Logs: use `docker compose logs -f` or the app writes structured JSONL to `logs/`.

Notes
- SQLite is sufficient for single-node deployments. For HA, move to Postgres and point `DATABASE_URL` accordingly.
- Secrets can be provided by env or `.secrets.json` or a system keyring. For cloud, prefer secret manager (AWS/GCP).

