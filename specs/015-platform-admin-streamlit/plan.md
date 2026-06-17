# Implementation Plan: Platform Admin Dashboard

**Branch**: `[015-platform-admin-streamlit]` | **Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-platform-admin-streamlit/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Expand the existing placeholder Streamlit admin app into a real read-only platform admin dashboard. Reuse the current platform-admin bearer auth/session flow, add a dedicated dashboard access permission gate, and serve the Streamlit UI from backend-owned read APIs rather than direct database access from the admin container. Build aggregate-only marketplace demand insights from existing search and listing data, expose a redacted in-app AI audit log viewer with filtering and pagination, and add a role/permission overview page. Keep all platform routes read-only and explicitly separate from agency-scoped operational screens.

## Technical Context

**Language/Version**: Python 3.11 for backend/admin; TypeScript 5.5 for React apps

**Primary Dependencies**: FastAPI, SQLAlchemy asyncio, Streamlit, requests, PostgreSQL + pgvector, Redis, MinIO, Pydantic Settings

**Storage**: PostgreSQL + pgvector for metadata/search/vector data; MinIO for blobs/text; Redis for cache/queue/rate limit/token blacklist

**Testing**: Backend service unit tests, API integration tests, RBAC authorization tests, query-service aggregation tests, and Streamlit smoke/UI tests for dashboard rendering and auth failure states

**Target Platform**: Browser-based Streamlit admin app plus FastAPI services running in the existing Docker Compose stack

**Project Type**: Modular monolith web platform with a separate Streamlit admin surface and background workers

**Performance Goals**: Dashboard scope changes remain internally consistent across all visible panels, audit log tables remain paginated and filterable, and all backend I/O remains async and bounded

**Constraints**: No buyer-to-agency real-time chat; tenant isolation for agency data/RAG/tool calls; provider logic behind interfaces; all secrets read from HashiCorp Vault; unspecified providers/libraries require user clarification

**Scale/Scope**: Multi-tenant agency platform covering user app, agency dashboard, platform admin, AI search/RAG, leads, and viewings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: Uses React + TypeScript, Streamlit + Python, FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, and background workers.
- **Architecture**: Preserves the modular monolith and feature folders; does not introduce microservices or duplicate DAO/repository layers.
- **Product boundaries**: Does not add buyer-to-agency real-time chat; keeps homepage AI search-only; separates leads from scheduled viewings.
- **Tenant/RBAC**: Enforces platform-admin-only access plus a dedicated dashboard permission gate; preserves tenant-safe aggregate reads and read-only audit views.
- **RAG/search**: Reuses existing search logs and AI audit records; no new RAG ingestion or retrieval behavior is introduced.
- **Reliability/security/performance**: Uses read-only backend APIs, redacted audit payloads, pagination, PgBouncer, async I/O, and explicit cache handling for platform insight views.
- **Testing/quality**: Includes required unit, integration, RBAC, and admin-app validation tests; avoids unused architecture patterns.

## Project Structure

### Documentation (this feature)

```text
specs/015-platform-admin-streamlit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── analytics/
│   ├── admin/
│   ├── audit/
│   ├── auth/
│   ├── common/
│   ├── listings/
│   ├── search/
│   └── users/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

admin/
├── app.py
├── api_client.py
├── auth.py
├── components.py
├── Dockerfile
├── requirements.txt
├── pages/
└── tests/

docker-compose.yml
```

**Structure Decision**: Keep the Streamlit app in the existing `admin/` service and add platform-admin-specific backend routes and query services inside the existing modular monolith. Reuse `auth`, `audit`, `search`, `analytics`, and listing/query modules instead of introducing a second admin backend or direct database access from Streamlit.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |

## Phase 0 Research Output

- Use the existing platform-admin bearer auth/session and `/auth/me`, but require a new dedicated dashboard access permission on all platform dashboard routes and on Streamlit entry checks.
- Keep all platform insight views aggregate-only in this phase; do not add per-agency drill-down or tenant comparison views.
- Source marketplace demand insights from existing `search_logs`, listing inventory counts, and audit data through backend query services; support `city`, `property_type`, and `listing_purpose` filters; do not let Streamlit query PostgreSQL directly.
- Keep AI audit investigations as redacted in-app views only, with no export path in this phase.
- Extend the existing `admin/` Streamlit service rather than creating a new frontend surface.

## Post-Design Constitution Check

- **Fixed stack**: Still uses Streamlit + Python for platform admin and FastAPI + Python for backend APIs. No unapproved provider or library decisions were introduced.
- **Architecture**: Keeps admin behavior split between the existing `admin/` app and the backend modular monolith; no microservice or DAO drift.
- **Product boundaries**: Platform admin remains read-only and marketplace-level. No agency chat or agency-data mutation was added.
- **Tenant/RBAC**: Platform routes require platform-admin identity plus dedicated dashboard permission. Returned metrics stay aggregate and audit payloads stay redacted.
- **RAG/search**: Reuses existing search and audit records only. No new RAG behavior is added.
- **Reliability/security/performance**: Pagination, backend-side authz, redaction, PgBouncer-backed queries, and bounded tables remain in force.
- **Testing/quality**: Plan includes backend unit/integration/RBAC tests and Streamlit validation coverage.
