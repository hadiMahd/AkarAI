# Implementation Plan: Listing Page User Agent

**Branch**: `[extra/002-listing-page-user-agent]`

## Summary

Add a listing-scoped AI widget to `ListingDetailPage` that answers questions about the current listing and prepares, but never directly executes, inquiry and viewing-booking actions. The implementation must run through backend-owned LangChain + Azure OpenAI orchestration with LangSmith tracing, keep transcript state session-only, and preserve the existing inquiry and booking forms as manual fallback paths.

## Scope

- add a compact assistant widget to `apps/user/src/pages/listing-detail/ListingDetailPage.tsx`
- answer listing-specific questions from current listing data only
- prepare confirmable inquiry payloads for the current listing
- prepare confirmable viewing-booking payloads by matching natural-language timing against current active slots
- reuse existing inquiry and viewing mutation APIs and their current validation rules
- emit backend-side LangSmith traces for assistant runs
- keep user transcript state session-only with no persisted backend chat thread
- keep profile identity details owned by the profile page instead of duplicating them across inquiry and viewing activity surfaces

## Non-Goals

- no buyer-to-agency real-time chat
- no autonomous send or booking without explicit button confirmation
- no broader marketplace assistant inside this widget
- no persistent backend chat threads in this phase
- no browser-side Azure or LangSmith calls
- no duplicate lead or viewing workflow outside the existing source-of-truth APIs

## Branch Outcome

This branch should produce a safe listing-page orchestration layer, not a separate messaging or workflow domain.

## Locked Product Decisions

- **Chat state**: Session-only. The client resends `conversation_messages` on each turn; the backend persists no thread rows.
- **Mutation confirmation**: Button-based only. Freeform messages such as "yes" do not trigger writes.
- **Placement**: The assistant is an additive widget on `ListingDetailPage` and does not replace `InquiryForm` or `BookingForm`.
- **Answer scope**: Listing facts and current active viewing slots for the current listing only.
- **Lead contact rule**: Keep the current backend source of truth: `name AND (email OR phone)`.
- **Identity handling**: Prepared inquiry and booking flows use available stored profile fields only and do not introduce duplicate identity dumps into activity screens.
- **Provider boundary**: The browser never calls Azure OpenAI, LangSmith, or other providers directly.

## Backend Plan

### Route Contract

- Add `POST /api/v1/listings/{listing_id}/assistant/messages`.
- Request body:
  - `message: string`
  - `conversation_messages: Array<{ role: "user" | "assistant"; content: string }>`
- Response body:
  - `assistant_message: string`
  - `pending_action: null | { type: "lead_inquiry" | "viewing_booking"; payload: object }`
  - `metadata?: object`

Example response:

```json
{
  "assistant_message": "I found one viewing slot tomorrow at 6:00 PM. Review it below before booking.",
  "pending_action": {
    "type": "viewing_booking",
    "payload": {
      "viewing_slot_id": "slot-uuid",
      "scheduled_start_at": "2026-06-19T18:00:00Z",
      "scheduled_end_at": "2026-06-19T18:30:00Z",
      "notes": "User asked for tomorrow after 5"
    }
  },
  "metadata": {
    "matched_slot_reason": "closest_active_slot"
  }
}
```

### Orchestration

- Implement a backend-owned LangChain assistant/orchestrator using Azure OpenAI chat models.
- Emit one LangSmith trace per assistant run with listing ID, actor ID, and non-sensitive tool metadata.
- Keep the tool set constrained to:
  - get current listing context
  - get current active viewing slots
  - prepare inquiry action
  - prepare viewing action
- Enforce a hard guardrail that assistant code prepares payloads only and never writes leads or scheduled viewings directly.
- Reuse existing `app.ai` provider indirection, safety defaults, and audit patterns where possible.

### Data and Validation Boundaries

- Listing context comes from the current listing only.
- Viewing availability comes from the existing public active-slot source for that listing only.
- Inquiry confirmation still relies on the existing lead profile rule from `UsersService`.
- Booking confirmation still relies on the existing availability and conflict handling in `ViewingBookingService`.
- No backend chat-thread model, migration, or transcript persistence is added in this phase.

## Frontend Plan

- Add a compact assistant widget beside the existing listing actions and forms on `ListingDetailPage`.
- Keep `InquiryForm` and `BookingForm` visible and fully functional as fallback flows.
- Store transcript state in-session only on the client for the current listing.
- Render assistant messages inline in the widget transcript.
- When `pending_action` is returned, show a structured confirmation card:
  - inquiry card with prepared message preview
  - booking card with matched slot time and optional notes
- Confirm button calls the existing mutation hooks.
- Cancel button clears only the prepared action and keeps the transcript visible.

## Booking Behavior

- The assistant can interpret natural-language requests such as "tomorrow after 5", "this weekend morning", or "next Tuesday around noon".
- The backend matches that request against real active slots for the current listing.
- If one or more matches exist, return the best valid proposal plus lightweight reasoning metadata.
- If no match exists, return a clean retry message instead of inventing a slot.
- The user still confirms explicitly before the existing booking mutation runs.

## Profile and Auth Behavior

- Unauthenticated users may open the widget and ask factual listing questions, but any inquiry or booking preparation that requires a mutation path must route them to sign-in before confirmation.
- Incomplete profiles block inquiry confirmation and route the user to `/profile`.
- Existing inquiry and viewing activity screens should not be expanded to repeat stored identity details that already belong to the profile page.

## Testing Plan

- Listing fact Q&A succeeds for the current listing only.
- Inquiry preparation returns a confirmable action, and the existing inquiry API succeeds after confirmation.
- A request such as "tomorrow evening" maps to a valid slot when one exists.
- An unavailable-slot case returns a clean retry path.
- Unauthenticated users are blocked cleanly from mutation flows.
- Incomplete-profile users are blocked cleanly from inquiry confirmation and routed to `/profile`.
- Canceling a prepared action does not mutate anything.
- LangSmith tracing is emitted for assistant runs.
