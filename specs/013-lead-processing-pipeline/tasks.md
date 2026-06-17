# Tasks: Lead Processing Pipeline

**Input**: Design documents from `/specs/013-lead-processing-pipeline/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included for backend unit, API integration, transaction/outbox, RBAC/tenant-isolation, worker, model-service, and focused agency UI coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare config, secrets, and local service wiring for the external lead model service

- [X] T001 Add lead-processing and model-service configuration placeholders in `backend/app/common/config.py` and `.env.example`
- [X] T002 [P] Seed local Vault values and Docker Compose wiring for the lead model service in `vault/seed.py` and `docker-compose.yml`
- [X] T003 [P] Scaffold the dedicated inference service runtime files in `model-service/requirements.txt`, `model-service/Dockerfile`, `model-service/app/__init__.py`, and `model-service/tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared persistence, eventing, and service primitives required by all lead-processing stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add shared lead-processing event names, callback auth settings, and stage constants in `backend/app/common/events.py`, `backend/app/common/config.py`, and `backend/app/leads/schemas.py`
- [X] T005 Add Alembic schema changes and ORM fields for lead-processing metadata, retries, and analytics indexes in `backend/alembic/versions/0019_lead_processing_pipeline.py` and `backend/app/leads/models.py`
- [X] T006 Extend repository and query primitives for pending-result creation, idempotent result upserts, and trend aggregation in `backend/app/leads/repository.py` and `backend/app/leads/query_service.py`
- [X] T007 [P] Add shared lead-processing audit, redaction, and rate-limit hooks in `backend/app/rag/redaction.py`, `backend/app/audit/service.py`, and `backend/app/common/rate_limit.py`
- [X] T008 Implement worker-side HTTP client and retry helpers for the external model service in `workers/requirements.txt` and `workers/handlers/lead_processing_client.py`
- [X] T009 [P] Add model-service configuration, schema, and loader abstractions for the two-stage classifiers in `model-service/app/config.py`, `model-service/app/schemas.py`, and `model-service/app/predictors.py`

**Checkpoint**: Shared schema, retry, persistence, and model-service primitives are ready

---

## Phase 3: User Story 1 - Automatic Lead Classification (Priority: P1) 🎯 MVP

**Goal**: Save every lead immediately, classify it asynchronously as spam first and Hot/Normal second, and persist the outcome without losing the lead on inference failure

**Independent Test**: Create a new lead, verify the lead record exists before classification finishes, then confirm spam or Hot/Normal results appear after the worker and callback pipeline completes

### Tests for User Story 1

- [X] T010 [P] [US1] Add lead-processing service unit tests for stage ordering, fail-open defaults, and idempotent callbacks in `backend/tests/unit/test_lead_processing_service.py`
- [X] T011 [P] [US1] Add inquiry and callback API integration tests for asynchronous classification in `backend/tests/integration/test_lead_processing_api.py`
- [X] T012 [P] [US1] Add transaction and outbox durability tests for `lead.created` emission and pending result creation in `backend/tests/integration/test_lead_processing_transactions.py`
- [X] T013 [P] [US1] Add tenant-isolation and callback-auth RBAC coverage in `backend/tests/rbac/test_lead_processing_isolation.py`
- [X] T014 [P] [US1] Add worker and model-service retry pipeline tests in `workers/tests/test_lead_processing.py` and `model-service/tests/test_inference_pipeline.py`
- [X] T015 [P] [US1] Add empty-message spam classification and duplicate-submission idempotency tests in `backend/tests/unit/test_lead_processing_service.py` and `backend/tests/integration/test_lead_processing_api.py`

### Implementation for User Story 1

- [X] T016 [US1] Extend lead creation and callback persistence flows for pending spam and Hot/Normal records, empty-message spam defaults, and per-lead idempotent processing in `backend/app/leads/service.py` and `backend/app/leads/repository.py`
- [X] T017 [US1] Add lead-processing request and response contracts plus internal callback routes with late-callback review-state protection in `backend/app/leads/schemas.py` and `backend/app/leads/router.py`
- [X] T018 [US1] Register `lead.created` worker handling with bounded retries and fail-open completion in `workers/handlers/leads.py` and `workers/main.py`
- [X] T019 [US1] Implement the model-service HTTP routes and two-stage inference orchestration in `model-service/app/main.py`, `model-service/app/routes.py`, and `model-service/app/service.py`
- [X] T020 [US1] Move the local classifier artifacts into `model-service/artifacts/` and wire runtime loading in `model-service/app/predictors.py` and `model-service/README.md`
- [X] T021 [US1] Surface lead classification status and labels in inquiry and agency lead responses in `backend/app/leads/schemas.py`, `backend/app/leads/router.py`, and `backend/app/leads/service.py`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Lead Review Workbench (Priority: P2)

**Goal**: Let support employees and agency admins review classified leads, isolate spam leads, and persist review actions with visible classification metadata

**Independent Test**: Open the agency lead workbench, filter to spam leads, review a lead, refresh, and confirm the review state and classification badges remain visible

### Tests for User Story 2

- [X] T022 [P] [US2] Add lead review workbench unit tests for spam filters, review persistence, and late-callback classification updates on reviewed leads in `backend/tests/unit/test_lead_review_workbench.py`
- [X] T023 [P] [US2] Add agency lead workbench API integration tests for spam queue, Hot/Normal badges, review actions, and pending-state refresh in `backend/tests/integration/test_agency_lead_workbench_api.py`
- [X] T024 [P] [US2] Add support/admin access and tenant-isolation coverage for spam and review views in `backend/tests/rbac/test_lead_review_workbench_access.py`
- [X] T025 [P] [US2] Add agency lead workbench UI coverage for active, reviewed, spam queues, and auto-repoll while classification is pending in `apps/agency/tests/lead-review-flow.test.tsx` and `apps/agency/tests/support-role-routing.test.tsx`

### Implementation for User Story 2

- [X] T026 [US2] Extend lead list and detail filters plus review payloads to expose spam and Hot/Normal metadata in `backend/app/leads/repository.py`, `backend/app/leads/schemas.py`, and `backend/app/leads/service.py`
- [X] T027 [US2] Add lead workbench routes for spam-only filtering and review actions in `backend/app/leads/router.py` and `backend/app/audit/service.py`
- [X] T028 [US2] Update agency lead data hooks, polling behavior, and error mapping for classified lead queues in `apps/agency/src/features/leads/useAgencyLeads.ts` and `apps/agency/src/lib/api/errors.ts`
- [X] T029 [US2] Replace the placeholder spam queue and wire navigation/routes for the workbench in `apps/agency/src/pages/placeholders/SpamLeadsPage.tsx`, `apps/agency/src/app/router.tsx`, and `apps/agency/src/features/navigation/useAgencyNavigation.ts`
- [X] T030 [US2] Update lead tables and detail review UX to show processing state, spam and Hot/Normal labels, persistent reviewed state, and auto-repoll pending leads in `apps/agency/src/pages/leads/LeadsPage.tsx`, `apps/agency/src/pages/leads/ReviewedLeadsPage.tsx`, `apps/agency/src/features/leads/LeadReviewForm.tsx`, and `apps/agency/src/pages/leads/LeadDetailPage.tsx`

**Checkpoint**: User Story 2 is fully functional and independently testable

---

## Phase 5: User Story 3 - Lead Analytics Trail (Priority: P3)

**Goal**: Record and expose tenant-scoped lead-processing summaries so agencies can track spam volume, Hot/Normal mix, review activity, and fallback behavior over time

**Independent Test**: Create and review leads, then open the agency dashboard and confirm lead-processing metrics and trend summaries match stored processing records

### Tests for User Story 3

- [X] T031 [P] [US3] Add lead analytics unit tests for trend aggregation and review-rate summaries from existing event and result tables in `backend/tests/unit/test_lead_analytics.py`
- [X] T032 [P] [US3] Add lead analytics API integration tests for tenant-scoped trend summaries in `backend/tests/integration/test_lead_analytics_api.py`
- [X] T033 [P] [US3] Add dashboard analytics UI tests for lead-processing metrics and callback-driven refresh in `apps/agency/tests/dashboard-admin-flow.test.tsx`

### Implementation for User Story 3

- [X] T034 [US3] Implement lead-processing summary queries and response schemas on top of existing event and result tables in `backend/app/leads/query_service.py`, `backend/app/leads/repository.py`, and `backend/app/leads/schemas.py`
- [X] T035 [US3] Add tenant-scoped lead analytics endpoints for spam volume, Hot volume, review activity, and fallback counts in `backend/app/leads/router.py` and `backend/app/analytics/router.py`
- [X] T036 [US3] Extend agency dashboard data fetching, query keys, and pending-result repoll behavior for lead-processing trends in `apps/agency/src/features/dashboard/useDashboardSummary.ts` and `apps/agency/src/lib/query/query-client.ts`
- [X] T037 [US3] Surface lead-processing trend cards and reporting summaries in `apps/agency/src/features/dashboard/DashboardCards.tsx` and `apps/agency/src/pages/dashboard/DashboardPage.tsx`

**Checkpoint**: User Story 3 is fully functional and independently testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, docs, and focused regression coverage across the whole pipeline

- [X] T038 [P] Document the lead-processing service topology, local model artifacts, callback contract, and repolling behavior in `backend/app/ai/README.md`, `model-service/README.md`, and `specs/013-lead-processing-pipeline/quickstart.md`
- [X] T039 Harden duplicate-protection, observability, and failure logging for worker callbacks and review actions in `backend/app/leads/service.py`, `workers/handlers/leads.py`, `model-service/app/service.py`, and `backend/app/common/events.py`
- [X] T040 [P] Run focused regression coverage in `backend/tests/unit/test_lead_processing_service.py`, `backend/tests/unit/test_lead_review_workbench.py`, `backend/tests/unit/test_lead_analytics.py`, `backend/tests/integration/test_lead_processing_api.py`, `backend/tests/integration/test_lead_processing_transactions.py`, `backend/tests/integration/test_agency_lead_workbench_api.py`, `backend/tests/integration/test_lead_analytics_api.py`, `backend/tests/rbac/test_lead_processing_isolation.py`, `backend/tests/rbac/test_lead_review_workbench_access.py`, `workers/tests/test_lead_processing.py`, `model-service/tests/test_inference_pipeline.py`, `apps/agency/tests/lead-review-flow.test.tsx`, `apps/agency/tests/support-role-routing.test.tsx`, and `apps/agency/tests/dashboard-admin-flow.test.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Stories (Phases 3-5)**: Depend on Foundational completion
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1**: Starts after Foundational and has no dependency on other stories
- **US2**: Starts after Foundational and depends on US1 only for the presence of stored classification outcomes
- **US3**: Starts after Foundational and depends on US1 result persistence plus US2 review activity to make the reporting useful

### Within Each User Story

- Write tests first and make sure they fail before implementation
- Backend persistence and schemas before routes
- Worker/model-service orchestration before frontend exposure
- Finish each story to an independently testable state before treating it as done

### Parallel Opportunities

- Phase 1 tasks marked `[P]` can run in parallel
- Phase 2 tasks marked `[P]` can run in parallel after the shared event/config constants exist
- In each user story, all test tasks marked `[P]` can run in parallel
- US1 worker and model-service code can proceed in parallel once callback contracts are stable
- US2 frontend route/navigation work can proceed in parallel with backend filter exposure once response schemas are stable
- US3 dashboard frontend work can proceed in parallel with analytics endpoint implementation once response contracts are stable

---

## Parallel Example: User Story 1

```bash
# Launch backend, worker, and model-service tests together
Task: "Add lead-processing service unit tests in backend/tests/unit/test_lead_processing_service.py"
Task: "Add inquiry and callback API integration tests in backend/tests/integration/test_lead_processing_api.py"
Task: "Add worker and model-service retry pipeline tests in workers/tests/test_lead_processing.py and model-service/tests/test_inference_pipeline.py"

# Build the async legs in parallel after contracts are defined
Task: "Register lead.created worker handling in workers/handlers/leads.py and workers/main.py"
Task: "Implement the model-service HTTP routes in model-service/app/main.py, model-service/app/routes.py, and model-service/app/service.py"
```

## Parallel Example: User Story 2

```bash
# Backend access/filter tests can run together
Task: "Add agency lead workbench API integration tests in backend/tests/integration/test_agency_lead_workbench_api.py"
Task: "Add support/admin access coverage in backend/tests/rbac/test_lead_review_workbench_access.py"

# Frontend queue screens can be split across files
Task: "Replace the placeholder spam queue in apps/agency/src/pages/placeholders/SpamLeadsPage.tsx"
Task: "Update lead tables and detail review UX in apps/agency/src/pages/leads/LeadsPage.tsx and apps/agency/src/features/leads/LeadReviewForm.tsx"
```

## Parallel Example: User Story 3

```bash
# Analytics backend and dashboard frontend can move together once schemas exist
Task: "Implement lead-processing summary queries in backend/app/leads/query_service.py and backend/app/leads/repository.py"
Task: "Extend agency dashboard data fetching in apps/agency/src/features/dashboard/useDashboardSummary.ts"
Task: "Surface lead-processing trend cards in apps/agency/src/features/dashboard/DashboardCards.tsx"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate asynchronous lead classification end to end

### Incremental Delivery

1. Ship US1 to make every new lead classified asynchronously
2. Add US2 to give support employees and admins a usable review workbench
3. Add US3 to expose lead-processing summaries and reporting value
4. Finish with Phase 6 hardening and focused regressions

### Suggested MVP Scope

- **Recommended MVP**: Phase 1 + Phase 2 + User Story 1

---

## Notes

- All tasks follow the required checklist format with task IDs, optional `[P]` markers, story labels where required, and exact file paths
- The separate `model-service/` is intentional and matches the architecture decision recorded for this phase
