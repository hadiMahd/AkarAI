# Implementation Plan: Lead Processing Pipeline

**Branch**: `[013-lead-processing-pipeline]` | **Date**: 2026-06-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-lead-processing-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add two-stage lead processing for new inquiries: save the lead first, emit `lead.created`, have the worker forward the job to a dedicated lead model service, classify spam first, then Hot/Normal for non-spam, and persist the results plus review metadata. Empty-message leads are treated as spam, duplicate submissions remain separate leads with per-lead idempotent processing, late callbacks may update classification fields without touching review state, and agency lead views auto-refresh while classification is pending. Use the simpler callback path for result delivery so the model service can stay scalable without adding queue consumer complexity in the API.

## Technical Context

**Language/Version**: Python 3.12 for backend/admin; TypeScript 5.x for React apps

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO, OpenRouter reranking where useful; scikit-learn/joblib for the spam model runtime and Transformers/PyTorch for the Hot/Normal ranker runtime

**Storage**: PostgreSQL + pgvector for metadata/search/vector data; MinIO for blobs/text; Redis for cache/queue/rate limit/token blacklist

**Testing**: Service unit tests, API integration tests, transaction behavior tests, RBAC tenant-isolation tests, and worker/model-service tests for retry and callback behavior

**Target Platform**: Web apps plus FastAPI/Streamlit services on local Docker Compose

**Project Type**: Modular monolith web platform with background workers and a separate model inference service

**Performance Goals**: Lead creation remains fast because classification is asynchronous; classification retries are bounded; lead processing results are visible without manual refresh after the callback succeeds because agency lead surfaces repoll while status is pending

**Constraints**: No buyer-to-agency real-time chat; tenant isolation for agency data/RAG/tool calls; provider logic behind interfaces; all secrets read from HashiCorp Vault; unspecified providers/libraries require user clarification

**Scale/Scope**: Multi-tenant agency platform covering user app, agency dashboard, platform admin, AI search/RAG, leads, and viewings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: Uses React + TypeScript, Streamlit + Python, FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, background workers, and a separate inference service. Any missing library/provider choice is marked `NEEDS CLARIFICATION`.
- **Architecture**: Preserves the modular monolith plus separate model service; does not introduce duplicate DAO/repository layers.
- **Product boundaries**: Does not add buyer-to-agency real-time chat; keeps homepage AI search-only; separates leads from scheduled viewings.
- **Tenant/RBAC**: Enforces tenant ID and role permissions for lead data, classification results, review actions, audit logs, and metrics.
- **RAG/search**: No new RAG scope; lead processing is isolated from area RAG and policy RAG.
- **Reliability/security/performance**: Uses transactions for lead creation and result persistence, idempotent async events, retry/backoff for model inference, JWT invalidation, rate limits, PII redaction, HashiCorp Vault secret access, pagination, PgBouncer, async I/O, and explicit cache invalidation.
- **Testing/quality**: Includes required unit, integration, transaction, worker, and RBAC tests where applicable; avoids unused architecture patterns.

## Project Structure

### Documentation (this feature)

```text
specs/013-lead-processing-pipeline/
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
│   ├── leads/
│   ├── common/
│   ├── ai/
│   ├── auth/
│   └── audit/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

apps/
├── user/
└── agency/

workers/
└── handlers/

model-service/
```

**Structure Decision**: Keep lead CRUD and result persistence in the existing backend `leads` and `common` modules, use the existing worker entrypoint for `lead.created`, use existing `domain_event_logs` plus lead result tables as the reporting source, and add a dedicated `model-service/` app for spam and Hot/Normal inference so scaling stays independent from the main API.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate model service | Needed for scalable inference and independent rollout | Embedding inference inside the main API would tie latency and scaling to user traffic |
