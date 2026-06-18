# Feature Specification: Listing Page User Agent

**Feature Branch**: `extra/002-listing-page-user-agent`

**Created**: 2026-06-18

**Status**: Draft

**Input**: Revision plan for `extra-specs/002-listing-page-user-agent`

## User Scenarios & Testing

### User Story 1 - Ask Listing Questions In Place (Priority: P1)

A signed-in user opens a public listing detail page and uses a compact assistant widget to ask questions about that listing without leaving the page or opening a separate support workflow.

**Why this priority**: Listing-specific Q&A is the minimum useful assistant behavior and anchors the widget to one listing instead of a broad marketplace chatbot.

**Independent Test**: Open one active listing, ask factual questions about price, purpose, property attributes, and viewing availability, and verify that answers stay grounded in that listing only.

**Acceptance Scenarios**:

1. **Given** a signed-in user is on `ListingDetailPage`, **When** the user asks a factual question about the current listing, **Then** the assistant answers from the current listing data only.
2. **Given** the user asks about another listing, neighborhood recommendations, or general marketplace advice, **When** the question exceeds the listing scope, **Then** the assistant declines or redirects without inventing unsupported answers.
3. **Given** the listing has active viewing slots, **When** the user asks about availability, **Then** the assistant may summarize the active slots for that listing without booking anything.

---

### User Story 2 - Prepare a Confirmable Inquiry (Priority: P1)

A signed-in user asks the widget to help contact the agency about the current listing, reviews a prepared inquiry draft, and explicitly confirms the send action through the existing inquiry API flow.

**Why this priority**: Inquiry preparation is the first write-adjacent workflow and must prove that the assistant can help without becoming the source of truth for lead submission.

**Independent Test**: Ask the widget to prepare an inquiry, review the confirmation card, confirm it, and verify that the existing `/listings/{listing_id}/inquiries` flow succeeds only after the explicit button click.

**Acceptance Scenarios**:

1. **Given** the user is signed in and has a lead-complete profile, **When** the assistant prepares an inquiry, **Then** the UI shows a confirmation card and nothing is submitted until the user clicks confirm.
2. **Given** the user cancels a prepared inquiry, **When** the card is dismissed, **Then** no lead is created and the transcript remains visible for continued chat.
3. **Given** the user profile is missing `name` or both contact methods, **When** the assistant reaches inquiry preparation, **Then** the flow blocks cleanly and routes the user to `/profile`.

---

### User Story 3 - Prepare a Confirmable Viewing Booking (Priority: P1)

A signed-in user asks for a viewing in natural language such as "tomorrow after 5", reviews the best valid slot match returned by the backend, and explicitly confirms the booking through the existing viewing API flow.

**Why this priority**: Slot matching is the highest-risk orchestration step because the assistant must interpret free text while staying constrained to real slot inventory and explicit confirmation.

**Independent Test**: Ask for a viewing with natural language timing, inspect the returned matched-slot card, confirm it, and verify that the existing `/listings/{listing_id}/viewings` mutation is called only after the confirm button.

**Acceptance Scenarios**:

1. **Given** a listing has active viewing slots, **When** the user asks for "tomorrow evening" or a similar time window, **Then** the backend maps the request against real slots and returns the best valid proposal or a clean no-match response.
2. **Given** the assistant returns a valid slot proposal, **When** the user confirms it, **Then** the existing booking API creates the viewing and the assistant does not write directly.
3. **Given** the matched slot becomes unavailable before confirmation, **When** the user confirms anyway, **Then** the existing booking API returns its normal conflict error and the assistant surfaces a retry path.

### Edge Cases

- What happens when the user is not authenticated and asks the assistant to prepare an inquiry or booking?
- What happens when the user asks for broader buying advice, agency chat, negotiation help, or another listing comparison from inside the widget?
- What happens when no viewing slot matches the natural-language request?
- What happens when the listing is archived or inactive mid-session?
- What happens when the user cancels a prepared action after several transcript turns?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST add a compact listing-scoped assistant widget to `apps/user/src/pages/listing-detail/ListingDetailPage.tsx`.
- **FR-002**: The widget MUST keep the existing `InquiryForm` and `BookingForm` visible as manual fallback paths.
- **FR-003**: The widget MUST be listing-scoped and MUST answer from the current listing facts and current active viewing slots only.
- **FR-004**: The widget MUST support exactly three jobs in this phase: listing fact Q&A, inquiry preparation, and viewing-booking preparation.
- **FR-005**: The widget MUST NOT become a buyer-to-agency live chat surface.
- **FR-006**: The widget MUST NOT act as a broader marketplace assistant for search, recommendations, neighborhood advice, or cross-listing exploration.
- **FR-007**: Chat state MUST be session-only for this phase. The backend MUST NOT persist chat threads or transcript history.
- **FR-008**: The backend MUST expose a listing assistant route at `POST /api/v1/listings/{listing_id}/assistant/messages`.
- **FR-009**: The request body MUST accept the current user message plus `conversation_messages` so the client can resend session context on each turn.
- **FR-010**: The response body MUST return `assistant_message` and `pending_action`, where `pending_action` is either `null`, `lead_inquiry`, or `viewing_booking`.
- **FR-011**: Any prepared action MUST be confirmation-only. The assistant route MUST NEVER create leads or scheduled viewings directly.
- **FR-012**: Mutation confirmation MUST be button-based in the UI. Freeform messages such as "yes" MUST NOT trigger a mutation.
- **FR-013**: Inquiry confirmation MUST reuse the existing `POST /listings/{listing_id}/inquiries` API and its current validation rules.
- **FR-014**: Viewing confirmation MUST reuse the existing `POST /listings/{listing_id}/viewings` API and its current validation and availability rules.
- **FR-015**: The source-of-truth lead profile requirement MUST remain `name AND (email OR phone)`, matching the current backend `UsersService` validation rule.
- **FR-016**: Inquiry preparation MUST include available stored profile fields only and MUST NOT dump duplicate identity details into user-facing activity surfaces unless required by the existing source-of-truth APIs.
- **FR-017**: Unauthenticated users MUST be blocked from mutation flows and routed to sign-in before confirmable inquiry or booking actions can proceed.
- **FR-018**: Users with incomplete lead profiles MUST be blocked from inquiry confirmation and routed to `/profile`.
- **FR-019**: The browser MUST NOT call Azure OpenAI or LangSmith directly. All assistant orchestration, tool use, and provider calls MUST run through the backend.
- **FR-020**: The backend assistant implementation MUST use LangChain with Azure OpenAI and emit LangSmith traces for each assistant run.
- **FR-021**: The backend assistant tool set MUST be constrained to listing context lookup, active viewing-slot lookup, inquiry preparation, and viewing preparation for the current listing only.
- **FR-022**: Viewing preparation MUST map natural-language timing requests against real active slots and return either a best valid proposal or a clear no-match message.
- **FR-023**: Canceling a prepared action MUST clear only the pending action state and MUST NOT clear the transcript automatically.
- **FR-024**: Existing inquiry and viewing activity screens MUST avoid duplicating profile identity details that already belong to the profile page.

### Key Entities

- **Listing Assistant Session**: Client-managed transcript state for one listing page session with no backend thread persistence.
- **Listing Assistant Message**: One user or assistant turn sent through the listing assistant route.
- **Pending Assistant Action**: A structured proposal returned by the assistant route for either `lead_inquiry` or `viewing_booking`, requiring explicit UI confirmation.
- **Prepared Inquiry Payload**: A normalized, unsent payload that can be passed to the existing inquiry mutation only after confirmation.
- **Matched Viewing Proposal**: A normalized, unsent slot proposal mapped from natural language to one active viewing slot for the current listing.

### Constitution Alignment

- **Product Boundary**: This feature adds a listing-page widget only. It does not add live agency chat, autonomous actions, or a site-wide assistant.
- **Tenant/RBAC Impact**: The feature affects signed-in users on public listing routes and reuses existing listing, inquiry, and viewing authorization rules. No agency-side tenant tools are exposed to the browser.
- **AI/RAG Scope**: This feature uses AI orchestration for listing-page assistance only. It does not expand homepage AI search, agency support assistant scope, or persistent chat storage.
- **Reliability/Security/Performance**: The assistant remains backend-mediated, tool-constrained, traceable with LangSmith, and mutation-safe through explicit confirmation plus existing write APIs.
- **Unknowns to Clarify**: None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A signed-in user can get a listing-fact answer from the widget without leaving `ListingDetailPage`.
- **SC-002**: Inquiry and viewing mutations triggered from the assistant occur only after an explicit confirmation button click in 100% of validation scenarios.
- **SC-003**: Natural-language viewing requests return either one valid slot proposal or a clean no-match response without inventing availability.
- **SC-004**: Assistant runs emit LangSmith traces while the browser makes no direct provider calls.
- **SC-005**: Manual fallback paths through `InquiryForm` and `BookingForm` remain available even when the widget is unused or fails.

## Assumptions

- Existing listing detail, inquiry, booking, auth, and profile routes remain the source of truth for user-facing mutations and validation.
- The listing assistant route can be synchronous for this phase because it prepares actions rather than running long async jobs.
- The widget transcript is ephemeral to the current session and does not require server-side history, analytics, or resume behavior in this phase.
