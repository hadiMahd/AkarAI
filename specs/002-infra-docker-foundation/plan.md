# Implementation Plan: Infrastructure and Docker Compose Foundation

**Branch**: `002-infra-docker-foundation` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-infra-docker-foundation/spec.md`

## Summary

Build Phase 1 local infrastructure only: repo structure, root Docker Compose,
PostgreSQL with pgvector, Redis, MinIO, PgBouncer, backend/user/agency/admin
app skeletons, worker skeleton, `.env.example`, health checks, and basic
quickstart documentation. Auth, listings, RAG, AI, leads, and viewings stay out
of scope.

## Technical Context

**Language/Version**: Python 3.11+ for backend/admin/worker skeletons; TypeScript with Node.js 20 LTS for React app skeletons

**Primary Dependencies**: Docker Compose, FastAPI skeleton health service, React TypeScript user app skeleton, React TypeScript agency app skeleton, Streamlit admin skeleton, PostgreSQL with pgvector, Redis, MinIO, PgBouncer

**Storage**: PostgreSQL with pgvector enabled for later persistence/vector work; MinIO for later blobs/text; Redis for later cache/queue/rate limit/token blacklist duties

**Testing**: Local smoke checks for service startup, backend health, dependency readiness, pgvector availability through PgBouncer, Redis reachability, MinIO reachability, React app boot, Streamlit boot, and worker Redis connectivity

**Target Platform**: Local development environment started from the repository root with Docker Compose

**Project Type**: Modular monolith web platform foundation with background worker skeleton

**Performance Goals**: Full local foundation starts and verifies in under 15 minutes from a clean checkout after prerequisites are installed; health/readiness checks fail fast for missing configuration or unavailable dependencies

**Constraints**: Phase 1 MUST NOT implement auth, listings, RAG, AI behavior, leads, or viewings; secret values MUST NOT be committed; `.env.example` MAY include only non-secret runtime configuration and Vault bootstrap placeholders

**Scale/Scope**: One local development foundation covering backing services and app skeleton startup only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses React + TypeScript, Streamlit + Python, FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, PgBouncer, and background workers. AI provider choices are not needed because AI behavior is excluded.
- **Architecture**: PASS. Establishes modular monolith repo structure and skeleton service areas without microservices or duplicate DAO/repository layers.
- **Product boundaries**: PASS. Does not add buyer-to-agency real-time chat and excludes auth, listings, RAG, AI, leads, and viewings.
- **Tenant/RBAC**: PASS. Creates no tenant data or RBAC behavior in Phase 1; later tenant paths remain scaffold-only.
- **RAG/search**: PASS. Creates no RAG ingestion/retrieval/search behavior; only infrastructure storage needed by later phases is made reachable.
- **Reliability/security/performance**: PASS. Requires health checks, repeatable smoke verification, PgBouncer, pgvector verification, no committed secrets, and bounded startup validation.
- **Testing/quality**: PASS. Uses smoke/readiness validation appropriate for infrastructure; domain unit/RBAC/RAG tests are not applicable until later phases.

## Project Structure

### Documentation (this feature)

```text
specs/002-infra-docker-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
docker-compose.yml
.env.example
README.md

backend/
├── app/
│   ├── auth/
│   ├── users/
│   ├── agencies/
│   ├── listings/
│   ├── media/
│   ├── search/
│   ├── leads/
│   ├── viewings/
│   ├── rag/
│   ├── ai/
│   ├── notifications/
│   ├── analytics/
│   ├── audit/
│   └── common/
└── tests/
    ├── unit/
    ├── integration/
    ├── rbac/
    └── smoke/

apps/
├── user/
└── agency/

admin/

workers/
```

**Structure Decision**: Use a single root `docker-compose.yml` for Phase 1 local
orchestration. Create app/service skeleton directories now, but keep domain
behavior empty until the relevant later phase.

## Complexity Tracking

No constitution violations or added complexity.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
