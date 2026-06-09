# Research: Backend Core Foundation

## SQLAlchemy Async Session Pattern

Decision: Use one shared async engine and async session factory for backend
database access, exposed through a common session dependency.

Rationale: Phase 1 already uses async database connectivity and the project
constitution requires async/non-blocking I/O where practical. A single session
factory keeps future repositories consistent and avoids competing connection
patterns.

Alternatives considered: Direct per-feature engines were rejected because they
fragment pooling and settings. Synchronous database access was rejected because
the backend is async-first.

## PgBouncer Connection Strategy

Decision: Application database URLs should route through PgBouncer for normal
runtime access, with migration tooling allowed to use the configured migration
connection if needed.

Rationale: PgBouncer is part of the fixed stack and keeps connection usage
bounded. Some migration operations may need direct connection behavior later,
so the settings layer should keep runtime and migration URLs distinct.

Alternatives considered: Direct PostgreSQL-only runtime access was rejected
because it bypasses required pooling.

## Transaction Helper Pattern

Decision: Provide a unit-of-work style transaction helper around the shared
session that commits on success and rolls back on failure.

Rationale: Later phases require all-or-nothing behavior for lead creation,
viewing booking, listing publish, RAG metadata writes, event recording, and
review updates. A common helper prevents each feature from inventing its own
transaction convention.

Alternatives considered: Manual commit/rollback in every service was rejected
because it increases partial-commit risk.

## Repository, Service, Router Architecture

Decision: Preserve feature modules with router, service, repository, schemas,
and models files; create a base repository contract in common; do not create
DAO files.

Rationale: This matches the constitution and keeps data access ownership clear.
The common base should provide conventions, not a heavy generic abstraction
that hides feature-specific behavior.

Alternatives considered: DAO plus repository was rejected by constitution.
Direct database access in routers was rejected because it mixes HTTP and data
access responsibilities.

## RBAC Foundation

Decision: Define the approved roles, permission records, role-permission
mapping, and reusable permission-check placeholders in Phase 2.

Rationale: Later protected features need the same role vocabulary from the
start: User, Agency Admin, Support Employee, and Platform Admin. Phase 2 should
prepare the foundation but not implement full endpoint authorization flows.

Alternatives considered: Delaying all RBAC schema until Phase 3 was rejected
because the Phase 2 brief explicitly allows foundation models and utility
tests. Implementing full RBAC enforcement now was rejected as out of scope.

## Tenant Context Foundation

Decision: Provide a tenant context object and propagation strategy that carries
actor ID, role, permissions, tenant ID where applicable, request ID, and source
metadata.

Rationale: Tenant isolation is mandatory for future agency-owned data, AI tool
calls, audit logs, RAG chunks, and metrics. Phase 2 can define the shared shape
without creating tenant-owned business data.

Alternatives considered: Passing raw tenant IDs as loose parameters was
rejected because it weakens auditability and permission checks.

## Redis Rate Limiting

Decision: Plan a Redis-backed rate limiter with explicit key formats by
IP/session/user and configurable windows and limits.

Rationale: Later auth, AI, search, uploads, lead creation, and viewing booking
need consistent throttling. Redis is fixed for rate limiting.

Alternatives considered: In-memory rate limiting was rejected because it does
not work reliably across multiple processes.

## Redis Caching

Decision: Provide a cache wrapper with namespaced keys, TTLs, and explicit
invalidation conventions.

Rationale: Later listing search, dashboard metrics, RAG retrieval, and demand
insights need predictable invalidation. A common naming convention prevents
key collisions.

Alternatives considered: Feature-local Redis calls were rejected because they
encourage inconsistent key formats.

## Outbox and Inbox Foundation

Decision: Create base outbox_events and inbox_events records with status,
idempotency key, retry counts, scheduling, error fields, and consumed markers.

Rationale: Queue delivery is at-least-once. Later events such as lead.created,
viewing.scheduled, viewing.cancelled, rag.document_uploaded,
listing.image_uploaded, and email.notification_requested need reliable handoff
and duplicate protection.

Alternatives considered: Fire-and-forget worker calls were rejected because
they can lose side effects. Full event streaming infrastructure was rejected
as unnecessary for the MVP foundation.

## MinIO Abstraction

Decision: Provide object storage helpers for bucket configuration, object path
construction, upload/download, existence checks, and optional presigned URL
planning.

Rationale: Later RAG and media phases depend on stable bucket and path
conventions. Phase 2 should not implement RAG ingestion or image processing.

Alternatives considered: Direct MinIO calls inside feature services were
rejected because they duplicate path and bucket rules.

## AI Provider Interface Abstraction

Decision: Define provider contracts for chat/completion, embeddings,
reranking, OCR, STT, TTS, image moderation, image quality, spam classification,
and lead classification. Concrete providers remain `TBD_ASK_USER`.

Rationale: The constitution requires provider interfaces and user
clarification for unspecified providers. Phase 2 can define the boundaries
without choosing providers or implementing workflows.

Alternatives considered: Choosing default providers now was rejected because
the user has not selected exact providers or models.

## Notification and Email Abstraction

Decision: Define notification records, email service interface, and
email.notification_requested event payload conventions. Concrete email
provider remains `TBD_ASK_USER`.

Rationale: Later viewing reminders and lead notifications need reliable
event-driven email behavior, but Phase 2 should not send emails.

Alternatives considered: Direct email sending from business services was
rejected because it couples transactions to external side effects.

## Error and Response Pattern

Decision: Use consistent application error responses with status, detail,
request ID, and optional error code, plus standardized success metadata where
useful.

Rationale: Request correlation and predictable error shapes help debugging and
future frontend integration.

Alternatives considered: Framework-default error shapes only were rejected
because they do not consistently include application codes or request IDs.

## Testing Foundation

Decision: Plan unit and integration tests for app startup, health,
dependency checks, settings loading, exception response format, request IDs,
pagination, rate limiting, cache helpers, database connectivity, transaction
rollback, PgBouncer connectivity, Redis, MinIO, auth utilities, permission
checks, outbox/inbox idempotency, and worker startup.

Rationale: Phase 2 is shared foundation work; regressions here would affect
every later phase.

Alternatives considered: Smoke tests only were rejected because utility and
transaction behavior require focused tests.
