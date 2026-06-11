# Tasks: Agency Dashboard Core UI Without AI

**Input**: Design documents from `specs/007-agency-dashboard-core-ui-without-ai/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/dashboard-routes.md`, `quickstart.md`

**Tests**: Constitution-required frontend route/component/browser tests and backend integration/RBAC tests are included for role restrictions, employee onboarding, lead review, and viewing schedule behavior.

**React UI Library**: `shadcn/ui` is the confirmed component approach for Phase 6 implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same phase because it touches different files or depends only on completed earlier phases.
- **[Story]**: User story label for story phases only.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Structure)

**Purpose**: Prepare the agency-app structure, design system baseline, and test scaffolding for Phase 6.

- [X] T001 Create Phase 6 agency-app folder scaffolds in `apps/agency/src/app/`, `apps/agency/src/pages/`, `apps/agency/src/features/`, `apps/agency/src/components/`, `apps/agency/src/lib/`, `apps/agency/src/styles/`, and `apps/agency/tests/`
- [X] T002 Update `apps/agency/package.json`, `apps/agency/tsconfig.json`, and `apps/agency/vite.config.ts` with the Phase 6 dependency, test-tooling, Playwright, and `shadcn/ui` baseline
- [X] T003 [P] Create agency frontend test bootstrap files in `apps/agency/tests/setup.ts` and `apps/agency/tests/render-app.tsx`
- [X] T004 [P] Create shared UI theme and utility entry files in `apps/agency/src/styles/global.css`, `apps/agency/src/styles/theme.css`, and `apps/agency/src/lib/utils.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build auth/session reuse, shared API access, route guards, and shell primitives that every agency story depends on.

**CRITICAL**: No user story work begins until this phase is complete.

### Tests for Foundational Phase

- [X] T005 [P] Create agency auth-routing and protected-route tests in `apps/agency/tests/auth-routing.test.tsx`
- [X] T006 [P] Create agency providers, session-restore, and query-client tests in `apps/agency/tests/app-providers.test.tsx`
- [X] T007 [P] Create backend employee existing-account-by-email onboarding tests in `backend/tests/integration/test_agency_employee_email_invite_api.py`

### Implementation for Foundational Phase

- [X] T008 Implement agency app providers, route guards, router shell, and root app wiring in `apps/agency/src/app/providers.tsx`, `apps/agency/src/app/guards.tsx`, `apps/agency/src/app/router.tsx`, `apps/agency/src/main.tsx`, and `apps/agency/src/App.tsx`
- [X] T009 Implement shared API client, auth transport, query client, and memory-only session helpers in `apps/agency/src/lib/api/client.ts`, `apps/agency/src/lib/api/auth.ts`, `apps/agency/src/lib/query/query-client.ts`, and `apps/agency/src/lib/session/auth-session.ts`
- [X] T010 Implement shared protected layout, sidebar, header, loading, empty, and error primitives in `apps/agency/src/components/ProtectedLayout.tsx`, `apps/agency/src/components/LoadingSkeleton.tsx`, `apps/agency/src/components/EmptyState.tsx`, `apps/agency/src/components/ErrorState.tsx`, and `apps/agency/src/features/navigation/AgencySidebar.tsx`
- [X] T011 Implement agency sign-in page and auth-form flow in `apps/agency/src/pages/auth/SignInPage.tsx`, `apps/agency/src/features/auth/SignInForm.tsx`, and `apps/agency/src/features/auth/useAgencyAuth.ts`
- [X] T012 Implement shared role-aware navigation state and tenant-session helpers in `apps/agency/src/features/navigation/useAgencyNavigation.ts`, `apps/agency/src/features/navigation/RouteAccess.ts`, and `apps/agency/src/lib/session/tenant-session.ts`
- [X] T013 Run foundational validation commands for the agency auth/session shell from `specs/007-agency-dashboard-core-ui-without-ai/quickstart.md`

**Checkpoint**: Agency sign-in, protected routing, shared fetch/query infrastructure, and role-aware shell are ready.

---

## Phase 3: User Story 1 - Agency Admin Operations (Priority: P1) 🎯 MVP

**Goal**: Agency admins can use a protected dashboard to manage profile settings, support employees, listings, and listing viewing slots.

**Independent Test**: Sign in as `agency.admin@akarai.test`, open the dashboard, update the agency profile, add a support employee by email, create a listing that publishes immediately, and manage viewing slots for that listing.

### Tests for User Story 1

- [X] T014 [P] [US1] Create agency-admin dashboard and role-visibility tests in `apps/agency/tests/dashboard-admin-flow.test.tsx`
- [X] T015 [P] [US1] Create employee-management frontend tests in `apps/agency/tests/employee-management.test.tsx`
- [X] T016 [P] [US1] Create listing-management and slot-manager frontend tests in `apps/agency/tests/listing-management.test.tsx`
- [X] T017 [P] [US1] Create backend agency profile and existing-account-by-email onboarding regression tests in `backend/tests/integration/test_agency_core_api.py` and `backend/tests/rbac/test_support_employee_restrictions.py`

### Implementation for User Story 1

- [X] T018 [US1] Implement existing-account-by-email support-employee onboarding in `backend/app/agencies/schemas.py`, `backend/app/agencies/repository.py`, `backend/app/agencies/service.py`, `backend/app/agencies/router.py`, and `backend/app/users/repository.py`
- [X] T019 [US1] Implement agency dashboard summary hooks and cards in `apps/agency/src/pages/dashboard/DashboardPage.tsx`, `apps/agency/src/features/dashboard/useDashboardSummary.ts`, and `apps/agency/src/features/dashboard/DashboardCards.tsx`
- [X] T020 [US1] Implement agency profile settings form and mutation flow in `apps/agency/src/pages/profile/AgencyProfilePage.tsx`, `apps/agency/src/features/profile/ProfileForm.tsx`, and `apps/agency/src/features/profile/useAgencyProfile.ts`
- [X] T021 [US1] Implement employee directory, existing-account-by-email add flow, edit, and deactivate flows in `apps/agency/src/pages/employees/EmployeesPage.tsx`, `apps/agency/src/features/employees/EmployeeTable.tsx`, `apps/agency/src/features/employees/EmployeeInviteForm.tsx`, and `apps/agency/src/features/employees/useEmployees.ts`
- [X] T022 [US1] Implement listings table, listing editor, and immediate-publish request mapping in `apps/agency/src/pages/listings/ListingsPage.tsx`, `apps/agency/src/pages/listings/ListingEditorPage.tsx`, `apps/agency/src/features/listings/ListingForm.tsx`, and `apps/agency/src/features/listings/useAgencyListings.ts`
- [X] T023 [US1] Implement listing viewing-slot manager flows in `apps/agency/src/pages/listings/ViewingSlotsPage.tsx`, `apps/agency/src/features/listings/ViewingSlotsManager.tsx`, and `apps/agency/src/features/listings/useViewingSlots.ts`
- [X] T024 [US1] Wire admin-only navigation and route exposure for profile, employees, listings, and slot-manager pages in `apps/agency/src/app/router.tsx`, `apps/agency/src/app/guards.tsx`, and `apps/agency/src/features/navigation/AgencySidebar.tsx`
- [X] T025 [US1] Integrate dashboard counts, profile save feedback, employee onboarding feedback, and listing publish feedback in `apps/agency/src/pages/dashboard/DashboardPage.tsx`, `apps/agency/src/pages/employees/EmployeesPage.tsx`, and `apps/agency/src/pages/listings/ListingEditorPage.tsx`

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Support Employee Workflows (Priority: P2)

**Goal**: Support employees can review leads and view filtered schedules while admin-only actions remain inaccessible.

**Independent Test**: Sign in as `support@akarai.test`, confirm the restricted dashboard navigation, review an active lead so it moves to reviewed leads, and open the viewing schedules page with working filters while admin-only pages stay blocked.

### Tests for User Story 2

- [X] T026 [P] [US2] Create support-role route and navigation restriction tests in `apps/agency/tests/support-role-routing.test.tsx`
- [X] T027 [P] [US2] Create active-leads, reviewed-leads, and lead-review frontend tests in `apps/agency/tests/lead-review-flow.test.tsx`
- [X] T028 [P] [US2] Create viewing-schedule filter and read-only frontend tests in `apps/agency/tests/viewing-schedules.test.tsx`
- [X] T029 [P] [US2] Create backend reviewed-leads and non-reviewed queue filter tests in `backend/tests/integration/test_agency_reviewed_leads_api.py`
- [X] T030 [P] [US2] Create backend viewing-schedule filter and admin-only schedule-mutation tests in `backend/tests/integration/test_agency_viewing_filters_api.py` and `backend/tests/rbac/test_support_employee_restrictions.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement `reviewed=true|false` agency lead filtering and reviewed-queue support in `backend/app/leads/schemas.py`, `backend/app/leads/repository.py`, `backend/app/leads/service.py`, and `backend/app/leads/router.py`
- [X] T032 [US2] Implement agency viewing-schedule filters and admin-only schedule-status mutation enforcement in `backend/app/viewings/schemas.py`, `backend/app/viewings/repository.py`, `backend/app/viewings/service.py`, and `backend/app/viewings/router.py`
- [X] T033 [US2] Implement active leads, lead detail, and reviewed leads pages in `apps/agency/src/pages/leads/LeadsPage.tsx`, `apps/agency/src/pages/leads/LeadDetailPage.tsx`, `apps/agency/src/pages/leads/ReviewedLeadsPage.tsx`, `apps/agency/src/features/leads/useAgencyLeads.ts`, and `apps/agency/src/features/leads/LeadReviewForm.tsx`
- [X] T034 [US2] Implement viewing schedules page, filter controls, and schedule detail presentation in `apps/agency/src/pages/viewings/ViewingsPage.tsx`, `apps/agency/src/features/viewings/useAgencyViewings.ts`, and `apps/agency/src/features/viewings/ViewingFilters.tsx`
- [X] T035 [US2] Enforce support-employee page visibility and read-only schedule behavior in `apps/agency/src/app/router.tsx`, `apps/agency/src/app/guards.tsx`, and `apps/agency/src/features/navigation/AgencySidebar.tsx`

**Checkpoint**: User Story 2 is functional and independently testable.

---

## Phase 5: User Story 3 - Operational Placeholders and Navigation (Priority: P3)

**Goal**: Agency users can reach placeholder-only spam leads and policy document pages while the whole dashboard keeps coherent loading and empty-state behavior.

**Independent Test**: Sign in as an agency user, open the placeholder pages, switch across dashboard sections with empty or slow data, and verify stable loading/empty/placeholder states instead of broken pages.

### Tests for User Story 3

- [X] T036 [P] [US3] Create placeholder-route and navigation tests in `apps/agency/tests/placeholders-navigation.test.tsx`
- [X] T037 [P] [US3] Create dashboard loading and empty-state frontend tests in `apps/agency/tests/loading-empty-states.test.tsx`

### Implementation for User Story 3

- [X] T038 [US3] Implement placeholder-only spam leads and policy document pages in `apps/agency/src/pages/placeholders/SpamLeadsPage.tsx` and `apps/agency/src/pages/placeholders/PolicyDocumentsPage.tsx`
- [X] T039 [US3] Implement shared page-header, loading, empty, and no-results patterns across agency pages in `apps/agency/src/features/navigation/PageHeader.tsx`, `apps/agency/src/components/LoadingSkeleton.tsx`, `apps/agency/src/components/EmptyState.tsx`, and `apps/agency/src/components/ErrorState.tsx`
- [X] T040 [US3] Wire placeholder routes and dashboard links into `apps/agency/src/app/router.tsx`, `apps/agency/src/features/navigation/AgencySidebar.tsx`, and `apps/agency/src/pages/dashboard/DashboardPage.tsx`

**Checkpoint**: User Story 3 is functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, validation, and scope guardrails across all Phase 6 stories.

- [X] T041 [P] Update Phase 6 validation guidance and local responsiveness checks in `specs/007-agency-dashboard-core-ui-without-ai/quickstart.md`
- [X] T042 [P] Sync the Phase 6 route and employee-onboarding contract details in `specs/007-agency-dashboard-core-ui-without-ai/contracts/dashboard-routes.md`
- [X] T043 [P] Update Phase 6 architecture notes in `docs/DECISIONS.md` and `backend/app/README.md`
- [X] T044 Run backend regression tests and agency-app build from `specs/007-agency-dashboard-core-ui-without-ai/quickstart.md`
- [X] T045 Run agency-admin and support-employee browser validation from `specs/007-agency-dashboard-core-ui-without-ai/quickstart.md`
- [X] T046 Run the Phase 6 scope guard scan from `specs/007-agency-dashboard-core-ui-without-ai/quickstart.md` to confirm no AI, spam-classification, policy-upload, or email-delivery implementation drift
- [X] T047 Confirm no `dao.py` files, no `.env` staging, and no `.codex/` or `graphify-out/` staging in repository status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Foundational. This is the MVP slice.
- **Phase 4 US2**: Depends on Foundational and reuses the protected shell and route/role infrastructure established for US1.
- **Phase 5 US3**: Depends on Foundational and benefits from the dashboard shell created in US1.
- **Phase 6 Polish**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational. No dependency on US2 or US3.
- **US2 (P2)**: Starts after Foundational; full validation benefits from the shared shell and auth/session patterns from US1.
- **US3 (P3)**: Starts after Foundational; full validation benefits from the route/navigation shell established in US1.

### Within Each User Story

- Write the listed tests first and confirm they fail before implementation.
- Backend contract adjustments before frontend flows that consume them.
- Shared hooks/data loaders before page composition.
- Route-guard and navigation restrictions before story checkpoint validation.
- Story validation must pass before moving to the next priority if working sequentially.

## Parallel Opportunities

- Setup tasks T003-T004 can run in parallel after T001-T002.
- Foundational tests T005-T007 can run in parallel.
- US1 tests T014-T017 can run in parallel.
- US2 tests T026-T030 can run in parallel.
- US3 tests T036-T037 can run in parallel.
- Polish documentation tasks T041-T043 can run in parallel.

## Parallel Example: User Story 1

```text
Task: "T014 [P] [US1] Create agency-admin dashboard and role-visibility tests in apps/agency/tests/dashboard-admin-flow.test.tsx"
Task: "T015 [P] [US1] Create employee-management frontend tests in apps/agency/tests/employee-management.test.tsx"
Task: "T016 [P] [US1] Create listing-management and slot-manager frontend tests in apps/agency/tests/listing-management.test.tsx"
Task: "T017 [P] [US1] Create backend agency profile and email-onboarding regression tests in backend/tests/integration/test_agency_core_api.py and backend/tests/rbac/test_support_employee_restrictions.py"
```

## Parallel Example: User Story 2

```text
Task: "T026 [P] [US2] Create support-role route and navigation restriction tests in apps/agency/tests/support-role-routing.test.tsx"
Task: "T027 [P] [US2] Create active-leads, reviewed-leads, and lead-review frontend tests in apps/agency/tests/lead-review-flow.test.tsx"
Task: "T028 [P] [US2] Create viewing-schedule filter and read-only frontend tests in apps/agency/tests/viewing-schedules.test.tsx"
Task: "T029 [P] [US2] Create backend reviewed-lead queue transition tests in backend/tests/integration/test_agency_reviewed_leads_api.py"
Task: "T030 [P] [US2] Create backend viewing-schedule filter and support-role access tests in backend/tests/integration/test_agency_viewing_filters_api.py and backend/tests/rbac/test_support_employee_restrictions.py"
```

## Parallel Example: User Story 3

```text
Task: "T036 [P] [US3] Create placeholder-route and navigation tests in apps/agency/tests/placeholders-navigation.test.tsx"
Task: "T037 [P] [US3] Create dashboard loading and empty-state frontend tests in apps/agency/tests/loading-empty-states.test.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational auth/session/query/shell infrastructure.
3. Complete Phase 3 / US1 dashboard, profile, employee management, listings, and slot manager.
4. Stop and validate the agency-admin workflow before moving to support-role and placeholder work.

### Incremental Delivery

1. Foundation ready.
2. Deliver US1 agency-admin operations MVP.
3. Deliver US2 support-employee leads and schedules workflow.
4. Deliver US3 placeholder and navigation hardening.
5. Run full quickstart validation and scope scan.

### Guardrails

- Do not implement AI widgets, chat, voice, match score, spam classification, policy upload processing, media upload, or email delivery in this phase.
- Do not create `dao.py`.
- Do not stage `.env`, `.codex/`, or `graphify-out/`.
