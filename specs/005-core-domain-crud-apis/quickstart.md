# Quickstart: Core Domain Database and CRUD APIs

## Prerequisites

- Phase 1-3 foundations are merged into `main`.
- Current branch is `005-core-domain-crud-apis`.
- `.env` is configured for local Docker Compose and Vault bootstrap as in previous phases.

## Start Services

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Expected:
- Backend is healthy.
- PostgreSQL/PgBouncer/Redis/MinIO services remain healthy.
- Latest Phase 4 migration is applied.

## Run Backend Test Suite

```bash
docker compose exec backend pytest
```

Expected:
- Existing Phase 1-3 tests still pass.
- New Phase 4 unit, integration, transaction, RBAC, tenant-isolation, pagination, and scope tests pass.

## Validate Agency Admin Flow

1. Sign in as a seeded agency admin.
2. Update agency profile.
3. Create or update an agency employee.
4. Create a listing with status `inactive`.
5. Activate the listing.
6. Add listing photo metadata.
7. Add a viewing slot.

Expected:
- Records are scoped to the admin's agency tenant.
- Domain event or transaction logs exist for critical creates/status changes.
- List endpoints are paginated.

## Validate Support Employee Restrictions

1. Sign in as a seeded support employee.
2. Attempt to update agency profile.
3. Attempt to manage employees.
4. Attempt to create a listing.
5. List allowed leads, scheduled viewings, notifications, and reviewed lead records.

Expected:
- Agency-admin-only mutations return forbidden.
- Allowed operational reads return tenant-scoped paginated results.
- No forbidden mutation changes data.

## Validate Public Listing Flow

1. Search active listings using location text, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, area size, and sort options.
2. Confirm inactive and archived listings are not returned publicly.
3. View active listing detail.
4. Save and unsave a listing.
5. Create a comparison session and add up to four listings.
6. Attempt to add a fifth comparison listing.
7. Exceed the public listing search rate limit.

Expected:
- Search logs record manual search filters and result count.
- Over-limit public search requests return rate-limit responses.
- Saved listings are unique per user/listing.
- Fifth comparison item is rejected.

## Validate Lead Flow

1. Submit an inquiry for an active listing.
2. Sign in as an agency actor for that listing's agency.
3. List and view leads.
4. Mark the lead reviewed.
5. Close the lead.
6. Exceed the inquiry rate limit.

Expected:
- Inquiry creates a tenant-owned lead with status `new`.
- Review creates a reviewed lead record and changes status to `reviewed`.
- Closing changes status to `closed`.
- Over-limit inquiry requests return rate-limit responses without creating leads.
- Lead spam, lead level, and suggested reply records are not computed automatically.

## Validate Viewing Flow

1. Schedule a viewing from an active listing's available viewing slot.
2. Confirm the scheduled viewing has status `scheduled`.
3. Confirm initial status history exists.
4. Fetch the scheduled viewing through both user and agency detail endpoints.
5. Change status to `cancelled_by_user`, `cancelled_by_agency`, `completed`, or `no_show` using allowed transitions.
6. Attempt an invalid transition.
7. Exceed the viewing booking rate limit.

Expected:
- Booking and initial history are created atomically.
- Valid status changes append history.
- Invalid transitions are rejected without partial writes.
- Over-limit booking requests return rate-limit responses without partial writes.

## Validate Notifications and Operational Logs

1. Create records that trigger notification and domain log writes.
2. List and fetch notification detail.
3. Mark a notification read, then dismiss it.
4. List tenant search logs.
5. List tenant domain event logs.

Expected:
- Notification detail, read, and dismiss flows work only for intended recipients.
- Search log and domain log list endpoints return paginated tenant-scoped results.
- Cross-tenant access to notifications or logs is denied.

## Validate Tenant Isolation

1. Use an agency actor from tenant A to access tenant B listings, employees, leads, viewings, notifications, search logs, and domain logs.
2. Use a user account to access another user's saved listings, comparison sessions, inquiries, and scheduled viewings.

Expected:
- All cross-tenant and cross-user ownership attempts fail closed.

## Scope Guard

Run a scope scan after implementation:

```bash
rg -n "AI search|RAG|OCR|email send|chatbot|buyer-to-agency|spam classifier|lead scoring|generated reply|image moderation|image quality|WebP|dashboard" backend specs/005-core-domain-crud-apis
```

Expected:
- Matches are only in documentation, tests asserting absence, or explicit out-of-scope guardrails.

## Shutdown

```bash
docker compose down
```
