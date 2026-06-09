# Tasks: Auth, RBAC, and Tenant Isolation

**Input**: Design documents from `/specs/004-auth-rbac-tenant-isolation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Constitution-required tests included where applicable: service unit tests, important API integration tests, critical transaction tests, and RBAC tenant-isolation tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks
- **[Story]**: User story label for story phases only
- Every task includes a concrete file path

## Phase 1: Setup (Shared Security Scaffolding)

**Purpose**: Prepare the auth and agency module boundaries for Phase 3 security work.

- [X] T001 [P] Create Phase 3 module guardrail docs in `backend/app/auth/README.md`, `backend/app/agencies/README.md`, and `AGENTS.md`
- [X] T002 [P] Create missing Phase 3 module entrypoints and support files in `backend/app/auth/router.py`, `backend/app/auth/repository.py`, `backend/app/auth/schemas.py`, `backend/app/users/repository.py`, `backend/app/users/service.py`, `backend/app/agencies/models.py`, `backend/app/agencies/repository.py`, and `backend/app/agencies/service.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared security schema, guards, and helpers required by all Phase 3 stories.

**Critical**: Complete this phase before starting any user story work.

- [X] T003 [P] Add migration coverage test for the Phase 3 auth/RBAC/tenant schema in `backend/tests/integration/test_auth_migrations.py`
- [X] T004 [P] Add unit tests for role, permission, tenant, and session model constraints in `backend/tests/unit/test_auth_models.py`
- [X] T005 Implement the Phase 3 Alembic migration for users, roles, permissions, agency tenants, agency employee memberships, refresh-session changes, access revocations, and audit additions in `backend/alembic/versions/0003_auth_rbac_tenant_isolation.py`
- [X] T006 [P] Extend auth and session models in `backend/app/auth/models.py` for user role/status fields, refresh-session fields, and access-revocation records
- [X] T007 [P] Implement agency tenant and employee membership models in `backend/app/agencies/models.py`
- [X] T008 [P] Update approved role and permission catalogs in `backend/app/auth/permissions.py` for login, refresh, logout, password reset, session revocation, employee deactivation, platform oversight, and tenant checks
- [X] T009 [P] Update auth dependency placeholders in `backend/app/auth/dependencies.py` to expose current actor, role guard, permission guard, and tenant-context dependencies
- [X] T010 [P] Update tenant-context fail-closed guardrails in `backend/app/common/tenant.py` and `backend/app/common/repository.py`
- [X] T011 [P] Extend auth-flow rate-limit helpers in `backend/app/common/rate_limit.py`
- [X] T012 [P] Extend security audit helpers in `backend/app/audit/service.py` and `backend/app/audit/repository.py` for auth, role, tenant, and revocation events
- [X] T013 [P] Extend auth session and credential helpers in `backend/app/auth/service.py` and `backend/app/auth/repository.py` for issuance, rotation, revocation, and password-reset primitives
- [X] T014 Wire the new auth routes and tenant-context route skeletons into `backend/app/auth/router.py` and `backend/app/main.py`
- [X] T015 Update Alembic and ORM metadata imports for the new Phase 3 models in `backend/alembic/env.py` and `backend/app/common/database.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Authenticate Existing Actors (Priority: P1) MVP

**Goal**: Existing active actors can sign in, refresh, sign out, and change passwords with session invalidation.

**Independent Test**: Sign in an active actor, refresh access, sign out, and verify old sessions fail; verify current-password password reset invalidates prior sessions.

### Tests for User Story 1

- [X] T016 [P] [US1] Add login/refresh/logout flow tests in `backend/tests/integration/test_auth_flow.py`
- [X] T017 [P] [US1] Add token issuance and refresh-rotation unit tests in `backend/tests/unit/test_auth_tokens.py`
- [X] T018 [P] [US1] Add current-password reset flow tests in `backend/tests/integration/test_password_reset_skeleton.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement login and refresh session issuance in `backend/app/auth/router.py` and `backend/app/auth/service.py`
- [X] T020 [US1] Implement logout and single-session invalidation in `backend/app/auth/router.py`, `backend/app/auth/service.py`, and `backend/app/auth/repository.py`
- [X] T021 [US1] Implement current-password password reset and full-session invalidation in `backend/app/auth/router.py`, `backend/app/auth/service.py`, and `backend/app/auth/repository.py`
- [X] T022 [US1] Persist last-login, password-changed, and session-rotation state in `backend/app/auth/models.py` and `backend/app/users/models.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Enforce Roles and Permissions (Priority: P1)

**Goal**: Protected actions only succeed when the actor has the required approved role and explicit permission.

**Independent Test**: Verify allowed actions pass for the correct role/permission pair and forbidden actions are denied for missing or overreaching roles.

### Tests for User Story 2

- [X] T023 [P] [US2] Add role-guard unit tests in `backend/tests/rbac/test_role_guards.py`
- [X] T024 [P] [US2] Add permission-evaluation unit tests in `backend/tests/rbac/test_permissions.py`
- [X] T025 [P] [US2] Add support-employee and platform-admin restriction tests in `backend/tests/rbac/test_role_restrictions.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement role and permission checks in `backend/app/auth/dependencies.py`
- [X] T027 [US2] Update approved role and permission seed/lookup behavior in `backend/app/auth/models.py` and `backend/alembic/versions/0003_auth_rbac_tenant_isolation.py`
- [X] T028 [US2] Emit audit events for denied role and permission checks in `backend/app/audit/service.py`

**Checkpoint**: User Story 2 should work independently and deny unauthorized access consistently.

---

## Phase 5: User Story 3 - Establish Tenant Context for Agencies (Priority: P1)

**Goal**: Protected requests carry tenant context and agency actors cannot access another agency's protected context.

**Independent Test**: Create two agency tenants, attach actors to one tenant each, and verify cross-tenant access is denied while allowed tenant-scoped work receives context.

### Tests for User Story 3

- [X] T029 [P] [US3] Add tenant-context unit tests in `backend/tests/rbac/test_tenant_context.py`
- [X] T030 [P] [US3] Add cross-tenant access integration tests in `backend/tests/integration/test_tenant_isolation.py`
- [X] T031 [P] [US3] Add single-agency membership validation tests in `backend/tests/integration/test_agency_memberships.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement agency tenant and single-membership enforcement in `backend/app/agencies/models.py` and `backend/alembic/versions/0003_auth_rbac_tenant_isolation.py`
- [X] T033 [US3] Implement tenant-context propagation and fail-closed repository guards in `backend/app/common/tenant.py` and `backend/app/common/repository.py`
- [X] T034 [US3] Apply tenant-aware authorization checks in `backend/app/auth/dependencies.py` and `backend/app/auth/service.py`
- [X] T035 [US3] Emit audit events for tenant-denied access in `backend/app/audit/service.py`

**Checkpoint**: User Story 3 should be independently testable with clear tenant isolation behavior.

---

## Phase 6: User Story 4 - Revoke Access After Security Events (Priority: P2)

**Goal**: Password reset, employee deactivation, and suspicious-session revocation invalidate the correct sessions.

**Independent Test**: Reset a password, deactivate an employee, and revoke a suspicious session; confirm old credentials fail while unaffected actors remain signed in.

### Tests for User Story 4

- [X] T036 [P] [US4] Add employee deactivation and session revocation integration tests in `backend/tests/integration/test_employee_deactivation.py`
- [X] T037 [P] [US4] Add suspicious-session revocation integration tests in `backend/tests/integration/test_session_revocation.py`

### Implementation for User Story 4

- [X] T038 [US4] Implement employee deactivation and revoke-all-sessions behavior in `backend/app/agencies/service.py`, `backend/app/auth/service.py`, and `backend/app/audit/service.py`
- [X] T039 [US4] Implement suspicious-session and single-session revocation handling in `backend/app/auth/service.py` and `backend/app/auth/repository.py`
- [X] T040 [US4] Persist revocation markers and employee deactivation state in `backend/app/auth/models.py` and `backend/alembic/versions/0003_auth_rbac_tenant_isolation.py`

**Checkpoint**: User Story 4 should revoke only the intended sessions and leave unrelated actors unaffected.

---

## Phase 7: User Story 5 - Throttle Authentication Abuse (Priority: P2)

**Goal**: Auth entry points are rate limited without blocking normal use.

**Independent Test**: Repeated abusive auth attempts from the same source are throttled, while normal-volume attempts continue to work.

### Tests for User Story 5

- [X] T041 [P] [US5] Add auth rate-limit integration tests in `backend/tests/integration/test_auth_rate_limits.py`
- [X] T042 [P] [US5] Add auth rate-limit keying unit tests in `backend/tests/unit/test_auth_rate_limit_keys.py`

### Implementation for User Story 5

- [X] T043 [US5] Extend `backend/app/common/rate_limit.py` with auth-specific buckets, limits, and retry messaging
- [X] T044 [US5] Enforce rate limits in `backend/app/auth/router.py` for login, refresh, logout, password reset, and revocation endpoints
- [X] T045 [US5] Record audit events for rate-limited auth attempts in `backend/app/audit/service.py`

**Checkpoint**: User Story 5 should throttle abuse without breaking normal authentication flows.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation alignment across the feature.

- [X] T046 [P] Update `specs/004-auth-rbac-tenant-isolation/quickstart.md` with the final validation commands and pass criteria
- [X] T047 [P] Update `specs/004-auth-rbac-tenant-isolation/contracts/openapi.yaml` and `specs/004-auth-rbac-tenant-isolation/data-model.md` if field or route names changed during implementation
- [X] T048 Run the full Phase 3 verification suite, including Vault-secret-source verification, and scope scan documented in `specs/004-auth-rbac-tenant-isolation/quickstart.md`
- [X] T049 Run a final scope scan confirming no listings, leads, scheduled viewings, RAG, AI workflows, email sending, dashboards, buyer-to-agency real-time chat, or business CRUD in `backend/app/` and `backend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No story dependency, but should complete before foundational work.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Stories (Phase 3+)**: All depend on the Foundational phase.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational; no dependency on other stories.
- **User Story 2 (P1)**: Can start after Foundational; independent of US1.
- **User Story 3 (P1)**: Can start after Foundational; may reuse US2 role/permission data but must stay independently testable.
- **User Story 4 (P2)**: Can start after Foundational; relies on session and revocation primitives from US1.
- **User Story 5 (P2)**: Can start after Foundational; relies on auth endpoints and shared rate-limit helpers.

### Within Each User Story

- Constitution-required tests are written before implementation where applicable.
- Models and schema changes come before service and router behavior.
- Security auditing and fail-closed checks are part of the same story, not deferred.
- Each story must be independently demonstrable before moving to the next priority.

### Parallel Opportunities

- Setup tasks T001-T002 can run in parallel.
- Foundational tasks T003-T015 can be split across models, migration, guards, repositories, and audit helpers.
- Story-specific test tasks marked [P] can run in parallel within each story.
- Independent user stories can be worked in parallel once the Foundational phase is complete.

## Parallel Example: User Story 1

```bash
Task: "T016 [P] [US1] Add login/refresh/logout flow tests in backend/tests/integration/test_auth_flow.py"
Task: "T017 [P] [US1] Add token issuance and refresh-rotation unit tests in backend/tests/unit/test_auth_tokens.py"
Task: "T018 [P] [US1] Add current-password reset flow tests in backend/tests/integration/test_password_reset_skeleton.py"
```

## Parallel Example: User Story 3

```bash
Task: "T029 [P] [US3] Add tenant-context unit tests in backend/tests/rbac/test_tenant_context.py"
Task: "T030 [P] [US3] Add cross-tenant access integration tests in backend/tests/integration/test_tenant_isolation.py"
Task: "T031 [P] [US3] Add single-agency membership validation tests in backend/tests/integration/test_agency_memberships.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational security work.
3. Complete User Story 1.
4. Stop and validate sign-in, refresh, logout, and password reset behavior.

### Incremental Delivery

1. Finish setup and foundational work.
2. Deliver User Story 1.
3. Add role/permission enforcement in User Story 2.
4. Add tenant isolation in User Story 3.
5. Add revocation/deactivation behavior in User Story 4.
6. Add auth rate limiting in User Story 5.
7. Finish with documentation and full verification.
