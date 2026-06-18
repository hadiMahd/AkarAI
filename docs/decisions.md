# Technical Decisions

This document captures the decisions that are most worth explaining to a reviewer, interviewer, or engineer onboarding to the project.

## 1. Modular monolith first, not microservices

### Decision

Keep the platform as a modular monolith with background workers and a dedicated model-service only where separation is clearly worth it.

### Why

- auth, tenancy, RLS, transactions, and audit rules are cross-cutting
- premature service splitting would increase operational overhead fast
- most domains still benefit from shared schemas and local transactions

## 2. Repository + service + router separation, no DAO layer

### Decision

Use `repository.py` as the data-access layer and keep business logic in `service.py`.

### Why

- avoids duplicated persistence abstractions
- makes files predictable
- keeps HTTP concerns out of persistence
- matches the project’s architecture rule set

## 3. PostgreSQL + pgvector as the core data platform

### Decision

Use PostgreSQL as the transactional source of truth and pgvector for retrieval embeddings.

### Why

- domain writes, history, audits, and auth records need strong transactional behavior
- RAG metadata and vectors benefit from staying close to the domain source of truth
- it avoids introducing a second search datastore too early

## 4. PgBouncer on the runtime path

### Decision

Use PgBouncer in front of PostgreSQL for app/runtime traffic.

### Why

- async app surfaces and workers can create bursty connection patterns
- pooling is a pragmatic hardening step for a multi-surface system

## 5. Vault-backed secrets bootstrap

### Decision

Load runtime secrets through centralized configuration and Vault bootstrap.

### Why

- avoids scattering secret handling across services
- keeps provider credentials and JWT secrets out of ad hoc local code paths

## 6. Redis for more than caching

### Decision

Use Redis for:

- rate limiting
- token blacklist/session invalidation
- cache invalidation
- short-lived cached read models

### Why

- these are hot-path, bounded-lifetime concerns
- Redis is a better fit than database-only implementations for this shape of traffic

## 7. Refresh tokens + invalidation, not stateless-only JWT auth

### Decision

Use short-lived access tokens with refresh sessions, rotation, and invalidation markers.

### Why

- logout, password reset, employee deactivation, and suspicious-session revocation need real invalidation
- fully stateless JWT auth is operationally weaker for this product

## 8. Transaction-scoped RLS context

### Decision

Apply tenant/user/role context to database sessions through transaction-scoped `set_config`.

### Why

- tenant isolation should not rely only on route-level discipline
- this adds a database-side enforcement layer
- it helps contain mistakes in upper layers

## 9. Durable outbox pattern for async side effects

### Decision

Record outbox rows in the same transaction as source business writes and let workers process them.

### Why

- prevents write-succeeded / event-lost races
- gives retries and dead-letter state explicit persistence
- fits RAG ingestion, media processing, and lead classification well

## 10. Dedicated model service for lead inference

### Decision

Run lead classification in `model-service/` instead of embedding model runtime directly in the API process.

### Why

- isolates model dependencies
- allows independent scaling and rollout
- keeps the main API process focused on domain and orchestration logic

## 11. OpenRouter reranking on top of pgvector recall

### Decision

Use vector search for recall and reranking for better final ordering.

### Why

- vector similarity alone is often enough for recall but not ideal ranking
- reranking is a smaller increment than replacing the whole storage design

## 12. Shared guardrails layer for AI generation

### Decision

Route policy answers and agency drafting features through shared guarded generation helpers.

### Why

- prevents feature-by-feature policy drift
- centralizes injection detection, safety checks, and output blocking
- keeps future AI features aligned with the same safety model

## 13. Presidio-backed PII redaction with regex fallback

### Decision

Use Presidio where possible, but never fail open if it is unavailable.

### Why

- PII protection needs a real detection layer
- operationally, fallback matters as much as the primary tool
- a good redaction system must degrade safely

## 14. Azure Whisper for voice search

### Decision

Use Azure Whisper as the speech-to-text path for voice search.

### Why

- provider choice was already fixed in project direction
- backend-owned STT keeps logs, rate limits, and failure handling consistent

## 15. Azure Computer Vision Read for OCR

### Decision

Use Azure Computer Vision Read for listing spec-sheet OCR.

### Why

- good fit for document-style extraction
- provider abstraction already exists
- keeps OCR off the frontend and inside audited backend workflows

## 16. Laplacian blur scoring over a CNN

### Decision

Use Laplacian variance for blur detection in the listing-media pipeline.

### Why

- artifact comparison showed similar practical detection quality
- much lower compute and system complexity
- easier debugging and calibration

### Evidence

- [CNN vs Laplacian metrics](artifacts/laplacian-vs-cnn/cnn-vs-lapl-metrics.png)
- [Accuracy comparison](artifacts/laplacian-vs-cnn/cnn-vs-laplacian-test-acc.png)
- [Laplacian notebook](artifacts/laplacian-vs-cnn/blur_laplacian_vs_cnn_kaggle_notebook.ipynb)

## 17. WebP derivatives for listings

### Decision

Generate optimized WebP derivatives for listing display while keeping originals private.

### Why

- better storage and delivery efficiency
- clearer separation between internal originals and browser-facing assets

## 18. Read-only platform admin over backend APIs

### Decision

Do not let the Streamlit admin app query Postgres directly.

### Why

- preserves backend authorization and redaction logic
- keeps platform-admin behavior read-only and shaped
- avoids a second data-access path with weaker controls

## 19. CQRS only where it pays off

### Decision

Use `query_service.py` selectively for aggregate and read-optimized views.

### Why

- some reads deserve their own shaping path
- most CRUD flows do not need full CQRS ceremony

## 20. Production-oriented evaluation, not only local demos

### Decision

Document and run deterministic quality slices plus live RAG evals.

### Why

- retrieval quality, latency, and tenant leakage should be measurable
- CI should separate deterministic checks from provider-dependent judge runs
