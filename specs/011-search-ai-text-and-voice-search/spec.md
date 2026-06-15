# Feature Specification: Search, AI Text Search, and Voice Search

**Feature Branch**: `011-search-ai-text-and-voice-search`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Phase 10 from PLAN.md: Search, AI Text Search, and Voice Search. Build it with production-grade search contracts, provider boundaries, logs, rate limits, RLS where needed, and no e2e scope."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search Listings With Reliable Filters (Priority: P1)

Users need to search available listings using clear filters and receive results that match the filters they applied.

**Why this priority**: Manual search is the source of truth for all search flows. AI text and voice search must end by producing the same kind of confirmed filter set used by manual search.

**Independent Test**: A user applies filters for location, price, purpose, property type, bedrooms, bathrooms, parking, floor, furnished status, and area size, then verifies the results match the applied filters and can be sorted or paginated without losing the filter state.

**Acceptance Scenarios**:

1. **Given** active listings exist across multiple locations and prices, **When** a user searches with specific filters, **Then** the results include only matching active listings.
2. **Given** a user changes sort order after searching, **When** the results reload, **Then** the same filters remain applied and only ordering changes.
3. **Given** a user navigates between result pages, **When** the next page loads, **Then** the filter and sort state remain consistent.

---

### User Story 2 - Convert Natural Language Into Confirmed Search Filters (Priority: P2)

Users need to describe what they want in natural language, review the interpreted filters, edit them if needed, and then run a normal listing search.

**Why this priority**: AI text search improves discovery, but user confirmation prevents incorrect or surprising searches.

**Independent Test**: A user enters a query such as "3 bedroom apartment for rent in Beirut under 1200 with parking", reviews the interpreted filters, edits one value, confirms, and verifies the final results use the confirmed values rather than the original unedited interpretation.

**Acceptance Scenarios**:

1. **Given** a user enters a natural-language search request, **When** the system interprets it, **Then** the user sees editable filters before results are applied.
2. **Given** the interpreted filters are partially wrong, **When** the user edits the confirmation panel, **Then** the final search uses the user's edited filters.
3. **Given** the request contains unsupported or ambiguous preferences, **When** filters are interpreted, **Then** unsupported parts are shown as unconfirmed notes instead of silently affecting results.

---

### User Story 3 - Keep Unclear Locations Reviewable (Priority: P3)

Users need vague location phrases such as "near Beirut" or "calm area close to Beirut" to be surfaced as unclear location intent so they can choose concrete locations manually before search.

**Why this priority**: Lebanese real-estate search often starts with rough area intent rather than exact city names. Since area expansion is excluded from this phase, unclear location intent must not silently become hidden filters.

**Independent Test**: A user enters a vague location query, sees that the location needs manual selection, chooses concrete locations, and verifies the final listing results use only the confirmed locations.

**Acceptance Scenarios**:

1. **Given** a user searches for a vague area, **When** the search intent is interpreted, **Then** the confirmation panel marks location as needing manual selection.
2. **Given** a user selects concrete locations after an unclear location request, **When** they confirm search, **Then** only the selected locations are used in final results.
3. **Given** a user does not resolve unclear location intent, **When** they confirm the search, **Then** the system lets them proceed without a location filter and makes that outcome visible in the confirmation state.

---

### User Story 4 - Search by Voice (Priority: P4)

Users need to speak into the microphone, have their spoken request transcribed, review the extracted property features, edit them if needed, and run the same confirmed listing search flow used by AI text search.

**Why this priority**: Voice search should reuse the same confirmation and filter logic as text search so it does not become a separate, inconsistent search path.

**Independent Test**: A user records a voice search, sees the transcript, reviews extracted property features, corrects any transcription or filter mistakes, confirms, and receives matching listing results.

**Acceptance Scenarios**:

1. **Given** a user records a clear search request, **When** transcription succeeds, **Then** the transcript and extracted property features are shown for confirmation.
2. **Given** transcription or extraction is partially wrong, **When** the user edits the confirmation panel, **Then** the final search uses the corrected values.
3. **Given** voice search is unavailable, rate-limited, or cannot understand the recording, **When** the user attempts to search by voice, **Then** the user receives a clear recovery path without losing current search state.

### Edge Cases

- A natural-language query includes both rental and sale intent.
- A voice transcript contains wrong city names or missing numbers.
- A user asks for unsupported preferences such as "best match", "luxury vibe", or personal profiling.
- A vague area request cannot be converted to concrete locations in this phase.
- No listings match the confirmed filters.
- The AI interpretation service is unavailable or returns low-confidence filters.
- Speech-to-text is unavailable, times out, or returns an empty transcript.
- A user repeatedly submits AI or voice searches beyond allowed limits.
- Search logs must not store raw secrets or unnecessary personal data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to run listing searches using explicit filters for purpose, property type, location, price range, bedrooms, bathrooms, parking, floor, furnished status, and area size.
- **FR-002**: Search results MUST include only listings that are active and publicly viewable.
- **FR-003**: Search results MUST preserve filter and sort state while users paginate or change ordering.
- **FR-004**: Users MUST be able to enter natural-language search requests and receive an editable confirmation panel before results are applied.
- **FR-005**: The confirmation panel MUST show interpreted filters, omitted unsupported criteria, and any fields that need user confirmation.
- **FR-006**: The final search MUST use only the confirmed filter object, including user edits made after interpretation.
- **FR-007**: The same confirmed filter object MUST be usable by manual search, AI text search, and voice search.
- **FR-008**: The system MUST log manual searches, AI text interpretations, voice transcriptions, confirmation edits, final applied filters, fallback outcomes, and rate-limit outcomes.
- **FR-009**: Search logs MUST avoid unnecessary personal data and MUST redact secrets or personal data where they may appear in user-provided search text.
- **FR-010**: AI search requests MUST be rate-limited separately from ordinary manual search.
- **FR-011**: Voice search requests MUST be rate-limited separately from AI text search.
- **FR-012**: The system MUST handle AI interpretation failure by letting the user continue with manual filters or edit the raw query.
- **FR-013**: Voice search MUST let users record from a microphone and convert the recording into visible transcript text.
- **FR-014**: Voice search MUST show the transcript and extracted property features before applying interpreted filters.
- **FR-015**: The system MUST NOT introduce buyer-to-agency real-time chat, listing match scores, renter personality profiling, or AI-generated agency replies in this phase.
- **FR-016**: Area expansion MUST be excluded from this phase; vague locations MUST be surfaced for manual user selection rather than expanded automatically, and unresolved vague locations MAY proceed as searches with no location filter.
- **FR-017**: Voice search MUST let the user edit or discard the transcript before confirmation.
- **FR-018**: Spoken or text-to-speech result summaries MUST NOT be included in this phase.

### Key Entities *(include if feature involves data)*

- **Search Intent**: A normalized representation of the user's desired search, including extracted filters, unsupported criteria, confidence, source mode, and fields needing confirmation.
- **Confirmed Search Filters**: The user-approved filter set used to fetch final listing results.
- **Unclear Location Intent**: A vague or unsupported location phrase that requires the user to choose concrete locations manually before final search.
- **Voice Search Transcript**: The user-visible transcript generated from a voice recording before filter confirmation.
- **Search Log**: A privacy-safe audit record covering search mode, interpreted intent, confirmation edits, final filters, fallback outcomes, and rate-limit outcomes.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature affects homepage/listing search only. It must not add buyer-to-agency real-time chat, listing match scores, AI persona profiling, generated replies, inquiry creation, or viewing booking.
- **Tenant/RBAC Impact**: Public listing search must expose only public active listing data. Any platform-owned area knowledge must remain separate from agency tenant policy documents. Search logs must be scoped so they do not leak agency-private or user-private data.
- **AI/RAG Scope**: This feature covers AI text search and voice search feature extraction. It excludes automatic area expansion and must keep future area search knowledge separate from agency policy RAG.
- **Reliability/Security/Performance**: Search must use bounded result sets, preserve pagination, apply rate limits for AI and voice requests, redact sensitive text in logs, and avoid storing raw secrets or unnecessary personal data.
- **Unknowns to Clarify**: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of manual search flows preserve the selected filters across sorting, pagination, and reloads until the user changes or resets them.
- **SC-002**: 100% of AI text search attempts return either a confirmation-ready filter set or a clear fallback path without applying unconfirmed filters.
- **SC-003**: 100% of AI text and voice-derived search flows require user confirmation before final results are applied.
- **SC-004**: 100% of final searches use the same confirmed filter structure regardless of whether the flow began as manual, AI text, or voice.
- **SC-005**: 100% of rate-limited AI or voice requests return a clear user-facing recovery message without losing current search state.
- **SC-006**: 100% of search logs used for validation avoid raw secrets and unnecessary personal data.
- **SC-007**: 100% of successful voice search attempts produce an editable transcript and a confirmation flow before any search results are applied, while failed attempts return a clear recovery path.

## Assumptions

- Existing listing data, public listing search, pagination, sorting, and image availability remain the result source.
- Existing authentication and session behavior remain unchanged.
- No e2e browser automation is included in this specification; validation will use unit, service, integration, and component-level coverage for this phase.
- The AI text and voice flows must end in ordinary listing search, not a chatbot answer.
- Users can always fall back to manual filter editing when AI interpretation, unclear location handling, or voice transcription is unavailable.
- Spoken result summaries are excluded from this phase.
- Search logs are for product quality, troubleshooting, and abuse prevention, not for profiling users.
