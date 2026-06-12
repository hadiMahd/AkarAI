# Feature Specification: Media Pipeline and Listing Image Processing

**Feature Branch**: `008-media-pipeline-and-listing-image-processing`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "phase 7 only, ask if there is any decisions to be made"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Valid Listing Photos (Priority: P1)

Agency admins upload photos for listings and see those photos accepted only when they are valid, safe, and linked to the correct listing.

**Why this priority**: Listing photos are required before later listing AI and media workflows can work reliably.

**Independent Test**: Can be tested by uploading a valid image to a tenant-owned listing and verifying that the listing shows the photo with accepted media metadata.

**Acceptance Scenarios**:

1. **Given** an agency admin owns a listing, **When** they upload a valid image file within allowed size limits, **Then** the image is accepted, stored, associated with that listing, and visible through the listing photo record.
2. **Given** a support employee or unrelated agency user, **When** they attempt to upload a photo to a listing they cannot manage, **Then** the upload is denied without storing media.

---

### User Story 2 - Reject Unsafe or Invalid Uploads (Priority: P2)

Agency admins receive clear rejection outcomes when an uploaded file is invalid, unsupported, too large, unsafe, or otherwise not suitable for a listing.

**Why this priority**: Invalid and unsafe media must be blocked before it pollutes listing records or public surfaces.

**Independent Test**: Can be tested by attempting invalid file uploads and unsafe image uploads, then verifying no accepted photo is created.

**Acceptance Scenarios**:

1. **Given** an agency admin uploads an unsupported file type, **When** validation runs, **Then** the file is rejected before durable storage and the user sees a clear reason.
2. **Given** an agency admin uploads an image detected as NSFW, **When** moderation completes, **Then** the image is rejected, hidden from listing surfaces, and the rejection is logged.

---

### User Story 3 - Process Photos for Quality and Delivery (Priority: P3)

Agency admins can upload acceptable photos and receive quality warnings while the system prepares optimized versions for efficient display.

**Why this priority**: Optimized media improves listing performance and quality warnings help agencies improve bad photos without blocking acceptable work.

**Independent Test**: Can be tested by uploading a low-quality but safe image and verifying it remains attached to the listing with a warning and optimized derivative.

**Acceptance Scenarios**:

1. **Given** an agency admin uploads a safe low-quality image, **When** quality checks complete, **Then** the photo is accepted with a warning status visible to agency staff.
2. **Given** an accepted listing photo, **When** processing completes, **Then** an optimized derivative is available for listing display.

### Edge Cases

- Upload is interrupted after validation but before processing completes.
- The same image is uploaded more than once to the same listing.
- Image metadata cannot be read or contains corrupt dimensions.
- Processing succeeds for the original image but fails for one derivative.
- A listing is archived while its media processing job is still pending.
- A photo is removed while processing is still running.
- Media access is requested by an anonymous user, a different agency, and a platform admin.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow agency admins to upload image files to listings owned by their agency.
- **FR-002**: System MUST prevent support employees from creating or replacing listing photos unless an existing permission explicitly allows it.
- **FR-003**: System MUST reject uploads for listings outside the actor's tenant.
- **FR-004**: System MUST validate file type, file extension, content signature, and file size before accepting an upload as listing media.
- **FR-005**: System MUST define clear maximum file size and allowed image types for listing photo uploads.
- **FR-006**: System MUST store accepted original media under a tenant-scoped listing media location.
- **FR-007**: System MUST create or update listing photo metadata with storage path, processing status, content type, size, width, height, and moderation result.
- **FR-008**: System MUST trigger asynchronous processing when a listing image is uploaded.
- **FR-009**: System MUST make image upload and processing outcomes idempotent so retries do not duplicate accepted listing photos or audit logs.
- **FR-010**: System MUST reject unsafe images using the Hugging Face `Falconsai/nsfw_image_detection` image classification model.
- **FR-011**: System MUST assess image blur quality using Laplacian variance with a warning threshold of `208.12155306730278`.
- **FR-012**: System MUST reject NSFW images and keep them unavailable from listing display surfaces.
- **FR-013**: System MUST accept safe low-quality images with a warning rather than rejecting them, unless they fail hard validation rules.
- **FR-014**: System MUST generate optimized WebP derivatives for accepted listing photos.
- **FR-015**: System MUST keep derivative metadata linked to the original listing photo.
- **FR-016**: System MUST expose approved listing media through public-safe URLs after moderation and quality checks, while retaining original uploads privately in storage.
- **FR-017**: System MUST record audit logs for upload accepted, upload rejected, moderation rejected, quality warning, processing completed, and processing failed outcomes.
- **FR-018**: System MUST keep media processing state visible enough for agency users to distinguish pending, accepted, warning, rejected, and failed photos.
- **FR-019**: System MUST prevent rejected media from being used as the listing's primary or gallery image.
- **FR-020**: System MUST preserve tenant isolation for media metadata, storage paths, processing jobs, and audit logs.

### Key Entities

- **Listing Photo**: Represents a photo attached to a listing, including order, status, storage references, dimensions, content type, and moderation or quality outcome.
- **Media Derivative**: Represents an optimized version of a listing photo, including derivative type, dimensions, format, and storage reference.
- **Media Processing Job**: Represents asynchronous processing work for moderation, quality checks, optimization, and retry status.
- **Media Audit Log**: Represents an auditable event for upload, rejection, warning, processing completion, and processing failure.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature touches listing management and media processing only. It does not add buyer-to-agency chat, AI search, RAG search, lead scoring, generated replies, or platform admin workflows.
- **Tenant/RBAC Impact**: Agency Admin can upload and manage listing photos for their own tenant. Support Employee cannot create listings or manage listing photos unless explicitly permitted later. Platform Admin may inspect audit outcomes without tenant leakage.
- **AI/RAG Scope**: This phase introduces provider decisions for media moderation and image quality only. It does not introduce RAG ingestion, OCR listing extraction, AI chat, voice search, or listing AI answers.
- **Reliability/Security/Performance**: Upload validation, tenant authorization, rate limiting, asynchronous processing, idempotent retries, audit logging, access-controlled media URLs, and optimized WebP derivatives are required.
- **Unknowns to Clarify**: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unsupported file types and oversized uploads are rejected before becoming accepted listing photos.
- **SC-002**: 100% of NSFW images identified by the chosen moderation policy are rejected from listing display surfaces.
- **SC-003**: 95% of valid image uploads reach a final accepted, warning, rejected, or failed status within 60 seconds under normal operating conditions.
- **SC-004**: 100% of accepted listing photos have original media metadata and at least one optimized display derivative recorded.
- **SC-005**: 100% of media access attempts respect tenant and public-safety rules defined by the selected access strategy.
- **SC-006**: Agency admins can understand whether each uploaded photo is pending, accepted, warning, rejected, or failed without contacting support.

## Assumptions

- Existing agency authentication, tenant isolation, listing ownership, background worker, object storage, and audit logging foundations are reused.
- Listing photo upload is limited to agency dashboard workflows in this phase.
- OCR and automatic listing extraction from documents or images are outside Phase 7.
- User-facing listing pages may display accepted optimized derivatives, but this phase does not add new AI listing features.
- Upload rate limiting follows the existing project-wide rate limit pattern for sensitive write operations.
