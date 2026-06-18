# Architecture

## Overview

AkarAI is built as a modular monolith with separate runtime surfaces rather than a distributed microservice mesh. That choice keeps tenancy, auth, transactions, RAG, and audit logic coherent while still allowing specialized processes for background work and model inference.

## Runtime topology

```text
apps/user        React user-facing app
apps/agency      React agency dashboard
admin/           Streamlit platform-admin app
backend/         FastAPI modular monolith
workers/         async event consumers
model-service/   dedicated lead inference service
```

Supporting infrastructure:

- PostgreSQL as the transactional source of truth
- pgvector for retrieval embeddings
- Redis for caching, rate limiting, invalidation, and token/session state
- MinIO for private blobs and derived media assets
- PgBouncer for the runtime DB connection path
- Vault for secrets bootstrap

## Backend design

Each backend feature follows the same layout:

```text
backend/app/<feature>/
  router.py
  service.py
  repository.py
  schemas.py
  models.py
  query_service.py  # only where useful
```

Responsibilities:

- `router.py`: request/response wiring and auth dependencies
- `service.py`: business rules, transaction coordination, side effects
- `repository.py`: CRUD and ORM access
- `query_service.py`: read-optimized CQRS path for aggregate or complex reads

This keeps transport, domain logic, and persistence separate without adding a redundant DAO layer.

## Tenant isolation and RBAC

Tenant safety is enforced in multiple layers:

- role/permission dependencies at the FastAPI boundary
- tenant context propagation through shared dependencies
- PostgreSQL row-level security with transaction-scoped `set_config(...)`
- feature-level service checks for agency, support, and platform-admin boundaries

Key properties:

- agency data stays tenant-scoped
- support roles are constrained where admin-only writes/reads matter
- platform-admin routes are isolated and read-only

The platform-admin dashboard is especially strict: the actor must be `platform_admin` and must also hold `platform:dashboard_read`.

## Data and storage strategy

### PostgreSQL

Used for:

- auth and session records
- agency, listing, lead, and viewing domain data
- AI/RAG job metadata
- audit and domain-event logs
- outbox/inbox coordination

### pgvector

Used for tenant-scoped RAG chunk embeddings and similarity search.

### MinIO

Used for:

- original RAG documents
- extracted page text
- original listing images
- public-safe WebP derivatives

### Redis

Used for:

- auth token blacklisting
- session invalidation markers
- rate limits
- listing/platform cache invalidation
- cached response payloads

## Event-driven work

The project uses a DB-backed outbox pattern for reliable async handoff.

Flow:

1. a write request commits the business row and outbox row together
2. workers claim events with `FOR UPDATE SKIP LOCKED`
3. handlers process the work
4. events are marked delivered, retried with backoff, or dead-lettered

Why this matters:

- avoids lost side effects
- supports at-least-once delivery semantics
- keeps retries explicit
- allows business writes to stay all-or-nothing

Current event-driven areas include:

- `rag.document_uploaded`
- `listing.image_uploaded`
- `lead.created`
- notification-related event scaffolding

## AI architecture

The backend owns all provider interactions. Browsers never call LLM, OCR, STT, or moderation providers directly.

Provider interfaces exist for:

- chat
- embeddings
- reranking
- OCR
- STT
- TTS
- image moderation
- image quality
- spam classification
- lead classification

That indirection is what makes fallback, testing, redaction, and future provider swaps manageable.

## RAG architecture

RAG is split into ingestion and retrieval.

### Ingestion

1. upload tenant-scoped PDF
2. store original in MinIO
3. write document metadata and outbox row atomically
4. worker extracts page text
5. worker chunks pages with FastCDC child chunks
6. embed new chunks with Azure OpenAI embeddings
7. store vectors in pgvector
8. orphan stale chunks on replace

### Retrieval

1. embed query
2. vector search in pgvector
3. fetch parent-page context
4. re-check document status to avoid stale replace races
5. rerank through OpenRouter when available
6. assemble citations/evidence/debug metadata
7. run guarded answer generation

## Media-processing architecture

Listing media is asynchronous and audit-heavy.

1. upload original image
2. validate bytes and dimensions
3. moderate NSFW content
4. score blur with Laplacian variance
5. produce optimized WebP derivative
6. persist photo and derivative metadata
7. log audit outcome

The result states are operationally useful:

- `accepted`
- `warning`
- `rejected`
- `failed`

## Model-serving architecture

Lead inference is deliberately separated into `model-service/`:

- main backend saves lead first
- backend emits `lead.created`
- worker forwards the payload
- model service performs spam detection, then hot-vs-normal ranking
- model service calls back to the backend
- backend persists results idempotently

This keeps the API process from owning heavy model dependencies and creates a cleaner scaling boundary.

## Frontend architecture

The React apps use feature folders and query-driven state patterns. The admin app is intentionally separate because its audience, access model, and presentation style are different.

Patterns used across frontend surfaces:

- TanStack Query for server state
- route guards for protected surfaces
- paginated list views
- skeleton/loading states
- explicit empty/error states

## Operational architecture notes

- startup loads secrets from Vault through centralized config
- lifespan hooks initialize logging, Redis, and shared runtime resources
- app code stays async on I/O paths
- platform dashboards use cache-aware read APIs rather than direct DB access from Streamlit
