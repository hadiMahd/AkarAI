# Quickstart: Media Pipeline and Listing Image Processing

## Prerequisites

- Local Docker Compose stack is running.
- MinIO bootstrap has created the `property-media` bucket.
- Backend migrations are current.
- Agency admin test account exists.

## Start Services

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Expected:
- `backend`, `worker`, `agency-app`, `redis`, `minio`, and `pgbouncer` are healthy.
- The media bucket exists before uploads are tested.

## Run Validation Tests

```bash
docker compose exec backend pytest
docker compose exec agency-app npm test -- --run
docker compose exec agency-app npm run build
```

Expected:
- Backend tests covering media validation and processing pass.
- Agency UI tests covering upload and media-state rendering pass.
- The agency app builds successfully.

## Validate Safe Upload

1. Open the agency app and sign in as an agency admin.
2. Open the listing photo upload flow for an existing tenant listing.
3. Upload a valid image.

Expected:
- The upload is accepted.
- A photo record appears with a processing state.
- A final accepted state appears after worker processing completes.

## Validate Rejection Paths

1. Upload an unsupported file type.
2. Upload a file larger than the allowed limit.
3. Upload the NSFW sample image used by the test suite.

Expected:
- Unsupported and oversized uploads are rejected immediately.
- NSFW uploads are rejected by moderation.
- Rejections are visible in the listing photo status history.

## Validate Quality Warning

1. Upload a valid but blurry image.
2. Wait for processing to finish.

Expected:
- The image is accepted with a warning status.
- The photo remains usable for the listing, but the warning is visible to agency staff.

## Validate Display Media

1. Open the public listing detail page for a listing with accepted media.
2. Inspect the returned media references.

Expected:
- The public view only exposes approved public-safe media.
- The original upload path remains private.

## Shutdown

```bash
docker compose down
```
