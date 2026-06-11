# Data Model: Agency Dashboard Core UI Without AI

## Conventions

- Backend domain entities created in earlier phases remain the source of truth for agency profile, employee memberships, listings, viewing slots, leads, reviewed-lead records, and scheduled viewings.
- Phase 6 adds UI-facing view models and one minimal employee-onboarding contract adjustment needed to support the agreed existing-account-by-email flow.
- Authenticated agency routes require a tenant-scoped session with a role of either `agency_admin` or `support_employee`.
- No browser storage becomes the source of truth for operational agency data.

## Entities

### AgencyDashboardSession

Purpose: Protected session state for an authenticated agency user inside the agency app.

Fields:
- `user_id`
- `tenant_id`
- `membership_id`
- `role_slug`
- `permissions`
- `is_authenticated`

Relationships:
- Governs access to every protected agency route.

Validation:
- Missing or expired auth redirects to sign-in.
- Users without a valid agency membership cannot enter the dashboard.
- Role checks must drive both route access and visible navigation.

### AgencySummaryCardSet

Purpose: Dashboard headline counts shown on the main agency home screen.

Fields:
- `listings_total`
- `active_leads_total`
- `reviewed_leads_total`
- `scheduled_viewings_total`

Relationships:
- Composed from existing listings, leads, reviewed-lead, and viewing totals.

Validation:
- Counts must represent the signed-in tenant only.
- Empty tenants still render zero-value cards instead of blank content.

### AgencyProfileForm

Purpose: Admin-only editable profile state for the agency settings page.

Fields:
- `display_name`
- `legal_name`
- `description`
- `phone`
- `email`
- `website_url`
- `address`
- `city`
- `country`
- `status`

Relationships:
- Reads and updates one Agency Profile record for the active tenant.

Validation:
- Support employees may not update this form.
- Invalid contact values show a clear validation failure.

### EmployeeEmailAssignmentSubmission

Purpose: Admin-only employee onboarding payload for the agreed existing-account-by-email flow.

Fields:
- `work_email`
- `display_name`
- `role_slug`

Relationships:
- Creates one Agency Employee Membership for an existing user account matched by email.

Validation:
- `work_email` is required and must be a valid email-shaped value.
- `role_slug` is limited to `support_employee` in this phase.
- Submission fails clearly when no matching user account exists.

### EmployeeDirectoryEntry

Purpose: Row-level employee data shown in the agency employees page.

Fields:
- `membership_id`
- `user_id`
- `display_name`
- `work_email`
- `role_slug`
- `status`
- `created_at`
- `updated_at`

Relationships:
- Belongs to one tenant and one user.

Validation:
- Only admin users can mutate employee rows.
- Deactivated employees remain distinguishable from active employees.

### AgencyListingForm

Purpose: Admin-only listing create or edit submission state.

Fields:
- `title`
- `description`
- `property_type`
- `listing_purpose`
- `price`
- `currency`
- `bedrooms`
- `bathrooms`
- `area_size`
- `area_unit`
- `furnishing`
- `location_text`
- `address`
- `city`
- `country`
- `status`

Relationships:
- Creates or updates one tenant-scoped Listing.

Validation:
- New listings submit with `status=active` to satisfy the immediate-publish rule.
- Support employees may not submit this form.

### AgencyListingRow

Purpose: Listing summary shown in the tenant listings table.

Fields:
- `listing_id`
- `title`
- `status`
- `price`
- `currency`
- `location_text`
- `listing_purpose`
- `updated_at`

Relationships:
- Links to one listing detail/edit context and one viewing-slot manager context.

Validation:
- Only tenant-owned listings appear.
- Empty listing sets show a stable empty state.

### ViewingSlotEntry

Purpose: Listing-level viewing-slot data shown in the slot manager.

Fields:
- `slot_id`
- `listing_id`
- `starts_at`
- `ends_at`
- `capacity`
- `reserved_count`
- `status`

Relationships:
- Belongs to one Listing and feeds scheduled viewing activity.

Validation:
- Admin users may create, edit, and deactivate slots.
- Support employees do not receive slot-management actions in this phase.

### LeadQueueEntry

Purpose: Non-reviewed lead item shown in the main leads queue.

Fields:
- `lead_id`
- `listing_id`
- `status`
- `name`
- `email`
- `phone`
- `message`
- `created_at`
- `updated_at`

Relationships:
- Belongs to one tenant and can transition to a reviewed-lead record.

Validation:
- Tenant scoping is mandatory.
- The active queue contains all non-reviewed leads.
- Marking reviewed removes the item from the active queue.

### ReviewedLeadEntry

Purpose: Lead review record shown in the reviewed leads page.

Fields:
- `review_id`
- `lead_id`
- `reviewed_by_user_id`
- `outcome`
- `notes`
- `created_at`

Relationships:
- Created from one LeadQueueEntry when a review action completes and the source lead status becomes `reviewed`.

Validation:
- Review entries must be tenant-scoped.
- The reviewed queue is loaded from lead records filtered by reviewed status, with review records used for review metadata.
- Support employees may create review records but do not manage employees, listings, or schedules.

### ViewingScheduleFilterState

Purpose: Filter and pagination state for the agency viewings page.

Fields:
- `page`
- `page_size`
- `status_filter`
- `listing_filter`
- `date_from`
- `date_to`

Relationships:
- Produces paginated Scheduled Viewing result pages.

Validation:
- Filters must keep the current page stable and degrade cleanly when no records match.
- Support employees remain read-only on schedule results.

### PlaceholderPageState

Purpose: Explicit placeholder view state for spam leads and policy documents.

Fields:
- `section`
- `title`
- `message`
- `next_phase_reference`

Relationships:
- Used by placeholder-only screens.

Validation:
- Must clearly indicate non-availability instead of pretending the feature works.
