# Architecture Decisions

## Phase 5: User App Core UI Without AI

**Date**: 2026-06-10  
**Status**: Implemented

### Context
Phase 5 delivers the first user-facing application slice: landing page, authentication, listing browse, listing detail with inquiry and viewing booking, and profile activity tabs.

### Decisions

#### 1. Frontend Stack
- **React 18** with **TypeScript** for type safety
- **Vite** for build tooling
- **shadcn/ui** for component library (Radix UI primitives + Tailwind CSS)
- **TanStack Query** for server state management
- **React Router** for routing with protected route guards

#### 2. Backend API Additions
Phase 5 added minimal backend support endpoints:
- `GET /listings/{id}/viewing-slots` - Public viewing slots for a listing (returns `PublicViewingSlotResponse` without internal fields)
- `GET /me/inquiries` - User's inquiry history
- Existing endpoints for save/unsave, inquiry submission, and viewing booking were already in place

#### 3. Session-Only Comparison
- Comparison state stored in browser `sessionStorage` only
- No backend persistence for comparison
- Maximum 4 listings per session
- Cleared on sign-out or session end

#### 4. Saved Listings
- Stored in browser `localStorage` for persistence across sessions
- Backend has `/me/saved-listings` endpoints but frontend uses local storage for Phase 5
- Allows offline browsing of saved listings

#### 5. Public vs Internal Data
- `PublicViewingSlotResponse` excludes `agency_tenant_id`, `created_by_user_id` from API responses
- Listing detail uses `PublicListingResponse` schema for public endpoints
- RLS policies enforce tenant isolation at database level

#### 6. Profile Scope
- Profile page limited to activity tabs only (saved listings, inquiries, viewings)
- No account settings or profile editing in Phase 5
- Each tab shows only the authenticated user's own data via RLS

### Rationale
These decisions support the Phase 5 goal of delivering a functional user app without AI features while maintaining security (RLS), performance (client-side state for comparison), and clear separation of concerns (repository pattern, no DAO files).
