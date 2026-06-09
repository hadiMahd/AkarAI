# Implementation Plan: Akarai MVP

**Branch**: `001-akarai-mvp` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-akarai-mvp/spec.md` plus the planning brief in the attached prompt.

## Summary

Build Akarai as an AI-first, multi-tenant real estate MVP for Lebanon with a
React user app, React agency dashboard, Streamlit platform admin, and FastAPI
modular monolith backend. Core flows cover AI/manual/voice search, listing
detail AI widget, structured leads, scheduled viewings, agency operations,
platform demand insights, and tenant-aware RAG over uploaded agency policy
documents plus platform-owned area knowledge.

The technical approach is a modular monolith with feature folders, PostgreSQL
+ pgvector as the transactional and vector metadata core, MinIO for original
documents and extracted page text, Redis for queues/cache/rate limits/token
blacklist, PgBouncer for connection pooling, and background workers for OCR,
RAG ingestion, image moderation/optimization, email, reminders, and AI-heavy
jobs.

## Technical Context

**Language/Version**: Python 3.11+ for backend/admin/workers; TypeScript 5.x
for React apps.

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector,
Redis, MinIO, PgBouncer, Cohere rerankers where useful. Exact auth library,
worker library, email provider, AI provider/model, STT provider, TTS provider,
OCR provider, and React UI library are `TBD` and must remain behind interfaces
until selected.

**Storage**: PostgreSQL + pgvector for relational metadata, vectors, search,
and audit state; MinIO for original documents, extracted page text, and listing
image objects; Redis for queueing, cache, rate limiting, and token blacklist.

**Testing**: Service-level unit tests, API integration tests, transaction
behavior tests for critical flows, RBAC/tenant-isolation tests, and RAG
ingestion tests for chunk/hash/orphan deletion.

**Target Platform**: Local Docker Compose for development; deployment target
`TBD`.

**Project Type**: Multi-app web platform with FastAPI modular monolith backend,
React user/agency apps, Streamlit platform admin, and background workers.

**Performance Goals**: Paginated reads for all large lists; bounded search and
RAG latency; async/non-blocking backend I/O; WebP image optimization; explicit
cache invalidation for search, dashboard metrics, RAG retrieval, and demand
insights. Concrete p95 targets remain `TBD` for planning with real datasets.

**Constraints**: No buyer-to-agency real-time chat; homepage AI is search-only;
listing page has no chatbot and uses one unified AI widget; inquiries create
Lead records; viewing bookings create ScheduledViewing records; match score is
removed; generic amenities are not a core MVP field; agency policies are
uploaded documents ingested into RAG; all secrets come from HashiCorp Vault
through central settings/config.

**Scale/Scope**: MVP-scale multi-tenant platform for users, agencies, support
employees, and platform admins across search, listings, leads, scheduled
viewings, RAG, AI audit, and demand insights.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Plan uses React + TypeScript, Streamlit + Python,
  FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, PgBouncer, and
  background workers. Exact optional provider/library choices are `TBD` and
  isolated behind interfaces.
- **Architecture**: PASS. Plan uses modular monolith feature folders and
  repository.py as the only data-access layer. `query_service.py` is limited to
  listing search, agency dashboard, platform demand insights, RAG retrieval,
  leads list, and viewing schedules list.
- **Product boundaries**: PASS. No buyer-to-agency real-time chat, homepage AI
  is search-only, listing page has one unified AI widget, leads and scheduled
  viewings remain separate, and match score is excluded.
- **Tenant/RBAC**: PASS. Tenant ID and role permissions are mandatory for
  listings, leads, viewings, policy documents, RAG chunks, AI tool calls, audit
  logs, and metrics.
- **RAG/search**: PASS. PostgreSQL is the RAG metadata source of truth, MinIO
  stores documents/text, pgvector stores embeddings, tenant filtering is
  mandatory, and `company_internal` is reserved for platform-owned area RAG.
- **Reliability/security/performance**: PASS. Plan includes all-or-nothing
  transactions, outbox/inbox where needed, idempotent workers, JWT
  invalidation, Redis rate limits, PII redaction, HashiCorp Vault, pagination,
  PgBouncer, async I/O, and cache invalidation.
- **Testing/quality**: PASS. Required unit, integration, transaction, RAG, and
  RBAC tests are called out for task generation.

## Project Structure

### Documentation (this feature)

```text
specs/001-akarai-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/              # settings, Vault client, DB/session, Redis, MinIO
│   ├── auth/
│   ├── users/
│   ├── agencies/
│   ├── listings/
│   ├── leads/
│   ├── viewings/
│   ├── rag/
│   ├── ai/
│   ├── notifications/
│   ├── audit/
│   └── metrics/
└── tests/
    ├── unit/
    ├── integration/
    ├── rbac/
    └── rag/

apps/
├── user/
└── agency/

admin/

workers/
├── image_processing/
├── ocr/
├── rag_ingestion/
├── notifications/
├── reminders/
└── ai_jobs/

infra/
└── docker-compose.yml
```

**Structure Decision**: Use a modular monolith backend with feature folders and
separate frontend/admin applications. Backend features use `router.py`,
`service.py`, `repository.py`, `schemas.py`, and `models.py`; `query_service.py`
is added only to the read-heavy areas listed in the architecture constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). All technical unknowns are either resolved as
architecture decisions or explicitly recorded as `TBD` provider/library choices
that must stay behind interfaces.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Artifacts preserve the constitution stack and leave
  exact provider/library selections as `TBD`.
- **Architecture**: PASS. Data model and contracts map to modular monolith
  feature boundaries and avoid DAO duplication.
- **Product boundaries**: PASS. Contracts exclude real-time buyer-agency chat,
  match score, generic amenities as core fields, and manual policy text editing.
- **Tenant/RBAC**: PASS. Tenant ownership and role constraints are explicit in
  entities and contracts.
- **RAG/search**: PASS. Data model includes document/page/chunk/hash metadata,
  MinIO path rules, pgvector references, tenant filtering, and area knowledge
  tenant `company_internal`.
- **Reliability/security/performance**: PASS. Data model includes outbox/inbox,
  audit logs, retries, idempotency, JWT invalidation, rate-limit scope,
  pagination, and cache invalidation concerns.
- **Testing/quality**: PASS. Quickstart defines validation scenarios for core
  user, agency, admin, RAG, transaction, and RBAC behavior.
