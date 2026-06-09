# Implementation Plan: Backend Core Foundation

**Branch**: `003-backend-core-foundation` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-backend-core-foundation/spec.md`,
root [PLAN.md](../../PLAN.md), project constitution, Phase 1 outputs, and the
Phase 2 planning brief.

## Summary

Build the Phase 2 backend core foundation after the Docker Compose foundation
is working. This phase prepares reusable backend conventions, shared settings,
database/session/transaction utilities, repository/service/router patterns,
request IDs, standardized errors, pagination, rate limiting, cache wrappers,
MinIO abstraction, auth utility foundations, RBAC/tenant foundations,
outbox/inbox reliability records, audit logs, notification/email abstractions,
AI provider interfaces, worker dispatch foundations, and base test utilities.

Phase 2 does not implement business features. It must not add listings, leads,
viewings, RAG ingestion/retrieval, AI workflows, image processing, dashboards,
frontend business pages, Streamlit analytics, registration/login endpoints, or
email sending.

## Technical Context

**Language/Version**: Python 3.11+ for backend/admin/workers; TypeScript 5.x
for existing React app skeletons.

**Primary Dependencies**: FastAPI, Pydantic Settings, SQLAlchemy async,
Alembic, PostgreSQL + pgvector, PgBouncer, Redis, MinIO, pytest,
pytest-asyncio, httpx. Exact auth helper library, background worker library,
email provider, AI provider/model, embedding model, STT provider, TTS provider,
OCR provider, image moderation model, image quality model, spam classifier,
and lead classifier are `TBD_ASK_USER` and must remain behind interfaces.

**Storage**: PostgreSQL + pgvector for foundation schema and future vector
support; Redis for cache, rate limiting, worker coordination, and token
invalidation foundations; MinIO for object-storage abstraction over
`rag-vault` and `property-media`.

**Testing**: Backend unit tests, backend integration tests, transaction
rollback tests, utility tests for pagination/rate limiting/cache/auth,
outbox/inbox idempotency tests, worker startup tests, and RBAC/tenant
foundation tests. RAG ingestion tests are not applicable until RAG phases.

**Target Platform**: Local Docker Compose development environment. Deployment
target remains `TBD_ASK_USER`.

**Project Type**: Modular monolith web platform with background workers.

**Performance Goals**: Bounded pagination defaults and maximums; async
non-blocking I/O for database/cache/storage checks; PgBouncer-backed database
connectivity; Redis-backed rate-limit/cache helpers. Concrete production p95
targets remain later-phase work because Phase 2 has no user-facing business
traffic.

**Constraints**: No buyer-to-agency real-time chat; no business features in
Phase 2; repository.py is the data access layer; no DAO layer; provider logic
behind interfaces; all committed files must avoid secret values; exact
providers/libraries remain `TBD_ASK_USER` until the user selects them.

**Scale/Scope**: Backend foundation only for future Akarai MVP phases. Phase 2
touches backend common utilities, minimal foundation tables, interfaces,
worker foundations, contracts, and tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses FastAPI + Python, PostgreSQL + pgvector, Redis,
  MinIO, PgBouncer, Pydantic Settings, Alembic, and background workers. Exact
  provider/library choices remain `TBD_ASK_USER` behind interfaces.
- **Architecture**: PASS. Preserves modular monolith feature folders and
  repository.py as the data access layer. Does not create DAO files or
  microservices.
- **Product boundaries**: PASS. Does not add buyer-to-agency real-time chat,
  search/listing AI, leads, viewings, dashboards, or frontend business flows.
- **Tenant/RBAC**: PASS. Creates role, permission, tenant-context, and
  guardrail foundations only. Full tenant enforcement on business data remains
  for later phases.
- **RAG/search**: PASS. No RAG ingestion/retrieval/search behavior is added.
  pgvector support and AI/RAG provider interfaces are foundations only.
- **Reliability/security/performance**: PASS. Covers request IDs, errors,
  transactions, outbox/inbox, rate-limit/cache foundations, audit records,
  pooled database connectivity, and no committed secrets.
- **Testing/quality**: PASS. Plans focused unit, integration, transaction,
  RBAC foundation, and worker startup tests. RAG tests are deferred because no
  RAG behavior changes in this phase.

## Project Structure

### Documentation (this feature)

```text
specs/003-backend-core-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py
│   ├── common/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── storage.py
│   │   ├── security.py
│   │   ├── pagination.py
│   │   ├── rate_limit.py
│   │   ├── cache.py
│   │   ├── transactions.py
│   │   ├── repository.py
│   │   ├── responses.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── request_id.py
│   │   ├── events.py
│   │   ├── audit.py
│   │   └── dependencies.py
│   ├── auth/
│   ├── users/
│   ├── agencies/
│   ├── listings/
│   ├── leads/
│   ├── viewings/
│   ├── rag/
│   ├── ai/
│   ├── notifications/
│   └── admin/
├── alembic/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

workers/
└── main.py
```

**Structure Decision**: Use the existing Phase 1 backend skeleton and deepen
the shared `backend/app/common/` foundation. Feature directories remain
placeholders unless a Phase 2 foundation file belongs there. Later feature
modules must use `router.py`, `service.py`, `repository.py`, `schemas.py`,
`models.py`, and `query_service.py` only where lightweight CQRS is useful.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover async SQLAlchemy/PgBouncer,
transactions, repository conventions, RBAC/tenant foundations, Redis
rate-limit/cache helpers, outbox/inbox records, MinIO abstraction, provider
interfaces, notification/email abstraction, error/response patterns, and test
foundations. Unspecified external providers and helper libraries remain
`TBD_ASK_USER` by project rule.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Design uses the fixed stack and leaves exact external
  providers/libraries as `TBD_ASK_USER`.
- **Architecture**: PASS. Design keeps modular monolith boundaries,
  repository.py as the data access layer, and no DAO layer.
- **Product boundaries**: PASS. Contracts expose health/system foundation
  endpoints only. No business APIs are added.
- **Tenant/RBAC**: PASS. Data model includes role, permission, and tenant
  context foundations without implementing business tenant data.
- **RAG/search**: PASS. No RAG/search behavior is designed. Storage and AI
  provider abstractions only prepare later phases.
- **Reliability/security/performance**: PASS. Design includes transactions,
  outbox/inbox, request IDs, standardized errors, audit logs, pagination,
  rate-limit/cache foundations, and no committed secrets.
- **Testing/quality**: PASS. Quickstart and plan define base tests for startup,
  dependencies, utility behavior, transaction rollback, outbox/inbox
  idempotency, RBAC/tenant foundations, and worker startup.
