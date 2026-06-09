# Data Model: Core Domain Database and CRUD APIs

## Conventions

- IDs are UUIDs.
- Mutable records include `created_at` and `updated_at`.
- Agency-owned records include `tenant_id` or an equivalent agency tenant reference and must fail closed on tenant mismatch.
- User-owned records include `user_id` and must fail closed on owner mismatch.
- Soft deactivation/archive is preferred for operational records that need history.
- Phase 4 does not store AI/RAG outputs except empty placeholder result containers listed here.

## Entities

### AgencyProfile

Purpose: Public and operational profile for an agency tenant.

Fields:
- `id`
- `agency_tenant_id`
- `display_name`
- `legal_name`
- `description`
- `phone`
- `email`
- `website_url`
- `address`
- `city`
- `country`
- `status`: active, inactive
- `created_at`
- `updated_at`

Relationships:
- Belongs to AgencyTenant.
- Has many Listings through AgencyTenant.

Validation:
- One active profile per agency tenant.
- Agency Admin can create/update/deactivate.
- Support Employee cannot create/update/deactivate.

### AgencyEmployee

Purpose: Employee management view over agency membership records.

Fields:
- `id`
- `agency_tenant_id`
- `user_id`
- `role_id`
- `status`: active, deactivated
- `display_name`
- `work_email`
- `created_at`
- `updated_at`

Relationships:
- Belongs to AgencyTenant.
- References one User and one Role.

Validation:
- One employee belongs to one agency.
- Role must be Agency Admin or Support Employee.
- Agency Admin can manage employees in their tenant.
- Support Employee cannot manage employees.

### Listing

Purpose: Property listing owned by an agency.

Fields:
- `id`
- `agency_tenant_id`
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
- `status`: active, inactive, archived
- `created_by_user_id`
- `updated_by_user_id`
- `created_at`
- `updated_at`
- `archived_at`

Relationships:
- Belongs to AgencyTenant.
- Has many ListingPhotoMetadata records.
- Has many ListingViewingSlot records.
- Has many Leads.
- Has many ScheduledViewings.
- Has many SavedListings.
- Has many ComparisonItems.

Validation:
- Agency Admin can create/update/archive.
- Support Employee can list/view only.
- Public users can list/view active listings only.
- Archived listings are excluded from public search.
- Status changes and searchable field changes explicitly invalidate cached public listing search results.

State transitions:
- `inactive -> active`
- `active -> inactive`
- `active -> archived`
- `inactive -> archived`

### ListingPhotoMetadata

Purpose: Metadata and object reference for future listing media.

Fields:
- `id`
- `listing_id`
- `agency_tenant_id`
- `object_key`
- `caption`
- `alt_text`
- `display_order`
- `status`: pending_upload, active, removed
- `created_at`
- `updated_at`

Relationships:
- Belongs to Listing.
- Belongs to AgencyTenant through listing ownership.

Validation:
- Listing must belong to the same tenant.
- Display order is unique per listing.
- Actual upload, moderation, quality checks, and optimization are out of scope.

### ListingViewingSlot

Purpose: Availability slot for manually scheduled listing viewings.

Fields:
- `id`
- `listing_id`
- `agency_tenant_id`
- `starts_at`
- `ends_at`
- `capacity`
- `reserved_count`
- `status`: active, inactive
- `created_by_user_id`
- `created_at`
- `updated_at`

Relationships:
- Belongs to Listing.
- Has many ScheduledViewings.

Validation:
- Slot listing must belong to tenant.
- `starts_at` must be before `ends_at`.
- Capacity must be positive.
- User booking requires active, non-expired slot with remaining capacity.

### ScheduledViewing

Purpose: User booking for a listing viewing slot.

Fields:
- `id`
- `agency_tenant_id`
- `listing_id`
- `viewing_slot_id`
- `user_id`
- `status`: scheduled, cancelled_by_user, cancelled_by_agency, completed, no_show
- `scheduled_start_at`
- `scheduled_end_at`
- `notes`
- `created_at`
- `updated_at`

Relationships:
- Belongs to AgencyTenant.
- Belongs to Listing.
- Belongs to ListingViewingSlot.
- Belongs to User.
- Has many ScheduledViewingStatusHistory records.

Validation:
- Booking creates ScheduledViewing and initial ScheduledViewingStatusHistory atomically.
- User can view own scheduled viewings.
- Allowed agency actors can view/update tenant scheduled viewings.
- Invalid status transitions are rejected.
- Booking requests are rate limited before persistence work begins.

State transitions:
- `scheduled -> cancelled_by_user`
- `scheduled -> cancelled_by_agency`
- `scheduled -> completed`
- `scheduled -> no_show`

### ScheduledViewingStatusHistory

Purpose: Append-only history for scheduled viewing status changes.

Fields:
- `id`
- `scheduled_viewing_id`
- `agency_tenant_id`
- `old_status`
- `new_status`
- `changed_by_user_id`
- `reason`
- `created_at`

Relationships:
- Belongs to ScheduledViewing.

Validation:
- Initial row has no old status and new status `scheduled`.
- Every status change appends one history row.

### SavedListing

Purpose: User's saved listing record.

Fields:
- `id`
- `user_id`
- `listing_id`
- `created_at`
- `deleted_at`

Relationships:
- Belongs to User.
- Belongs to Listing.

Validation:
- Only active listings can be saved.
- A user/listing pair can have at most one active saved record.
- User can list and remove only own saved listings.

### ComparisonSession

Purpose: User-owned grouping of listings for comparison.

Fields:
- `id`
- `user_id`
- `name`
- `created_at`
- `updated_at`
- `deleted_at`

Relationships:
- Belongs to User.
- Has many ComparisonItems.

Validation:
- User owns all access and mutations.
- Session can contain up to four active listing items.

### ComparisonItem

Purpose: Listing included in a comparison session.

Fields:
- `id`
- `comparison_session_id`
- `listing_id`
- `position`
- `created_at`

Relationships:
- Belongs to ComparisonSession.
- Belongs to Listing.

Validation:
- Position is unique per session.
- Listing is unique per session.
- Maximum four items per session.

### Lead

Purpose: Structured inquiry from a user about a listing.

Fields:
- `id`
- `agency_tenant_id`
- `listing_id`
- `user_id`
- `status`: new, reviewed, closed
- `name`
- `email`
- `phone`
- `message`
- `source`
- `created_at`
- `updated_at`
- `closed_at`

Relationships:
- Belongs to AgencyTenant.
- Belongs to Listing.
- Belongs to User.
- Has optional LeadSpamResult.
- Has optional LeadLevelResult.
- Has many LeadSuggestedReplies.
- Has many ReviewedLeadRecords.

Validation:
- User inquiry creates lead for the listing agency.
- Allowed agency actors can view/update tenant leads.
- Status values are limited to new, reviewed, closed.
- Inquiry creation is rate limited before lead persistence work begins.

State transitions:
- `new -> reviewed`
- `new -> closed`
- `reviewed -> closed`

### LeadSpamResult

Purpose: Placeholder for future spam classification result.

Fields:
- `id`
- `lead_id`
- `agency_tenant_id`
- `status`: pending, available
- `label`
- `score`
- `details`
- `created_at`
- `updated_at`

Relationships:
- Belongs to Lead.

Validation:
- Phase 4 does not compute or populate classifier output automatically.

### LeadLevelResult

Purpose: Placeholder for future Hot/Normal lead evaluation result.

Fields:
- `id`
- `lead_id`
- `agency_tenant_id`
- `status`: pending, available
- `level`
- `score`
- `details`
- `created_at`
- `updated_at`

Relationships:
- Belongs to Lead.

Validation:
- Phase 4 does not compute or populate lead level automatically.

### LeadSuggestedReply

Purpose: Placeholder for future generated agency reply.

Fields:
- `id`
- `lead_id`
- `agency_tenant_id`
- `status`: draft, accepted, discarded
- `body`
- `created_by`
- `created_at`
- `updated_at`

Relationships:
- Belongs to Lead.

Validation:
- Phase 4 does not generate replies.

### ReviewedLeadRecord

Purpose: Audit-style record that an agency actor reviewed a lead.

Fields:
- `id`
- `lead_id`
- `agency_tenant_id`
- `reviewed_by_user_id`
- `outcome`
- `notes`
- `created_at`

Relationships:
- Belongs to Lead.
- References reviewing User.

Validation:
- Reviewer must be an allowed actor in the same agency tenant.
- Marking reviewed creates or appends this record.

### Notification

Purpose: Persisted notification record for users or agency actors.

Fields:
- `id`
- `recipient_user_id`
- `agency_tenant_id`
- `channel`
- `template_key`
- `payload`
- `status`: pending, read, dismissed
- `created_at`
- `updated_at`
- `read_at`

Relationships:
- Optional agency tenant scope.
- Optional recipient user.

Validation:
- Intended recipient can list, view, mark read, and dismiss.
- Delivery and email sending are out of scope.

### SearchLog

Purpose: Durable manual search activity record.

Fields:
- `id`
- `user_id`
- `agency_tenant_id`
- `filters`
- `sort`
- `result_count`
- `created_at`

Relationships:
- Optional User.
- Optional AgencyTenant.

Validation:
- Records manual search only.
- AI search, voice search, and area expansion are out of scope.
- Manual listing search is rate limited.
- Allowed agency actors can list tenant-scoped search logs with pagination.

### DomainEventLog

Purpose: Durable record of critical domain changes for audit and later async processing.

Fields:
- `id`
- `agency_tenant_id`
- `actor_user_id`
- `event_name`
- `aggregate_type`
- `aggregate_id`
- `payload`
- `created_at`

Relationships:
- Optional AgencyTenant.
- Optional actor User.

Validation:
- Critical listing status, lead creation/review, viewing booking/status, saved listing, comparison, and notification state changes create domain logs.
- Later workflow processing is out of scope.
- Allowed agency actors can list tenant-scoped domain logs with pagination.
