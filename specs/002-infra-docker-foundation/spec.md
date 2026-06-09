# Feature Specification: Infrastructure and Docker Compose Foundation

**Feature Branch**: `002-infra-docker-foundation`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "read PLAN.md and make a spec for Phase 1 — Infrastructure and Docker Compose Foundation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start the Local Platform Foundation (Priority: P1)

A developer can start the local foundation and see every required platform
service become available without implementing any product feature.

**Why this priority**: This is the minimum foundation for all later phases; no
backend, user app, agency app, admin app, worker, or data-dependent feature can
be validated until the local platform services boot together.

**Independent Test**: From a clean checkout with only documented local
configuration values filled in, start the local foundation and confirm all
required services report healthy or reachable.

**Acceptance Scenarios**:

1. **Given** a clean checkout and completed local configuration placeholders,
   **When** the developer starts the local foundation, **Then** the required
   backing services and app skeletons start without manual ordering.
2. **Given** the local foundation is running, **When** the developer checks the
   service status, **Then** the data store, cache/queue, object store,
   connection proxy, backend skeleton, two web app skeletons, admin skeleton,
   and worker skeleton are all reachable or healthy.

---

### User Story 2 - Verify Required Connectivity (Priority: P2)

A developer can verify that each app skeleton can reach the required supporting
service it depends on for later phases.

**Why this priority**: Connectivity failures must be caught before domain
features are added, otherwise later phase failures will be harder to diagnose.

**Independent Test**: Run the documented connectivity checks and confirm the
data store is reachable through the connection proxy, vector support is enabled,
the cache/queue is reachable, the object store is reachable, and the worker can
connect to the cache/queue.

**Acceptance Scenarios**:

1. **Given** the local foundation is running, **When** the data connectivity
   check runs through the connection proxy, **Then** it succeeds and confirms
   vector support is enabled.
2. **Given** the local foundation is running, **When** cache/queue and object
   storage checks run, **Then** both return successful connectivity results.
3. **Given** the worker skeleton is running, **When** its startup check runs,
   **Then** it confirms cache/queue connectivity.

---

### User Story 3 - Onboard With Basic Documentation (Priority: P3)

A developer can read the basic setup documentation and know exactly how to
configure, start, verify, and stop the local foundation.

**Why this priority**: Later contributors need a stable, repeatable entry point
before implementation tasks expand across apps and services.

**Independent Test**: Follow only the documented quickstart from a clean local
checkout and complete the full start-and-verify flow without asking for missing
commands or hidden configuration values.

**Acceptance Scenarios**:

1. **Given** a new developer has the project files, **When** they follow the
   quickstart, **Then** they can fill local configuration placeholders and start
   the foundation.
2. **Given** the quickstart has been followed, **When** the developer runs the
   documented verification steps, **Then** all Phase 1 acceptance checks can be
   completed.

### Edge Cases

- If a required port or local service name conflicts with another process, the
  documentation must identify the failure and the expected resolution path.
- If local configuration values are missing, startup must fail with clear
  guidance rather than silently using unsafe defaults.
- If a service starts before a dependency is ready, health checks must prevent
  it from being treated as ready too early.
- If persistent local data already exists from a previous run, the start and
  verification flow must still be repeatable or document the reset step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a local foundation that starts the
  required backing services and app skeletons for Phase 1 as one coordinated
  environment.
- **FR-002**: The local foundation MUST include a data store with vector-search
  capability enabled and verifiable.
- **FR-003**: The local foundation MUST expose the data store through a
  connection proxy and provide a verification check that uses that proxy path.
- **FR-004**: The local foundation MUST include a cache/queue service and a
  verification check proving it is reachable.
- **FR-005**: The local foundation MUST include an object storage service and a
  verification check proving it is reachable.
- **FR-006**: The local foundation MUST include skeletons for the backend, user
  app, agency app, platform admin, and worker, each with a simple startup or
  health signal.
- **FR-007**: The backend skeleton MUST expose a health check that confirms the
  backend process is running.
- **FR-008**: The worker skeleton MUST confirm it can connect to the cache/queue
  service during startup or verification.
- **FR-009**: The project MUST provide local configuration placeholders for all
  Phase 1 services without committing secret values.
- **FR-010**: The project MUST provide basic README or quickstart instructions
  covering configuration, startup, verification, shutdown, and reset guidance.
- **FR-011**: The Phase 1 scope MUST NOT implement authentication, listings,
  RAG, AI behavior, leads, or scheduled viewings.
- **FR-012**: The project structure MUST establish the app and service areas
  needed by later phases without filling them with domain behavior.

### Key Entities

- **Local Foundation**: The coordinated local environment used to start and
  verify all Phase 1 services and app skeletons.
- **Service Skeleton**: A minimal app or worker process that proves startup and
  dependency connectivity without domain behavior.
- **Configuration Placeholder**: A documented local setting required to start
  the foundation, excluding committed secret values.
- **Health Check**: A verification signal showing that a service is running,
  reachable, or dependency-ready.
- **Quickstart**: The documentation that guides setup, startup, verification,
  shutdown, and reset.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature does not touch AI search, listing AI,
  leads, viewings, or admin workflows beyond skeleton startup. It explicitly
  avoids buyer-to-agency real-time chat and all domain behavior.
- **Tenant/RBAC Impact**: No tenant-scoped data or role permissions are created
  in Phase 1. The foundation must not introduce cross-tenant data paths because
  tenant models are out of scope until later phases.
- **AI/RAG Scope**: No AI, embedding, reranking, OCR, STT, TTS, RAG ingestion,
  or RAG retrieval behavior is implemented. Only future service areas may be
  scaffolded.
- **Reliability/Security/Performance**: Local startup must include health
  checks, repeatable verification, non-secret configuration placeholders, and
  clear failure behavior. Secrets must not be committed.
- **Unknowns to Clarify**: None for Phase 1. Provider and library decisions for
  later feature phases remain out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can complete local foundation startup and all
  documented verification checks from a clean checkout in under 15 minutes after
  prerequisites are installed.
- **SC-002**: 100% of required Phase 1 services and skeletons report healthy or
  reachable in the documented verification flow.
- **SC-003**: The data connectivity verification confirms vector capability is
  available through the configured connection path.
- **SC-004**: The setup documentation enables a new contributor to start,
  verify, stop, and reset the local foundation without undocumented commands.
- **SC-005**: No Phase 1 deliverable contains implemented auth, listings, RAG,
  AI behavior, leads, or scheduled viewings.

## Assumptions

- Phase 1 is limited to local development infrastructure and container/app
  skeleton readiness.
- The project plan is the source of truth for required services and exclusions.
- Local machines have the standard prerequisites needed to run containerized
  development services.
- Configuration placeholders may include non-secret runtime values and the
  minimum bootstrap information needed for later secret-management work.
- Domain models, tenant isolation behavior, authentication, and AI/RAG provider
  behavior are deferred to later phases.
