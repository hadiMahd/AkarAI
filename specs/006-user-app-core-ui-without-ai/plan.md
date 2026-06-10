# Implementation Plan: User App Core UI Without AI

**Branch**: `006-user-app-core-ui-without-ai` | **Date**: 2026-06-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-user-app-core-ui-without-ai/spec.md`, root [PLAN.md](../../PLAN.md), project constitution, and completed Phase 1-4 foundations.

## Summary

Implement Phase 5 as the first real user-facing app slice on top of the completed backend foundation. This phase delivers a public landing page with working sign-in and sign-up entry flows, then a protected React user app with homepage manual search, listings results, listing detail, save listing, session-only comparison, inquiry submission, manual viewing booking, and a profile area limited to saved listings, submitted inquiries, and scheduled viewings.

The primary implementation surface is `apps/user`, but Phase 5 also needs small supporting backend additions where the current API surface is incomplete for the agreed UI scope: user registration, user-owned inquiry history, and user-visible available viewing slots for listing detail. Phase 5 explicitly excludes AI search, voice search, microphone input, chatbots, listing AI widgets, match score, buyer-to-agency real-time chat, editable profile/account settings, and any agency/admin dashboard work.

## Technical Context

**Language/Version**: TypeScript 5.5 with React 18.3 for the user app; Python 3.11 for required backend support endpoints.

**Primary Dependencies**: React, React DOM, Vite, `react-router-dom` for route orchestration, `@tanstack/react-query` for server-state fetch/caching/invalidation, `shadcn/ui` for app UI building blocks, FastAPI auth/listings/leads/viewings endpoints, pytest for backend regression coverage, Vitest plus React Testing Library for user-app route/component/state tests.

**Storage**: PostgreSQL remains the source of truth for auth sessions, listings, saved listings, inquiries, and scheduled viewings. Browser `sessionStorage` holds the temporary signed-in comparison selection for the current browser session only. Access/refresh tokens follow the existing backend auth flow.

**Testing**: User-app unit/component tests for route guards, auth entry flows, search/filter state, session-only comparison behavior, inquiry/viewing form flows, and profile tabs; backend integration tests for registration, user-owned inquiry history, and public listing-slot read support; smoke validation for Docker Compose startup, auth flow, manual search flow, save flow, inquiry flow, booking flow, and profile activity flow.

**Target Platform**: Local Docker Compose development on the existing `user-app` service at `http://localhost:3000`, backed by the existing FastAPI service at `http://localhost:8000`. Production hosting remains outside this phase.

**Project Type**: Modular monolith web platform with a React user app and a FastAPI backend.

**Performance Goals**: Protected route shells and loading states should appear immediately on navigation; first-page listing/profile tab fetches should complete within about 1 second on a healthy local Docker stack; sign-in, sign-up, inquiry, and viewing-booking submissions should return a success or failure state within about 2 seconds locally; all list views remain paginated; these local responsiveness goals must be validated during Phase 5 polish.

**Constraints**: No buyer-to-agency real-time chat; no AI search, voice search, microphone input, listing AI, area/policy RAG, match score, or account-settings editing; protect all Phase 5 user pages except the landing page; comparison remains current-session only; use `repository.py`, not `dao.py`; all secrets remain Vault-backed through existing config; Phase 5 UI implementation must use the user-confirmed `shadcn/ui` component approach.

**Scale/Scope**: Phase 5 covers only the user app and the minimum backend support required for that UI to work end-to-end. Agency app, admin app, media pipeline, RAG, AI workflows, notifications delivery, and later analytics stay out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Fixed stack**: PASS. Uses the required React + TypeScript user app and existing FastAPI backend. The previously unresolved React UI library has now been explicitly confirmed as `shadcn/ui` per the constitution.
- **Architecture**: PASS. Preserves the modular monolith. Backend support stays within existing `auth`, `leads`, and `viewings` modules using `router.py`, `service.py`, `repository.py`, and `schemas.py`.
- **Product boundaries**: PASS. No buyer-to-agency real-time chat. Inquiries remain structured leads. Viewing booking remains scheduled viewing creation. AI and match-score flows stay excluded.
- **Tenant/RBAC**: PASS. User-facing pages require authentication after landing/auth entry. Saved listings, inquiries, and scheduled viewings remain user-scoped. Public-safe listing data only is exposed in the user app.
- **RAG/search**: PASS. Manual search only. No AI search, voice search, area RAG, or agency policy RAG.
- **Reliability/security/performance**: PASS. Existing JWT auth, refresh flow, and rate-limited inquiry/booking/search behaviors remain in force. Loading states, paginated lists, and fail-closed protected routing are planned explicitly.
- **Testing/quality**: PASS. Includes frontend component/smoke coverage and backend regression tests for any new support endpoints.

## Project Structure

### Documentation (this feature)

```text
specs/006-user-app-core-ui-without-ai/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/
└── user/
    ├── src/
    │   ├── app/
    │   │   ├── router.tsx
    │   │   ├── providers.tsx
    │   │   └── guards.tsx
    │   ├── pages/
    │   │   ├── landing/
    │   │   ├── auth/
    │   │   ├── home/
    │   │   ├── listings/
    │   │   ├── listing-detail/
    │   │   ├── comparison/
    │   │   └── profile/
    │   ├── features/
    │   │   ├── auth/
    │   │   ├── search/
    │   │   ├── listings/
    │   │   ├── saved-listings/
    │   │   ├── comparison/
    │   │   ├── inquiries/
    │   │   ├── viewings/
    │   │   └── profile/
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
│   ├── auth/
│   ├── leads/
│   ├── listings/
│   ├── viewings/
│   └── common/
└── tests/
    ├── integration/
    └── unit/
```

**Structure Decision**: `apps/user` is the primary implementation surface. The app should grow from the current Vite skeleton into route-based pages, feature modules, and shared UI primitives built with `shadcn/ui`. Backend work stays minimal and only covers gaps that block agreed user flows: user registration in `backend/app/auth`, user-owned inquiry history in `backend/app/leads`, and user-visible available viewing-slot reads in `backend/app/viewings`. Existing `listings`, `saved-listings`, `viewings`, and `auth/me` endpoints remain the main integration surface.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research Summary

See [research.md](./research.md). Decisions cover route structure, the `shadcn/ui` component approach, data-fetching/state choices, session-only comparison handling, and the minimal backend support needed for working sign-up, inquiry history, and listing-slot browse support.

## Phase 1 Design Summary

- Data model: [data-model.md](./data-model.md)
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Fixed stack**: PASS. Final design stays on React + TypeScript in `apps/user` and FastAPI in existing backend modules, and the React UI library choice is now explicitly resolved as `shadcn/ui`.
- **Architecture**: PASS. Route/UI work stays in `apps/user`; backend support stays in existing feature modules and keeps `repository.py` as the data layer.
- **Product boundaries**: PASS. The design includes landing/auth/manual browse/save/inquiry/booking/profile only. No AI, no match score, no chat, and no account-settings expansion.
- **Tenant/RBAC**: PASS. Landing/auth are the only public routes. All app routes are protected. User-owned data remains scoped by the authenticated user, and listing data shown in the UI remains public-safe only.
- **RAG/search**: PASS. Manual search only, using existing filtered listing search endpoints. No AI/RAG additions.
- **Reliability/security/performance**: PASS. Existing auth/session handling, search/inquiry/booking rate limits, paginated lists, and explicit loading/error states are preserved. Session-only comparison is contained to browser session storage and does not create server-side persistence drift.
- **Testing/quality**: PASS. Design requires targeted frontend route/component coverage plus backend regression tests for any support endpoints added for Phase 5.
