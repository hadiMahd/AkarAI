# Feature Specification: Backend Core Foundation

**Feature Branch**: `003-backend-core-foundation`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "read PLAN.md and create the spec for Phase 2 only."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Backend Core Reliably (Priority: P1)

A developer can start the backend foundation and confirm that runtime
configuration, lifecycle startup, service connections, logging, and health
status are working before any business feature is added.

**Why this priority**: Every later phase depends on a stable backend runtime
that can start, stop, report health, and connect to required infrastructure.

**Independent Test**: Start the local stack, call the backend health and
readiness checks, and confirm that required service checks pass without using
auth, listings, leads, viewings, RAG, or AI workflows.

**Acceptance Scenarios**:

1. **Given** the local infrastructure is running, **When** the backend starts,
   **Then** it loads central settings, initializes lifecycle resources, and
   exposes successful health status.
2. **Given** a required backing service is unavailable, **When** readiness is
   checked, **Then** the backend reports a not-ready state with the failed
   dependency identified.
3. **Given** the backend receives a request, **When** the request is processed,
   **Then** logs and responses can be correlated with a request identifier.

---

### User Story 2 - Prepare Safe Data and Transaction Foundations (Priority: P1)

A backend developer can use standard data access, transaction, pagination, and
event-recording foundations so later domain features do not invent competing
patterns.

**Why this priority**: Domain phases need shared foundations for consistent
database access, atomic changes, bounded list responses, and reliable async
event handoff.

**Independent Test**: Run migration and backend foundation tests that prove the
base schema, transaction helper, repository contract, pagination helper, and
outbox/inbox event records work without creating business tables.

**Acceptance Scenarios**:

1. **Given** an empty local database, **When** migrations run, **Then** only
   Phase 2 foundation schema changes are applied successfully.
2. **Given** a transaction fails midway, **When** the transaction helper exits,
   **Then** the partial changes are rolled back and no inconsistent state
   remains.
3. **Given** a list-style request uses pagination inputs, **When** pagination
   is applied, **Then** the response has bounded page size and predictable
   metadata.
4. **Given** a future workflow needs async processing, **When** it records an
   event, **Then** the event can be stored once and later marked consumed
   without duplicate side effects.

---

### User Story 3 - Prepare Security Foundations Without Auth Flows (Priority: P1)

A backend developer can rely on shared authentication utility, permission, role,
tenant-context, rate-limit, and audit foundations before protected business
features are implemented.

**Why this priority**: Later multi-tenant features cannot be implemented safely
unless common security foundations exist first.

**Independent Test**: Run foundation tests that prove token utilities,
password hashing utilities, role/permission checks, tenant context placeholders,
rate-limit helpers, and audit records work without exposing login,
registration, or business APIs.

**Acceptance Scenarios**:

1. **Given** a future protected route needs actor context, **When** it depends
   on the Phase 2 placeholders, **Then** it can receive an explicit current-user
   and tenant context contract without implementing login.
2. **Given** a future route needs permission checks, **When** it uses the shared
   permission dependency, **Then** role and permission rules can be evaluated
   through a reusable foundation.
3. **Given** authentication-sensitive actions need throttling or invalidation,
   **When** the foundation helpers are called, **Then** they use consistent
   key formats and invalidation conventions without exposing full auth flows.

---

### User Story 4 - Define Provider and Worker Interfaces Only (Priority: P2)

A backend developer can depend on stable email, AI-provider, and worker
interfaces without selecting or implementing exact external providers in this
phase.

**Why this priority**: Later AI, email, OCR, STT, TTS, reranking, and worker
features need extension points, but choosing providers now would violate the
project rule that unspecified providers require user clarification.

**Independent Test**: Inspect and test the provider and worker contracts to
confirm they are callable placeholders with no provider-specific business
logic or external side effects.

**Acceptance Scenarios**:

1. **Given** the backend loads provider contracts, **When** no concrete
   provider is configured, **Then** the system exposes explicit placeholder
   behavior instead of silently choosing a provider.
2. **Given** the worker process starts, **When** no real jobs are registered,
   **Then** it starts, logs readiness, and shuts down cleanly.
3. **Given** a later feature needs an email or AI capability, **When** it
   depends on the Phase 2 contract, **Then** the provider can be selected later
   without changing feature ownership boundaries.

---

### Edge Cases

- A required environment value is missing or malformed.
- A non-secret setting is present, but the secret value it points to is not
  available through the approved secret path.
- PostgreSQL, PgBouncer, Redis, or MinIO is unavailable during startup or
  readiness checks.
- A database transaction raises an error after writing intermediate state.
- A pagination request asks for a negative page, zero page size, or an
  excessive page size.
- The same outbox or inbox event is observed more than once.
- A future provider interface is called before a concrete provider has been
  selected.
- The worker receives a shutdown signal while idle.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one central settings source for backend,
  worker, database, cache, object storage, request tracing, and provider
  placeholders.
- **FR-002**: The system MUST keep secret values out of committed files and
  treat ordinary environment values as non-secret runtime configuration or
  minimum secret-store bootstrap information only.
- **FR-003**: The backend MUST start and shut down through a managed lifecycle
  that initializes and closes shared infrastructure resources.
- **FR-004**: The backend MUST expose health and readiness status for the
  runtime and required backing services.
- **FR-005**: The system MUST provide a shared asynchronous database session
  path that uses the configured pooled database connection.
- **FR-006**: The system MUST provide shared Redis and object-storage client
  access that can be checked from readiness validation.
- **FR-007**: The system MUST support migrations for foundation schema changes
  and MUST NOT create business domain tables in this phase.
- **FR-008**: The system MUST enable the vector extension required by later RAG
  features if it was not already enabled in Phase 1.
- **FR-009**: The system MUST provide base exception handling with consistent
  error response shape for application-level errors.
- **FR-010**: The system MUST attach a request identifier to backend requests,
  logs, and error responses where a request context exists.
- **FR-011**: The system MUST provide reusable pagination behavior with bounded
  page size and clear response metadata.
- **FR-012**: The system MUST provide a transaction helper or unit-of-work
  pattern that commits successful work and rolls back failed work.
- **FR-013**: The system MUST provide a base repository contract or pattern so
  later feature repositories do not create a competing DAO layer.
- **FR-014**: The system MUST provide foundation role, permission, and
  role-permission records for future RBAC enforcement.
- **FR-015**: The system MAY provide a minimal base user record and refresh
  session record only where needed to test authentication foundation utilities.
- **FR-016**: The system MUST provide password hashing, token utility,
  token-setting, token invalidation, current-user placeholder, and role
  dependency placeholder behavior without exposing full login or registration
  flows.
- **FR-017**: The system MUST provide a tenant context object, tenant
  propagation conventions, and tenant-aware repository guardrails for future
  agency isolation.
- **FR-018**: The system MUST provide Redis-backed rate-limit and cache helper
  foundations with explicit key naming and invalidation conventions.
- **FR-019**: The system MUST provide base audit log records for future
  security and operational events.
- **FR-020**: The system MUST provide base outbox and inbox event records for
  reliable async handoff and duplicate-consumption protection.
- **FR-021**: The system MUST provide a background worker entrypoint that
  starts, logs readiness, handles graceful shutdown, and supports future job
  registration without implementing domain jobs.
- **FR-022**: The system MUST provide an email service interface only, with no
  concrete email provider selected in this phase.
- **FR-023**: The system MUST provide AI provider interfaces only for future
  chat/completion, embedding, reranking, OCR, STT, TTS, image moderation,
  image quality, spam classification, and lead classification.
- **FR-024**: The system MUST provide object-storage helper foundations for
  configured buckets and object path construction without implementing RAG
  ingestion or media processing.
- **FR-025**: The system MUST fail explicitly or return placeholder behavior
  when a provider interface is called before a concrete provider has been
  selected.
- **FR-026**: The system MUST include base tests for configuration loading,
  lifecycle startup, health/readiness, service connectivity checks, exception
  handling, request identifiers, pagination, transaction rollback, repository
  behavior, outbox/inbox records, auth utility behavior, permission utility
  behavior, rate limiting, caching, and worker startup.
- **FR-027**: The Phase 2 scope MUST NOT implement registration endpoints,
  login endpoints, password reset user flows, business auth flows, listings,
  leads, viewings, RAG ingestion, RAG retrieval, AI workflows, media
  processing, email sending, dashboards, frontend business pages, Streamlit
  analytics, or business database tables.

### Key Entities *(include if feature involves data)*

- **Runtime Settings**: Central non-secret runtime configuration and
  secret-store bootstrap references used by backend and worker processes.
- **Service Health Check**: A named dependency check with pass/fail state and
  diagnostic message for readiness reporting.
- **Request Context**: Per-request correlation information used by logging and
  error responses.
- **Base User**: A minimal actor identity record used only where needed for
  future authentication foundation tests.
- **Role**: One of the approved project roles used by future permission checks.
- **Permission**: A named capability that can be assigned to roles.
- **Role Permission**: The association that grants permissions to roles.
- **Refresh Session**: A foundation session or refresh-token record used for
  future invalidation behavior.
- **Tenant Context**: The actor, role, tenant, and permission information that
  future tenant-scoped work must carry.
- **Pagination Parameters**: Page number and page size inputs validated before
  list responses are produced.
- **Pagination Result**: A bounded list response with current page, page size,
  total count where available, and next/previous indicators.
- **Unit of Work**: A transaction boundary that groups writes and event
  recording into all-or-nothing operations.
- **Base Repository Contract**: The common data-access shape used by later
  feature repositories.
- **Outbox Event**: A stored event waiting to be delivered to a worker or
  async consumer.
- **Inbox Event**: A stored consumption record used to prevent duplicate
  processing.
- **Audit Log**: A base security or operational record tied to an actor,
  tenant where applicable, action, and request context.
- **Notification**: A base outbound notification record used to validate
  notification and email abstractions without sending real messages.
- **Provider Contract**: A placeholder capability boundary for future email
  and AI providers.
- **Worker Registration**: A named job placeholder and lifecycle state used by
  the background worker process.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: Phase 2 does not touch AI search, listing AI, leads,
  viewings, marketplace dashboards, or buyer-to-agency communication. It only
  prepares shared backend foundations.
- **Tenant/RBAC Impact**: Phase 2 creates reusable role, permission, tenant
  context, and guardrail foundations only. Full enforcement on business data
  remains in later phases.
- **AI/RAG Scope**: Phase 2 defines provider contracts only. It does not
  implement RAG ingestion, retrieval, embeddings, reranking, OCR, STT, TTS,
  image moderation, or AI business workflows.
- **Reliability/Security/Performance**: Phase 2 covers startup/shutdown,
  request IDs, base exception handling, transaction rollback, outbox/inbox base
  event records, pagination helpers, pooled database connectivity, and no
  committed secret values.
- **Unknowns to Clarify**: Exact AI provider, embedding model, STT provider,
  TTS provider, OCR provider, email provider, background worker library, image
  moderation model, image quality model, spam classifier, and lead classifier
  remain intentionally unselected. Phase 2 must not choose them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can start the backend foundation and receive a
  healthy runtime status within 60 seconds after required local infrastructure
  is available.
- **SC-002**: Readiness status correctly reports all required dependency
  checks as passed when services are available and reports not-ready when any
  required dependency is unavailable.
- **SC-003**: Foundation migrations run successfully from an empty local
  database and create no business domain tables.
- **SC-004**: At least 95% of backend requests in local verification include a
  request identifier in logs or response metadata.
- **SC-005**: Transaction failure tests prove that partial writes are rolled
  back in 100% of covered rollback scenarios.
- **SC-006**: Pagination validation prevents unbounded list requests in 100%
  of covered boundary cases.
- **SC-007**: Duplicate event-consumption tests prove inbox/outbox duplicate
  protection works for 100% of covered duplicate scenarios.
- **SC-008**: Base backend and worker tests pass locally before Phase 3
  planning begins.
- **SC-009**: A scope review finds zero implemented login, registration,
  password reset user flow, business RBAC enforcement flow, business tenant
  isolation flow, listing, lead, viewing, RAG, AI workflow, media pipeline,
  email sending, or dashboard behavior in Phase 2.
- **SC-010**: A repository scan finds zero committed secret values in Phase 2
  files.

## Assumptions

- Phase 1 infrastructure is complete and local services can be started through
  the existing Docker Compose setup.
- `PLAN.md` is the primary phased implementation source of truth for this
  feature.
- Phase 2 uses the existing Phase 1 app skeletons and extends backend
  foundation behavior only.
- Provider choices remain deferred until the phase that actually needs a
  concrete provider.
- Full auth, RBAC, and tenant isolation flows remain later work; Phase 2 covers
  utilities, base records, placeholders, and guardrails only.
