# Tasks: Media Pipeline and Listing Image Processing

**Input**: Design documents from `/specs/008-media-pipeline-and-listing-image-processing/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/listing-media.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the repository for listing-media processing work and lock the local runtime assumptions.

- [X] T001 Update local development documentation in `specs/008-media-pipeline-and-listing-image-processing/quickstart.md` to reflect the media-upload validation flow and the current Docker Compose runtime.
- [X] T002 Add any missing media runtime settings to `backend/app/common/config.py` for upload limits, bucket/prefix names, moderation threshold, and derivative behavior.
- [X] T003 [P] Add backend dependencies needed for media moderation and image processing in `backend/requirements.txt`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared media foundations required before any story can be completed.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create media-processing data fields and status support for listing photos in `backend/app/listings/models.py`.
- [X] T005 [P] Extend listing-photo schemas for upload, processing status, derivative metadata, and public-safe display in `backend/app/listings/schemas.py`.
- [X] T006 [P] Add repository helpers for listing-photo lookup, metadata updates, and tenant-safe listing media queries in `backend/app/listings/repository.py`.
- [X] T007 Add MinIO media helpers for safe upload, download, delete, and presigned/public-safe access in `backend/app/common/storage.py`.
- [X] T008 Extend the domain event catalog and audit log support for `listing.image_uploaded` and media lifecycle outcomes in `backend/app/common/events.py`.
- [X] T009 Add media-processing worker scaffolding and event dispatch wiring for `listing.image_uploaded` in `workers/` and `backend/app/common/events.py`.
- [X] T010 Add backend migration support for the new listing media fields and derivative metadata in `backend/alembic/versions/`.
- [X] T011 Add shared media validation helpers for file type, file signature, size, and blur scoring in `backend/app/common/`.
- [X] T012 Add shared upload/processing tests for the new media foundation in `backend/tests/unit/` and `backend/tests/integration/`.

**Checkpoint**: Listing-media upload and processing primitives are ready.

---

## Phase 3: User Story 1 - Upload Valid Listing Photos (Priority: P1)

**Goal**: Agency admins can upload valid listing photos and see them stored and attached to the correct tenant-owned listing.

**Independent Test**: Upload a valid image to a tenant-owned listing and confirm the photo is stored, linked, and visible with accepted metadata.

### Tests for User Story 1

- [X] T013 [P] [US1] Add backend integration coverage for successful tenant-owned listing photo upload in `backend/tests/integration/test_listing_photo_upload_api.py`.
- [X] T014 [P] [US1] Add backend RBAC/tenant-isolation coverage for unsupported users or cross-tenant photo uploads in `backend/tests/rbac/test_listing_photo_upload_rbac.py`.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement upload validation and accepted-photo creation flow in `backend/app/listings/service.py`.
- [X] T016 [US1] Wire the upload endpoint to the media validation flow in `backend/app/listings/router.py`.
- [X] T017 [US1] Persist upload metadata, tenant-scoped object paths, and accepted photo status in `backend/app/listings/service.py`.
- [X] T018 [US1] Add agency UI upload entry and form state for listing photos in `apps/agency/src/features/listings/` and `apps/agency/src/pages/listings/`.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Reject Unsafe or Invalid Uploads (Priority: P2)

**Goal**: Invalid, oversized, and NSFW uploads are rejected before they can become displayable listing media.

**Independent Test**: Attempt invalid file uploads and an NSFW image upload, then confirm nothing becomes an accepted listing photo.

### Tests for User Story 2

- [X] T019 [P] [US2] Add backend service tests for file validation and rejection behavior in `backend/tests/unit/test_listing_photo_validation.py`.
- [X] T020 [P] [US2] Add backend integration coverage for NSFW and invalid upload rejection in `backend/tests/integration/test_listing_photo_rejection_api.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement Hugging Face NSFW moderation integration in `backend/app/listings/service.py` and `backend/app/workers/`.
- [X] T022 [US2] Implement rejection status updates and audit logging for invalid or unsafe uploads in `backend/app/listings/service.py` and `backend/app/common/events.py`.
- [X] T023 [US2] Expose rejection states in the agency upload and photo-status UI in `apps/agency/src/features/listings/` and `apps/agency/src/pages/listings/`.

**Checkpoint**: User Story 2 should now work independently from the safe-upload path.

---

## Phase 5: User Story 3 - Process Photos for Quality and Delivery (Priority: P3)

**Goal**: Safe photos receive quality warnings when needed and are converted into optimized public-safe derivatives.

**Independent Test**: Upload a safe blurry image and confirm it is accepted with warning status and an optimized derivative.

### Tests for User Story 3

- [X] T024 [P] [US3] Add backend service tests for Laplacian quality scoring and WebP derivative generation in `backend/tests/unit/test_listing_photo_processing.py`.
- [X] T025 [P] [US3] Add backend integration coverage for the worker-driven processing lifecycle in `backend/tests/integration/test_listing_photo_processing_api.py`.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement Laplacian-based quality scoring and warning thresholds in `backend/app/listings/service.py` or `backend/app/common/`.
- [X] T027 [US3] Implement WebP derivative generation and derivative metadata persistence in `backend/app/workers/` and `backend/app/listings/service.py`.
- [X] T028 [US3] Implement public-safe media URL handling for approved derivatives in `backend/app/common/storage.py` and `backend/app/listings/router.py`.
- [X] T029 [US3] Render approved media and warning states in the agency listing UI in `apps/agency/src/features/listings/` and `apps/agency/src/pages/listings/`.

**Checkpoint**: All three user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, validation, and cross-feature hardening.

- [X] T030 [P] Add documentation updates for listing media behavior in `specs/008-media-pipeline-and-listing-image-processing/quickstart.md` and `contracts/listing-media.md`.
- [X] T031 [P] Add any remaining scope-guard coverage for media-only functionality in `backend/tests/` and `apps/agency/tests/`.
- [X] T032 Run the quickstart validation flow and verify end-to-end upload, rejection, warning, and derivative behavior in Docker Compose.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and provides the base listing-photo upload flow.
- **User Story 2 (P2)**: Starts after Foundational and can be implemented independently of the quality/derivative work.
- **User Story 3 (P3)**: Starts after Foundational and builds on the accepted-photo workflow.

### Within Each User Story

- Write tests first where they are listed.
- Implement validation and persistence before UI wiring.
- Keep tenant checks and audit logging inside the service layer.
- Complete each story before moving to the next one.

### Parallel Opportunities

- `T003`, `T005`, `T006`, `T007`, `T008`, `T009`, `T011`, and `T012` can run in parallel where files do not overlap.
- `T013` and `T014` can run in parallel.
- `T019` and `T020` can run in parallel.
- `T024` and `T025` can run in parallel.
- `T030` and `T031` can run in parallel.

## Implementation Strategy

Deliver the safe upload path first, then rejection handling, then quality warnings and derivative delivery. Keep the backend as the source of truth for photo state and use the agency app only to surface upload and status information.
