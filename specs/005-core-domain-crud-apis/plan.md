# Implementation Plan: Core Domain Database and CRUD APIs

**Branch**: `005-core-domain-crud-apis` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-core-domain-crud-apis/spec.md`, root [PLAN.md](../../PLAN.md), project constitution, and completed Phase 1-3 foundations.

## Summary

Implement Phase 4 core domain database and CRUD API foundations without AI. This phase adds tenant-scoped agency profile, employee management extensions, listings, listing photo metadata, viewing slots, scheduled viewings and status history, saved listings, comparison sessions/items, leads, lead result placeholder tables, reviewed lead records, notifications, search logs, and domain event/transaction logs.

Phase 4 must not implement AI search, RAG, image upload/processing, OCR, email sending, dashboards, chatbot behavior, buyer-to-agency real-time chat, spam classification, lead scoring, or generated replies. AI-adjacent result tables are storage foundations only.

## Technical Context

**Language/Version**: Python 3.11+ for backend/workers; TypeScript 5.x apps remain skeleton-only unless smoke validation needs endpoint placeholders.

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy async, Alembic, PostgreSQL + pgvector, PgBouncer, Redis for existing platform duties, MinIO references only for future media paths, pytest, pytest-asyncio, httpx. No new AI, RAG, OCR, image, email, dashboard, or worker provider dependencies are selected in this phase.

**Storage**: PostgreSQL for all Phase 4 domain records, status/history records, search logs, and domain event/transaction logs. Existing outbox events may be reused for durable event signaling where already available. Redis and MinIO are not expanded beyond existing foundations.

**Testing**: Backend unit tests for services/repositories/status transitions/filter validation, rate-limit policies, and cache invalidation; API integration tests for CRUD routes; transaction tests for viewing booking and domain logs; RBAC tests for support-employee restrictions; tenant-isolation tests for all agency-owned records; scope guard tests for excluded later-phase behavior.

**Target Platform**: Local Docker Compose development environment. Deployment target remains outside Phase 4.

**Project Type**: Modular monolith web platform with background workers.

**Performance Goals**: All list endpoints return bounded paginated results; manual listing search supports indexed filters and deterministic sort options; listing-search cache invalidation is explicit when public-search-affecting listing data changes; cross-tenant checks remain fail-closed; critical create/status-change flows commit atomically.

**Constraints**: No buyer-to-agency real-time chat; no AI/RAG/media/OCR/email/dashboard behavior; no DAO files; use repository.py for data access; routers delegate to services; tenant and role checks reuse Phase 3 guards; one employee belongs to only one agency; manual search, lead creation, and viewing booking must be rate limited; secrets remain Vault-backed through existing configuration.

**Scale/Scope**: Backend domain foundation for the MVP. Phase 4 touches backend agencies/listings/leads/viewings/notifications/search/common/audit or event modules, migrations, contracts, docs, and tests. User and agency React apps are not feature-built in this phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Reuses the fixed FastAPI, PostgreSQL, Redis, MinIO-reference, and test stack; selects no new provider/library.
- **Architecture**: PASS. Preserves modular monolith feature folders and repository.py as the data access layer. No DAO layer or microservices.
- **Product boundaries**: PASS. User inquiries create leads; viewing bookings create scheduled viewing records; no buyer-to-agency real-time chat.
- **Tenant/RBAC**: PASS. Uses Phase 3 tenant context and role guards for agency-owned records and support-employee restrictions.
- **RAG/search**: PASS. Manual listing search only. No AI search, voice search, area RAG, agency policy RAG, retrieval, or ingestion.
- **Reliability/security/performance**: PASS. Uses transactions for viewing booking/status history and critical domain logs; all list endpoints are paginated; search, inquiry, and booking rate limits are planned; listing-search cache invalidation is explicit; tenant isolation and user ownership are blocking.
- **Testing/quality**: PASS. Requires unit, integration, transaction, RBAC, tenant-isolation, pagination, and scope guard tests.

## Project Structure

### Documentation (this feature)

```text
specs/005-core-domain-crud-apis/
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
│   ├── agencies/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   ├── listings/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   └── query_service.py
│   ├── leads/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   ├── viewings/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   ├── notifications/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   ├── search/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   ├── common/
│   └── auth/
├── alembic/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/
```

**Structure Decision**: Deepen existing backend modules only. Listings own listing records, listing photo metadata, saved listings, comparison records, and listing search read models. Leads own lead records, lead result placeholder records, and reviewed lead records. Viewings own viewing slots, scheduled viewings, and status history. Agencies extend existing agency tenant/employee foundations with profile and employee management behavior. Notifications extends existing persisted notifications only; delivery remains later. Search stores manual search logs and tenant-scoped operational log list APIs. Existing `backend/app/common/cache.py` and `backend/app/common/rate_limit.py` are reused for explicit listing-search cache invalidation and Phase 4 rate-limit enforcement.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover module ownership, tenant-scoped CRUD patterns, status enumerations, manual search filters, atomic viewing booking, result placeholder tables, notification persistence without delivery, and scope boundaries.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Design reuses existing stack and introduces no unspecified provider or service.
- **Architecture**: PASS. Feature ownership stays in backend modules with repository.py as data access; no DAO layer.
- **Product boundaries**: PASS. No buyer-to-agency real-time chat; leads and scheduled viewings remain separate.
- **Tenant/RBAC**: PASS. Every agency-owned route and model is tenant-scoped; support-employee restrictions are explicit.
- **RAG/search**: PASS. Only manual listing search and search logs are included; AI/RAG search is out of scope.
- **Reliability/security/performance**: PASS. Critical domain changes are transactional, paginated, rate limited where required, cache-safe for listing search, and auditable through domain logs/events.
- **Testing/quality**: PASS. Quickstart and design require CRUD, RBAC, tenant, pagination, transaction, and scope tests.
