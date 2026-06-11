# Quickstart: Agency Dashboard Core UI Without AI

## Prerequisites

- Phase 1-5 foundations are merged into `main`.
- Current branch is `007-agency-dashboard-core-ui-without-ai`.
- `.env` is configured for local Docker Compose and Vault bootstrap.
- The agency app runs on `http://localhost:3001` and the backend on `http://localhost:8000`.
- Seeded agency test users exist after migrations:
  - `agency.admin@akarai.test`
  - `support@akarai.test`
  - `user@akarai.test`

## Start Services

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Expected:
- `backend`, `agency-app`, `user-app`, `admin`, and `worker` services are healthy.
- Latest migrations are applied before UI validation begins.

## Run Targeted Validation Commands

```bash
docker compose exec backend pytest
docker compose exec agency-app npm test -- --run
docker compose exec agency-app npm run build
```

Expected:
- Backend regression tests pass, including any employee email-onboarding coverage added for Phase 6.
- Agency frontend tests pass.
- The agency app builds successfully.

## Validate Agency Admin Entry

1. Open `http://localhost:3001`.
2. Confirm the app opens on the agency sign-in entry.
3. Sign in as `agency.admin@akarai.test`.
4. Refresh the page once after sign-in.

Expected:
- Unauthenticated users cannot reach protected agency routes.
- Sign-in succeeds and lands inside the protected dashboard shell.
- Refresh preserves the session and keeps the user inside the protected app.

## Validate Dashboard Cards and Navigation

1. Open `/dashboard`.
2. Confirm the summary cards render.
3. Navigate through profile, employees, listings, leads, reviewed leads, viewings, spam leads, and policy documents.

Expected:
- The dashboard shell and cards show loading states immediately, then resolve with tenant-scoped data.
- Every implemented page loads with either content, an empty state, or a placeholder state.
- Placeholder screens do not behave like finished workflows.

## Validate Agency Profile and Employee Management

1. Open `/profile` as the agency admin.
2. Update one profile field and save.
3. Open `/employees`.
4. Add `user@akarai.test` as a support employee using the Phase 6 existing-account-by-email flow.
5. Edit an employee row if that flow is implemented.
6. Deactivate an employee if that flow is implemented.

Expected:
- Profile updates succeed only for admins.
- Employee management is admin-only.
- Employee creation uses email plus role against an existing account and returns a clear success or failure state.
- Duplicate or missing-account employee creates fail cleanly.

## Validate Listing and Viewing Slot Management

1. Open `/listings`.
2. Open `/listings/new`.
3. Create a listing with valid data.
4. Confirm the new listing appears as published immediately.
5. Open the listing slot manager for that listing.
6. Create, edit, and deactivate one viewing slot.

Expected:
- Listing pages remain tenant-scoped and paginated.
- New listings publish immediately after creation.
- Viewing-slot actions are available only to admins.
- Slot validation failures return a clear error state.

## Validate Lead Review Flow

1. Open `/leads` as the agency admin.
2. Open one lead detail page.
3. Mark the lead as reviewed.
4. Revisit `/leads`.
5. Open `/leads/reviewed`.

Expected:
- The reviewed lead leaves the active non-reviewed queue.
- The reviewed lead appears in reviewed leads.
- The detail page shows the updated reviewed state.

## Validate Viewing Schedules

1. Open `/viewings` as the agency admin.
2. Apply supported filters for `status`, `listing`, `date_from`, and `date_to`.
3. Clear filters.

Expected:
- Viewing schedules remain paginated.
- Filters return the expected subset and recover cleanly when no rows match.
- Empty-filter results show a stable empty state.

## Validate Support Employee Restrictions

1. Sign out and sign in as `support@akarai.test`.
2. Open `/dashboard`, `/leads`, `/leads/reviewed`, and `/viewings`.
3. Review one lead and confirm it moves from active to reviewed.
4. Attempt to access `/profile`, `/employees`, `/listings/new`, and listing slot-management routes directly.

Expected:
- Support employees can access dashboard, leads, reviewed leads, lead detail, and schedules only.
- Support employees can mark leads as reviewed.
- Support employees cannot create listings, manage employees, update agency profile, or mutate schedules/slots; direct schedule-status update attempts fail.
- Hidden routes either stay inaccessible or redirect to an allowed page.

## Validate Placeholder Surfaces

1. Open `/spam-leads`.
2. Open `/policy-documents`.

Expected:
- Both pages show explicit placeholder messaging.
- The policy document page does not accept uploads in this phase.
- No AI, classification, or document-processing workflow is exposed.

## Validate Local Responsiveness

1. Sign in as each role and navigate across the protected pages.
2. Open listings, leads, and viewings on a healthy local stack.
3. Perform one profile save, one employee add attempt, one listing create, and one lead review action.
4. Use browser DevTools or equivalent request timing capture.

Expected:
- Protected route shells and loading states appear immediately.
- First-page dashboard, listings, leads, and viewing fetches resolve within about 1 second locally.
- Profile save, employee create, listing create, and lead review actions show a result within about 2 seconds locally.

## Scope Guard

Run a scope scan after implementation:

```bash
grep -rn "AI\\|chatbot\\|voice\\|match score\\|spam classifier\\|policy upload\\|email send\\|real-time chat" apps/agency backend specs/007-agency-dashboard-core-ui-without-ai | grep -v "node_modules\\|\\.pyc\\|__pycache__"
```

Expected:
- Matches appear only in docs, tests asserting absence, or placeholder copy that clearly says the feature is deferred.

## Shutdown

```bash
docker compose down
```
