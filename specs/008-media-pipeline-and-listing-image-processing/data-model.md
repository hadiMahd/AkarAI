# Data Model: Media Pipeline and Listing Image Processing

## Listing Photo Metadata

Represents a photo attached to a tenant-owned listing.

Fields:
- `id`
- `listing_id`
- `agency_tenant_id`
- `object_key`
- `caption`
- `alt_text`
- `display_order`
- `status`
- `content_type`
- `file_size_bytes`
- `width`
- `height`
- `moderation_label`
- `moderation_score`
- `quality_score`
- `created_at`
- `updated_at`

Relationships:
- Belongs to one listing.
- Belongs to one agency tenant.
- May have one or more derivative records.
- Emits one or more audit events over its lifecycle.

Validation rules:
- Uploads must belong to the current tenant.
- File type and file size must be valid before the record is accepted.
- Rejected media must not be eligible for listing display.

State transitions:
- `pending_upload` -> `uploaded`
- `uploaded` -> `processing`
- `processing` -> `accepted`
- `processing` -> `warning`
- `processing` -> `rejected`
- `processing` -> `failed`
- Any non-terminal state -> `removed`

## Media Derivative

Represents an optimized variant of a listing photo.

Fields:
- `id`
- `listing_photo_metadata_id`
- `variant_name`
- `object_key`
- `format`
- `width`
- `height`
- `file_size_bytes`
- `is_public_safe`
- `created_at`

Relationships:
- Belongs to one listing photo.
- May be used by the public listing detail view after approval.

Validation rules:
- Derivatives are created only for photos that pass validation and moderation.
- Public-safe derivatives must never expose the original object path.

## Media Processing Job

Represents asynchronous work for moderation, quality scoring, and derivative generation.

Fields:
- `id`
- `listing_photo_metadata_id`
- `event_name`
- `status`
- `retry_count`
- `max_retries`
- `last_error`
- `available_at`
- `processed_at`
- `created_at`
- `updated_at`

Relationships:
- Belongs to one listing photo.
- Is created from the `listing.image_uploaded` workflow event.

Validation rules:
- Jobs must be idempotent so repeated delivery does not create duplicate accepted photos or derivatives.

## Media Audit Log

Represents a durable history of media lifecycle events.

Fields:
- `id`
- `agency_tenant_id`
- `actor_user_id`
- `listing_photo_metadata_id`
- `event_name`
- `result`
- `details`
- `created_at`

Relationships:
- Belongs to one tenant.
- Optionally references the acting user and listing photo.

Validation rules:
- Upload, rejection, warning, processing completion, and failure outcomes must be logged.
- Audit rows must remain tenant-scoped.
