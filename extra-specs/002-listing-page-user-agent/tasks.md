# Tasks: Listing Page User Agent

**Input**: Design documents from `/extra-specs/002-listing-page-user-agent/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: Include focused backend unit/integration coverage, widget UI tests, and manual validation steps for confirmation-only mutation flows.

## Phase 1: Contracts and Config

- [ ] T001 Define the listing assistant request/response schemas and normalized `pending_action` contract in `backend/app/ai/schemas.py`.
- [ ] T002 Add the public listing assistant route `POST /api/v1/listings/{listing_id}/assistant/messages` in `backend/app/listings/router.py` and wire it in `backend/app/main.py` if needed.
- [ ] T003 Add LangChain/LangSmith/Azure OpenAI config placeholders and environment documentation in `backend/app/common/config.py`, `backend/requirements.backend.txt`, `.env.example`, and `backend/app/ai/README.md`.

## Phase 2: Backend Orchestration Foundations

- [ ] T004 Implement the listing-page assistant orchestrator and LangSmith tracing hooks in `backend/app/ai/listing_user_assistant.py` and `backend/app/ai/registry.py`.
- [ ] T005 Add constrained listing-context and active-slot tool helpers in `backend/app/listings/service.py` and `backend/app/viewings/service.py`.
- [ ] T006 Implement inquiry-preparation payload shaping, including the current lead-profile rule handoff, in `backend/app/ai/listing_user_assistant.py` and `backend/app/leads/service.py`.
- [ ] T007 Implement natural-language viewing-slot matching and proposal shaping in `backend/app/ai/listing_user_assistant.py` and `backend/app/viewings/service.py`.
- [ ] T008 Add explicit guardrails so the assistant route prepares payloads only and never writes leads or viewings directly in `backend/app/ai/listing_user_assistant.py`.

## Phase 3: Frontend Widget and Confirmation Flow

- [ ] T009 Add user-app types and API client support for the assistant route in `apps/user/src/lib/api/errors.ts`, `apps/user/src/lib/query/query-client.ts`, and a new `apps/user/src/features/listing-assistant/useListingAssistant.ts`.
- [ ] T010 Build the compact transcript widget with session-only state in `apps/user/src/features/listing-assistant/ListingAssistantWidget.tsx`.
- [ ] T011 Integrate the widget into `apps/user/src/pages/listing-detail/ListingDetailPage.tsx` while keeping `InquiryForm` and `BookingForm` visible as fallback paths.
- [ ] T012 Add structured confirmation cards for `lead_inquiry` and `viewing_booking` actions and wire confirm buttons to the existing `useSubmitInquiry` and `useBookViewing` hooks in `apps/user/src/features/listing-assistant/ListingAssistantWidget.tsx`.
- [ ] T013 Add sign-in and `/profile` routing behavior for blocked mutation flows in `apps/user/src/features/listing-assistant/ListingAssistantWidget.tsx` and `apps/user/src/app/router.tsx` if route helpers are needed.

## Phase 4: Existing Surface Alignment

- [ ] T014 Review `apps/user/src/features/profile/SubmittedInquiriesTab.tsx` and `apps/user/src/features/profile/ScheduledViewingsTab.tsx` so assistant-triggered flows do not introduce redundant profile identity dumps into activity surfaces.
- [ ] T015 Align widget copy and error states with existing inquiry and booking validation messages in `apps/user/src/lib/api/errors.ts`, `apps/user/src/features/inquiries/InquiryForm.tsx`, and `apps/user/src/features/viewings/BookingForm.tsx`.

## Phase 5: Validation and Docs

- [ ] T016 Add backend unit tests for listing Q&A scope, inquiry preparation, slot matching, and prepare-only guardrails in `backend/tests/unit/test_listing_user_assistant.py`.
- [ ] T017 Add backend API integration tests for `POST /api/v1/listings/{listing_id}/assistant/messages`, unauthenticated blocking, incomplete-profile blocking, and no-match slot responses in `backend/tests/integration/test_listing_user_assistant_api.py`.
- [ ] T018 Add frontend widget tests for transcript rendering, confirmation cards, cancel behavior, and mutation triggering only after button clicks in `apps/user/tests/listing-user-assistant.test.tsx`.
- [ ] T019 Add manual validation steps and trace expectations in `extra-specs/002-listing-page-user-agent/quickstart.md`.
