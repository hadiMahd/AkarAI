# Quickstart: User App Core UI Without AI

## Prerequisites

- Phase 1-4 foundations are merged into `main`.
- Current branch is `006-user-app-core-ui-without-ai`.
- `.env` is configured for local Docker Compose and Vault bootstrap.
- The user app runs on `http://localhost:3000` and the backend on `http://localhost:8000`.

## Start Services

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Expected:
- `backend`, `user-app`, `agency-app`, `admin`, and `worker` services are healthy.
- The latest migration is applied before UI validation begins.

## Run Targeted Validation Commands

```bash
docker compose exec backend pytest
docker compose exec user-app npm test -- --run
docker compose exec user-app npm run build
```

Expected:
- All backend regression tests pass, including Phase 5 auth/leads/viewings support coverage.
- All frontend unit and component tests pass.
- The user app builds successfully.

## Validate Landing and Auth Entry

1. Open `http://localhost:3000`.
2. Confirm the landing page exposes sign-in and sign-up entry points only.
3. Attempt to navigate directly to a protected route such as listings or profile while signed out.
4. Complete the sign-up flow with a new user account.
5. Complete the sign-in flow with valid credentials.

Expected:
- The landing page does not expose protected app content before authentication.
- Protected routes redirect to sign-in while signed out.
- Sign-up succeeds through the working registration flow.
- Sign-in succeeds and redirects into the protected app shell.

## Validate Manual Search and Listings Flow

1. After sign-in, open the homepage manual search.
2. Submit filters for location, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, area size, and sort order.
3. Navigate to the listings results page.
4. Change sort order and page number.
5. Refresh the page and confirm the current search state remains intact.

Expected:
- Listings load with visible loading states, then render paginated results.
- Filter, sort, and pagination state remain synchronized with the route.
- Empty-result searches show a stable empty state.
- Search rate-limit responses show a clear failure state instead of a broken page.

## Validate Save and Session-Only Comparison

1. Save a listing from search results.
2. Open the listing detail page and confirm the saved state matches.
3. Add up to four listings to comparison.
4. Attempt to add a fifth listing.
5. Refresh the browser and confirm the current-session comparison remains.
6. Sign out or end the browser session, then sign back in.

Expected:
- Save/unsave actions stay synchronized across listings, detail, and profile.
- The fifth comparison add is rejected cleanly.
- Comparison persists only for the current browser session.
- Comparison does not reappear automatically after a new session starts.

## Validate Listing Detail, Inquiry, and Viewing Booking

1. Open an active listing detail page.
2. Confirm public-safe listing fields and available viewing slots render.
3. Submit an inquiry.
4. Book a viewing from a valid slot.
5. Try an invalid or already-unavailable slot selection.

Expected:
- Listing detail shows no chatbot, AI widget, microphone control, or match score.
- Unavailable listings show a clear unavailable state.
- Inquiry submission returns a clear success or failure state.
- Viewing booking succeeds only for valid available slots.
- Invalid slot attempts fail cleanly without partial UI corruption.

## Validate Profile Activity Tabs

1. Open the profile page after saving listings, submitting an inquiry, and booking a viewing.
2. Open the saved listings tab.
3. Open the submitted inquiries tab.
4. Open the scheduled viewings tab.

Expected:
- The profile page is limited to activity tabs only.
- Each tab shows only the signed-in user's own data.
- No editable account-settings form appears in this phase.

## Validate Auth Guard Behavior

1. While signed in, revisit landing or auth routes.
2. Sign out.
3. Attempt to revisit homepage, listings, detail, comparison, and profile routes.

Expected:
- Signed-in users are redirected away from landing/auth routes into the protected app.
- Sign-out clears protected access and session-only comparison state.
- Signed-out access to protected routes is blocked consistently.

## Validate Local Responsiveness

1. Sign in and navigate from landing to homepage.
2. Open listings results and a profile activity tab on a healthy local stack.
3. Submit an inquiry and a viewing booking.
4. Use browser DevTools network/request timing or equivalent local timing capture while running the above checks.

Expected:
- Protected route shell and loading states appear immediately on navigation.
- First-page listings and profile tab data load within about 1 second locally.
- Sign-in, sign-up, inquiry, and booking submissions return a clear result within about 2 seconds locally.
- Timing evidence is captured during validation instead of estimated by eye alone.

## Validate Frontend Tests

```bash
docker compose exec user-app npm test -- --run
```

Expected:
- All frontend tests pass including:
  - Auth routing tests (protected routes, public-only routes)
  - Landing and auth flow tests
  - Manual search flow tests
  - Saved listings and comparison tests
  - Listing detail and inquiry tests
  - Viewing booking flow tests
  - Profile activity tabs tests
  - Profile auth ownership tests

## Scope Guard

Run a scope scan after implementation:

```bash
grep -rn "AI search\|voice search\|microphone\|chatbot\|listing AI\|match score\|buyer-to-agency\|account settings\|profile edit" apps/user backend specs/006-user-app-core-ui-without-ai | grep -v "node_modules\|\.pyc\|__pycache__"
```

Expected:
- Matches appear only in docs, tests asserting absence, or explicit out-of-scope guardrails.

## Shutdown

```bash
docker compose down
```
