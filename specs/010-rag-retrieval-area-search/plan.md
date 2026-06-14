# Implementation Plan: RAG Retrieval and Reranking

**Branch**: `010-rag-retrieval-openrouter-reranking-and-area-search-rag` | **Date**: 2026-06-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-rag-retrieval-area-search/spec.md`

## Summary

Build tenant-safe agency policy retrieval on top of the existing RAG ingestion foundation. The feature adds a reusable backend retrieval contract, a basic agency policy Q&A screen, reranked evidence ordering, source citations, raw evidence/debug fields for validation, retrieval logs, and repeatable retrieval evaluation baselines. Area knowledge management and area search RAG are intentionally deferred from this phase.

## Technical Context

**Language/Version**: Python 3.11 for backend/admin; TypeScript ^5.5.0 for React apps

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO, Azure OpenAI embeddings, OpenRouter SDK reranking through the existing AI provider interface pattern

**Storage**: PostgreSQL + pgvector for RAG metadata, vectors, retrieval logs, and evaluation run metadata; MinIO for original PDFs and parent page text; Redis only if retrieval caching becomes justified during implementation

**Testing**: Service unit tests, API integration tests, RBAC tenant-isolation tests, retrieval/reranking fallback tests, agency UI tests, and retrieval evaluation smoke runs

**Target Platform**: local Docker Compose

**Project Type**: Modular monolith web platform with background workers

**Performance Goals**: Return 95% of retrieval requests with a grounded answer, ranked evidence, or clear fallback within 5 seconds under local development data volume. Keep retrieval evidence bounded and logs paginated.

**Constraints**: No buyer-to-agency real-time chat; no area search RAG in this phase; tenant isolation for policy documents, chunks, parent pages, retrieval logs, and AI provider calls; provider logic behind interfaces; all secrets read from HashiCorp Vault.

**Scale/Scope**: Multi-tenant agency policy retrieval for Agency Admin and Support Employee roles, with backend contracts reusable by later assistant phases.

## Constitution Check

- **Fixed stack**: Uses React + TypeScript, FastAPI + Python, PostgreSQL + pgvector, Redis where justified, MinIO, and existing background-worker foundations. Azure OpenAI embeddings are already configured; OpenRouter is the selected reranking provider for this phase per user direction.
- **Architecture**: Preserves the modular monolith and feature folders. Adds retrieval behavior under `backend/app/rag/` and provider integration under `backend/app/ai/`; no DAO layer or microservice split.
- **Product boundaries**: Adds agency policy Q&A and retrieval contracts only. Does not add buyer-to-agency chat, listing page AI chat, generated replies, voice search, or area search RAG.
- **Tenant/RBAC**: Retrieval is tenant-scoped to the requesting agency and role-checked for Agency Admin and Support Employee. Retrieval logs retain tenant and actor scope.
- **RAG/search**: Keeps PostgreSQL as RAG metadata and vector source of truth, MinIO as parent page/object storage, pgvector for vector retrieval, and reranking behind a provider interface. Area RAG is explicitly deferred.
- **Reliability/security/performance**: Logs retrieval outcomes, provider fallbacks, confidence outcomes, and selected sources. Secrets remain Vault-backed. Retrieval returns bounded evidence and avoids unnecessary PII in logs.
- **Testing/quality**: Requires service, API, RBAC, provider fallback, UI, and evaluation tests.

## Project Structure

### Documentation (this feature)

```text
specs/010-rag-retrieval-area-search/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── rag-retrieval.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── ai/
│   │   ├── providers.py
│   │   ├── registry.py
│   │   └── openrouter.py
│   └── rag/
│       ├── router.py
│       ├── service.py
│       ├── repository.py
│       ├── schemas.py
│       ├── models.py
│       └── retrieval.py
└── tests/
    ├── unit/
    │   ├── test_rag_retrieval.py
    │   └── test_openrouter_reranker.py
    ├── integration/
    │   └── test_rag_retrieval_api.py
    └── rbac/
        └── test_rag_retrieval_tenant_isolation.py

apps/
└── agency/
    └── src/
        ├── features/
        │   └── rag/
        └── pages/
            └── rag/

scripts/
└── ci/
    └── run_rag_eval.py

backend/tests/fixtures/
└── rag_eval/
    └── policy_retrieval_baseline.jsonl
```

**Structure Decision**: Keep retrieval in the existing `rag` module and provider-specific reranking in `ai`. The agency app receives only the basic policy Q&A screen and hooks needed to validate retrieval behavior.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
