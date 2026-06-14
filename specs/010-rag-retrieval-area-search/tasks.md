# Tasks: RAG Retrieval and Reranking

**Input**: Design documents from `/specs/010-rag-retrieval-area-search/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included: service unit tests, API integration tests, RBAC tenant-isolation tests, provider fallback tests, agency UI tests, and retrieval evaluation smoke checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/app/`, `backend/tests/`
- Frontend: `apps/agency/src/`
- Workers/Scripts: `workers/`, `scripts/ci/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add provider/config dependencies and create the feature scaffolding.

- [X] T001 [P] Add OpenRouter SDK and retrieval/eval dependencies to `backend/requirements.txt`
- [X] T002 [P] Add Phase 9 secret/config placeholders and Vault loading paths in `backend/app/common/config.py`, `.env.example`, and `vault/seed.py`
- [X] T003 [P] Create feature test stubs in `backend/tests/unit/test_rag_retrieval.py`, `backend/tests/unit/test_openrouter_reranker.py`, `backend/tests/integration/test_rag_retrieval_api.py`, `backend/tests/rbac/test_rag_retrieval_tenant_isolation.py`, and `apps/agency/tests/rag-policy-qa.test.tsx`
- [X] T004 [P] Create the baseline retrieval evaluation dataset in `backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core retrieval infrastructure that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Create retrieval log and evaluation persistence model changes in `backend/app/rag/models.py`
- [X] T006 Create Alembic migration for retrieval logs and evaluation storage in `backend/alembic/versions/`
- [X] T007 [P] Add retrieval/evaluation schemas in `backend/app/rag/schemas.py`
- [X] T008 [P] Implement retrieval repository primitives for active chunks, parent pages, processed documents, and paginated retrieval logs in `backend/app/rag/repository.py`
- [X] T009 [P] Add OpenRouter SDK reranking provider implementation in `backend/app/ai/openrouter.py`
- [X] T010 [P] Register reranking provider selection in `backend/app/ai/registry.py`
- [X] T011 Create shared retrieval orchestration in `backend/app/rag/retrieval.py`
- [X] T012 [P] Add retrieval log write helpers and evaluation run helpers in `backend/app/rag/service.py`
- [X] T013 [P] Add query keys and client types for policy retrieval/logs in `apps/agency/src/lib/query/query-client.ts` and `apps/agency/src/features/rag/useRagDocuments.ts`

**Checkpoint**: Foundation ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Retrieve Agency Policy Answers (Priority: P1) 🎯 MVP

**Goal**: Agency admins and support employees can ask grounded policy questions and see answer, citations, evidence, and debug metadata.

**Independent Test**: Sign in as an agency employee with processed policy PDFs, ask a covered question, and verify the answer uses only that agency's documents with citations and evidence.

### Tests for User Story 1

- [ ] T014 [P] [US1] Write service unit tests for retrieval ranking, parent-page fetch, and insufficient-evidence fallback in `backend/tests/unit/test_rag_retrieval.py`
- [ ] T015 [P] [US1] Write provider unit tests for OpenRouter reranking success and fallback behavior in `backend/tests/unit/test_openrouter_reranker.py`
- [ ] T016 [P] [US1] Write API integration tests for `POST /api/v1/agencies/rag/query` answered and insufficient-evidence flows in `backend/tests/integration/test_rag_retrieval_api.py`
- [ ] T017 [P] [US1] Write agency UI tests for question submit, answer rendering, citations, and evidence/debug panel in `apps/agency/tests/rag-policy-qa.test.tsx`
- [ ] T018 [P] [US1] Write replace-while-retrieving consistency coverage in `backend/tests/integration/test_rag_retrieval_api.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement policy retrieval service flow with vector search, parent page fetch, answer assembly, and debug payload in `backend/app/rag/service.py`
- [X] T020 [US1] Implement `POST /api/v1/agencies/rag/query` endpoint in `backend/app/rag/router.py`
- [X] T021 [US1] Add retrieval log creation for each query in `backend/app/rag/service.py`
- [X] T022 [US1] Harden retrieval against document replacement during in-flight reads in `backend/app/rag/service.py` and `backend/app/rag/repository.py`
- [X] T023 [P] [US1] Add agency policy Q&A hooks and request types in `apps/agency/src/features/rag/useRagDocuments.ts`
- [X] T024 [US1] Build the agency policy Q&A UI in `apps/agency/src/pages/rag/RagDocumentsPage.tsx`
- [X] T025 [US1] Add loading, empty, and fallback states for policy Q&A in `apps/agency/src/pages/rag/RagDocumentsPage.tsx`

**Checkpoint**: User Story 1 is fully functional and testable on its own.

---

## Phase 4: User Story 2 - Support Assistant Retrieval (Priority: P2)

**Goal**: Support employees can use the same policy retrieval flow within role boundaries, and agency admins can inspect retrieval logs.

**Independent Test**: Sign in as a support employee and verify allowed policy retrieval works while admin-only or cross-tenant behavior is blocked; sign in as admin and verify retrieval logs are visible.

### Tests for User Story 2

- [ ] T026 [P] [US2] Write RBAC tenant-isolation tests for support employee retrieval and cross-tenant denial in `backend/tests/rbac/test_rag_retrieval_tenant_isolation.py`
- [ ] T027 [P] [US2] Write API integration tests for `GET /api/v1/agencies/rag/retrieval-logs` authorization and pagination in `backend/tests/integration/test_rag_retrieval_api.py`
- [ ] T028 [P] [US2] Extend agency UI tests for support-role restrictions and admin log visibility in `apps/agency/tests/rag-policy-qa.test.tsx`

### Implementation for User Story 2

- [X] T029 [US2] Enforce agency-admin and support-employee retrieval permissions plus scope checks in `backend/app/rag/service.py`
- [X] T030 [US2] Implement paginated retrieval-log listing with filter support in `backend/app/rag/router.py`, `backend/app/rag/service.py` and `backend/app/rag/repository.py`
- [X] T031 [US2] Add retrieval-log filter schemas in `backend/app/rag/schemas.py`
- [X] T032 [P] [US2] Add admin-only retrieval-log hooks in `apps/agency/src/features/rag/useRagDocuments.ts`
- [X] T033 [US2] Add retrieval-log UI to `apps/agency/src/pages/rag/RagDocumentsPage.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently with correct RBAC boundaries.

---

## Phase 5: User Story 3 - Evaluate Retrieval Quality (Priority: P3)

**Goal**: The project has a repeatable retrieval evaluation baseline and can compare runs after changes.

**Independent Test**: Run the evaluation command twice against the same document fixtures and verify comparable metrics, failed examples, and source evidence are recorded.

### Tests for User Story 3

- [ ] T034 [P] [US3] Write unit tests for evaluation result aggregation and failed-example reporting in `backend/tests/unit/test_rag_retrieval.py`
- [ ] T035 [P] [US3] Write integration tests for evaluation run persistence and summary output in `backend/tests/integration/test_rag_retrieval_api.py`
- [ ] T036 [P] [US3] Add smoke coverage for the evaluation command in `scripts/ci/run_rag_eval.py`
- [ ] T037 [P] [US3] Add latency-threshold validation coverage for the evaluation command in `scripts/ci/run_rag_eval.py`

### Implementation for User Story 3

- [X] T038 [US3] Add evaluation dataset loader and run orchestration in `scripts/ci/run_rag_eval.py`
- [X] T039 [US3] Implement evaluation result persistence and summary generation in `backend/app/rag/service.py`
- [X] T040 [US3] Add evaluation-run schemas and repository helpers in `backend/app/rag/schemas.py` and `backend/app/rag/repository.py`
- [X] T041 [US3] Record and enforce retrieval latency summary metrics in `scripts/ci/run_rag_eval.py`
- [X] T042 [US3] Document baseline evaluation fixtures and expected outcomes in `specs/010-rag-retrieval-area-search/quickstart.md`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, hardening, and end-to-end validation.

- [ ] T043 [P] Add production-safe error handling and no-secret debug sanitization in `backend/app/rag/service.py` and `backend/app/ai/openrouter.py`
- [ ] T044 [P] Optimize retrieval query limits, ordering, and log pagination in `backend/app/rag/repository.py`
- [ ] T045 [P] Update feature docs and API contract details in `specs/010-rag-retrieval-area-search/contracts/rag-retrieval.md` and `specs/010-rag-retrieval-area-search/quickstart.md`
- [ ] T046 Run backend retrieval tests, agency tests, evaluation command checks, and quickstart validation scenarios referenced in `specs/010-rag-retrieval-area-search/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and builds on the retrieval flow from US1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and reuses retrieval behavior from US1.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: First deliverable and MVP.
- **US2**: Reuses the retrieval flow and adds role/logging boundaries.
- **US3**: Reuses retrieval flow and adds evaluation baseline/reporting.

### Within Each User Story

- Write tests first and confirm they fail before implementation.
- Backend retrieval/repository/schema changes before route wiring.
- Route wiring before frontend integration.
- Story-level validation before moving to the next priority.

### Parallel Opportunities

- `T001-T004` can run in parallel.
- `T007-T010` can run in parallel after the migration shape is clear.
- All tests marked `[P]` within a story can run in parallel.
- Frontend hook work and backend schema work marked `[P]` can run in parallel inside the same story.

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 tests together:
Task: "Write service unit tests in backend/tests/unit/test_rag_retrieval.py"
Task: "Write provider unit tests in backend/tests/unit/test_openrouter_reranker.py"
Task: "Write API integration tests in backend/tests/integration/test_rag_retrieval_api.py"
Task: "Write agency UI tests in apps/agency/tests/rag-policy-qa.test.tsx"
Task: "Write replace-while-retrieving consistency coverage in backend/tests/integration/test_rag_retrieval_api.py"

# Launch parallel implementation setup after tests:
Task: "Add policy Q&A hooks in apps/agency/src/features/rag/useRagDocuments.ts"
Task: "Implement POST /api/v1/agencies/rag/query schemas in backend/app/rag/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate the agency policy Q&A flow end to end

### Incremental Delivery

1. Finish setup and shared retrieval foundations
2. Deliver agency policy Q&A with grounded answers and citations
3. Add support-role retrieval boundaries and retrieval-log visibility
4. Add repeatable evaluation runs and baseline reporting
5. Finish polish and validation

### Parallel Team Strategy

1. One developer handles provider/config/repository foundations
2. One developer handles agency Q&A UI and hooks after contracts are stable
3. One developer handles evaluation dataset and run reporting after retrieval response shape is stable

---

## Notes

- All tasks follow the required checklist format with IDs and file paths.
- Area knowledge management and area search RAG are intentionally excluded from this phase.
