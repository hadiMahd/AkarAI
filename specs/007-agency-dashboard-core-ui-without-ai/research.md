# Research: Agency Dashboard Core UI Without AI

## Decision: Build Phase 6 in `apps/agency` Using the Same Route-Based App Shape Proven in `apps/user`

Rationale: The current agency app is still a Phase 1 placeholder. Phase 6 needs protected routes, role-aware navigation, multiple list/detail screens, and reusable page-state handling. Reusing the same high-level app structure as the user app keeps the product consistent and avoids inventing a second frontend pattern.

Alternatives considered:
- Keep everything inside the current `App.tsx`: rejected because multi-page role-aware flows become brittle and hard to test.
- Merge agency UI into `apps/user`: rejected because agency and user audiences, permissions, and routes are distinct.

## Decision: Agency Access Starts at a Sign-In Page, Not a Public Landing Page

Rationale: The agency dashboard is an operational tool for authenticated staff, not a public discovery surface. A direct sign-in entry keeps the app focused and avoids copying the user-app landing-page pattern where it adds no value.

Alternatives considered:
- Add a public landing page first: rejected because agency usage starts from known staff accounts and protected operations.
- Auto-open the dashboard without auth entry: rejected because the app relies on existing JWT/cookie auth and role checks.

## Decision: Use `shadcn/ui`, `react-router-dom`, and `@tanstack/react-query` in the Agency App

Rationale: The user app already established a production-ready path with `shadcn/ui`, route guards, and React Query. Reusing those patterns in `apps/agency` keeps the frontend coherent and reduces the cost of building dense operational screens with loading, empty, and error states.

Alternatives considered:
- Leave the agency app on custom inline styles only: rejected because the current skeleton is too limited for a multi-screen dashboard.
- Pick a different UI library for the agency app: rejected because it would create unnecessary design and maintenance drift.

## Decision: Support Employee Access Is Limited to Dashboard, Active Leads, Reviewed Leads, Lead Detail, and Viewing Schedules

Rationale: The clarified spec only grants support employees lead review and view-only schedule access. Limiting their visible navigation to those routes keeps the least-privilege model simple and aligned with the current RBAC rules.

Alternatives considered:
- Expose the full listings area read-only: rejected because it adds UI surface the clarified phase does not require.
- Let support employees edit viewing schedules or slots: rejected because the clarified behavior is schedule view-only and existing backend rules already block slot creation.

## Decision: Treat “Add by Email” as Existing-Account Membership Provisioning Without Outbound Email Delivery in This Phase

Rationale: The clarified requirement is employee onboarding by email entry, but this phase explicitly excludes notification delivery. The practical Phase 6 contract is: an admin enters work email, display name, and role; the backend resolves an existing user account by email and creates the agency membership. If no matching user account exists, the UI returns a clear failure state instead of pretending an invitation was sent.

Alternatives considered:
- Keep the existing `user_id`/`role_id` contract in the UI: rejected because it does not satisfy the agreed email-entry admin workflow.
- Add a full invitation-delivery pipeline now: rejected because email sending belongs to later phases and would widen scope.
- Create pending invitation records with no acceptance flow: rejected because it adds dead-end domain state without operational value in this phase.

## Decision: Restrict the Employee Create Flow to Support Employees in This Phase

Rationale: The clarified Phase 6 workflow is about support-employee management, not provisioning additional agency admins. Limiting the create flow to the support-employee role reduces privilege-escalation risk and keeps the UI simpler.

Alternatives considered:
- Allow arbitrary agency role assignment: rejected because it widens scope and increases RBAC risk.
- Remove role selection entirely: rejected because the clarified flow explicitly includes role assignment.

## Decision: New Listings Publish Immediately by Sending Active Status on Creation

Rationale: The user explicitly chose immediate publish. The existing listing create contract defaults to `inactive`, so the Phase 6 listing form must send the explicit status needed to satisfy the clarified behavior.

Alternatives considered:
- Keep draft-first behavior: rejected by clarification.
- Add a draft/publish toggle anyway: rejected because it adds a branch the user did not choose.

## Decision: Compose Dashboard Summary Cards From Existing Endpoint Totals Instead of Adding a New Aggregate Dashboard Endpoint

Rationale: The current backend already exposes paginated listings, leads, and viewings responses with totals. The agency dashboard can compose basic cards from those totals without widening the API surface just for Phase 6 summary tiles.

Alternatives considered:
- Add a dedicated `/agency/dashboard` summary endpoint: rejected because it is unnecessary for the agreed basic-card scope.
- Hardcode card counts: rejected because operational metrics must stay DB-backed.

## Decision: Keep Spam Leads and Policy Documents Placeholder-Only

Rationale: The clarified spec says policy documents remain placeholder-only and Phase 6 does not include spam classification. Clear placeholders preserve navigation without creating fake functionality.

Alternatives considered:
- Add basic upload processing for policy documents: rejected by clarification and because media/RAG phases handle that later.
- Add a fake spam workflow with no backend meaning: rejected because it would mislead users and muddy later phases.
