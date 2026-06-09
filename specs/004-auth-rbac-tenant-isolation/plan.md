# Implementation Plan: Auth, RBAC, and Tenant Isolation

**Branch**: `004-auth-rbac-tenant-isolation` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-auth-rbac-tenant-isolation/spec.md`, root [PLAN.md](../../PLAN.md), project constitution, Phase 1 infrastructure, and Phase 2 backend core foundation.

## Summary

Implement Phase 3 authentication, RBAC, and tenant-isolation foundations before multi-tenant domain work starts. This phase adds sign-in, refresh, sign-out, password reset skeleton, session revocation, employee deactivation, role/permission guards, tenant context propagation, tenant-aware repository enforcement hooks, auth-flow rate limiting, and security audit coverage.

Phase 3 must not implement public registration, listings, leads, scheduled viewings, RAG ingestion/retrieval, AI workflows, email sending, dashboards, or full agency business CRUD. Minimal agency tenant and agency employee records are included only to support tenant isolation and employee deactivation.

## Technical Context

**Language/Version**: Python 3.11+ for backend/workers; TypeScript 5.x for existing React skeletons only if minimal auth-state placeholders are needed.

**Primary Dependencies**: FastAPI, Pydantic Settings, SQLAlchemy async, Alembic, PostgreSQL + pgvector, PgBouncer, Redis, MinIO, pytest, pytest-asyncio, httpx, passlib+bcrypt, python-jose. No new auth, worker, email, AI, OCR, STT, TTS, image moderation, or UI library is selected in this phase.

**Storage**: PostgreSQL for actor, role, permission, agency tenant, agency employee, refresh-session, revocation, and audit records; Redis for token blacklist/session invalidation and auth-flow rate limiting; HashiCorp Vault for secret values.

**Testing**: Backend unit tests for credential utilities, permission guards, tenant context, and rate-limit keying; integration tests for sign-in, refresh, sign-out, password reset skeleton, session revocation, employee deactivation, tenant isolation, audit records, and scope guard checks.

**Target Platform**: Local Docker Compose development environment. Deployment target remains outside Phase 3.

**Project Type**: Modular monolith web platform with background workers.

**Performance Goals**: Auth verification and guard checks must remain bounded and non-blocking for I/O; rate limits must prevent repeated abuse without blocking normal-volume usage; tenant and permission checks must be deterministic for every protected request.

**Constraints**: No buyer-to-agency real-time chat; no business domain APIs; no self-registration; no email sending; tenant isolation must fail closed; repository.py remains the data access layer; no DAO layer; secrets must be read through the central Vault-backed settings path; provider logic remains behind interfaces.

**Scale/Scope**: Backend security foundation only for future Akarai MVP phases. Phase 3 touches backend auth/users/agencies/common/audit modules, migrations, contracts, docs, and tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses the existing fixed backend stack and Phase 2 security foundations. No unspecified provider/library is silently selected.
- **Architecture**: PASS. Preserves modular monolith feature folders and repository.py as the data access layer. No DAO layer or microservices.
- **Product boundaries**: PASS. Does not add buyer-to-agency real-time chat, listings, leads, scheduled viewings, search, RAG, AI workflows, dashboards, or email sending.
- **Tenant/RBAC**: PASS. This phase directly implements approved roles, permissions, employee deactivation, tenant context, and guardrails needed before tenant-scoped domain work.
- **RAG/search**: PASS. No RAG/search behavior is implemented. Tenant context prepared here will be consumed by later RAG/search phases.
- **Reliability/security/performance**: PASS. Covers JWT access/refresh use, invalidation for logout/password reset/deactivation/suspicious revocation, Vault secrets, auth rate limits, audit records, and fail-closed authorization.
- **Testing/quality**: PASS. Requires service/unit tests, integration route tests, transaction/revocation tests, RBAC tests, tenant-isolation tests, and scope scans.

## Project Structure

### Documentation (this feature)

```text
specs/004-auth-rbac-tenant-isolation/
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
│   ├── auth/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   └── permissions.py
│   ├── users/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── agencies/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── audit/
│   └── common/
│       ├── security.py
│       ├── tenant.py
│       ├── repository.py
│       ├── rate_limit.py
│       └── dependencies.py
├── alembic/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

apps/
├── user/
└── agency/

workers/
```

**Structure Decision**: Deepen the existing Phase 2 backend foundation. Auth HTTP routes live in `backend/app/auth/router.py`; business logic remains in services; database access remains in repositories; tenant guardrails remain shared in `backend/app/common/tenant.py` and `backend/app/common/repository.py`. Frontend changes are limited to minimal auth-state placeholders only if required for validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover using the existing Phase 2 passlib+bcrypt and python-jose foundations, refresh-session rotation and revocation, Redis-backed blacklist/rate limits, minimal agency tenant and employee records, permission seed strategy, audit events, and fail-closed tenant guardrails.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Design reuses the existing stack and selects no new unspecified providers/libraries.
- **Architecture**: PASS. Feature ownership stays in auth/users/agencies/common/audit modules with repository.py as the data layer.
- **Product boundaries**: PASS. Contracts include auth/security endpoints only and no business APIs.
- **Tenant/RBAC**: PASS. Design creates minimal agency tenant/employee records and enforces tenant context for protected work.
- **RAG/search**: PASS. No RAG/search behavior. Only future-safe tenant and role context is created.
- **Reliability/security/performance**: PASS. Design includes revocation, rate limiting, audit logs, Vault-backed secrets, and fail-closed authorization.
- **Testing/quality**: PASS. Quickstart and design artifacts require auth, revocation, RBAC, tenant-isolation, audit, rate-limit, and scope tests.
