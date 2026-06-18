# AkarAI

AI-first multi-tenant real estate platform for Lebanon. Modular monolith backend (FastAPI + Python), React user/agency apps, Streamlit platform admin, and background workers.

## Architecture

```
apps/user/        React + TypeScript user app (search, listings, AI)
apps/agency/      React + TypeScript agency dashboard (leads, viewings, docs)
admin/            Streamlit platform admin (insights, audit logs)
backend/
  app/
    auth/
    users/
    agencies/
    listings/
    media/
    search/
    leads/
    viewings/
    rag/
    ai/
    notifications/
    analytics/
    audit/
    common/
  FastAPI modular monolith
workers/          Background workers (OCR, RAG ingestion, email, reminders)
```

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Python 3.11+ |
| Frontend | React + TypeScript |
| Admin | Streamlit + Python |
| Database | PostgreSQL + pgvector |
| Connection Pool | PgBouncer |
| Cache/Queue | Redis |
| Object Storage | MinIO |
| Orchestration | Docker Compose |
| Secrets | HashiCorp Vault |

## Prerequisites

- Docker with Docker Compose v2
- Git
- No required ports already occupied (see port table below)

## Service Ports

| Service | Port | Notes |
|---------|------|-------|
| Backend API | 8000 | FastAPI health at `/health`, readiness at `/ready` |
| PgBouncer | 6432 | PostgreSQL connection proxy |
| PostgreSQL | 5432 | Direct DB access (dev only) |
| Redis | 6379 | Cache, queue, rate limiting |
| MinIO API | 9000 | S3-compatible object storage |
| MinIO Console | 9001 | Web UI for MinIO |
| User App | 3000 | React user-facing app |
| Agency App | 3001 | React agency dashboard |
| Streamlit Admin | 8501 | Platform admin dashboard |

## Quickstart (Phase 1)

For full Phase 1 setup and verification, see [`specs/002-infra-docker-foundation/quickstart.md`](specs/002-infra-docker-foundation/quickstart.md).

```bash
# Prepare configuration
cp .env.example .env

# Start all services
docker compose up --build

# Verify backend health
curl http://localhost:8000/health

# Verify dependency readiness
curl http://localhost:8000/ready

# Access apps
# User app:       http://localhost:3000
# Agency app:     http://localhost:3001
# Streamlit admin: http://localhost:8501
# MinIO console:   http://localhost:9001

# Stop all services
docker compose down

# Reset local state (destroys volumes)
docker compose down --volumes
```

## Quality Pipeline

The shared local/CI command map is documented in
[`docs/quality-pipeline.md`](docs/quality-pipeline.md).

Common entry points:

```bash
make quality-precommit
make quality-backend
make quality-user
make quality-agency
make quality-admin
make quality-workers
make quality-model-service
```
