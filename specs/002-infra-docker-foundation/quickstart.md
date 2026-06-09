# Quickstart: Infrastructure and Docker Compose Foundation

Use this guide to validate Phase 1 after implementation tasks are complete.

## Prerequisites

- Docker with Docker Compose v2
- Local shell from the repository root
- No required project ports already occupied (see port table in [README.md](../../../README.md))

## 1. Prepare Configuration

```bash
cp .env.example .env
```

Review `.env` and keep it limited to non-secret local runtime values plus the
minimum Vault bootstrap placeholders. Do not add real secret values.

## 2. Start The Local Foundation

```bash
docker compose up --build
```

Expected outcome:

- PostgreSQL with pgvector starts (port 5432).
- PgBouncer starts and proxies PostgreSQL access (port 6432).
- Redis starts (port 6379).
- MinIO starts (API port 9000, Console port 9001).
- `rag-vault` and `property-media` buckets are created in MinIO.
- Backend skeleton starts (port 8000).
- User app skeleton starts (port 3000).
- Agency app skeleton starts (port 3001).
- Streamlit admin skeleton starts (port 8501).
- Worker skeleton starts and connects to Redis.

Wait for all services to report healthy. Monitor with:

```bash
docker compose ps
```

## 3. Verify Backend Health Contract

The backend health contract is defined in
[`contracts/openapi.yaml`](./contracts/openapi.yaml).

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"backend"}
```

## 4. Verify Dependency Readiness

```bash
curl http://localhost:8000/ready
```

Expected outcome:

- `postgres_via_proxy` is `passed`.
- `pgvector_enabled` is `passed`.
- `redis` is `passed`.
- `object_storage` is `passed`.

If any check reports `failed`, inspect the corresponding service logs:

```bash
docker compose logs postgres
docker compose logs pgbouncer
docker compose logs redis
docker compose logs minio
```

## 5. Verify App Skeletons

```bash
# User app (React — skeleton page with Phase 1 badge)
curl -s http://localhost:3000 | head -20

# Agency app (React — dashboard grid with metrics placeholders)
curl -s http://localhost:3001 | head -20

# Streamlit admin (backend health and dependency display)
curl -s http://localhost:8501 | head -20
```

Or open in a browser:

| App | URL |
|-----|-----|
| User App | http://localhost:3000 |
| Agency App | http://localhost:3001 |
| Streamlit Admin | http://localhost:8501 |
| Backend API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

## 6. Run Alembic Migrations

After the services are running, apply the initial migration to enable pgvector:

```bash
cd backend && pip install -r requirements.txt && alembic upgrade head
```

Or from within the backend container:

```bash
docker compose exec backend alembic upgrade head
```

Verify migration status:

```bash
docker compose exec backend alembic current
```

Expected: `0001`

## 7. Run Smoke Tests

```bash
# Backend smoke tests
cd backend && pip install -r requirements.txt && pytest tests/smoke/ -v

# Worker tests
cd workers && pip install -r requirements.txt && python -m pytest tests/ -v
```

## 8. Stop The Foundation

```bash
docker compose down
```

## 9. Reset Local State

Use this only when persistent local data from a previous run interferes with
validation.

```bash
docker compose down --volumes
rm -rf miniodata/ redisdata/
```

## Verification Checklist

- [ ] `docker compose up --build` starts all 9 services without errors
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok","service":"backend"}`
- [ ] `curl http://localhost:8000/ready` returns all 4 checks as `passed`
- [ ] `curl http://localhost:3000` returns user app HTML
- [ ] `curl http://localhost:3001` returns agency app HTML
- [ ] `curl http://localhost:8501` returns admin app HTML
- [ ] `docker compose exec backend alembic upgrade head` succeeds
- [ ] `docker compose logs worker \| grep "Connected to Redis"` succeeds
- [ ] `docker compose ps` shows all services as healthy

## Stop Gate

Phase 1 is complete when every item in the verification checklist passes and no
auth, listings, RAG, AI behavior, leads, or viewings have been implemented.
