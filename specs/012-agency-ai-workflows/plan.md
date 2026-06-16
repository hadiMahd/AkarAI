# Implementation Plan: Agency AI Workflows

**Branch**: `012-agency-ai-workflows` | **Date**: 2026-06-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-agency-ai-workflows/spec.md`

## Summary

Add five connected AI workflows on top of the current platform foundations: worker-backed temporary OCR spec extraction inside the agency listing form, worker-backed AI listing copy generation for agency admins, a broadened tenant-safe agency assistant that combines policy RAG with approved read-only listing/lead tools and remains synchronous for small tool-backed answers, one suggested reply on lead detail pages, and a user-facing listing comparison summary on the protected compare page. The design reuses the existing provider interfaces, shared guardrailed generation path, tenant context handling, and current React surfaces instead of introducing a separate AI subsystem.

## Technical Context

**Language/Version**: Python 3.11 for backend/admin; TypeScript ^5.5.0 for React apps

**Primary Dependencies**: FastAPI, React 18, TanStack Query, PostgreSQL + pgvector, Redis, MinIO, existing AI provider interfaces, Azure OpenAI chat/embeddings, Azure Computer Vision Read OCR, existing NeMo/OpenRouter guardrails path, React Markdown already present in the agency app, worker outbox/job processing

**Storage**: PostgreSQL for listings, leads, RAG chat threads/messages, AI job state, and audit/log metadata; Redis for existing assistant cache/rate limits and job dispatch; MinIO unchanged for existing RAG/media storage; temporary OCR uploads are processed by a worker and discarded instead of being stored as durable blobs

**Testing**: Backend service unit tests, API integration tests, RBAC tenant-isolation tests, assistant tool authorization tests, and focused React component tests in both `apps/agency` and `apps/user`

**Target Platform**: local Docker Compose

**Project Type**: Modular monolith web platform with background workers; this phase adds worker-backed OCR and long-generation jobs plus synchronous small assistant/tool answers on existing backend/app modules

**Performance Goals**: Job requests are acknowledged quickly and return a queued/pending state; listing draft, lead reply draft, and comparison summary jobs complete within 30 seconds for typical inputs; OCR extraction returns reviewable fields within 60 seconds for a normal property spec sheet; assistant answers preserve the current bounded 4-turn history and paginated/admin-bounded supporting views

**Constraints**: No buyer-to-agency real-time chat; policy assistant route becomes available to support employees but document-management and retrieval-log admin surfaces stay admin-only; assistant operational tools stay read-only and tenant-scoped; user comparison summary stays on the protected user compare page; temporary OCR uploads are discarded after worker processing/review; provider logic stays behind interfaces; secrets remain Vault-backed

**Scale/Scope**: Agency listing create/edit flow, agency lead detail flow, agency assistant chat flow, and the protected user comparison page; no platform-admin work and no new real-time communication channel

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: Uses the existing React + TypeScript apps, FastAPI + Python backend, PostgreSQL + pgvector, Redis, MinIO, and provider interfaces. OCR is explicitly fixed to Azure Computer Vision Read for this phase.
- **Architecture**: Preserves the modular monolith. Work is split across `app/ai/`, `app/listings/`, `app/leads/`, and `app/rag/` plus the existing user/agency React apps. No DAO layer or new service boundary is introduced.
- **Product boundaries**: Does not add buyer-to-agency chat. Agency replies remain draft-only and open externally. The user compare summary is a one-shot AI summary, not a conversational channel.
- **Tenant/RBAC**: Agency assistant and all agency-side AI flows remain tenant-scoped. Support employees gain assistant access but only through read-only operational tools. User comparison summaries use the signed-in user context and public-safe listing fields only.
- **RAG/search**: Existing agency policy RAG remains the grounding layer for policy questions. Assistant operational data access is additive and read-only; homepage search-only boundaries stay unchanged.
- **Reliability/security/performance**: Reuses existing guardrails, PII redaction, JWT session model, Redis-backed limits/caches, PgBouncer-backed DB access, and worker-backed async processing. Temporary OCR files are discarded after extraction, reducing long-lived sensitive artifact exposure.
- **Testing/quality**: Adds unit, integration, RBAC, and UI coverage for each new flow without widening into unrelated e2e scope.

## Project Structure

### Documentation (this feature)

```text
specs/012-agency-ai-workflows/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── agency-ai-workflows-api.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── ai/
│   │   ├── azure_openai.py
│   │   ├── guardrails.py
│   │   ├── jobs.py
│   │   ├── providers.py
│   │   ├── registry.py
│   │   └── router.py
│   ├── listings/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── leads/
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── rag/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   └── common/
│       └── config.py
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

apps/
├── agency/
│   └── src/
│       ├── app/
│       ├── features/
│       │   ├── listings/
│       │   ├── leads/
│       │   └── rag/
│       └── pages/
│           ├── listings/
│           ├── leads/
│           └── rag/
└── user/
    └── src/
        ├── features/
        │   └── comparison/
        └── pages/
            └── comparison/

workers/
```

**Structure Decision**: Extend the existing shared `ai` provider layer, worker handlers, and the current `listings`, `leads`, and `rag` feature modules instead of creating a new top-level assistant module. Agency AI UI stays inside current agency listing/lead/policy pages, and the compare summary stays in the existing protected user comparison page.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
