# Data Model: User App Core UI Without AI

## Conventions

- Backend domain entities created in earlier phases remain the source of truth for listings, saved listings, leads, viewing slots, and scheduled viewings.
- Phase 5 adds UI-facing view models and browser-session state needed to render the user app consistently.
- Protected app routes require an authenticated user session; the landing page and auth entry flows are the only public surfaces.
- Comparison data is session-scoped only and must not persist across separate sign-in sessions.

## Entities

### AuthEntry

Purpose: Public landing-page entry state for accessing the protected user app.

Fields:
- `mode`: sign_in, sign_up
- `redirect_target`
- `is_authenticated`

Relationships:
- Leads into LoginSubmission or RegistrationSubmission.

Validation:
- Only landing/auth routes are accessible when unauthenticated.
- Authenticated users visiting landing/auth routes are redirected into the protected app.

### RegistrationSubmission

Purpose: Sign-up data submitted from the Phase 5 sign-up flow.

Fields:
- `name`
- `email`
- `phone`
- `password`
- `confirm_password`

Relationships:
- Creates one User account through the backend auth module.

Validation:
- Email must be syntactically valid.
- Password confirmation must match.
- Duplicate email must be rejected with a clear user-facing error.
- Successful sign-up returns the user to the agreed post-registration path without exposing protected pages prematurely.

### LoginSubmission

Purpose: Sign-in data submitted from the Phase 5 sign-in flow.

Fields:
- `email`
- `password`

Relationships:
- Creates or refreshes one UserSession.

Validation:
- Invalid credentials show a clear failure state.
- Successful sign-in stores the access/refresh tokens and redirects into the protected app.

### UserSession

Purpose: Authenticated browser session for the signed-in user.

Fields:
- `access_token`
- `refresh_token`
- `expires_in`
- `actor`
- `is_authenticated`

Relationships:
- Governs access to homepage, listings, listing detail, comparison, and profile routes.

Validation:
- Missing or expired auth redirects protected routes back to sign-in.
- Logout clears local session state and any session-scoped comparison state.

### SearchFilterState

Purpose: Manual search state that drives the homepage form and listings page.

Fields:
- `location`
- `min_price`
- `max_price`
- `bedrooms`
- `bathrooms`
- `property_type`
- `listing_purpose`
- `furnishing`
- `min_area_size`
- `max_area_size`
- `sort`
- `page`
- `page_size`

Relationships:
- Produces ListingSearchResult pages.

Validation:
- Query-string state must remain consistent on refresh and share.
- Invalid or partial filter values degrade gracefully to empty or default values.

### ListingSearchResult

Purpose: Paginated listing result returned to the signed-in user app.

Fields:
- `items`
- `page`
- `page_size`
- `total`
- `has_next`
- `has_previous`

Relationships:
- Contains many ListingSummary entries.

Validation:
- Only public-safe listing data is displayed.
- Empty results show an empty state instead of a broken page.

### ListingSummary

Purpose: Public-safe listing card data used in search results and saved listings.

Fields:
- `id`
- `title`
- `price`
- `currency`
- `location_text`
- `property_type`
- `listing_purpose`
- `bedrooms`
- `bathrooms`
- `area_size`
- `furnishing`
- `status`
- `primary_photo`
- `is_saved`

Relationships:
- Links to one ListingDetailView.

Validation:
- Only active listings appear in the user browse experience.
- Saved-state indicators reflect the signed-in user's backend saved-listing state.

### ListingDetailView

Purpose: Full listing page data required for review, saving, inquiry, and booking.

Fields:
- `listing`
- `photo_gallery`
- `available_viewing_slots`
- `save_state`
- `inquiry_enabled`
- `booking_enabled`

Relationships:
- References one ListingSummary, many AvailableViewingSlot records, and downstream InquiryDraft / ViewingBookingDraft actions.

Validation:
- Missing or inaccessible listings show an unavailable state.
- Agency-internal fields are never exposed.

### AvailableViewingSlot

Purpose: User-visible bookable viewing slot shown on listing detail.

Fields:
- `id`
- `listing_id`
- `starts_at`
- `ends_at`
- `capacity`
- `reserved_count`
- `status`

Relationships:
- Feeds one ViewingBookingDraft.

Validation:
- Only active, non-expired, still-bookable slots are exposed to the user app.
- Unavailable slots cannot be selected for booking.

### SavedListingState

Purpose: User-owned save/unsave state for one listing.

Fields:
- `listing_id`
- `is_saved`
- `saved_at`

Relationships:
- Links the signed-in user to one ListingSummary or ListingDetailView.

Validation:
- Duplicate save attempts must not create duplicate records.
- Save state must stay in sync across listings, detail, and profile saved-listings tab.

### ComparisonTrayState

Purpose: Session-scoped listing comparison selection.

Fields:
- `listing_ids`
- `items`
- `count`
- `last_updated_at`

Relationships:
- Contains up to four ListingSummary entries for the current browser session.

Validation:
- Maximum size is four listings.
- State persists across refreshes inside the current session only.
- State clears when the browser session ends or the user logs out.

### InquiryDraft

Purpose: User-entered inquiry payload for a listing.

Fields:
- `listing_id`
- `message`
- `contact_phone`

Relationships:
- Submits to one backend Lead record.

Validation:
- Required fields must be present before submit.
- Over-limit or invalid submits must return clear failure states without duplicate UI submission.

### SubmittedInquirySummary

Purpose: User-owned inquiry history entry shown in the profile activity tab.

Fields:
- `id`
- `listing_id`
- `listing_title`
- `agency_name`
- `status`
- `submitted_at`

Relationships:
- Belongs to one signed-in user.

Validation:
- Only the owner can view their inquiry history.
- The tab remains activity-only and does not allow lead-management actions.

### ViewingBookingDraft

Purpose: Pending booking submission for a selected viewing slot.

Fields:
- `listing_id`
- `viewing_slot_id`
- `notes`

Relationships:
- Creates one ScheduledViewingSummary on success.

Validation:
- Selected slot must still be valid at submit time.
- Failed bookings must leave the UI in a recoverable state.

### ScheduledViewingSummary

Purpose: User-owned scheduled-viewing data shown after booking and in the profile tab.

Fields:
- `id`
- `listing_id`
- `listing_title`
- `scheduled_start_at`
- `scheduled_end_at`
- `status`
- `created_at`

Relationships:
- Belongs to one signed-in user.

Validation:
- Only the owner can view their scheduled viewings.
- Status reflects backend truth and is read-only in Phase 5.

### ProfileActivityWorkspace

Purpose: Profile page state for the three agreed Phase 5 activity tabs.

Fields:
- `active_tab`: saved_listings, submitted_inquiries, scheduled_viewings
- `saved_listings_result`
- `submitted_inquiries_result`
- `scheduled_viewings_result`

Relationships:
- Aggregates SavedListingState, SubmittedInquirySummary, and ScheduledViewingSummary.

Validation:
- Phase 5 profile scope stops at activity review.
- No editable account-settings fields are part of this workspace in this phase.
