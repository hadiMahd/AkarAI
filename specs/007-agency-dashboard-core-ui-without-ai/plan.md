# Implementation Plan: Agency Dashboard Core UI Without AI

**Branch**: `007-agency-dashboard-core-ui-without-ai` | **Date**: 2026-06-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-agency-dashboard-core-ui-without-ai/spec.md`, root [PLAN.md](../../PLAN.md), project constitution, and completed Phase 1-5 foundations.

## Summary

Implement Phase 6 as the first dedicated agency-facing React app slice on top of the completed auth, RBAC, tenant isolation, and core domain backend. This phase delivers a protected agency dashboard with role-aware navigation, agency admin pages for profile settings, employee management, listing creation, listings oversight, and viewing-slot management, plus shared agency-user workflows for active leads, reviewed leads, lead detail, and viewing schedules. Spam leads and policy documents remain placeholder-only surfaces in this phase.

The primary implementation surface is `apps/agency`. Backend work should stay minimal and only close gaps that block the agreed UI behavior. The known backend gaps from current Phase 1-5 foundations are: employee onboarding by matching an existing account by email instead of accepting raw `user_id`/`role_id`, reviewed-leads listing support for the agency queue, viewing-schedule filters, and explicit admin-only enforcement for viewing-status mutation. No AI, RAG, notifications delivery, media upload, or admin-streamlit work is part of this phase.

## Technical Context

**Language/Version**: TypeScript 5.5 with React 18.3 for the agency app; Python 3.11 for any required backend support adjustments.

**Primary Dependencies**: React, React DOM, Vite, `react-router-dom` for route composition and role-aware guards, `@tanstack/react-query` for server-state fetching and invalidation, `shadcn/ui` for app UI primitives aligned with the user app, FastAPI auth/agencies/listings/leads/viewings endpoints, Vitest plus React Testing Library for agency-app route/component tests, Playwright for browser smoke coverage, pytest for backend regression coverage when employee onboarding support changes.

**Storage**: PostgreSQL remains the source of truth for agency profile, employee memberships, listings, leads, reviewed-lead records, viewing slots, and scheduled viewings. The agency app keeps only transient route and form state in browser memory and query cache. Auth follows the existing HttpOnly refresh-cookie and memory-only access-token pattern already used in the user app.

**Testing**: Agency-app unit/component tests for route guards, role-based navigation, dashboard cards, employee management, listing workflows, lead review, viewing schedule filters, loading states, and placeholder pages; Playwright smoke tests for agency-admin and support-employee happy paths; backend integration tests for employee email-match onboarding, reviewed-leads queue behavior, viewing filters, and support-role schedule restrictions.

**Target Platform**: Local Docker Compose development on the existing `agency-app` service at `http://localhost:3001`, backed by the existing FastAPI service at `http://localhost:8000`. Production hosting topology remains outside this phase.

**Project Type**: Modular monolith web platform with a dedicated React agency app and FastAPI backend.

**Performance Goals**: Protected route shells and loading states should appear immediately on navigation; first-page dashboard cards, listings, leads, and viewing schedules should resolve within about 1 second on a healthy local Docker stack; employee create/update, listing create/update, and lead-review actions should return a visible success or failure state within about 2 seconds locally; all list-heavy surfaces remain paginated.

**Constraints**: No buyer-to-agency real-time chat; no AI widgets, voice features, match score, spam classification, policy-document processing, media uploads, or email delivery in this phase; support employees may review leads and view schedules only; create-listing, employee-management, and profile-settings mutations remain admin-only; use `repository.py`, not `dao.py`; all secrets remain Vault-backed through existing config.

**Scale/Scope**: Phase 6 covers only the agency dashboard UI and the minimum backend support needed for the agreed employee onboarding flow. User app expansion, media pipeline, RAG, AI agency workflows, notifications delivery, and platform admin work remain out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses the required React + TypeScript agency app and existing FastAPI backend on Python 3.11, plus the repo-established PostgreSQL/Redis/MinIO foundation.
- **Architecture**: PASS. Preserves the modular monolith. The agency UI work stays in `apps/agency`; any backend adjustments stay in existing `agencies`, `listings`, `leads`, `viewings`, and `auth` modules with `repository.py` as the data access layer.
- **Product boundaries**: PASS. No buyer-to-agency real-time chat, no AI workflows, no spam classification, and no policy-document processing are introduced.
- **Tenant/RBAC**: PASS. Agency admin and support employee remain tenant-scoped. The plan explicitly restricts support employees from employee-management and listing-create flows while keeping lead review and schedule read access.
- **RAG/search**: PASS. No RAG, listing AI, homepage AI, or area search work is introduced.
- **Reliability/security/performance**: PASS. The plan reuses the existing auth/session model, preserves rate-limited backend actions, keeps all agency data DB-backed, and requires paginated lists plus visible loading/error states.
- **Testing/quality**: PASS. Includes frontend route/component/browser coverage and targeted backend regression only where a real API gap exists.

## Project Structure

### Documentation (this feature)

```text
specs/007-agency-dashboard-core-ui-without-ai/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── dashboard-routes.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/
└── agency/
    ├── src/
    │   ├── app/
    │   │   ├── router.tsx
    │   │   ├── providers.tsx
    │   │   └── guards.tsx
    │   ├── pages/
    │   │   ├── auth/
    │   │   ├── dashboard/
    │   │   ├── profile/
    │   │   ├── employees/
    │   │   ├── listings/
    │   │   ├── leads/
    │   │   ├── viewings/
    │   │   └── placeholders/
    │   ├── features/
    │   │   ├── auth/
    │   │   ├── dashboard/
    │   │   ├── profile/
    │   │   ├── employees/
    │   │   ├── listings/
    │   │   ├── leads/
    │   │   ├── viewings/
    │   │   └── navigation/
    │   ├── components/
    │   ├── lib/
    │   │   ├── api/
    │   │   ├── session/
    │   │   └── query/
    │   ├── styles/
    │   └── main.tsx
    └── tests/

backend/
├── app/
│   ├── agencies/
│   ├── auth/
│   ├── listings/
│   ├── leads/
│   ├── viewings/
│   └── common/
└── tests/
    ├── integration/
    └── rbac/
```

**Structure Decision**: `apps/agency` should be expanded from the current Phase 1 skeleton into the same route-based, feature-organized app shape already proven in `apps/user`. Backend work should remain minimal and limited to genuine contract gaps, with employee onboarding by email as the main expected addition. Existing agency/listings/leads/viewings endpoints remain the primary integration surface.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover agency-app routing and auth entry, the shared `shadcn/ui` and React Query approach, the support-employee access matrix, the minimal backend contract needed for existing-account-by-email onboarding, immediate listing publish behavior, and the decision to keep dashboard cards and placeholders within the existing backend scope.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- UI and API contracts: [contracts/dashboard-routes.md](./contracts/dashboard-routes.md)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Final design stays on React + TypeScript in `apps/agency` and FastAPI in existing backend modules.
- **Architecture**: PASS. The app moves from a single-file skeleton to a route- and feature-based structure without introducing a second backend architecture style.
- **Product boundaries**: PASS. The design stays inside agency operations UI and placeholder-only operational sections, with no AI or real-time chat expansion.
- **Tenant/RBAC**: PASS. Route guards, nav visibility, and backend dependencies all follow agency admin vs support employee rules and tenant-scoped access.
- **RAG/search**: PASS. No RAG or AI search behavior is introduced.
- **Reliability/security/performance**: PASS. Existing auth/session handling, rate limits on backend mutations, paginated tables, and explicit loading/error states are preserved. No browser-side source of truth is introduced for business data.
- **Testing/quality**: PASS. Design requires targeted agency-app route/component coverage, browser smoke checks, and backend regression only where the employee-onboarding contract changes.
