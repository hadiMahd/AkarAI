# Research: Media Pipeline and Listing Image Processing

## Decision: Use the Current Local Docker Compose Stack

Rationale: The user explicitly chose local-only for this phase. The repository already bootstraps MinIO, Redis, PostgreSQL, PgBouncer, backend, worker, and agency app in Docker Compose, so the cleanest plan is to extend that environment instead of introducing a new deployment target.

Alternatives considered:
- Managed cloud runtime: rejected because the user requested local-only for now.
- New isolated service: rejected because the repo is already organized as a modular monolith with workers.

## Decision: Store Originals Privately in MinIO and Serve Only Approved Public-Safe Derivatives

Rationale: Listing photos are user-facing, but originals should remain private to keep the source upload protected. Approved WebP derivatives can be surfaced safely and cached by the UI without exposing raw uploads.

Alternatives considered:
- Signed URLs for everything: rejected because it adds unnecessary URL churn for a listing photo workflow.
- Public originals: rejected because it weakens control over unapproved media.

## Decision: Use the Existing `property-media` Bucket

Rationale: Docker Compose already creates `property-media`, and the current backend config already knows about the media bucket. Reusing it keeps the phase aligned with the existing bootstrap.

Alternatives considered:
- New bucket per media variant: rejected because it fragments storage with no clear benefit.
- Reuse the RAG bucket: rejected because media and RAG assets have different lifecycle expectations.

## Decision: Trigger Processing from the Existing Outbox / Worker Flow

Rationale: The repository already uses an outbox-style event pattern, and `listing.image_uploaded` is already reserved as an event name. That makes asynchronous moderation and derivative generation fit the current reliability model.

Alternatives considered:
- Run moderation and conversion synchronously inside the upload request: rejected because it would slow the upload path and make retries less reliable.
- Poll MinIO directly without domain events: rejected because it weakens auditability and idempotency.

## Decision: Use Hugging Face `Falconsai/nsfw_image_detection` for NSFW Moderation

Rationale: The user specified the model and provided the usage snippet. The Hugging Face Inference Client gives a direct way to classify an uploaded image without introducing a second moderation vendor.

Alternatives considered:
- Another managed moderation API: rejected because the user already chose the model.
- Self-hosted moderation model: rejected because it adds unnecessary operational burden for this phase.

## Decision: Use Laplacian Variance for Quality Scoring

Rationale: The user already measured the threshold and wants deterministic low-quality warnings, not a black-box score. Laplacian variance is simple, explainable, and good enough for blur detection.

Alternatives considered:
- ML-based quality scoring: rejected because the threshold-based approach is already defined and easier to validate.
- Manual review only: rejected because it does not scale and does not satisfy automated warning behavior.

## Decision: Use Existing Listing Photo Metadata as the Core Record

Rationale: The repository already has `listing_photo_metadata` as a first-class table and photo routes in the listings module. Extending that model is simpler than introducing a separate parallel media model.

Alternatives considered:
- New photo table parallel to the current one: rejected because it duplicates listing-photo state.
- Store media state only in worker payloads: rejected because the UI needs durable status and audit history.
