# Research: User App Core UI Without AI

## Decision: Keep Phase 5 Centered on `apps/user`, With Minimal Backend Support Only Where the Current API Is Incomplete

Rationale: The goal of Phase 5 is the first usable user app, not a broad backend rewrite. Most browse, save, inquiry, and viewing actions already have Phase 4 API support. The only backend additions needed to make the clarified UI work end-to-end are: user registration, user-owned inquiry history, and user-visible available viewing-slot reads.

Alternatives considered:
- Build the whole user UI against mock data only: rejected because the phase is supposed to validate real end-to-end flows.
- Expand backend broadly during Phase 5: rejected because that would collapse UI work back into another backend-heavy phase.

## Decision: Use `shadcn/ui` as the React UI Library

Rationale: The constitution requires an explicit user decision for the exact React UI library when the repo does not already establish one. The user selected `shadcn/ui`, which fits the need for a cleaner product feel and app-owned control over presentation while staying inside the React + TypeScript stack for `apps/user`.

Alternatives considered:
- Assume no UI library: rejected because it would add more UI implementation overhead in a phase that already spans multiple user flows.
- Use Material UI: rejected because the chosen direction is `shadcn/ui` for lighter, more customizable building blocks.

## Decision: Use Route-Based Navigation With `react-router-dom`

Rationale: Phase 5 explicitly needs a landing page, auth entry flows, homepage, listings, listing detail, comparison, and profile pages. Route-level composition, route guards, and redirects are first-class concerns, so `react-router-dom` is the most direct fit.

Alternatives considered:
- Manual view switching inside a single `App.tsx`: rejected because protected routes, direct links, and page refresh behavior become brittle.
- Next.js migration: rejected because the fixed stack is React + TypeScript and the repo is already Vite-based.

## Decision: Use `@tanstack/react-query` for Server State and a Thin Local Fetch Client for Transport

Rationale: The user app will have multiple paginated lists, mutation flows, cache refresh points, and route-based loading states. `@tanstack/react-query` covers data loading, invalidation, loading/error state orchestration, and stale response management without forcing a backend contract change. A small app-local fetch wrapper keeps transport simple and aligned with the existing API surface.

Alternatives considered:
- Raw `useEffect` + component-local state everywhere: rejected because it becomes repetitive across listings, saved items, profile tabs, and auth refresh handling.
- Axios plus custom cache logic: rejected because it adds transport abstraction without solving cache invalidation as well as React Query.

## Decision: Keep Comparison Session-Scoped in Browser `sessionStorage`

Rationale: The clarified spec says comparison is temporary for the current session only and must not automatically reappear later. Browser `sessionStorage` preserves state across refreshes within the same browser session, clears naturally when the session ends, and avoids fighting the persisted comparison-session APIs created in Phase 4.

Alternatives considered:
- Reuse persisted comparison-session endpoints: rejected because server persistence would outlive the current session unless extra cleanup logic is added.
- Keep comparison in memory only: rejected because a simple page refresh would unexpectedly erase the user's current comparison selection.

## Decision: Add a Minimal Registration Endpoint Under `backend/app/auth`

Rationale: The user clarified that Phase 5 includes working sign-in and sign-up pages. The current auth router supports login, refresh, logout, password reset, and session revocation, but not registration. The least disruptive approach is to extend the existing auth module with a single registration flow that creates a user account and returns a predictable success result for the sign-up UI.

Alternatives considered:
- Make sign-up UI non-functional: rejected by clarification.
- Add registration in a new backend module: rejected because auth ownership already exists in `backend/app/auth`.

## Decision: Add User-Owned Inquiry History and User-Visible Viewing-Slot Read Support

Rationale: The Phase 5 profile includes a submitted inquiries tab, and listing detail includes manual viewing booking from available slots. The current backend supports submitting inquiries and booking viewings, but not listing the signed-in user's inquiries or fetching user-visible available slots from listing detail. Small additions under existing `leads` and `viewings` modules close these gaps.

Alternatives considered:
- Remove submitted inquiries from profile: rejected because it is explicit in the phase scope.
- Embed slots manually in listing detail without an endpoint: rejected because it makes the contract implicit and harder to test.

## Decision: Keep Profile Scope Limited to Activity Tabs Only

Rationale: The user clarified that Phase 5 profile scope is saved listings, submitted inquiries, and scheduled viewings only. This avoids pulling account-settings editing, profile mutation validation, and more auth complexity into the same phase.

Alternatives considered:
- Add editable account fields now: rejected because it expands beyond the agreed phase scope.
- Show basic account fields read-only: deferred because the activity tabs are the only required profile surface in this phase.
