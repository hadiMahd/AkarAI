# Feature Specification: User App Core UI Without AI

**Feature Branch**: `006-user-app-core-ui-without-ai`

**Created**: 2026-06-09

**Status**: Ready for Implementation

**Input**: User description: "phase 5 in 006-user-app-core-ui-without-ai"

## Clarifications

### Session 2026-06-09

- Q: Should Phase 5 user pages stay public, or should the platform be available only to signed-in users? → A: All Phase 5 user pages require sign-in.
- Q: If all Phase 5 pages require sign-in, how do users enter the app? → A: Start with a landing page that offers sign in and sign up.
- Q: Should listing comparison persist to the signed-in user's account or remain temporary? → A: Comparison is temporary for the current session only.

### Session 2026-06-10

- Q: Does Phase 5 include working sign-in and sign-up pages? → A: Yes, Phase 5 includes working sign-in and sign-up pages.
- Q: Does the Phase 5 profile page include only activity tabs, or also basic account fields? → A: Profile includes activity tabs only in Phase 5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Listings Manually (Priority: P1)

Signed-in property seekers need a user-facing browsing experience that begins after a public landing page with working sign-in and sign-up entry points, then continues into a homepage manual search, filtered listing results, sorting, pagination, and save or compare actions without any AI assistance.

**Why this priority**: Manual browse is the first usable user journey in the app and the base for all later user-side search and conversion flows.

**Independent Test**: Can be tested by opening the homepage, entering manual filters, viewing listing results, changing sort order, paging through results, saving a listing, and adding listings to comparison.

**Acceptance Scenarios**:

1. **Given** active listings exist and the user is signed in, **When** they enter manual search filters from the homepage, **Then** the listings page opens with matching results, active filters, sorting controls, and pagination.
2. **Given** a signed-in user is viewing a listings page, **When** they change sort order or move to another page, **Then** the result set updates without losing the selected filters.
3. **Given** a signed-in user selects listings to save or compare, **When** they perform those actions, **Then** the interface reflects the saved state and a temporary comparison selection up to the allowed limit for the current session.

---

### User Story 2 - Review a Listing and Submit Interest (Priority: P2)

Signed-in property seekers need a listing detail page where they can review the listing, see core agency-facing information that is safe to expose publicly, submit a standard inquiry, and manually book a viewing from available slots.

**Why this priority**: Browsing alone is incomplete; the user app must let interested users convert listing interest into a lead or scheduled viewing.

**Independent Test**: Can be tested by opening a listing detail page, submitting an inquiry, selecting an available viewing slot, and confirming that the booking appears in the user account area.

**Acceptance Scenarios**:

1. **Given** a signed-in user opens an available listing detail page, **When** they review the listing, **Then** they can see listing details, media metadata, and available manual actions without any chatbot or AI widget.
2. **Given** a signed-in user wants more information, **When** they submit the inquiry form, **Then** the request is accepted as a structured inquiry and the user sees a clear success or failure state.
3. **Given** a listing has available viewing slots and the user is signed in, **When** they book a viewing manually, **Then** the booking completes only for a valid slot and the user sees the scheduled viewing reflected in their account area.

---

### User Story 3 - Track Personal Activity (Priority: P3)

Signed-in users need a profile workspace where they can review saved listings, submitted inquiries, and scheduled viewings in one place, without expanding into account-settings editing in this phase.

**Why this priority**: After browse and conversion flows exist, users need a reliable way to return to their saved and submitted activity.

**Independent Test**: Can be tested by signing in as a user with existing saved listings, inquiries, and scheduled viewings and confirming each tab shows only that user's records.

**Acceptance Scenarios**:

1. **Given** a signed-in user has saved listings, **When** they open the profile page, **Then** the saved listings tab shows only their saved items with links back to listing details.
2. **Given** a signed-in user has submitted inquiries, **When** they open the profile page, **Then** the submitted inquiries tab shows only their own inquiry history.
3. **Given** a signed-in user has scheduled viewings, **When** they open the profile page, **Then** the scheduled viewings tab shows only their own scheduled viewings and current status.

### Edge Cases

- Homepage manual search must handle empty-result searches without breaking the browsing flow.
- Listings page filters, sorting, and pagination must remain synchronized when a user refreshes or shares the current page URL.
- Comparison selection must reject attempts to add more than four listings.
- Comparison selections must clear at the end of the current session and must not reappear automatically in a later session.
- Saving the same listing more than once must not create duplicate saved states in the UI.
- The listing detail page must handle inactive, removed, or inaccessible listings with a clear unavailable state.
- Inquiry submission must fail cleanly when required fields are missing or the listing is no longer eligible for inquiries.
- Viewing booking must fail cleanly when the selected slot becomes unavailable, expires, or belongs to another listing.
- The landing page must remain limited to entry actions and must not expose signed-in app content before authentication.
- Sign-in and sign-up routes must complete the user entry flow successfully before protected Phase 5 pages become accessible.
- Unauthenticated access to homepage, listings, listing detail, comparison, or profile routes must be blocked consistently because the Phase 5 user platform is signed-in only.
- The Phase 5 profile area must stay limited to activity tabs and must not expand into editable account-settings flows in this phase.
- Profile tabs must require authentication and must never expose another user's saved listings, inquiries, or scheduled viewings.
- Slow page loads or slow actions must show a visible loading state on homepage search, listings, listing detail, comparison, and profile screens.
- This phase must not surface AI search, voice search, a listings page chatbot, or any match score indicator.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a public landing page that offers working sign-in and sign-up entry points to the Phase 5 user platform.
- **FR-002**: System MUST provide working sign-in and sign-up pages or flows that allow users to enter the protected Phase 5 app.
- **FR-003**: System MUST provide a signed-in user homepage with manual listing search as the primary action after authentication.
- **FR-004**: System MUST allow signed-in users to enter manual search criteria from the homepage and navigate to a listings results page.
- **FR-005**: System MUST provide a signed-in listings page that shows public listing cards with pagination, filtering, and sorting controls.
- **FR-006**: System MUST preserve active manual search criteria, sort order, and pagination state while the user navigates within listing results.
- **FR-007**: System MUST support the same manual listing filters already available in the core domain foundation for this phase's browse UI.
- **FR-008**: System MUST support the same listing sort options already available in the core domain foundation for this phase's browse UI.
- **FR-009**: System MUST allow signed-in users to open a listing detail page from a listing card or any other listing summary entry point.
- **FR-010**: System MUST show only public-safe listing and agency information in the user app and MUST NOT expose agency-internal fields.
- **FR-011**: System MUST allow signed-in users to save and unsave listings from listing results and listing detail views.
- **FR-012**: System MUST visually indicate saved state for listings that the signed-in user has already saved.
- **FR-013**: System MUST allow signed-in users to select listings for comparison during the current session only and MUST enforce a maximum of four listings in one comparison set.
- **FR-014**: System MUST provide a signed-in comparison page with a basic table view of the current session's selected listings' public attributes.
- **FR-015**: System MUST allow signed-in users to remove individual listings from the comparison set.
- **FR-016**: System MUST provide a listing detail page that includes a standard inquiry form without chatbot, generated replies, or AI assistance.
- **FR-017**: System MUST allow signed-in users to submit a standard inquiry from the listing detail page and receive a clear success or failure response.
- **FR-018**: System MUST provide a manual viewing booking flow from the listing detail page using available viewing slots only.
- **FR-019**: System MUST allow signed-in users to confirm a viewing booking and receive a clear success or failure response.
- **FR-020**: System MUST provide a user profile page that includes separate views for saved listings, submitted inquiries, and scheduled viewings only in this phase.
- **FR-021**: System MUST show only the signed-in user's own saved listings, submitted inquiries, and scheduled viewings in the profile area.
- **FR-022**: System MUST provide navigation paths between the signed-in homepage, listings, listing detail, comparison, and profile screens.
- **FR-023**: System MUST display visible loading states for homepage search, listings results, listing detail, comparison, and profile screens while data is loading.
- **FR-024**: System MUST handle empty, unavailable, unauthorized, and failed-request states with clear user-facing feedback.
- **FR-025**: System MUST require authentication for access to all Phase 5 user pages other than the landing page, including homepage, listings, listing detail, comparison, and profile areas.
- **FR-026**: System MUST respect the existing rate-limited backend behaviors for manual search, inquiry submission, and viewing booking by presenting a clear failure state when those actions are temporarily rejected.
- **FR-027**: System MUST NOT include AI search, voice search, microphone input, a listings page chatbot, a listing AI widget, or match score in this phase.
- **FR-028**: System MUST NOT include buyer-to-agency real-time chat in this phase.

### Key Entities *(include if feature involves data)*

- **Manual Search Criteria**: The user-selected browse inputs used to retrieve filtered listing results.
- **Listing Card**: A public listing summary presented in browse results and selection workflows such as save and compare.
- **Comparison Set**: The current session's temporary group of up to four listings shown side by side for manual review.
- **Inquiry Submission**: A user's standard non-AI request for more information about a listing.
- **Viewing Booking Request**: A user's manual selection of an available viewing slot for a listing.
- **User Activity Workspace**: The signed-in user's personal view of saved listings, submitted inquiries, and scheduled viewings.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This phase covers user-facing manual browse, listing review, inquiry submission, viewing booking, and personal activity review. It does not add buyer-to-agency real-time chat. Inquiries remain structured lead creation, and viewing bookings remain scheduled viewings rather than leads.
- **Tenant/RBAC Impact**: The main actor is the User role. The landing page is public only for sign in and sign up entry, and all other Phase 5 user pages require sign-in. Browse surfaces must expose only public-safe data. Saved listings, submitted inquiries, and scheduled viewings must remain scoped to the signed-in user only.
- **AI/RAG Scope**: This phase explicitly excludes AI search, voice search, listing AI, area RAG, agency policy RAG, OCR, generated replies, and provider-specific AI behavior.
- **Reliability/Security/Performance**: Save listing, inquiry submission, and viewing booking require authentication. Browse results and profile lists remain paginated. The UI must handle rate-limited failures for manual search, inquiry submission, and viewing booking. Loading states are required on all primary user screens.
- **Unknowns to Clarify**: Business scope is fully clarified. The React UI library choice has been explicitly confirmed as `shadcn/ui`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Signed-in users can complete a manual browse flow from homepage search to listing results and open a listing detail page in all tested primary scenarios.
- **SC-002**: Signed-in users can save listings, manage a temporary comparison set of up to four listings during the current session, and see those states reflected consistently across browse and detail views.
- **SC-003**: Signed-in users can submit a listing inquiry and manually book a viewing from a valid slot, with each action returning a clear completion or failure state.
- **SC-004**: Signed-in users can open the profile area and review their saved listings, submitted inquiries, and scheduled viewings without seeing another user's data in any tested scenario.
- **SC-005**: All primary user screens in this phase show a visible loading state before data is ready and show a clear empty or failure state when applicable.
- **SC-006**: The delivered Phase 5 user app contains no AI search, voice search, chatbot, listing AI widget, or match score behavior.

## Assumptions

- Existing core domain backend capabilities for listings, saved listings, comparisons, inquiries, viewing slots, and scheduled viewings are available for the user app to consume.
- Existing authentication from earlier phases is reused for all signed-in user actions in this phase.
- Access to the Phase 5 user platform begins only after successful sign-in.
- Phase 5 includes the working user auth entry screens needed to reach the protected app.
- Comparison behavior in this phase is session-scoped and does not persist across separate sign-in sessions.
- The profile surface in this phase is limited to activity review tabs rather than account-settings management.
- Homepage featured listings and agency cards may be shown when supporting data is available, but the required browse flow for this phase is manual search first.
- Inquiry submission in this phase is a standard form flow only and does not include generated suggestions, automated classification output, or conversational behavior.
- Mobile-responsive behavior is expected for the user app, but this phase focuses on core browsing and account workflows rather than advanced visual polish.
