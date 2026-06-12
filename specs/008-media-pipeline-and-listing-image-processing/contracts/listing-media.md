# Listing Media Contract

## Upload Photo

`POST /agency/listings/{listing_id}/photos`

Request:
- `multipart/form-data`
- `file`: image file
- `caption`: optional text
- `alt_text`: optional text
- `display_order`: optional integer

Response:
- `201 Created`
- Returns the photo metadata record with processing status and storage references.

Expected behavior:
- Reject unsupported file types and oversized files before durable storage.
- Reject uploads for listings outside the current tenant.
- Create a durable photo record for accepted uploads.
- Emit the listing image uploaded workflow event.

## List Listing Photos

`GET /agency/listings/{listing_id}/photos`

Response:
- `200 OK`
- Returns all photo metadata for the tenant-owned listing, including processing state.

Expected behavior:
- Support staff may view photos only for listings inside their tenant.
- Rejected and removed photos remain visible as status records, but not as active display candidates.

## Update Photo Metadata

`PATCH /agency/listings/{listing_id}/photos/{photo_id}`

Request:
- JSON body with optional `caption`, `alt_text`, and `display_order`

Response:
- `200 OK`

Expected behavior:
- Allow caption and ordering updates only for tenant-owned photos.
- Do not change moderation outcome through this route.

## Remove Photo

`DELETE /agency/listings/{listing_id}/photos/{photo_id}`

Response:
- `204 No Content`

Expected behavior:
- Mark the photo removed and prevent it from being used as a listing display image.

## Public Listing Detail Media

`GET /listings/{listing_id}`

Response:
- `200 OK`
- Includes only public-safe approved media references for display.

Expected behavior:
- Original uploads stay private.
- Public listing consumers only receive approved display media.

## Workflow Event

`listing.image_uploaded`

Payload:
- `listing_id`
- `listing_photo_id`
- `agency_tenant_id`
- `object_key`
- `content_type`
- `file_size_bytes`
- `uploaded_by_user_id`

Expected behavior:
- A worker consumes the event, runs moderation and quality scoring, and writes back the final photo state.
