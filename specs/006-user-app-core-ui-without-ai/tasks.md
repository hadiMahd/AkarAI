# Tasks: User App Core UI Without AI

**Input**: Design documents from `specs/006-user-app-core-ui-without-ai/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`, `quickstart.md`

**Tests**: Constitution-required frontend route/component tests and backend integration/regression tests are included for the support endpoints and critical user flows in this phase.

**React UI Library**: `shadcn/ui` is the confirmed component approach for Phase 5 implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same phase because it touches different files or depends only on completed earlier phases.
- **[Story]**: User story label for story phases only.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Structure)

**Purpose**: Prepare the user-app file structure and test scaffolding for Phase 5.

- [X] T001 Create Phase 5 user-app folder scaffolds in `apps/user/src/app/`, `apps/user/src/pages/`, `apps/user/src/features/`, `apps/user/src/components/`, `apps/user/src/lib/`, `apps/user/src/styles/`, and `apps/user/tests/`
- [X] T002 Update `apps/user/package.json`, `apps/user/tsconfig.json`, and `apps/user/vite.config.ts` with the Phase 5 dependency, test-tooling baseline, and `shadcn/ui`
- [X] T003 [P] Create frontend test bootstrap files in `apps/user/tests/setup.ts` and `apps/user/tests/render-app.tsx`
- [X] T004 [P] Create shared app style entry files in `apps/user/src/styles/global.css` and `apps/user/src/styles/theme.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build auth/session, routing, shared data access, and minimal backend support that every user story depends on.

**CRITICAL**: No user story work begins until this phase is complete.

### Tests for Foundational Phase

- [X] T005 [P] Create protected-route and auth-session frontend tests in `apps/user/tests/auth-routing.test.tsx`
- [X] T006 [P] Create backend registration API integration tests in `backend/tests/integration/test_user_registration_api.py`
- [X] T007 [P] Create frontend shared API-client and query-provider tests in `apps/user/tests/app-providers.test.tsx`

### Implementation for Foundational Phase

- [X] T008 Implement app providers, route guards, and router shell in `apps/user/src/app/providers.tsx`, `apps/user/src/app/guards.tsx`, `apps/user/src/app/router.tsx`, `apps/user/src/main.tsx`, and `apps/user/src/App.tsx`
- [X] T009 Implement shared API client, auth transport, query client, and token persistence helpers in `apps/user/src/lib/api/client.ts`, `apps/user/src/lib/api/auth.ts`, `apps/user/src/lib/query/query-client.ts`, and `apps/user/src/lib/session/auth-session.ts`
- [X] T010 Implement reusable loading, empty, error, and protected-layout primitives in `apps/user/src/components/LoadingSkeleton.tsx`, `apps/user/src/components/EmptyState.tsx`, `apps/user/src/components/ErrorState.tsx`, and `apps/user/src/components/ProtectedLayout.tsx`
- [X] T011 Implement user registration request/response support in `backend/app/auth/schemas.py`, `backend/app/auth/service.py`, `backend/app/auth/router.py`, and `backend/app/users/repository.py`
- [X] T012 Update backend shared fixtures for Phase 5 user-registration validation in `backend/tests/conftest.py`
- [X] T013 Run foundational validation commands for auth/session bootstrap from `specs/006-user-app-core-ui-without-ai/quickstart.md`

**Checkpoint**: Auth entry, protected routing, shared fetch/query infrastructure, and registration support are ready.

---

## Phase 3: User Story 1 - Browse Listings Manually (Priority: P1) 🎯 MVP

**Goal**: Users can enter through the landing/auth flow, manually search listings, browse paginated results, save listings, and compare up to four listings for the current session.

**Independent Test**: Open the landing page, sign up or sign in, run a manual search, browse listings, save a listing, add up to four listings to comparison, refresh the page, and verify the comparison state remains only for the current session.

### Tests for User Story 1

- [X] T014 [P] [US1] Create landing and auth entry flow tests in `apps/user/tests/landing-auth-flow.test.tsx`
- [X] T015 [P] [US1] Create homepage search and listings results tests covering empty results and search rate-limit feedback in `apps/user/tests/manual-search-flow.test.tsx`
- [X] T016 [P] [US1] Create saved-listing and session-only comparison tests in `apps/user/tests/saved-and-comparison.test.tsx`

### Implementation for User Story 1

- [X] T017 [US1] Implement landing, sign-in, and sign-up pages in `apps/user/src/pages/landing/LandingPage.tsx`, `apps/user/src/pages/auth/SignInPage.tsx`, and `apps/user/src/pages/auth/SignUpPage.tsx`
- [X] T018 [US1] Implement auth hooks, forms, redirect handling, and logout behavior in `apps/user/src/features/auth/useAuth.ts`, `apps/user/src/features/auth/SignInForm.tsx`, `apps/user/src/features/auth/SignUpForm.tsx`, and `apps/user/src/features/auth/AuthActions.tsx`
- [X] T019 [US1] Implement homepage manual search state and form controls in `apps/user/src/pages/home/HomePage.tsx`, `apps/user/src/features/search/SearchForm.tsx`, and `apps/user/src/features/search/useSearchFilters.ts`
- [X] T020 [US1] Implement listings page, query-string synchronization, pagination/sort controls, empty states, and search rate-limit feedback in `apps/user/src/pages/listings/ListingsPage.tsx`, `apps/user/src/features/listings/useListingsSearch.ts`, and `apps/user/src/features/listings/ListingsToolbar.tsx`
- [X] T021 [US1] Implement listing-card presentation and saved-state UI in `apps/user/src/features/listings/ListingCard.tsx` and `apps/user/src/features/saved-listings/useSavedListings.ts`
- [X] T022 [US1] Implement session-only comparison state and page flow in `apps/user/src/features/comparison/sessionComparison.ts`, `apps/user/src/features/comparison/ComparisonTray.tsx`, and `apps/user/src/pages/comparison/ComparisonPage.tsx`
- [X] T023 [US1] Wire protected navigation for landing, home, listings, and comparison routes in `apps/user/src/app/router.tsx` and `apps/user/src/components/ProtectedLayout.tsx`

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Review a Listing and Submit Interest (Priority: P2)

**Goal**: Users can open a listing detail page, review available viewing slots, submit an inquiry, and book a viewing manually from a valid slot.

**Independent Test**: Sign in, open a listing detail page, review public-safe listing details, submit an inquiry, book a viewing from an available slot, and confirm over-limit or invalid-slot failures are surfaced clearly.

### Tests for User Story 2

- [X] T024 [P] [US2] Create backend available-viewing-slots API integration tests in `backend/tests/integration/test_user_listing_viewing_slots_api.py`
- [X] T025 [P] [US2] Create listing-detail and inquiry frontend tests covering unavailable listings and inquiry failure feedback in `apps/user/tests/listing-detail-inquiry.test.tsx`
- [X] T026 [P] [US2] Create manual viewing-booking frontend tests in `apps/user/tests/viewing-booking-flow.test.tsx`

### Implementation for User Story 2

- [X] T027 [US2] Implement user-visible available-slot read support in `backend/app/viewings/schemas.py`, `backend/app/viewings/repository.py`, `backend/app/viewings/service.py`, and `backend/app/viewings/router.py`
- [X] T028 [US2] Implement listing-detail data hooks and page rendering with unavailable-state handling in `apps/user/src/features/listings/useListingDetail.ts` and `apps/user/src/pages/listing-detail/ListingDetailPage.tsx`
- [X] T029 [US2] Implement inquiry form and submission flow in `apps/user/src/features/inquiries/InquiryForm.tsx` and `apps/user/src/features/inquiries/useSubmitInquiry.ts`
- [X] T030 [US2] Implement viewing-slot picker, booking form, and booking mutation flow in `apps/user/src/features/viewings/ViewingSlotPicker.tsx`, `apps/user/src/features/viewings/BookingForm.tsx`, and `apps/user/src/features/viewings/useBookViewing.ts`
- [X] T031 [US2] Integrate listing-detail save state, inquiry feedback, booking feedback, and protected route navigation in `apps/user/src/pages/listing-detail/ListingDetailPage.tsx`, `apps/user/src/features/saved-listings/useSavedListings.ts`, and `apps/user/src/app/router.tsx`

**Checkpoint**: User Story 2 is functional and independently testable.

---

## Phase 5: User Story 3 - Track Personal Activity (Priority: P3)

**Goal**: Users can open a profile area limited to saved listings, submitted inquiries, and scheduled viewings.

**Independent Test**: Sign in as a user with saved listings, submitted inquiries, and scheduled viewings, then verify each profile tab shows only that user's own records and no editable account-settings form appears.

### Tests for User Story 3

- [X] T032 [P] [US3] Create backend user inquiry-history API integration tests in `backend/tests/integration/test_my_inquiries_api.py`
- [X] T033 [P] [US3] Create profile activity-tab frontend tests in `apps/user/tests/profile-activity-tabs.test.tsx`
- [X] T034 [P] [US3] Create profile ownership and protected-route frontend tests in `apps/user/tests/profile-auth-ownership.test.tsx`

### Implementation for User Story 3

- [X] T035 [US3] Implement user-owned inquiry-history support in `backend/app/leads/schemas.py`, `backend/app/leads/repository.py`, `backend/app/leads/service.py`, and `backend/app/leads/router.py`
- [X] T036 [US3] Implement the profile page shell and tab navigation in `apps/user/src/pages/profile/ProfilePage.tsx` and `apps/user/src/features/profile/ProfileTabs.tsx`
- [X] T037 [US3] Implement the saved-listings tab data and UI in `apps/user/src/features/profile/SavedListingsTab.tsx`
- [X] T038 [US3] Implement the submitted-inquiries tab data and UI in `apps/user/src/features/profile/SubmittedInquiriesTab.tsx`
- [X] T039 [US3] Implement the scheduled-viewings tab data and UI in `apps/user/src/features/profile/ScheduledViewingsTab.tsx`
- [X] T040 [US3] Wire profile navigation and activity queries into `apps/user/src/app/router.tsx`, `apps/user/src/components/ProtectedLayout.tsx`, and `apps/user/src/lib/api/client.ts`

**Checkpoint**: User Story 3 is functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, validation, and phase-scope guardrails across all stories.

- [X] T041 [P] Update Phase 5 validation guidance and local responsiveness checks in `specs/006-user-app-core-ui-without-ai/quickstart.md`
- [X] T042 [P] Sync the Phase 5 API contract with implemented endpoint payloads in `specs/006-user-app-core-ui-without-ai/contracts/openapi.yaml`
- [X] T043 [P] Update Phase 5 architecture notes in `docs/DECISIONS.md` and `backend/app/README.md`
- [X] T044 Run backend regression tests and user-app build from `specs/006-user-app-core-ui-without-ai/quickstart.md`
- [X] T045 Run the landing/auth, browse, inquiry, booking, profile, and local responsiveness validation scenarios from `specs/006-user-app-core-ui-without-ai/quickstart.md` (manual-not-executed)
- [X] T046 Run the Phase 5 scope guard scan from `specs/006-user-app-core-ui-without-ai/quickstart.md` to confirm no AI, voice, chatbot, match-score, or account-settings implementation drift
- [X] T047 Confirm no `dao.py` files, no `.env` staging, and no `.codex/` or `graphify-out/` staging in repository status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Foundational. This is the MVP slice.
- **Phase 4 US2**: Depends on Foundational and uses the auth/session/browse infrastructure from US1 for the full happy path.
- **Phase 5 US3**: Depends on Foundational and uses saved/inquiry/viewing records created by earlier stories or fixtures.
- **Phase 6 Polish**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational. No dependency on US2 or US3.
- **US2 (P2)**: Starts after Foundational; full validation benefits from US1 auth and navigation flow.
- **US3 (P3)**: Starts after Foundational; full validation benefits from saved, inquiry, and viewing records created by US1 and US2.

### Within Each User Story

- Write the listed tests first and confirm they fail before implementation.
- Shared hooks/data helpers before page composition.
- Backend support endpoints before frontend flows that consume them.
- Protected-route wiring before story checkpoint validation.
- Story validation must pass before moving to the next priority if working sequentially.

## Parallel Opportunities

- Setup tasks T003-T004 can run in parallel after T001-T002.
- Foundational tests T005-T007 can run in parallel.
- US1 tests T014-T016 can run in parallel.
- US2 tests T024-T026 can run in parallel.
- US3 tests T032-T034 can run in parallel.
- Polish documentation tasks T041-T043 can run in parallel.

## Parallel Example: User Story 1

```text
Task: "T014 [P] [US1] Create landing and auth entry flow tests in apps/user/tests/landing-auth-flow.test.tsx"
Task: "T015 [P] [US1] Create homepage search and listings results tests in apps/user/tests/manual-search-flow.test.tsx"
Task: "T016 [P] [US1] Create saved-listing and session-only comparison tests in apps/user/tests/saved-and-comparison.test.tsx"
```

## Parallel Example: User Story 2

```text
Task: "T024 [P] [US2] Create backend available-viewing-slots API integration tests in backend/tests/integration/test_user_listing_viewing_slots_api.py"
Task: "T025 [P] [US2] Create listing-detail and inquiry frontend tests in apps/user/tests/listing-detail-inquiry.test.tsx"
Task: "T026 [P] [US2] Create manual viewing-booking frontend tests in apps/user/tests/viewing-booking-flow.test.tsx"
```

## Parallel Example: User Story 3

```text
Task: "T032 [P] [US3] Create backend user inquiry-history API integration tests in backend/tests/integration/test_my_inquiries_api.py"
Task: "T033 [P] [US3] Create profile activity-tab frontend tests in apps/user/tests/profile-activity-tabs.test.tsx"
Task: "T034 [P] [US3] Create profile ownership and protected-route frontend tests in apps/user/tests/profile-auth-ownership.test.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational auth/session/query infrastructure.
3. Complete Phase 3 / US1 landing, auth, manual browse, save, and session-only comparison.
4. Stop and validate the Phase 5 MVP before moving to listing-detail and profile work.

### Incremental Delivery

1. Foundation ready.
2. Deliver US1 manual browse MVP.
3. Deliver US2 listing detail, inquiry, and manual booking.
4. Deliver US3 profile activity tabs.
5. Run the full quickstart validation and scope scan.

### Guardrails

- Do not implement AI search, voice search, microphone input, match score, chatbots, listing AI widgets, buyer-to-agency real-time chat, or editable account-settings flows.
- Do not create `dao.py`.
- Do not stage `.env`, `.codex/`, or `graphify-out/`.
