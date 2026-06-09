# Tasks: Backend Core Foundation

**Input**: Design documents from `specs/003-backend-core-foundation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, root `PLAN.md`, and Phase 1 implementation.

**Tests**: Required for this phase: unit tests, integration tests, transaction rollback tests, RBAC/tenant foundation tests, worker startup tests, and scope guard checks.

**Organization**: Tasks are grouped by setup, foundational prerequisites, and independently testable user stories from the Phase 2 spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks.
- **[Story]**: Used only for user-story phases.
- Every task includes concrete file paths and dependency notes.

---

## Phase 1: Setup (Backend Architecture Cleanup and Conventions)

**Purpose**: Align the existing Phase 1 backend skeleton with Phase 2 module and documentation conventions.

- [X] T001 Verify the Phase 1 backend skeleton and remove accidental `__pycache__` artifacts from `backend/app/` and `backend/tests/` (Dependencies: Phase 1 complete; Parallel: no)
- [X] T002 Ensure Phase 2 feature folders exist with package markers in `backend/app/auth/`, `backend/app/users/`, `backend/app/agencies/`, `backend/app/listings/`, `backend/app/leads/`, `backend/app/viewings/`, `backend/app/rag/`, `backend/app/ai/`, `backend/app/notifications/`, and `backend/app/admin/` (Dependencies: T001; Parallel: no)
- [X] T003 [P] Add backend module convention documentation in `backend/app/README.md` covering `router.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`, and optional `query_service.py` (Dependencies: T001; Parallel: yes)
- [X] T004 [P] Add a repository guard note that `dao.py` files are forbidden in `backend/app/README.md` and `AGENTS.md` (Dependencies: T003; Parallel: yes)
- [X] T005 [P] Create shared dependency-injection conventions in `backend/app/common/dependencies.py` (Dependencies: T001; Parallel: yes)
- [X] T006 [P] Update Phase 2 non-secret configuration placeholders in `.env.example` for `DATABASE_URL`, `PGBOUNCER_DATABASE_URL`, `REDIS_URL`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`, `AI_PRIMARY_PROVIDER`, `AI_FALLBACK_PROVIDERS`, `COHERE_API_KEY`, and `EMAIL_PROVIDER` with provider values set to `TBD_ASK_USER` where unknown (Dependencies: T001; Parallel: yes)
- [X] T007 [P] Update backend dependency list for Phase 2 foundation utilities in `backend/requirements.txt` without selecting unspecified auth, worker, email, or AI provider libraries (Dependencies: T001; Parallel: yes)
- [X] T008 [P] Confirm test package layout in `backend/tests/unit/`, `backend/tests/integration/`, and `backend/tests/rbac/` and add missing `__init__.py` files if needed (Dependencies: T001; Parallel: yes)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared modules that all Phase 2 user stories depend on.

**Critical**: Complete this phase before starting user-story implementation tasks.

- [X] T009 Update central settings schema and environment validation in `backend/app/common/config.py` (Dependencies: T006; Parallel: no)
- [X] T010 [P] Add settings loading and invalid environment tests in `backend/tests/unit/test_config.py` (Dependencies: T009; Parallel: yes)
- [X] T011 Update FastAPI lifespan resource registration and shutdown sequencing in `backend/app/common/lifespan.py` (Dependencies: T009; Parallel: no)
- [X] T012 [P] Add lifespan startup/shutdown tests in `backend/tests/integration/test_lifespan.py` (Dependencies: T011; Parallel: yes)
- [X] T013 Update async SQLAlchemy engine/session setup for PgBouncer runtime configuration in `backend/app/common/database.py` (Dependencies: T009; Parallel: no)
- [X] T014 [P] Add database and PgBouncer connectivity tests in `backend/tests/integration/test_database_foundation.py` (Dependencies: T013; Parallel: yes)
- [X] T015 Create base transaction helper in `backend/app/common/transactions.py` (Dependencies: T013; Parallel: no)
- [X] T016 [P] Add transaction commit and rollback behavior tests in `backend/tests/integration/test_transactions.py` (Dependencies: T015; Parallel: yes)
- [X] T017 Create base repository conventions in `backend/app/common/repository.py` (Dependencies: T013; Parallel: no)
- [X] T018 [P] Add base repository convention tests in `backend/tests/unit/test_repository.py` (Dependencies: T017; Parallel: yes)
- [X] T019 Create shared API response helpers in `backend/app/common/responses.py` (Dependencies: T009; Parallel: no)
- [X] T020 Update custom exception hierarchy and global handlers in `backend/app/common/exceptions.py` and `backend/app/main.py` (Dependencies: T019; Parallel: no)
- [X] T021 [P] Add exception response format tests in `backend/tests/integration/test_exceptions.py` (Dependencies: T020; Parallel: yes)
- [X] T022 Create request ID middleware in `backend/app/common/request_id.py` and register it in `backend/app/main.py` (Dependencies: T020; Parallel: no)
- [X] T023 [P] Add request ID middleware tests in `backend/tests/integration/test_request_id.py` (Dependencies: T022; Parallel: yes)
- [X] T024 Update structured logging setup to include request ID support in `backend/app/common/logging.py` (Dependencies: T022; Parallel: no)
- [X] T025 [P] Add structured logging tests in `backend/tests/unit/test_logging.py` (Dependencies: T024; Parallel: yes)
- [X] T026 Create pagination helpers in `backend/app/common/pagination.py` (Dependencies: T009; Parallel: no)
- [X] T027 [P] Add pagination bounds and metadata tests in `backend/tests/unit/test_pagination.py` (Dependencies: T026; Parallel: yes)

**Checkpoint**: Common settings, lifespan, database/session, transaction, repository, response, error, request ID, logging, and pagination foundations are ready.

---

## Phase 3: User Story 1 - Start Backend Core Reliably (Priority: P1) MVP

**Goal**: Backend starts, stops, reports health, exposes dependency status, and validates required infrastructure without business features.

**Independent Test**: Start the local stack, call `/health`, `/ready`, and `/health/dependencies`, and run startup/dependency tests without using auth, listings, leads, viewings, RAG, or AI workflows.

### Tests for User Story 1

- [X] T028 [P] [US1] Add health contract tests for `GET /health` in `backend/tests/integration/test_health_contract.py` (Dependencies: T019-T023; Parallel: yes)
- [X] T029 [P] [US1] Add readiness contract tests for `GET /ready` in `backend/tests/integration/test_readiness_contract.py` (Dependencies: T013, T020-T023; Parallel: yes)
- [X] T030 [P] [US1] Add dependency health contract tests for `GET /health/dependencies` in `backend/tests/integration/test_dependency_health.py` (Dependencies: T013, T020-T023; Parallel: yes)
- [X] T031 [P] [US1] Add MinIO foundation connectivity tests in `backend/tests/integration/test_storage_foundation.py` (Dependencies: T009; Parallel: yes)
- [X] T032 [P] [US1] Add Redis foundation connectivity tests in `backend/tests/integration/test_redis_foundation.py` (Dependencies: T009; Parallel: yes)

### Implementation for User Story 1

- [X] T033 [US1] Rename or wrap existing MinIO helper into storage abstraction in `backend/app/common/storage.py` while preserving `rag-vault` and `property-media` bucket checks (Dependencies: T009; Parallel: no)
- [X] T034 [US1] Update Redis client wrapper for shared readiness and utility use in `backend/app/common/redis.py` (Dependencies: T009; Parallel: no)
- [X] T035 [US1] Create dependency health service for DB/PgBouncer, pgvector, Redis, and MinIO checks in `backend/app/common/health.py` (Dependencies: T013, T033, T034; Parallel: no)
- [X] T036 [US1] Add `GET /health/dependencies` route and align `/health` and `/ready` with `contracts/openapi.yaml` in `backend/app/common/health.py` (Dependencies: T035; Parallel: no)
- [X] T037 [US1] Ensure health responses include request correlation where applicable in `backend/app/common/health.py` and `backend/app/common/request_id.py` (Dependencies: T022, T036; Parallel: no)
- [X] T038 [US1] Update OpenAPI contract if implementation changes response fields in `specs/003-backend-core-foundation/contracts/openapi.yaml` (Dependencies: T036; Parallel: no)
- [X] T039 [US1] Verify no business endpoints were added by scanning `backend/app/` and document the result in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T036; Parallel: no)

**Checkpoint**: User Story 1 is independently testable through startup, readiness, dependency health, and scope checks.

---

## Phase 4: User Story 2 - Prepare Safe Data and Transaction Foundations (Priority: P1)

**Goal**: Foundation schema, migrations, repository, transactions, pagination, audit, and outbox/inbox records support future all-or-nothing backend work without business tables.

**Independent Test**: Run migrations and backend foundation tests proving base schema, rollback behavior, pagination, audit, and event idempotency work without creating listings, leads, viewings, RAG, or media business tables.

### Tests for User Story 2

- [X] T040 [P] [US2] Add migration structure test for Phase 2 foundation tables in `backend/tests/integration/test_foundation_migrations.py` (Dependencies: T013; Parallel: yes)
- [X] T041 [P] [US2] Add pgvector extension continuity test in `backend/tests/integration/test_pgvector_foundation.py` (Dependencies: T013; Parallel: yes)
- [X] T042 [P] [US2] Add outbox idempotency and status lifecycle tests in `backend/tests/integration/test_outbox_events.py` (Dependencies: T015; Parallel: yes)
- [X] T043 [P] [US2] Add inbox duplicate-consumption tests in `backend/tests/integration/test_inbox_events.py` (Dependencies: T015; Parallel: yes)
- [X] T044 [P] [US2] Add audit log foundation tests in `backend/tests/integration/test_audit_logs.py` (Dependencies: T015; Parallel: yes)
- [X] T045 [P] [US2] Add notification foundation persistence tests in `backend/tests/integration/test_notifications_foundation.py` (Dependencies: T015; Parallel: yes)

### Implementation for User Story 2

- [X] T046 [US2] Add Phase 2 Alembic migration for `roles`, `permissions`, `role_permissions`, `users`, `refresh_sessions`, `audit_logs`, `outbox_events`, `inbox_events`, and `notifications` in `backend/alembic/versions/0002_backend_core_foundation.py` (Dependencies: T013; Parallel: no)
- [X] T047 [US2] Create foundation SQLAlchemy models for roles, permissions, and role-permissions in `backend/app/auth/models.py` (Dependencies: T046; Parallel: no)
- [X] T048 [US2] Create minimal base user and refresh session SQLAlchemy models in `backend/app/users/models.py` and `backend/app/auth/models.py` (Dependencies: T046; Parallel: no)
- [X] T049 [US2] Create audit log SQLAlchemy model in `backend/app/audit/models.py` (Dependencies: T046; Parallel: no)
- [X] T050 [US2] Create outbox and inbox event SQLAlchemy models in `backend/app/common/events.py` (Dependencies: T046; Parallel: no)
- [X] T051 [US2] Create notification SQLAlchemy model in `backend/app/notifications/models.py` (Dependencies: T046; Parallel: no)
- [X] T052 [US2] Create outbox event repository and service foundation in `backend/app/common/events.py` (Dependencies: T050; Parallel: no)
- [X] T053 [US2] Create inbox event repository and service foundation in `backend/app/common/events.py` (Dependencies: T050, T052; Parallel: no)
- [X] T054 [US2] Add idempotency key helper and event status constants for prepared future event names in `backend/app/common/events.py` (Dependencies: T052, T053; Parallel: no)
- [X] T055 [US2] Create audit log repository and service foundation in `backend/app/audit/repository.py` and `backend/app/audit/service.py` (Dependencies: T049; Parallel: no)
- [X] T056 [US2] Create notification repository and service foundation in `backend/app/notifications/repository.py` and `backend/app/notifications/service.py` (Dependencies: T051; Parallel: no)
- [X] T057 [US2] Update Alembic env metadata imports for Phase 2 foundation models in `backend/alembic/env.py` (Dependencies: T047-T051; Parallel: no)
- [X] T058 [US2] Run migration verification and confirm no business tables exist using `backend/tests/integration/test_foundation_migrations.py` (Dependencies: T040-T057; Parallel: no)

**Checkpoint**: User Story 2 is independently testable through migrations, rollback tests, outbox/inbox idempotency, audit logs, notifications foundation, and business-table scope checks.

---

## Phase 5: User Story 3 - Prepare Security Foundations Without Auth Flows (Priority: P1)

**Goal**: Password/token utilities, token invalidation, RBAC helpers, tenant context, cache, rate limiting, and security tests are ready without exposing login/register/business auth flows.

**Independent Test**: Run auth utility, RBAC utility, tenant context, Redis cache, rate limiter, and scope tests that prove the foundation works without protected business endpoints.

### Tests for User Story 3

- [X] T059 [P] [US3] Add password hashing and verification tests in `backend/tests/unit/test_security_passwords.py` (Dependencies: T009; Parallel: yes)
- [X] T060 [P] [US3] Add access and refresh token utility tests in `backend/tests/unit/test_security_tokens.py` (Dependencies: T009; Parallel: yes)
- [X] T061 [P] [US3] Add Redis token blacklist/invalidation tests in `backend/tests/integration/test_token_invalidation.py` (Dependencies: T034; Parallel: yes)
- [X] T062 [P] [US3] Add role and permission helper tests in `backend/tests/rbac/test_permissions.py` (Dependencies: T047; Parallel: yes)
- [X] T063 [P] [US3] Add tenant context tests in `backend/tests/rbac/test_tenant_context.py` (Dependencies: T017; Parallel: yes)
- [X] T064 [P] [US3] Add Redis cache helper tests in `backend/tests/integration/test_cache.py` (Dependencies: T034; Parallel: yes)
- [X] T065 [P] [US3] Add Redis rate limiter tests for IP/session/user key formats in `backend/tests/integration/test_rate_limit.py` (Dependencies: T034; Parallel: yes)

### Implementation for User Story 3

- [X] T066 [US3] Create password hashing and verification utilities in `backend/app/common/security.py` without selecting an unspecified auth helper library unless already present (Dependencies: T009; Parallel: no)
- [X] T067 [US3] Create JWT access and refresh token utility foundation in `backend/app/common/security.py` using configured token settings (Dependencies: T066; Parallel: no)
- [X] T068 [US3] Create Redis token blacklist and session invalidation utility in `backend/app/auth/service.py` (Dependencies: T034, T067; Parallel: no)
- [X] T069 [US3] Create current-user dependency placeholder and role dependency placeholder in `backend/app/auth/dependencies.py` (Dependencies: T067, T068; Parallel: no)
- [X] T070 [US3] Create role constants and permission constants in `backend/app/auth/permissions.py` for User, Agency Admin, Support Employee, and Platform Admin (Dependencies: T047; Parallel: no)
- [X] T071 [US3] Create permission-check dependency foundation in `backend/app/auth/dependencies.py` (Dependencies: T069, T070; Parallel: no)
- [X] T072 [US3] Create tenant context object and propagation conventions in `backend/app/common/tenant.py` (Dependencies: T022, T070; Parallel: no)
- [X] T073 [US3] Create tenant-aware repository guard placeholder in `backend/app/common/repository.py` (Dependencies: T017, T072; Parallel: no)
- [X] T074 [US3] Create Redis cache helper and key naming conventions in `backend/app/common/cache.py` (Dependencies: T034; Parallel: no)
- [X] T075 [US3] Create Redis-backed rate limiter and key strategy in `backend/app/common/rate_limit.py` (Dependencies: T034; Parallel: no)
- [X] T076 [US3] Document that login, registration, password reset user flows, and business auth endpoints remain out of scope in `backend/app/auth/README.md` (Dependencies: T069-T075; Parallel: no)
- [X] T077 [US3] Run security foundation scope check to confirm no login/register routes were added in `backend/app/auth/` (Dependencies: T066-T076; Parallel: no)

**Checkpoint**: User Story 3 is independently testable through auth utilities, token invalidation, RBAC helpers, tenant context, Redis cache/rate limiting, and auth-flow scope checks.

---

## Phase 6: User Story 4 - Define Provider and Worker Interfaces Only (Priority: P2)

**Goal**: Email, notification, AI provider, storage, and worker interface foundations exist without selecting concrete providers or implementing real AI/email/business jobs.

**Independent Test**: Inspect and test provider contracts, registry/factory placeholders, notification/email abstractions, storage helpers, and worker startup with no external provider side effects.

### Tests for User Story 4

- [X] T078 [P] [US4] Add AI provider interface tests in `backend/tests/unit/test_ai_provider_interfaces.py` (Dependencies: T009; Parallel: yes)
- [X] T079 [P] [US4] Add provider registry/factory placeholder tests in `backend/tests/unit/test_provider_registry.py` (Dependencies: T009; Parallel: yes)
- [X] T080 [P] [US4] Add email provider interface tests in `backend/tests/unit/test_email_provider.py` (Dependencies: T009; Parallel: yes)
- [X] T081 [P] [US4] Add notification payload schema tests in `backend/tests/unit/test_notification_schemas.py` (Dependencies: T056; Parallel: yes)
- [X] T082 [P] [US4] Add MinIO upload/download/delete/path helper tests in `backend/tests/integration/test_storage_helpers.py` (Dependencies: T033; Parallel: yes)
- [X] T083 [P] [US4] Add worker polling foundation tests in `workers/tests/test_event_polling.py` (Dependencies: T052-T054; Parallel: yes)

### Implementation for User Story 4

- [X] T084 [US4] Create AI provider protocol interfaces for chat, embeddings, reranking, OCR, STT, TTS, image moderation, image quality, spam classification, and lead classification in `backend/app/ai/providers.py` (Dependencies: T009; Parallel: no)
- [X] T085 [US4] Create fallback-ready AI provider registry/factory with `TBD_ASK_USER` placeholders in `backend/app/ai/registry.py` (Dependencies: T084; Parallel: no)
- [X] T086 [US4] Create email provider interface and placeholder provider in `backend/app/notifications/email_provider.py` (Dependencies: T009; Parallel: no)
- [X] T087 [US4] Create notification and email event payload schemas in `backend/app/notifications/schemas.py` (Dependencies: T056, T086; Parallel: no)
- [X] T088 [US4] Extend storage abstraction with object path builder, upload, download, delete, and presigned URL helpers in `backend/app/common/storage.py` (Dependencies: T033; Parallel: no)
- [X] T089 [US4] Add bucket existence helper coverage for `rag-vault` and `property-media` in `backend/app/common/storage.py` (Dependencies: T088; Parallel: no)
- [X] T090 [US4] Create worker polling and dispatch foundation for outbox events in `workers/main.py` without business event handlers (Dependencies: T052-T054; Parallel: no)
- [X] T091 [US4] Document provider decisions that remain `TBD_ASK_USER` in `specs/003-backend-core-foundation/research.md` and `backend/app/ai/README.md` (Dependencies: T084-T087; Parallel: no)
- [X] T092 [US4] Verify no OCR, RAG, image moderation, email sending, AI search, listing AI widget, agency support assistant, or analytics workflows were implemented in `backend/app/` and `workers/` (Dependencies: T084-T091; Parallel: no)

**Checkpoint**: User Story 4 is independently testable through provider-interface tests, storage helper tests, worker startup/polling tests, and provider workflow scope checks.

---

## Final Phase: Polish, Documentation, and Phase 2 Verification

**Purpose**: Ensure docs, contracts, tests, and scope checks are complete before Phase 2 implementation is accepted.

- [X] T093 [P] Update Phase 2 backend architecture documentation in `backend/app/README.md` and `specs/003-backend-core-foundation/quickstart.md` (Dependencies: all user stories complete; Parallel: yes)
- [X] T094 [P] Update environment variable documentation in `.env.example` and `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T006, T009; Parallel: yes)
- [X] T095 [P] Update migration and test commands in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T040-T058; Parallel: yes)
- [X] T096 [P] Update API contract if endpoint names or schemas changed in `specs/003-backend-core-foundation/contracts/openapi.yaml` (Dependencies: T036, T038; Parallel: yes)
- [X] T097 Run full backend test suite with `docker compose exec backend pytest` and record expected result in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T001-T096; Parallel: no)
- [X] T098 Run worker test suite with `docker compose exec worker python -m pytest tests` and record expected result in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T090; Parallel: no)
- [X] T099 Run migration verification with `docker compose exec backend alembic upgrade head` and confirm pgvector plus foundation tables in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T046-T058; Parallel: no)
- [X] T100 Run health verification for `/health`, `/ready`, and `/health/dependencies` and record expected HTTP results in `specs/003-backend-core-foundation/quickstart.md` (Dependencies: T028-T039; Parallel: no)
- [X] T101 Run final scope scan to prove no business feature implementation exists in `backend/app/`, `workers/`, `apps/`, or `admin/` for Phase 2 (Dependencies: T001-T100; Parallel: no)
- [X] T102 Run final secret scan for committed Phase 2 files and confirm no secret values are present in `.env.example`, `backend/app/`, `workers/`, and `specs/003-backend-core-foundation/` (Dependencies: T001-T101; Parallel: no)
- [X] T103 Update Phase 2 completion checklist in `specs/003-backend-core-foundation/quickstart.md` with central config, lifespan, DB/PgBouncer, migrations, pgvector, Redis, MinIO, JWT utilities, token invalidation, RBAC helper, tenant context, outbox/inbox, AI interfaces, email interfaces, audit logs, health endpoints, tests, and scope checks (Dependencies: T097-T102; Parallel: no)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately from Phase 1 implementation.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user-story tasks.
- **User Story 1 (Phase 3)**: Depends on Foundational tasks T009-T027.
- **User Story 2 (Phase 4)**: Depends on Foundational tasks T013-T018 and can run after foundational database/transaction work is complete.
- **User Story 3 (Phase 5)**: Depends on Foundational tasks T009, T017, T022, and Redis wrapper work from US1.
- **User Story 4 (Phase 6)**: Depends on Foundational settings and selected US1/US2 helpers.
- **Final Phase**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Start Backend Core Reliably**: MVP slice. No dependency on US2/US3/US4 after Foundational.
- **US2 Safe Data and Transaction Foundations**: Depends on database/session/transaction foundations; independent from US1 routes except shared health checks.
- **US3 Security Foundations Without Auth Flows**: Depends on role/user/session foundation models from US2 and Redis wrapper from US1.
- **US4 Provider and Worker Interfaces Only**: Depends on common config, storage abstraction, outbox foundation, and notification foundation.

### Parallel Opportunities

- Setup documentation and env tasks T003-T008 can run in parallel after T001.
- Test-writing tasks marked [P] in each user story can run in parallel before implementation.
- US1 connectivity tests T031-T032 can run in parallel with health contract tests T028-T030.
- US2 migration, event, audit, and notification tests T040-T045 can run in parallel.
- US3 auth utility, RBAC, tenant, cache, and rate-limit tests T059-T065 can run in parallel.
- US4 provider, storage, email, notification, and worker tests T078-T083 can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "T028 [P] [US1] Add health contract tests in backend/tests/integration/test_health_contract.py"
Task: "T029 [P] [US1] Add readiness contract tests in backend/tests/integration/test_readiness_contract.py"
Task: "T030 [P] [US1] Add dependency health contract tests in backend/tests/integration/test_dependency_health.py"
Task: "T031 [P] [US1] Add MinIO foundation connectivity tests in backend/tests/integration/test_storage_foundation.py"
Task: "T032 [P] [US1] Add Redis foundation connectivity tests in backend/tests/integration/test_redis_foundation.py"
```

## Parallel Example: User Story 2

```bash
Task: "T040 [P] [US2] Add migration structure test in backend/tests/integration/test_foundation_migrations.py"
Task: "T042 [P] [US2] Add outbox idempotency tests in backend/tests/integration/test_outbox_events.py"
Task: "T043 [P] [US2] Add inbox duplicate-consumption tests in backend/tests/integration/test_inbox_events.py"
Task: "T044 [P] [US2] Add audit log tests in backend/tests/integration/test_audit_logs.py"
```

## Parallel Example: User Story 3

```bash
Task: "T059 [P] [US3] Add password hashing tests in backend/tests/unit/test_security_passwords.py"
Task: "T060 [P] [US3] Add token utility tests in backend/tests/unit/test_security_tokens.py"
Task: "T062 [P] [US3] Add permission helper tests in backend/tests/rbac/test_permissions.py"
Task: "T063 [P] [US3] Add tenant context tests in backend/tests/rbac/test_tenant_context.py"
```

## Parallel Example: User Story 4

```bash
Task: "T078 [P] [US4] Add AI provider interface tests in backend/tests/unit/test_ai_provider_interfaces.py"
Task: "T080 [P] [US4] Add email provider interface tests in backend/tests/unit/test_email_provider.py"
Task: "T082 [P] [US4] Add storage helper tests in backend/tests/integration/test_storage_helpers.py"
Task: "T083 [P] [US4] Add worker polling tests in workers/tests/test_event_polling.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 Setup tasks T001-T008.
2. Complete Phase 2 Foundational tasks T009-T027.
3. Complete US1 tasks T028-T039.
4. Stop and validate backend startup, health, readiness, dependency checks, and scope boundaries.

### Incremental Delivery

1. Add US2 data/transaction foundations and validate migrations plus rollback/idempotency tests.
2. Add US3 security foundations and validate auth utility/RBAC/tenant/cache/rate-limit tests.
3. Add US4 provider/worker interfaces and validate placeholder behavior plus worker startup.
4. Run Final Phase verification T093-T103.

### Scope Guard

Phase 2 tasks must not implement frontend business screens, agency profile management, listings, listing photos, image moderation, WebP conversion, leads, lead scoring, scheduled viewings, viewing schedules, RAG ingestion, RAG retrieval, area RAG, AI search, listing AI widget, agency support assistant, platform analytics, Streamlit analytics, or real business workflows.
