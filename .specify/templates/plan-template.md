# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python [version or NEEDS CLARIFICATION] for backend/admin; TypeScript [version or NEEDS CLARIFICATION] for React apps

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO, Cohere rerankers where useful; [additional libraries or NEEDS CLARIFICATION]

**Storage**: PostgreSQL + pgvector for metadata/search/vector data; MinIO for blobs/text; Redis for cache/queue/rate limit/token blacklist

**Testing**: Service unit tests, API integration tests, transaction behavior tests, RBAC tenant-isolation tests, and RAG ingestion tests when RAG changes

**Target Platform**: Web apps plus FastAPI/Streamlit services on [deployment target or NEEDS CLARIFICATION]

**Project Type**: Modular monolith web platform with background workers

**Performance Goals**: Paginated data access, non-blocking FastAPI I/O, bounded search/RAG latency targets [specific numbers or NEEDS CLARIFICATION]

**Constraints**: No buyer-to-agency real-time chat; tenant isolation for agency data/RAG/tool calls; provider logic behind interfaces; all secrets read from HashiCorp Vault; unspecified providers/libraries require user clarification

**Scale/Scope**: Multi-tenant agency platform covering user app, agency dashboard, platform admin, AI search/RAG, leads, and viewings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: Uses React + TypeScript, Streamlit + Python, FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, and background workers. Any missing library/provider choice is marked `NEEDS CLARIFICATION`.
- **Architecture**: Preserves the modular monolith and feature folders; does not introduce microservices or duplicate DAO/repository layers.
- **Product boundaries**: Does not add buyer-to-agency real-time chat; keeps homepage AI search-only; separates leads from scheduled viewings.
- **Tenant/RBAC**: Enforces tenant ID and role permissions for data access, RAG chunks, AI tool calls, audit logs, and metrics.
- **RAG/search**: Keeps PostgreSQL as RAG metadata source of truth, MinIO as blob/text storage, pgvector for embeddings, and area RAG separate from agency policy RAG.
- **Reliability/security/performance**: Uses transactions for critical flows, idempotent async events where needed, JWT invalidation, rate limits, PII redaction, HashiCorp Vault secret access, pagination, PgBouncer, async I/O, and explicit cache invalidation.
- **Testing/quality**: Includes required unit, integration, transaction, RAG, and RBAC tests where applicable; avoids unused architecture patterns.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/
├── app/
│   ├── users/
│   ├── agencies/
│   ├── listings/
│   ├── leads/
│   ├── viewings/
│   ├── rag/
│   ├── ai/
│   ├── auth/
│   └── notifications/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

apps/
├── user/          # React + TypeScript
└── agency/        # React + TypeScript

admin/             # Streamlit + Python

workers/
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
