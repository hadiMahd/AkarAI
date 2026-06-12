# Implementation Plan: Media Pipeline and Listing Image Processing

**Branch**: `008-media-pipeline-and-listing-image-processing` | **Date**: 2026-06-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-media-pipeline-and-listing-image-processing/spec.md`, root [PLAN.md](../../PLAN.md), project constitution, and completed Phase 1-6 foundations.

## Summary

Implement Phase 7 as the media-processing layer for listing photos. The phase adds tenant-scoped photo upload into the existing `property-media` MinIO bucket, validates file type and size before storage, runs Hugging Face NSFW moderation with `Falconsai/nsfw_image_detection`, evaluates blur with Laplacian variance, stores accepted originals privately, generates public-safe optimized WebP derivatives, and records audit and processing state so agency admins can see whether a photo is pending, accepted, warning, rejected, or failed. The work stays inside the existing modular monolith and uses the current listing/media/domain-event foundation rather than introducing a new subsystem.

## Technical Context

**Language/Version**: Python 3.11 for backend and workers; TypeScript 5.5 with React 18.3 for the agency app.

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO, Hugging Face `huggingface-hub` client for NSFW moderation, OpenCV headless for Laplacian blur scoring, Pillow for WebP conversion, and the existing background worker/outbox stack.

**Storage**: PostgreSQL remains the source of truth for listing photo metadata, processing state, audit logs, and derivatives; MinIO stores original uploads privately and optimized derivatives under the existing `property-media` bucket; Redis continues to support cache, queue, and rate-limit duties.

**Testing**: Backend unit tests for upload validation, moderation, blur scoring, and status transitions; backend integration tests for listing photo upload, processing outcomes, tenant isolation, and media access control; worker tests for outbox-driven processing; agency-app tests for upload form, status display, and error states.

**Target Platform**: Local Docker Compose stack with the existing `backend`, `worker`, `agency-app`, `minio`, `redis`, and `pgbouncer` services.

**Project Type**: Modular monolith web platform with background workers.

**Performance Goals**: Upload validation should fail fast before durable storage when possible; accepted uploads should show a visible processing state immediately; 95% of valid uploads should reach a terminal status within about 60 seconds on the local stack; optimized derivatives should be available for display without forcing manual refreshes.

**Constraints**: No buyer-to-agency chat, no AI search, no RAG ingestion, no OCR extraction, and no media workflow outside listing photos in this phase; media moderation and quality checks must stay behind provider interfaces; all secrets remain Vault-backed; tenant isolation must hold for metadata, object paths, worker jobs, and logs.

**Scale/Scope**: Phase 7 covers listing-photo upload, moderation, quality assessment, derivative generation, access strategy, and auditability only. It does not add broader document ingestion, listing AI, or agency dashboard AI features.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses the existing Python backend, React agency app, PostgreSQL, Redis, MinIO, and worker stack.
- **Architecture**: PASS. Preserves the modular monolith and existing feature folders; any new logic stays in the current backend modules and workers.
- **Product boundaries**: PASS. The phase is limited to listing-photo media handling and does not add chat, search, RAG, or AI listing answers.
- **Tenant/RBAC**: PASS. Uploads, metadata, and processing remain tenant-scoped and admin-managed.
- **RAG/search**: PASS. No RAG or search feature is introduced.
- **Reliability/security/performance**: PASS. The design uses upload validation, asynchronous worker processing, explicit audit logging, public-safe derivative delivery, and tenant-scoped object paths.
- **Testing/quality**: PASS. The plan requires focused unit, integration, worker, and frontend validation around the new media workflow.

## Project Structure

### Documentation (this feature)

```text
specs/008-media-pipeline-and-listing-image-processing/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── listing-media.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── common/
│   │   ├── storage.py
│   │   ├── events.py
│   │   └── ...
│   ├── listings/
│   ├── agencies/
│   ├── auth/
│   └── workers/
└── tests/
    ├── unit/
    ├── integration/
    └── rbac/

apps/
├── user/
└── agency/

workers/
```

**Structure Decision**: Keep media logic inside the existing backend `listings`, `common`, and worker code paths, with the agency UI only adding the upload and status surfaces needed for listing photos. Do not introduce a separate media service.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover local Docker Compose deployment, MinIO `property-media` usage, Hugging Face NSFW moderation, Laplacian-based quality scoring, outbox-driven worker processing, and the public-safe derivative access strategy.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API / workflow contracts: [contracts/listing-media.md](./contracts/listing-media.md)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Final design stays on the repo’s existing Python/React/MinIO/Redis/PostgreSQL stack.
- **Architecture**: PASS. Media code remains inside the modular monolith and worker flow.
- **Product boundaries**: PASS. The design stays inside listing photo processing only.
- **Tenant/RBAC**: PASS. Uploads and processing remain tenant-scoped.
- **RAG/search**: PASS. No RAG or search behavior is introduced.
- **Reliability/security/performance**: PASS. The design preserves validation-first uploads, asynchronous processing, explicit audit logging, and public-safe derivative delivery.
- **Testing/quality**: PASS. The plan requires backend, worker, and agency-app coverage for the upload and processing lifecycle.
