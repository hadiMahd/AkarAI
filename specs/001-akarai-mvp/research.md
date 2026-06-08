# Research: Akarai MVP

## Modular Monolith vs Microservices

Decision: Start with a modular monolith.

Rationale: The MVP needs strong consistency across listings, leads, viewings,
RAG metadata, audit logs, and outbox events. A modular monolith keeps feature
ownership clear without adding service discovery, distributed transactions, or
deployment overhead.

Alternatives considered: Full microservices were rejected because the project
does not yet need independent scaling per domain. A single unstructured app was
rejected because tenant/RBAC/RAG boundaries need clear module ownership.

## FastAPI Architecture

Decision: Use FastAPI feature folders with `router.py`, `service.py`,
`repository.py`, `schemas.py`, and `models.py`; add `query_service.py` only for
read-heavy areas.

Rationale: This matches the constitution, keeps HTTP, business logic, data
access, validation, and persistence separated, and avoids DAO/repository
duplication.

Alternatives considered: Generic layered folders were rejected because feature
locality matters more for this domain. DAO plus repository was rejected as
duplicate abstraction.

## PostgreSQL + pgvector

Decision: Use PostgreSQL as transactional source of truth and pgvector for
embeddings with minimal filter metadata.

Rationale: Leads, scheduled viewings, RAG metadata, audit logs, tenant
ownership, and domain events need transactional consistency. pgvector keeps
vector retrieval close to metadata and filtering.

Alternatives considered: External vector DB was rejected for MVP complexity.
Document-only metadata was rejected because RAG chunk lifecycle needs
transactional records and deletion tracking.

## Redis Queues, Cache, Rate Limiting, Token Blacklist

Decision: Use Redis for queues/workers, rate limits, cache, and token
blacklist/session invalidation.

Rationale: Redis covers the MVP's async and transient state needs with a small
operational footprint.

Alternatives considered: Dedicated queue services were rejected until
deployment target is known. In-process queues were rejected because OCR, RAG,
email, and image jobs need retryable background execution.

## MinIO Blob Storage

Decision: Use MinIO for original documents, extracted page text, and uploaded
listing images.

Rationale: MinIO provides local S3-compatible object storage and keeps large
files out of PostgreSQL while PostgreSQL retains metadata and blob links.

Alternatives considered: Filesystem-only storage was rejected because it does
not model production object storage. Storing blobs in PostgreSQL was rejected
for large files and image/document workloads.

## PgBouncer

Decision: Use PgBouncer for PostgreSQL connection pooling.

Rationale: FastAPI, workers, and admin processes can create many connections.
PgBouncer prevents connection exhaustion and matches the constitution.

Alternatives considered: Direct application connections were rejected because
multiple processes and async workloads can exceed database connection limits.

## RAG Architecture

Decision: Use PostgreSQL metadata, MinIO parent page text, pgvector child
embeddings, tenant metadata filtering, parent-child retrieval, and
re-ingestion by chunk hash comparison.

Rationale: The system needs auditable source links, tenant safety, parent page
context for answer grounding, and deterministic cleanup of stale chunks.

Alternatives considered: Embedding full pages only was rejected for retrieval
precision. Storing all text in vectors only was rejected because parent context
and source metadata need a durable source of truth.

## Cohere Reranking

Decision: Use Cohere rerankers where useful for policy RAG, support assistant
RAG, and area/neighborhood RAG.

Rationale: Reranking improves answer relevance after hybrid retrieval without
changing the source-of-truth metadata model.

Alternatives considered: No reranking was rejected for vague area and policy
questions where initial retrieval may be noisy. Always reranking every query
was rejected because it can add latency and cost.

## Outbox/Inbox

Decision: Use outbox/inbox where async reliability matters, including
`lead.created`, `viewing.scheduled`, `viewing.cancelled`,
`rag.document_uploaded`, `listing.image_uploaded`, and
`email.notification_requested`.

Rationale: Critical writes and event recording must commit together. Workers
must be idempotent because queue delivery is at-least-once.

Alternatives considered: Direct event publish inside request handlers was
rejected because failed publishes can leave invisible side effects.

## Lightweight CQRS

Decision: Use `query_service.py` only for listing search, agency dashboard,
platform demand insights, RAG retrieval, leads list, and viewing schedules list.

Rationale: These areas are read-heavy and benefit from specialized query
composition without splitting the entire domain model.

Alternatives considered: CQRS everywhere was rejected as over-engineering.
No read services was rejected because search/dashboard/RAG queries will become
hard to maintain inside write services.

## JWT Refresh and Invalidation

Decision: Use short-lived access tokens, refresh tokens, and Redis-backed
blacklist/session invalidation for logout, password reset, employee
deactivation, and suspicious session revocation.

Rationale: The product needs persistent login and immediate revocation for
employee and tenant security.

Alternatives considered: Access tokens only were rejected because users and
employees need continued login. Long-lived access tokens were rejected because
revocation risk is too high.

## Streamlit Platform Admin

Decision: Build the platform admin dashboard in Streamlit.

Rationale: It is internal/admin-facing, data-heavy, and specified by the
constitution. Streamlit keeps demand insights and audit review efficient for
the MVP.

Alternatives considered: A React platform admin was rejected because the
constitution explicitly excludes it.

## React + TypeScript User and Agency UI

Decision: Build separate React + TypeScript apps for the user app and agency
dashboard.

Rationale: The user app and agency dashboard have different navigation,
permissions, and workflows while sharing API contracts.

Alternatives considered: One combined React app was rejected because user and
agency roles have different information architecture. Server-rendered UI was
rejected because the MVP includes interactive comparison, dashboards, and AI
widgets.

## Provider and Library TBDs

Decision: Exact LLM provider, embedding model, STT provider, TTS provider, OCR
provider, email provider, React UI library, worker library, auth library, and
deployment target remain `TBD`.

Rationale: The constitution requires asking the user for unspecified provider
or library choices. The plan keeps these decisions behind interfaces so tasks
can be generated without hardcoding provider-specific logic.

Alternatives considered: Picking defaults was rejected because the user
explicitly requested TBD/clarification for these choices.
