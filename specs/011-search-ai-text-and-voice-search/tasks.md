# Tasks: Search, AI Text Search, and Voice Search

**Input**: Design documents from `/specs/011-search-ai-text-and-voice-search/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included: service unit tests, API integration tests, provider tests, privacy/rate-limit coverage, and user-app component tests. No e2e browser automation is included in this phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/app/`, `backend/tests/`, `backend/alembic/versions/`
- Frontend: `apps/user/src/`, `apps/user/tests/`
- Docs: `specs/011-search-ai-text-and-voice-search/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the feature scaffolding, fixtures, and config placeholders needed across all search flows.

- [X] T001 [P] Add search AI/voice config placeholders and Vault seed fields in `backend/app/common/config.py`, `.env.example`, and `vault/seed.py`
- [X] T002 [P] Create backend and user-app test stubs in `backend/tests/unit/test_search_intent.py`, `backend/tests/unit/test_ai_search_extraction.py`, `backend/tests/unit/test_voice_search.py`, `backend/tests/integration/test_search_api.py`, `apps/user/tests/ai-search-flow.test.tsx`, and `apps/user/tests/voice-search-flow.test.tsx`
- [X] T003 [P] Add representative text and voice search fixtures in `backend/tests/fixtures/search/search_intent_examples.jsonl` and `backend/tests/fixtures/search/voice_search_examples.jsonl`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared search contracts, persistence, provider hooks, and rate-limit plumbing that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Extend listing and search persistence fields for parking, floor, and search event metadata in `backend/app/listings/models.py` and `backend/app/search/models.py`
- [X] T005 Create the Alembic migration for listing parking/floor support and search intent, transcript, provider, and fallback log fields in `backend/alembic/versions/0016_expand_search_logs_for_ai_and_voice.py`
- [X] T006 [P] Add canonical `SearchIntent`, confirmed-filter, unclear-location, and voice transcript schemas in `backend/app/search/schemas.py`
- [X] T007 [P] Implement structured search-log create/list helpers for manual, AI, voice, and confirmation events in `backend/app/search/repository.py`
- [X] T008 [P] Implement Azure Whisper STT support in `backend/app/ai/azure_openai.py`
- [X] T009 [P] Extend AI provider registry helpers and registry coverage for `STTProvider` lookup in `backend/app/ai/registry.py` and `backend/tests/unit/test_provider_registry.py`
- [X] T010 Implement shared search orchestration, redacted logging, and provider fallback scaffolding in `backend/app/search/service.py`
- [X] T011 [P] Add separate manual, AI-text, and voice rate-limit settings/helpers in `backend/app/common/config.py` and `backend/app/common/rate_limit.py`
- [X] T012 [P] Add shared user-app search types and query keys for confirmed filters, including parking/floor, and search intents in `apps/user/src/lib/query/query-client.ts` and `apps/user/src/features/search/useSearchFilters.ts`

**Checkpoint**: Foundation ready. Manual, AI text, vague-location confirmation, and voice flows can now be implemented independently.

---

## Phase 3: User Story 1 - Search Listings With Reliable Filters (Priority: P1) 🎯 MVP

**Goal**: Users can apply reliable manual filters, sort, and paginate without losing search state, and results stay limited to active public listings.

**Independent Test**: Apply manual filters on the listings page, change sort and pagination, and verify the results and URL state stay consistent across reloads.

### Tests for User Story 1

- [X] T013 [P] [US1] Expand query-service unit coverage for canonical filter mapping, including parking/floor, and stable sort ordering in `backend/tests/unit/test_listing_search_service.py`
- [X] T014 [P] [US1] Add public listing API integration coverage for parking/floor filters, filter preservation, active-only results, and pagination behavior in `backend/tests/integration/test_public_listing_api.py` and `backend/tests/integration/test_public_listing_cursor_pagination.py`
- [X] T015 [P] [US1] Extend manual search UI coverage for URL state, sort changes, and pagination continuity in `apps/user/tests/manual-search-flow.test.tsx`

### Implementation for User Story 1

- [X] T016 [US1] Normalize confirmed public search filter parsing and validation, including parking/floor, in `backend/app/listings/schemas.py` and `backend/app/listings/query_service.py`
- [X] T017 [US1] Add bounded manual search logging and result-count recording in `backend/app/listings/router.py` and `backend/app/search/service.py`
- [X] T018 [P] [US1] Tighten public search cache-key and parameter handling in `backend/app/listings/router.py`
- [X] T019 [P] [US1] Refactor user-app filter state and API parameter mapping, including parking/floor, in `apps/user/src/features/search/useSearchFilters.ts` and `apps/user/src/pages/listings/ListingsPage.tsx`
- [X] T020 [US1] Update the manual search form and sort controls to match the canonical filter contract, including parking/floor inputs, in `apps/user/src/features/search/SearchForm.tsx` and `apps/user/src/features/listings/ListingsToolbar.tsx`

**Checkpoint**: User Story 1 is fully functional and testable on its own.

---

## Phase 4: User Story 2 - Convert Natural Language Into Confirmed Search Filters (Priority: P2)

**Goal**: Users can enter a natural-language request, review the interpreted filters, edit them, and run the same listing search flow using only confirmed filters.

**Independent Test**: Submit a natural-language search, edit one interpreted value in the confirmation panel, confirm, and verify the final search uses the edited values.

### Tests for User Story 2

- [X] T021 [P] [US2] Add service unit tests for AI filter extraction parsing, including parking/floor extraction, fallback behavior, and sanitized logging in `backend/tests/unit/test_ai_search_extraction.py`
- [X] T022 [P] [US2] Add API integration tests for `POST /search/intent` and `POST /search/logs/confirmation` in `backend/tests/integration/test_search_api.py`
- [X] T023 [P] [US2] Add user-app confirmation flow coverage for AI text search in `apps/user/tests/ai-search-flow.test.tsx`

### Implementation for User Story 2

- [X] T024 [US2] Add AI text intent request/response and confirmation-log schemas with parking/floor support in `backend/app/search/schemas.py`
- [X] T025 [US2] Implement chat-provider-driven filter extraction, validation, including parking/floor normalization, and fallback behavior in `backend/app/search/service.py`
- [X] T026 [US2] Expose `POST /search/intent` and `POST /search/logs/confirmation` in `backend/app/search/router.py` and `backend/app/main.py`
- [X] T027 [P] [US2] Add user-app API/query hooks for AI text intent extraction and confirmation logging in `apps/user/src/lib/query/query-client.ts` and `apps/user/src/features/search/useSearchIntent.ts`
- [X] T028 [US2] Build the AI text search entry and confirmation panel in `apps/user/src/features/search/SearchForm.tsx` and `apps/user/src/pages/listings/ListingsPage.tsx`
- [X] T029 [US2] Route confirmed AI filters, including parking/floor, back through the existing listing result flow in `apps/user/src/pages/listings/ListingsPage.tsx` and `apps/user/src/features/listings/useListingsSearch.ts`

**Checkpoint**: User Stories 1 and 2 both work independently with the same confirmed-filter contract.

---

## Phase 5: User Story 3 - Keep Unclear Locations Reviewable (Priority: P3)

**Goal**: Vague area/location phrases stay explicit and reviewable instead of silently turning into hidden city filters.

**Independent Test**: Submit a vague location request, resolve it manually in the confirmation panel, and verify only the resolved locations affect the final search.

### Tests for User Story 3

- [X] T030 [P] [US3] Add unit tests for unresolved vague-location handling, continue-without-location behavior, and no-auto-expansion rules in `backend/tests/unit/test_search_intent.py`
- [X] T031 [P] [US3] Add API integration tests for unclear-location intent responses, continue-without-location confirmation, and confirmation edits in `backend/tests/integration/test_search_api.py`
- [X] T032 [P] [US3] Extend AI search UI coverage for vague-location resolution in `apps/user/tests/ai-search-flow.test.tsx`

### Implementation for User Story 3

- [X] T033 [US3] Represent unresolved location intent, continue-without-location outcomes, and unsupported criteria in `backend/app/search/schemas.py` and `backend/app/search/service.py`
- [X] T034 [US3] Prevent vague phrases from being converted into concrete city filters in `backend/app/search/service.py` and `backend/app/listings/query_service.py`
- [X] T035 [US3] Add manual location-resolution controls and explicit continue-without-location behavior in `apps/user/src/features/search/SearchForm.tsx` and `apps/user/src/pages/listings/ListingsPage.tsx`

**Checkpoint**: User Stories 1 through 3 are independently functional without area expansion.

---

## Phase 6: User Story 4 - Search by Voice (Priority: P4)

**Goal**: Users can record a voice search, review the Azure Whisper transcript and extracted filters, edit them, and run the same confirmed search flow.

**Independent Test**: Record a voice query, review the transcript, correct any issue, confirm, and verify the final listing search uses the corrected confirmed filters.

### Tests for User Story 4

- [X] T036 [P] [US4] Add provider/service unit coverage for Azure Whisper transcription success, parking/floor extraction from transcript, failure, and fallback in `backend/tests/unit/test_voice_search.py` and `backend/tests/unit/test_provider_registry.py`
- [X] T037 [P] [US4] Add API integration tests for `POST /search/voice`, payload validation, and voice rate limiting in `backend/tests/integration/test_search_api.py`
- [X] T038 [P] [US4] Add user-app tests for microphone, transcript editing, and recovery states in `apps/user/tests/voice-search-flow.test.tsx`

### Implementation for User Story 4

- [X] T039 [US4] Add voice transcription request/response schemas, parking/floor extraction fields, and audio validation rules in `backend/app/search/schemas.py` and `backend/app/search/service.py`
- [X] T040 [US4] Implement Azure Whisper transcription orchestration plus voice-specific logging and fallback handling in `backend/app/ai/azure_openai.py`, `backend/app/search/service.py`, and `backend/app/common/rate_limit.py`
- [X] T041 [US4] Expose `POST /search/voice` in `backend/app/search/router.py`
- [X] T042 [P] [US4] Add user-app voice capture and transcript submission hooks in `apps/user/src/features/search/useVoiceSearch.ts` and `apps/user/src/lib/api/client.ts`
- [X] T043 [US4] Build microphone controls, transcript review, and discard/edit UX in `apps/user/src/features/search/SearchForm.tsx` and `apps/user/src/pages/listings/ListingsPage.tsx`

**Checkpoint**: All four user stories are independently functional and use the same confirmed-filter contract.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final privacy hardening, docs, and validation across all search flows.

- [X] T044 [P] Update feature docs and contract details in `specs/011-search-ai-text-and-voice-search/contracts/search-api.md` and `specs/011-search-ai-text-and-voice-search/quickstart.md`
- [X] T045 [P] Harden privacy-safe search logging, fallback messaging, and unsupported-criteria handling in `backend/app/search/service.py` and `apps/user/src/pages/listings/ListingsPage.tsx`
- [X] T046 [P] Add or update provider-interface documentation for chat and STT usage in `backend/app/ai/README.md`
- [X] T047 Run focused backend tests, user-app search tests, and the quickstart validation scenarios referenced in `specs/011-search-ai-text-and-voice-search/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses the confirmed-filter contract from US1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and extends the AI text confirmation flow from US2.
- **User Story 4 (Phase 6)**: Depends on Foundational completion and reuses the AI text extraction/confirmation flow from US2.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: MVP and base result-query flow.
- **US2**: Builds on the shared contract and manual search result flow from US1.
- **US3**: Builds on US2 confirmation behavior without introducing area expansion.
- **US4**: Builds on US2 extraction/confirmation behavior and adds STT input.

### Within Each User Story

- Write the listed tests first and confirm they fail before implementation.
- Backend schema/service changes before route wiring.
- Route wiring before frontend integration.
- Story-level validation before moving to the next priority.

### Parallel Opportunities

- `T001-T003` can run in parallel.
- `T006-T009` and `T011-T012` can run in parallel after the migration shape is clear.
- All tests marked `[P]` within a story can run in parallel.
- Frontend hook/state work and backend service/schema work marked `[P]` can run in parallel inside the same story.

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 tests together:
Task: "Add service unit tests in backend/tests/unit/test_ai_search_extraction.py"
Task: "Add API integration tests in backend/tests/integration/test_search_api.py"
Task: "Add user-app confirmation flow tests in apps/user/tests/ai-search-flow.test.tsx"

# Launch User Story 2 implementation setup in parallel after tests:
Task: "Add AI text intent schemas in backend/app/search/schemas.py"
Task: "Add user-app API/query hooks in apps/user/src/features/search/useSearchIntent.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate the manual listing search flow end to end

### Incremental Delivery

1. Finish setup and shared search foundations
2. Deliver reliable manual listing search
3. Add AI text interpretation with confirmation
4. Add vague-location review behavior
5. Add voice search on top of the same confirmed-filter contract
6. Finish polish and validation

### Parallel Team Strategy

1. One developer handles migration, schemas, provider registry, and rate limits
2. One developer handles manual search/result-flow cleanup in the user app
3. One developer handles AI text and voice search UX after the shared contract is stable

---

## Notes

- All tasks follow the required checklist format with IDs and file paths.
- No e2e browser automation is included in this phase.
- Suggested MVP scope: Phase 1, Phase 2, and User Story 1 only.
