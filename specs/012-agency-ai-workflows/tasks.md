# Tasks: Agency AI Workflows

**Input**: Design documents from `/specs/012-agency-ai-workflows/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included for backend unit, API integration, RBAC/tenant-isolation, and focused frontend component coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare config, contracts, and shared client surfaces for the phase

- [x] T001 Add OCR and agency AI workflow configuration placeholders in `backend/app/common/config.py` and `.env.example`
- [x] T002 [P] Add phase query-key and API error slots for listing AI, lead reply drafts, and comparison summaries in `apps/agency/src/lib/query/query-client.ts`, `apps/agency/src/lib/api/errors.ts`, and `apps/user/src/lib/api/errors.ts`
- [x] T003 [P] Update the phase validation references in `specs/012-agency-ai-workflows/contracts/agency-ai-workflows-api.md` and `specs/012-agency-ai-workflows/quickstart.md` if setup-related path drift is found during implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared AI/provider primitives that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement Azure Computer Vision Read OCR provider support and worker job dispatch hooks in `backend/app/ai/azure_openai.py`, `backend/app/ai/registry.py`, and `workers/handlers/agency_ai.py`
- [x] T005 [P] Extend shared guardrailed generation helpers for listing drafts, lead reply drafts, and comparison summaries in `backend/app/ai/guardrails.py` and `backend/app/ai/jobs.py`
- [x] T006 [P] Add shared AI workflow request/response schemas and validation helpers, including job status envelopes, in `backend/app/listings/schemas.py`, `backend/app/leads/schemas.py`, `backend/app/rag/schemas.py`, and `backend/app/ai/jobs.py`
- [x] T007 Implement shared assistant read-only tool authorization and orchestration helpers in `backend/app/rag/service.py` and `backend/app/rag/repository.py`
- [x] T008 [P] Add cross-cutting rate-limit, redaction-safe defaults, and audit logging hooks for OCR and generation routes in `backend/app/common/config.py`, `backend/app/rag/redaction.py`, and `backend/app/audit/service.py`

**Checkpoint**: Shared OCR, guardrails, schemas, and tool primitives are ready

---

## Phase 3: User Story 1 - Generate Listing Drafts (Priority: P1) 🎯 MVP

**Goal**: Let agency admins upload a temporary spec sheet, review extracted fields, and generate editable listing copy before saving

**Independent Test**: As an agency admin, upload a spec sheet in the listing form, apply selected extracted fields, generate a draft, edit it, and save/publish only through existing human-controlled actions

### Tests for User Story 1

- [x] T009 [P] [US1] Add OCR extraction and listing draft unit tests, including queued job completion, in `backend/tests/unit/test_agency_listing_ai.py`
- [x] T010 [P] [US1] Add listing AI API integration tests for spec extraction, draft generation, and job polling in `backend/tests/integration/test_agency_listing_ai_api.py`
- [x] T011 [P] [US1] Add admin-only RBAC coverage for listing AI endpoints and job status access in `backend/tests/rbac/test_agency_listing_ai_rbac.py`
- [x] T012 [P] [US1] Add agency listing AI UI tests for pending and completed states in `apps/agency/tests/listing-ai-workflow.test.tsx`

### Implementation for User Story 1

- [x] T013 [US1] Add listing AI request/response schemas for temporary spec extraction, job status, and listing draft generation in `backend/app/ai/schemas.py`
- [x] T014 [US1] Implement temporary spec extraction, queued listing draft jobs, and audit log writes in `backend/app/ai/service.py`
- [x] T015 [US1] Add listing AI endpoints for `/agency/listings/spec-sheet-extractions`, `/agency/listings/draft`, and `/agency/ai/jobs/{job_id}` in `backend/app/ai/router.py`
- [x] T016 [US1] Add agency listing AI client hooks and job polling payload types in `apps/agency/src/features/agencyAi/useAgencyAi.ts`
- [x] T017 [US1] Build the dedicated spec-sheet upload/review area, pending state, and draft-generation controls in `apps/agency/src/features/listings/ListingForm.tsx`
- [x] T018 [US1] Add user-facing listing AI error mapping, queued-state copy, and recovery text in `apps/agency/src/lib/api/errors.ts`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Answer Agency Questions with Tools (Priority: P1)

**Goal**: Let agency admins and support employees use one assistant that combines policy RAG with approved read-only listing and lead tools

**Independent Test**: As a support employee, open the assistant, ask a policy question and an operational question such as “last 5 leads,” and verify tenant-scoped grounded answers while document-management pages stay restricted

### Tests for User Story 2

- [x] T019 [P] [US2] Add assistant tool orchestration unit tests in `backend/tests/unit/test_rag_assistant_tools.py`
- [x] T020 [P] [US2] Add chat API integration tests for policy-plus-tool answers in `backend/tests/integration/test_rag_chat_tools_api.py`
- [x] T021 [P] [US2] Add support-employee access and tenant-isolation tests for the assistant route and tool usage in `backend/tests/rbac/test_rag_assistant_support_access.py`
- [x] T022 [P] [US2] Extend assistant UI tests for operational answers and support-employee access in `apps/agency/tests/rag-policy-qa.test.tsx`

### Implementation for User Story 2

- [x] T023 [US2] Extend assistant message and debug schemas for tool-backed answers in `backend/app/ai/schemas.py`
- [x] T024 [US2] Add read-only listing and lead lookup helpers for assistant use in `backend/app/listings/service.py` and `backend/app/leads/service.py`
- [x] T025 [US2] Implement policy retrieval plus approved tool orchestration in `backend/app/rag/service.py`
- [x] T026 [US2] Update assistant route behavior, thread access, and diagnostics handling in `backend/app/rag/router.py` and `backend/app/rag/repository.py`
- [x] T027 [US2] Open the policy assistant route to support employees while keeping policy documents and retrieval logs admin-only in `apps/agency/src/app/router.tsx`, `apps/agency/src/features/navigation/useAgencyNavigation.ts`, and `apps/agency/src/features/navigation/RouteAccess.ts`
- [x] T028 [US2] Update assistant frontend data hooks and chat rendering for tool-backed answers in `apps/agency/src/features/rag/useRagDocuments.ts` and `apps/agency/src/pages/rag/RagDocumentsPage.tsx`

**Checkpoint**: User Story 2 is fully functional and independently testable

---

## Phase 5: User Story 3 - Draft Replies and Compare Listings (Priority: P2)

**Goal**: Let agency users generate one reviewed lead reply draft, and let signed-in users request an AI summary on the compare page

**Independent Test**: As an agency admin or support employee, generate a lead reply draft and launch the external channel; as a signed-in user, add 2-4 listings to compare and generate a summary from those selected listings

### Tests for User Story 3

- [x] T029 [P] [US3] Add lead reply draft and comparison summary unit tests in `backend/tests/unit/test_lead_reply_and_comparison_summary.py`
- [x] T030 [P] [US3] Add lead reply API integration tests in `backend/tests/integration/test_lead_reply_api.py`
- [x] T031 [P] [US3] Add comparison summary API integration tests in `backend/tests/integration/test_comparison_summary_api.py`
- [x] T032 [P] [US3] Add access-control tests for lead reply drafts and user comparison summaries in `backend/tests/rbac/test_lead_reply_and_comparison_summary_access.py`
- [x] T033 [P] [US3] Add agency lead reply UI tests in `apps/agency/tests/lead-reply-draft.test.tsx`
- [x] T034 [P] [US3] Add user compare summary UI tests in `apps/user/tests/comparison-ai-summary.test.tsx`

### Implementation for User Story 3

- [x] T035 [US3] Add lead reply draft schemas and queued-job endpoint contract in `backend/app/ai/schemas.py` and `backend/app/ai/router.py`
- [x] T036 [P] [US3] Add user comparison summary schemas and queued-job endpoint contract in `backend/app/ai/schemas.py` and `backend/app/ai/router.py`
- [x] T037 [US3] Implement lead reply draft generation, audit log writes, and external-channel payload shaping in `backend/app/ai/service.py`
- [x] T038 [P] [US3] Implement comparison summary generation from server-fetched listing IDs, audit log writes, and job completion handling in `backend/app/ai/service.py`
- [x] T039 [US3] Add agency lead reply draft client flow with queued-job polling in `apps/agency/src/features/agencyAi/useAgencyAi.ts`
- [x] T040 [P] [US3] Add user comparison summary client hook with queued-job polling in `apps/user/src/features/comparison/useComparisonSummary.ts` and `apps/user/src/lib/api/errors.ts`
- [x] T041 [US3] Build comparison summary UI on the protected compare page with pending and completed states in `apps/user/src/pages/comparison/ComparisonPage.tsx`

**Checkpoint**: User Story 3 is fully functional and independently testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, documentation, and focused validation across all stories

- [x] T042 [P] Update AI provider usage and workflow docs in `backend/app/ai/README.md`
- [x] T043 Harden cross-story observability, rate limits, sanitized diagnostics, and audit logging for OCR, assistant tools, drafts, and summaries in `backend/app/common/config.py`, `backend/app/rag/redaction.py`, `backend/app/rag/service.py`, `backend/app/audit/service.py`, `backend/app/audit/repository.py`, and `backend/app/audit/models.py`
- [x] T044 [P] Add latency-validation steps for OCR and generation jobs in `specs/012-agency-ai-workflows/quickstart.md`
- [x] T045 [P] Run focused regression coverage in `backend/tests/unit/test_agency_listing_ai.py`, `backend/tests/integration/test_agency_listing_ai_api.py`, `backend/tests/rbac/test_agency_listing_ai_rbac.py`, `backend/tests/unit/test_rag_assistant_tools.py`, `backend/tests/integration/test_rag_chat_tools_api.py`, `backend/tests/rbac/test_rag_assistant_support_access.py`, `backend/tests/unit/test_lead_reply_and_comparison_summary.py`, `backend/tests/integration/test_lead_reply_api.py`, `backend/tests/integration/test_comparison_summary_api.py`, `backend/tests/rbac/test_lead_reply_and_comparison_summary_access.py`, `apps/agency/tests/listing-ai-workflow.test.tsx`, `apps/agency/tests/rag-policy-qa.test.tsx`, `apps/agency/tests/lead-reply-draft.test.tsx`, and `apps/user/tests/comparison-ai-summary.test.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Stories (Phases 3-5)**: Depend on Foundational completion
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1**: Starts after Foundational and does not depend on other stories
- **US2**: Starts after Foundational and does not depend on US1, though both reuse shared AI primitives
- **US3**: Starts after Foundational and reuses the same guardrailed generation path, but remains independently testable from US1 and US2

### Within Each User Story

- Write tests first and make sure they fail before implementation
- Backend schemas before services
- Services before routes/hooks
- Backend contracts before frontend integration
- Finish each story to an independently testable state before treating it as done

### Parallel Opportunities

- Phase 1 tasks marked `[P]` can run in parallel
- Phase 2 tasks marked `[P]` can run in parallel after T004 starts provider support
- In each user story, all test tasks marked `[P]` can run in parallel
- US1 frontend work can begin once its backend contracts are stable
- US2 assistant route/navigation work can run in parallel with backend tool orchestration once schemas are defined
- US3 lead-reply and comparison-summary backend/frontend tracks can run in parallel after their schemas/routes are defined

---

## Parallel Example: User Story 2

```bash
# Launch all backend tests for US2 together
Task: "Add assistant tool orchestration unit tests in backend/tests/unit/test_rag_assistant_tools.py"
Task: "Add chat API integration tests for policy-plus-tool answers in backend/tests/integration/test_rag_chat_tools_api.py"
Task: "Add support-employee access and tenant-isolation tests in backend/tests/rbac/test_rag_assistant_support_access.py"

# Launch frontend access/rendering work in parallel after schemas are stable
Task: "Open the policy assistant route to support employees in apps/agency/src/app/router.tsx and apps/agency/src/features/navigation/useAgencyNavigation.ts"
Task: "Update assistant frontend data hooks and chat rendering in apps/agency/src/features/rag/useRagDocuments.ts and apps/agency/src/pages/rag/RagDocumentsPage.tsx"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate the full listing spec-extraction and draft flow

### Incremental Delivery

1. Ship US1 for immediate agency listing productivity
2. Add US2 to widen assistant usefulness for admins and support employees
3. Add US3 to cover outbound lead drafting and user comparison summaries
4. Finish with Phase 6 hardening and focused regressions

### Suggested MVP Scope

- **Recommended MVP**: Phase 1 + Phase 2 + User Story 1

---

## Notes

- All tasks follow the required checklist format with task IDs, optional `[P]` markers, story labels where required, and exact file paths
- The compare summary remains in the protected user app even though the rest of the phase is agency-heavy
