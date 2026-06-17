# Tasks: Platform Admin Dashboard

**Input**: Design documents from `/specs/015-platform-admin-streamlit/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included for backend unit, API integration, RBAC/access-gate coverage, query-service aggregation, and Streamlit dashboard rendering/auth states.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the admin app and platform-dashboard config/test scaffolding

- [X] T001 Add platform-dashboard configuration placeholders and limits in `backend/app/common/config.py` and `.env.example`
- [X] T002 [P] Add Streamlit test dependencies and admin test package scaffolding in `admin/requirements.txt`, `admin/tests/__init__.py`, and `admin/tests/conftest.py`
- [X] T003 [P] Create admin-side API client and auth helper scaffolding in `admin/api_client.py`, `admin/auth.py`, and `admin/components.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared auth, schema, routing, and query primitives required by all platform-admin stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add the dedicated platform-dashboard permission key and enforcement helper in `backend/app/auth/permissions.py` and `backend/app/auth/dependencies.py`
- [X] T005 Add Alembic permission seeding and any supporting auth seed updates in `backend/alembic/versions/0020_platform_admin_dashboard.py`
- [X] T006 [P] Create shared platform-admin response and filter schemas in `backend/app/admin/schemas.py`
- [X] T007 [P] Create shared platform-admin query/service scaffolding in `backend/app/admin/query_service.py`, `backend/app/admin/service.py`, and `backend/app/admin/__init__.py`
- [X] T008 [P] Add shared platform-admin router wiring in `backend/app/admin/router.py` and `backend/app/main.py`
- [X] T009 Add audit-log redaction and feature-area normalization helpers for platform reads in `backend/app/audit/repository.py`, `backend/app/audit/service.py`, and `backend/app/rag/redaction.py`
- [X] T010 Add shared Streamlit entry-gate, token handling, and backend error rendering in `admin/app.py`, `admin/api_client.py`, and `admin/auth.py`

**Checkpoint**: Platform-admin routes, permission gate, and admin-app wiring are ready

---

## Phase 3: User Story 1 - View Marketplace Demand Insights (Priority: P1) 🎯 MVP

**Goal**: Give platform admins a read-only marketplace dashboard for aggregate search demand, supply gaps, and trend analysis

**Independent Test**: Sign in as a platform admin with dashboard permission, open the insights page, change the date scope plus `city`, `property_type`, and `listing_purpose` filters, and confirm top areas, budgets, property types, demand gaps, and trends all refresh consistently with bounded empty states

### Tests for User Story 1

- [X] T011 [P] [US1] Add demand-insight query and service unit tests for scoped `city`, `property_type`, and `listing_purpose` filters in `backend/tests/unit/test_platform_dashboard_insights.py`
- [X] T012 [P] [US1] Add platform dashboard API integration tests for `/api/v1/platform/dashboard/insights` filter combinations in `backend/tests/integration/test_platform_dashboard_api.py`
- [X] T013 [P] [US1] Add platform-admin access-gate and non-platform denial coverage in `backend/tests/rbac/test_platform_dashboard_access.py`
- [X] T014 [P] [US1] Add Streamlit insights-page rendering and auth-failure tests in `admin/tests/test_marketplace_insights_page.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement aggregate demand-insight queries for search volume, top areas, budget bands, property types, supply counts, and scoped `city`/`property_type`/`listing_purpose` filtering in `backend/app/admin/query_service.py`, `backend/app/search/repository.py`, and `backend/app/listings/query_service.py`
- [X] T016 [US1] Implement demand-gap calculation, filter-scope validation, and bounded empty-state shaping in `backend/app/admin/service.py` and `backend/app/admin/schemas.py`
- [X] T017 [US1] Add the read-only insights endpoint and permission guard in `backend/app/admin/router.py` and `backend/app/main.py`
- [X] T018 [US1] Add scope-bounded caching and explicit invalidation hooks for marketplace insights in `backend/app/admin/service.py`, `backend/app/search/service.py`, and `backend/app/listings/service.py`
- [X] T019 [US1] Replace the placeholder admin home with dashboard shell, scoped `city`/`property_type`/`listing_purpose` filters, and overview metrics in `admin/app.py` and `admin/components.py`
- [X] T020 [US1] Build the marketplace insights page with synchronized filter controls in `admin/pages/1_Marketplace_Insights.py`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Review AI Audit Activity Safely (Priority: P2)

**Goal**: Let platform admins inspect redacted AI audit activity with filters and pagination while keeping the surface read-only

**Independent Test**: Open the audit page, filter by date/role/feature/result, inspect a row, and confirm the metadata is redacted, paginated, and non-exportable

### Tests for User Story 2

- [X] T021 [P] [US2] Add platform audit-log unit tests for redaction, feature mapping, and pagination shaping in `backend/tests/unit/test_platform_audit_logs.py`
- [X] T022 [P] [US2] Add audit-log API integration tests for `/api/v1/platform/audit-logs` in `backend/tests/integration/test_platform_audit_logs_api.py`
- [X] T023 [P] [US2] Add RBAC coverage for platform-only audit access and dashboard-permission denial in `backend/tests/rbac/test_platform_audit_access.py`
- [X] T024 [P] [US2] Add Streamlit audit-view rendering and filter-state tests in `admin/tests/test_ai_audit_logs_page.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement paginated platform audit-log queries with actor-role, feature-area, result, and date filters in `backend/app/admin/query_service.py` and `backend/app/audit/repository.py`
- [X] T026 [US2] Implement redacted audit-log response shaping and read-only guard logic in `backend/app/admin/service.py`, `backend/app/admin/schemas.py`, and `backend/app/audit/service.py`
- [X] T027 [US2] Add the read-only audit-log endpoint in `backend/app/admin/router.py`
- [X] T028 [US2] Build the Streamlit audit-log page with filters, detail drill-in, and empty states in `admin/pages/2_AI_Audit_Logs.py` and `admin/components.py`

**Checkpoint**: User Story 2 is fully functional and independently testable

---

## Phase 5: User Story 3 - Inspect Platform Access Boundaries (Priority: P3)

**Goal**: Give platform admins a clear read-only overview of supported product roles, permissions, and restricted surfaces

**Independent Test**: Open the access overview page and verify the shown roles, granted permissions, allowed surfaces, and restricted surfaces match the backend auth model

### Tests for User Story 3

- [X] T029 [P] [US3] Add role-overview unit tests for permission aggregation and surface summaries in `backend/tests/unit/test_platform_role_overview.py`
- [X] T030 [P] [US3] Add role-overview API integration tests for `/api/v1/platform/roles/overview` in `backend/tests/integration/test_platform_role_overview_api.py`
- [X] T031 [P] [US3] Add Streamlit role-overview rendering tests in `admin/tests/test_role_access_overview_page.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement role and permission overview queries in `backend/app/admin/query_service.py` and `backend/app/auth/repository.py`
- [X] T033 [US3] Implement role-access response shaping and permission-to-surface summaries in `backend/app/admin/service.py` and `backend/app/admin/schemas.py`
- [X] T034 [US3] Add the read-only role-overview endpoint in `backend/app/admin/router.py`
- [X] T035 [US3] Build the Streamlit role and surface overview page in `admin/pages/3_Role_Access_Overview.py` and `admin/components.py`

**Checkpoint**: User Story 3 is fully functional and independently testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, docs, and focused regression coverage across the whole platform-admin surface

- [X] T036 [P] Document platform-dashboard auth gating, aggregate insight definitions, and admin runbook updates in `backend/app/admin/README.md`, `admin/README.md`, and `specs/015-platform-admin-streamlit/quickstart.md`
- [X] T037 Harden platform-dashboard cache invalidation, stale-data messaging, and backend error states in `backend/app/admin/service.py`, `backend/app/admin/router.py`, `admin/api_client.py`, and `admin/components.py`
- [X] T038 [P] Run focused regression coverage in `backend/tests/unit/test_platform_dashboard_insights.py`, `backend/tests/unit/test_platform_audit_logs.py`, `backend/tests/unit/test_platform_role_overview.py`, `backend/tests/integration/test_platform_dashboard_api.py`, `backend/tests/integration/test_platform_audit_logs_api.py`, `backend/tests/integration/test_platform_role_overview_api.py`, `backend/tests/rbac/test_platform_dashboard_access.py`, `backend/tests/rbac/test_platform_audit_access.py`, `admin/tests/test_marketplace_insights_page.py`, `admin/tests/test_ai_audit_logs_page.py`, and `admin/tests/test_role_access_overview_page.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Stories (Phases 3-5)**: Depend on Foundational completion
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1**: Starts after Foundational and has no dependency on other stories
- **US2**: Starts after Foundational and depends on the shared platform router, schemas, and auth gate from Phase 2
- **US3**: Starts after Foundational and depends on the shared platform router, schemas, and auth gate from Phase 2

### Within Each User Story

- Write tests first and make sure they fail before implementation
- Query/repository work before service shaping
- Service shaping before route exposure
- Backend contracts before Streamlit page wiring
- Finish each story to an independently testable state before treating it as done

### Parallel Opportunities

- Phase 1 tasks marked `[P]` can run in parallel
- Phase 2 tasks marked `[P]` can run in parallel after the permission key and migration path are defined
- In each user story, all test tasks marked `[P]` can run in parallel
- US1 backend aggregation work can proceed in parallel with Streamlit dashboard shell work after shared schemas exist
- US2 backend audit filtering can proceed in parallel with Streamlit audit page work after response shapes stabilize
- US3 backend role-summary aggregation can proceed in parallel with Streamlit role-overview work after response shapes stabilize

---

## Parallel Example: User Story 1

```bash
# Run the insight test layers together
Task: "Add demand-insight query and service unit tests in backend/tests/unit/test_platform_dashboard_insights.py"
Task: "Add platform dashboard API integration tests in backend/tests/integration/test_platform_dashboard_api.py"
Task: "Add Streamlit insights-page tests in admin/tests/test_marketplace_insights_page.py"

# Build backend and Streamlit sides in parallel once schemas exist
Task: "Implement aggregate demand-insight queries in backend/app/admin/query_service.py and backend/app/listings/query_service.py"
Task: "Replace the placeholder admin home in admin/app.py and admin/components.py"
```

## Parallel Example: User Story 2

```bash
# Audit backend coverage can move together
Task: "Add platform audit-log unit tests in backend/tests/unit/test_platform_audit_logs.py"
Task: "Add audit-log API integration tests in backend/tests/integration/test_platform_audit_logs_api.py"
Task: "Add RBAC coverage in backend/tests/rbac/test_platform_audit_access.py"

# UI and backend implementation can split after contracts settle
Task: "Implement paginated platform audit-log queries in backend/app/admin/query_service.py and backend/app/audit/repository.py"
Task: "Build the Streamlit audit-log page in admin/pages/2_AI_Audit_Logs.py"
```

## Parallel Example: User Story 3

```bash
# Role overview work can split across backend and admin
Task: "Implement role and permission overview queries in backend/app/admin/query_service.py and backend/app/auth/repository.py"
Task: "Build the Streamlit role and surface overview page in admin/pages/3_Role_Access_Overview.py and admin/components.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate platform-admin entry plus aggregate demand insights end to end

### Incremental Delivery

1. Ship US1 to make the platform admin dashboard immediately useful for marketplace oversight
2. Add US2 to expose safe AI audit investigation
3. Add US3 to expose role and access governance
4. Finish with Phase 6 hardening and focused regressions

### Suggested MVP Scope

- **Recommended MVP**: Phase 1 + Phase 2 + User Story 1

---

## Notes

- All tasks follow the required checklist format with task IDs, optional `[P]` markers, story labels where required, and exact file paths
- The platform-admin surface stays inside the existing `backend/app/admin` module and `admin/` Streamlit service rather than introducing a second admin backend
