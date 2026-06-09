# Tasks: Core Domain Database and CRUD APIs

**Input**: Design documents from `specs/005-core-domain-crud-apis/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`, `quickstart.md`

**Tests**: Constitution-required backend unit, integration, transaction, RBAC, tenant-isolation, pagination, and scope tests are included. No AI/RAG/media/OCR/email/dashboard implementation tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same phase because it touches different files or depends only on completed earlier phases.
- **[Story]**: User story label for story phases only.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Structure)

**Purpose**: Prepare Phase 4 module files and route wiring without implementing business behavior.

- [X] T001 Create Phase 4 module placeholders in `backend/app/listings/router.py`, `backend/app/listings/service.py`, `backend/app/listings/repository.py`, `backend/app/listings/schemas.py`, `backend/app/listings/models.py`, and `backend/app/listings/query_service.py`
- [X] T002 Create Phase 4 module placeholders in `backend/app/leads/router.py`, `backend/app/leads/service.py`, `backend/app/leads/repository.py`, `backend/app/leads/schemas.py`, and `backend/app/leads/models.py`
- [X] T003 Create Phase 4 module placeholders in `backend/app/viewings/router.py`, `backend/app/viewings/service.py`, `backend/app/viewings/repository.py`, `backend/app/viewings/schemas.py`, and `backend/app/viewings/models.py`
- [X] T004 Create Phase 4 module placeholders in `backend/app/search/router.py`, `backend/app/search/service.py`, `backend/app/search/repository.py`, `backend/app/search/schemas.py`, and `backend/app/search/models.py`
- [X] T005 Extend existing notification module placeholders in `backend/app/notifications/router.py`, `backend/app/notifications/service.py`, `backend/app/notifications/repository.py`, and `backend/app/notifications/schemas.py`
- [X] T006 Extend existing agency module placeholders in `backend/app/agencies/router.py`, `backend/app/agencies/schemas.py`, `backend/app/agencies/models.py`, `backend/app/agencies/repository.py`, and `backend/app/agencies/service.py`
- [X] T007 Create shared Phase 4 dependency helpers for tenant-scoped CRUD routes in `backend/app/common/dependencies.py`
- [X] T008 Add Phase 4 permission keys for agency, listing, lead, viewing, notification, and search actions in `backend/app/auth/permissions.py`
- [X] T009 Update Alembic model imports for Phase 4 modules in `backend/alembic/env.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared domain foundations that all user stories require.

**CRITICAL**: No user story work begins until this phase is complete.

### Tests for Foundational Phase

- [X] T010 [P] Create migration coverage tests for all Phase 4 tables, indexes, foreign keys, and constraints in `backend/tests/integration/test_phase4_migrations.py`
- [X] T011 [P] Create permission seed coverage tests for Phase 4 permission keys in `backend/tests/rbac/test_phase4_permissions.py`
- [X] T012 [P] Create shared pagination, rate-limit, and cache invalidation tests in `backend/tests/integration/test_phase4_pagination_contract.py` and `backend/tests/unit/test_phase4_shared_guards.py`
- [X] T013 [P] Create scope guard test preventing AI/RAG/media/OCR/email/dashboard/chat behavior in `backend/tests/integration/test_phase4_scope_guard.py`

### Implementation for Foundational Phase

- [X] T014 Create shared Phase 4 domain constants and rate-limit policy entries in `backend/app/common/domain.py` and `backend/app/common/rate_limit.py`
- [X] T015 Implement Phase 4 Alembic migration for agency profiles, listings, photo metadata, viewing slots, scheduled viewings, viewing status history, saved listings, comparison sessions/items, leads, lead result placeholders, reviewed lead records, notifications update fields, search logs, and domain event logs in `backend/alembic/versions/0004_core_domain_crud.py`
- [X] T016 Implement AgencyProfile and employee-management model updates in `backend/app/agencies/models.py`
- [X] T017 Implement Listing, ListingPhotoMetadata, SavedListing, ComparisonSession, and ComparisonItem models in `backend/app/listings/models.py`
- [X] T018 Implement Lead, LeadSpamResult, LeadLevelResult, LeadSuggestedReply, and ReviewedLeadRecord models in `backend/app/leads/models.py`
- [X] T019 Implement ListingViewingSlot, ScheduledViewing, and ScheduledViewingStatusHistory models in `backend/app/viewings/models.py`
- [X] T020 Implement SearchLog model in `backend/app/search/models.py`
- [X] T021 Extend Notification model for Phase 4 read/dismiss state and recipient access in `backend/app/notifications/models.py`
- [X] T022 Implement DomainEventLog model and explicit listing-search cache invalidation helpers in `backend/app/common/events.py` and `backend/app/common/cache.py`
- [X] T023 Add Phase 4 permission seeds to migration and permission definitions in `backend/alembic/versions/0004_core_domain_crud.py` and `backend/app/auth/permissions.py`
- [X] T024 Update shared test fixtures for Phase 4 seeded agency admin, support employee, user, second tenant, active listing setup, and cache/rate-limit test helpers in `backend/tests/conftest.py`
- [X] T025 Run foundational validation commands documented in `specs/005-core-domain-crud-apis/quickstart.md`

**Checkpoint**: Database schema, permissions, imports, fixtures, and route shells are ready.

---

## Phase 3: User Story 1 - Manage Agency Core Records (Priority: P1) MVP

**Goal**: Agency admins can manage agency profile, employees, listings, listing photo metadata, and viewing slots while support employees are restricted from admin-only mutations.

**Independent Test**: Sign in as agency admin and support employee, perform allowed and forbidden operations inside one agency, and verify tenant boundaries and pagination.

### Tests for User Story 1

- [ ] T026 [P] [US1] Create agency profile and employee service unit tests in `backend/tests/unit/test_agency_core_service.py`
- [ ] T027 [P] [US1] Create listing management service unit tests for status validation and support-employee restrictions in `backend/tests/unit/test_listing_management_service.py`
- [ ] T028 [P] [US1] Create viewing slot service unit tests for slot validation and capacity rules in `backend/tests/unit/test_viewing_slot_service.py`
- [ ] T029 [P] [US1] Create agency profile and employee API integration tests in `backend/tests/integration/test_agency_core_api.py`
- [ ] T030 [P] [US1] Create agency listing, photo metadata, and viewing slot API integration tests in `backend/tests/integration/test_agency_listing_api.py`
- [ ] T031 [P] [US1] Create support employee restriction tests in `backend/tests/rbac/test_support_employee_restrictions.py`
- [ ] T032 [P] [US1] Create agency tenant isolation tests for profile, employees, listings, photo metadata, and viewing slots in `backend/tests/rbac/test_agency_core_tenant_isolation.py`
- [ ] T033 [P] [US1] Create agency list pagination tests in `backend/tests/integration/test_agency_core_pagination.py`

### Implementation for User Story 1

- [X] T034 [US1] Implement agency profile and employee schemas in `backend/app/agencies/schemas.py`
- [X] T035 [US1] Implement agency profile and employee repository methods in `backend/app/agencies/repository.py`
- [X] T036 [US1] Implement agency profile and employee service logic with Agency Admin restrictions in `backend/app/agencies/service.py`
- [X] T037 [US1] Implement agency profile and employee routes from `contracts/openapi.yaml` in `backend/app/agencies/router.py`
- [X] T038 [US1] Implement listing management schemas for agency create/update/list/detail in `backend/app/listings/schemas.py`
- [X] T039 [US1] Implement listing repository methods for tenant listing CRUD and status changes in `backend/app/listings/repository.py`
- [X] T040 [US1] Implement listing service logic for create/update/activate/deactivate/archive and support-employee restrictions in `backend/app/listings/service.py`
- [X] T041 [US1] Implement agency listing routes from `contracts/openapi.yaml` in `backend/app/listings/router.py`
- [X] T042 [US1] Implement listing photo metadata schemas and repository methods in `backend/app/listings/schemas.py` and `backend/app/listings/repository.py`
- [X] T043 [US1] Implement listing photo metadata service logic for create/list/update/reorder/remove without media upload in `backend/app/listings/service.py`
- [X] T044 [US1] Implement listing photo metadata routes from `contracts/openapi.yaml` in `backend/app/listings/router.py`
- [X] T045 [US1] Implement viewing slot schemas in `backend/app/viewings/schemas.py`
- [X] T046 [US1] Implement viewing slot repository methods in `backend/app/viewings/repository.py`
- [X] T047 [US1] Implement viewing slot service logic for create/list/update/deactivate and capacity validation in `backend/app/viewings/service.py`
- [X] T048 [US1] Implement viewing slot routes from `contracts/openapi.yaml` in `backend/app/viewings/router.py`
- [X] T049 [US1] Add domain event log writes for agency profile, employee, listing status, photo metadata, and viewing slot changes in `backend/app/common/events.py`
- [X] T050 [US1] Wire agency, listing, and viewing slot routers into FastAPI route prefixes in `backend/app/main.py`

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Browse, Save, Compare, and Request Listings (Priority: P2)

**Goal**: Users can search active listings manually, save listings, compare up to four listings, submit inquiries, and schedule viewings from available slots.

**Independent Test**: Create active listings and viewing slots, then act as a user to search, save, compare, inquire, and schedule a viewing.

### Tests for User Story 2

- [ ] T051 [P] [US2] Create public listing search filter, sort, rate-limit, and cache invalidation unit tests in `backend/tests/unit/test_listing_search_service.py`
- [ ] T052 [P] [US2] Create saved listing service unit tests for duplicate prevention and ownership in `backend/tests/unit/test_saved_listing_service.py`
- [ ] T053 [P] [US2] Create comparison service unit tests for four-item limit and ownership in `backend/tests/unit/test_comparison_service.py`
- [ ] T054 [P] [US2] Create user inquiry lead creation service unit tests in `backend/tests/unit/test_user_inquiry_service.py`
- [ ] T055 [P] [US2] Create viewing booking transaction and rate-limit tests for atomic viewing and initial history creation in `backend/tests/integration/test_viewing_booking_transaction.py`
- [ ] T056 [P] [US2] Create public listing search and detail API integration tests including search rate limits in `backend/tests/integration/test_public_listing_api.py`
- [ ] T057 [P] [US2] Create saved listings and comparison API integration tests in `backend/tests/integration/test_user_listing_actions_api.py`
- [ ] T058 [P] [US2] Create inquiry and viewing booking API integration tests including rate limits in `backend/tests/integration/test_user_inquiry_viewing_api.py`
- [ ] T059 [P] [US2] Create user ownership isolation tests for saved listings, comparison sessions, inquiries, and viewing detail access in `backend/tests/rbac/test_user_owned_domain_isolation.py`

### Implementation for User Story 2

- [X] T060 [US2] Implement public listing search schemas including filters and sort options in `backend/app/listings/schemas.py`
- [X] T061 [US2] Implement listing search query service for active listings, manual filters, sorting, and public field projection in `backend/app/listings/query_service.py`
- [X] T062 [US2] Implement public listing search and detail service methods with cached reads in `backend/app/listings/service.py`
- [X] T063 [US2] Implement public listing search and detail routes with search rate limits from `contracts/openapi.yaml` in `backend/app/listings/router.py`
- [X] T064 [US2] Implement saved listing repository methods in `backend/app/listings/repository.py`
- [X] T065 [US2] Implement saved listing service logic for save, unsave, list, duplicate prevention, and ownership in `backend/app/listings/service.py`
- [X] T066 [US2] Implement saved listing routes from `contracts/openapi.yaml` in `backend/app/listings/router.py`
- [X] T067 [US2] Implement comparison schemas for sessions and items in `backend/app/listings/schemas.py`
- [X] T068 [US2] Implement comparison repository methods in `backend/app/listings/repository.py`
- [X] T069 [US2] Implement comparison service logic for session CRUD, item add/remove, four-item limit, and ownership in `backend/app/listings/service.py`
- [X] T070 [US2] Implement comparison routes from `contracts/openapi.yaml` in `backend/app/listings/router.py`
- [X] T071 [US2] Implement lead inquiry schemas in `backend/app/leads/schemas.py`
- [X] T072 [US2] Implement lead repository create methods for user inquiries in `backend/app/leads/repository.py`
- [X] T073 [US2] Implement lead inquiry service logic that enforces inquiry rate limits and creates tenant-owned leads with status `new` in `backend/app/leads/service.py`
- [X] T074 [US2] Implement listing inquiry route with rate-limit handling from `contracts/openapi.yaml` in `backend/app/leads/router.py`
- [X] T075 [US2] Implement viewing booking schemas in `backend/app/viewings/schemas.py`
- [X] T076 [US2] Implement viewing booking repository methods for slot locking, scheduled viewing insert, and status history insert in `backend/app/viewings/repository.py`
- [X] T077 [US2] Implement viewing booking service transaction with booking rate limits for available slots and initial `scheduled` history in `backend/app/viewings/service.py`
- [X] T078 [US2] Implement viewing booking and user scheduled viewing list/detail routes from `contracts/openapi.yaml` in `backend/app/viewings/router.py`
- [X] T079 [US2] Implement manual search log schemas, repository methods, tenant-scoped list queries, and service creation in `backend/app/search/schemas.py`, `backend/app/search/repository.py`, and `backend/app/search/service.py`
- [X] T080 [US2] Write search log records, expose cached public listing search reads, and invalidate cached listing-search results on public-search-affecting listing mutations in `backend/app/listings/service.py` and `backend/app/common/cache.py`
- [X] T081 [US2] Add domain event log writes and shared rate-limit enforcement hooks for search, lead creation, and viewing booking in `backend/app/common/events.py`, `backend/app/common/rate_limit.py`, `backend/app/listings/router.py`, `backend/app/leads/router.py`, and `backend/app/viewings/router.py`

**Checkpoint**: User Story 2 is functional and independently testable.

---

## Phase 5: User Story 3 - Track Lead and Viewing Operations (Priority: P3)

**Goal**: Agency actors can track lead review, scheduled viewing status, notifications, and domain logs with tenant-safe history.

**Independent Test**: Change lead review state, scheduled viewing status, and notification state, then verify history and log records.

### Tests for User Story 3

- [X] T082 [P] [US3] Create agency lead status and review service unit tests in `backend/tests/unit/test_agency_lead_service.py`
- [X] T083 [P] [US3] Create scheduled viewing status transition unit tests in `backend/tests/unit/test_scheduled_viewing_status_service.py`
- [X] T084 [P] [US3] Create notification access and state service unit tests in `backend/tests/unit/test_notification_domain_service.py`
- [X] T085 [P] [US3] Create agency lead API integration tests in `backend/tests/integration/test_agency_lead_api.py`
- [X] T086 [P] [US3] Create agency viewing API integration tests in `backend/tests/integration/test_agency_viewing_api.py`
- [X] T087 [P] [US3] Create notification, search-log, and domain-log API integration tests in `backend/tests/integration/test_notification_domain_api.py` and `backend/tests/integration/test_operational_logs_api.py`
- [X] T088 [P] [US3] Create lead, viewing, notification, search log, and domain log tenant isolation tests in `backend/tests/rbac/test_operational_tenant_isolation.py`
- [X] T089 [P] [US3] Create domain event log, search log list, and scheduled viewing detail integration tests in `backend/tests/integration/test_domain_event_logs.py` and `backend/tests/integration/test_viewing_detail_api.py`

### Implementation for User Story 3

- [X] T090 [US3] Implement agency lead schemas for list/detail/status/review and result placeholders in `backend/app/leads/schemas.py`
- [X] T091 [US3] Implement agency lead repository methods for tenant list/detail/status/review and result placeholder reads in `backend/app/leads/repository.py`
- [X] T092 [US3] Implement agency lead service logic for status transitions `new`, `reviewed`, `closed` and reviewed lead records in `backend/app/leads/service.py`
- [X] T093 [US3] Implement agency lead routes from `contracts/openapi.yaml` in `backend/app/leads/router.py`
- [X] T094 [US3] Implement scheduled viewing status schemas in `backend/app/viewings/schemas.py`
- [X] T095 [US3] Implement scheduled viewing tenant and user list/detail/status repository methods in `backend/app/viewings/repository.py`
- [X] T096 [US3] Implement scheduled viewing status transition service for `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, and `no_show` in `backend/app/viewings/service.py`
- [X]  [US3] Implement agency scheduled viewing list/detail/status routes from `contracts/openapi.yaml` in `backend/app/viewings/router.py`
- [X]  [US3] Implement notification schemas for list/detail/read/dismiss in `backend/app/notifications/schemas.py`
- [X]  [US3] Implement notification repository methods for intended-recipient access in `backend/app/notifications/repository.py`
- [X] T100 [US3] Implement notification service logic for internal create/list/view/read/dismiss without email delivery in `backend/app/notifications/service.py`
- [X] T101 [US3] Implement notification routes and operational log list routes from `contracts/openapi.yaml` in `backend/app/notifications/router.py` and `backend/app/search/router.py`
- [X] T102 [US3] Implement domain event log and search log repository/query helpers in `backend/app/common/events.py` and `backend/app/search/repository.py`
- [X] T103 [US3] Add domain event log writes for lead review, lead close, viewing status changes, and notification state changes, plus tenant-scoped log list service methods in `backend/app/common/events.py` and `backend/app/search/service.py`
- [X] T104 [US3] Wire leads, viewings, notifications, and operational log routers into FastAPI route prefixes in `backend/app/main.py`

**Checkpoint**: User Story 3 is functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify Phase 4 scope, docs, contracts, and end-to-end behavior.

- [X] T105 [P] Update Phase 4 quickstart validation details in `specs/005-core-domain-crud-apis/quickstart.md`
- [X] T106 [P] Update Phase 4 OpenAPI contract if implementation endpoint names differ in `specs/005-core-domain-crud-apis/contracts/openapi.yaml`
- [X] T107 [P] Update backend module documentation for Phase 4 ownership in `backend/app/README.md`
- [X] T108 [P] Add Phase 4 notes to project decisions in `docs/DECISIONS.md`
- [X] T109 Run Alembic upgrade validation in Docker Compose using `specs/005-core-domain-crud-apis/quickstart.md`
- [X] T110 Run full backend pytest suite in Docker Compose using `specs/005-core-domain-crud-apis/quickstart.md`
- [X] T111 Run Phase 4 scope guard scan from `specs/005-core-domain-crud-apis/quickstart.md`
- [X] T112 Confirm no `dao.py` files, no `.env` staging, and no `.codex/` or `graphify-out/` staging in repository status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Foundational. MVP scope.
- **Phase 4 US2**: Depends on Foundational and active listings/viewing slots from US1 for full end-to-end validation, but user-owned actions remain independently testable with fixtures.
- **Phase 5 US3**: Depends on Foundational and can use fixtures or records from US2 for operational tracking validation.
- **Phase 6 Polish**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Start after Foundational. No dependency on US2 or US3.
- **US2 (P2)**: Start after Foundational; full happy path benefits from US1 listing/slot management.
- **US3 (P3)**: Start after Foundational; validates operational tracking for records created by US2 or fixtures.

### Within Each User Story

- Write tests first and confirm they fail before implementation.
- Models and migrations must exist before repository implementation.
- Repositories before services.
- Services before routers.
- Router wiring after route modules exist.
- Tenant/RBAC and transaction tests must pass before story checkpoint.

## Parallel Opportunities

- Setup placeholder tasks T001-T006 can be split by module.
- Foundational tests T010-T013 can run in parallel.
- Model tasks T016-T022 can run in parallel after migration shape is agreed.
- US1 tests T026-T033 can run in parallel.
- US2 tests T051-T059 can run in parallel.
- US3 tests T082-T089 can run in parallel.
- Polish documentation tasks T105-T108 can run in parallel.

## Parallel Example: User Story 1

```text
Task: "T026 [P] [US1] Create agency profile and employee service unit tests in backend/tests/unit/test_agency_core_service.py"
Task: "T027 [P] [US1] Create listing management service unit tests for status validation and support-employee restrictions in backend/tests/unit/test_listing_management_service.py"
Task: "T028 [P] [US1] Create viewing slot service unit tests for slot validation and capacity rules in backend/tests/unit/test_viewing_slot_service.py"
Task: "T031 [P] [US1] Create support employee restriction tests in backend/tests/rbac/test_support_employee_restrictions.py"
```

## Parallel Example: User Story 2

```text
Task: "T051 [P] [US2] Create public listing search filter and sort unit tests in backend/tests/unit/test_listing_search_service.py"
Task: "T052 [P] [US2] Create saved listing service unit tests for duplicate prevention and ownership in backend/tests/unit/test_saved_listing_service.py"
Task: "T053 [P] [US2] Create comparison service unit tests for four-item limit and ownership in backend/tests/unit/test_comparison_service.py"
Task: "T055 [P] [US2] Create viewing booking transaction tests for atomic viewing and initial history creation in backend/tests/integration/test_viewing_booking_transaction.py"
```

## Parallel Example: User Story 3

```text
Task: "T082 [P] [US3] Create agency lead status and review service unit tests in backend/tests/unit/test_agency_lead_service.py"
Task: "T083 [P] [US3] Create scheduled viewing status transition unit tests in backend/tests/unit/test_scheduled_viewing_status_service.py"
Task: "T084 [P] [US3] Create notification access and state service unit tests in backend/tests/unit/test_notification_domain_service.py"
Task: "T089 [P] [US3] Create domain event log integration tests for critical status and review changes in backend/tests/integration/test_domain_event_logs.py"
```

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational schema, permissions, fixtures, and guards.
3. Complete Phase 3 / US1 agency core records.
4. Stop and validate agency admin/support employee flows before user marketplace work.

### Incremental Delivery

1. Foundation ready.
2. Deliver US1 agency core records.
3. Deliver US2 user marketplace records.
4. Deliver US3 operational tracking.
5. Run full quickstart and scope guard validation.

### Guardrails

- Do not implement AI search, RAG, image upload/processing, OCR, email sending, dashboards, chatbot behavior, buyer-to-agency real-time chat, spam classification, lead scoring, or generated replies.
- Do not create `dao.py`.
- Do not stage `.env`, `.codex/`, or `graphify-out/`.
