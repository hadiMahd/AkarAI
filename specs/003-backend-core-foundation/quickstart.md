# Quickstart: Backend Core Foundation

## Prerequisites

- Phase 1 Docker Compose foundation is available.
- `.env.example` exists and contains only non-secret runtime values.
- Root `PLAN.md` is present and committed with this phase.

## Start Local Services

```bash
docker compose up --build
```

Expected result:

- PostgreSQL + pgvector is healthy.
- PgBouncer is healthy.
- Redis is healthy.
- MinIO is healthy.
- Backend starts.
- Worker starts.

## Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

Expected result:

- Foundation migrations apply successfully (`0001_enable_pgvector`, `0002_backend_core_foundation`).
- pgvector extension remains enabled.
- Phase 2 foundation tables exist: `roles`, `permissions`, `role_permissions`, `users`, `refresh_sessions`, `audit_logs`, `outbox_events`, `inbox_events`, `notifications`.
- No listings, leads, viewings, RAG document, or media business tables are created.

## Verify Health Contracts

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/health/dependencies
```

Expected result:

- `/health` returns HTTP 200 with `{"status":"ok","service":"backend","request_id":"..."}`.
- `/ready` returns HTTP 200 when PostgreSQL/PgBouncer, Redis, and MinIO are reachable. Returns HTTP 503 when a required dependency is unavailable. Response includes `checks` with `latency_ms` and `checked_at` per check.
- `/health/dependencies` returns HTTP 200 with `{"status":"ok","dependencies":{...},"request_id":"..."}`.

## Verify Backend Tests

```bash
docker compose exec backend pytest tests/unit -v
docker compose exec backend pytest tests/integration -v
docker compose exec backend pytest tests/rbac -v
```

## Verify Worker Skeleton

```bash
docker compose exec worker python -m pytest tests -v
```

## Scope Review

```bash
rg -n "listings|leads|viewings|rag_documents|rag_chunks|image moderation|email sent|login endpoint|register endpoint" backend/ workers/ specs/003-backend-core-foundation/
```

Expected: Mentions only in out-of-scope notes, future event names, or guardrail docs. No business feature implementation.

## Completion Checklist

- [x] Backend common utilities: config, database, redis, storage, security, pagination, rate_limit, cache, transactions, repository, responses, exceptions, logging, request_id, events, tenant
- [x] Async DB/session/transaction pattern with PgBouncer runtime URL
- [x] Base migrations: 0001 (pgvector), 0002 (roles, permissions, users, refresh_sessions, audit_logs, outbox_events, inbox_events, notifications)
- [x] pgvector extension continuity
- [x] Redis cache and rate-limit utilities
- [x] MinIO storage abstraction with upload/download/delete/presigned helpers
- [x] Auth utility foundation (password hashing, JWT tokens, Redis blacklist)
- [x] RBAC foundation (roles, permissions, permission-check placeholders)
- [x] Tenant context foundation
- [x] Outbox/inbox events with idempotency and status lifecycle
- [x] Audit log foundation with repository and service
- [x] AI provider interfaces (10 protocols) without provider logic
- [x] Notification/email abstraction without sending email
- [x] Unit tests (config, logging, pagination, security, permissions, AI interfaces, email, notifications, repository)
- [x] Integration tests (health, readiness, dependencies, database, transactions, storage, redis, cache, rate limit, token invalidation, migrations, pgvector, outbox, inbox, audit logs, notifications)
- [x] RBAC tests (permissions, tenant context)
- [x] Worker tests (startup, event polling)
- [x] Business features excluded (no listings/leads/viewings/RAG/frontend business)
