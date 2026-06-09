# Feature Specification: Core Domain Database and CRUD APIs

**Feature Branch**: `005-core-domain-crud-apis`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "read PLAN.md and create the spec for Phase 4 only: Core Domain Database and CRUD APIs. Do not include later phases."

## Clarifications

### Session 2026-06-09

- Q: Which scheduled viewing statuses should Phase 4 support? → A: `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, `no_show`
- Q: Which listing lifecycle statuses should Phase 4 support? → A: `active`, `inactive`, `archived`
- Q: Which lead lifecycle statuses should Phase 4 support? → A: `new`, `reviewed`, `closed`
- Q: Which manual listing filters should Phase 4 support? → A: location text, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, area size, and sort options

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Agency Core Records (Priority: P1)

Agency admins need to create and maintain the agency's core operational records: agency profile, employees, listings, listing photo metadata, and viewing slots. Support employees need restricted access to the records they are allowed to handle without being able to manage agency profile settings, employees, or listing creation.

**Why this priority**: Agency data ownership and role restrictions are the foundation for all later marketplace, AI, and dashboard work.

**Independent Test**: Can be tested by signing in as an agency admin and a support employee, performing allowed and forbidden record actions inside one agency, and confirming that permissions and tenant boundaries are enforced.

**Acceptance Scenarios**:

1. **Given** an agency admin belongs to an agency, **When** they update agency profile details, manage employees, create listings, add listing photo metadata, and define viewing slots, **Then** the records are saved under that agency and are visible only to allowed actors in that agency.
2. **Given** a support employee belongs to an agency, **When** they attempt to create a listing, manage employees, or edit agency profile settings, **Then** the action is denied.
3. **Given** a support employee belongs to an agency, **When** they view allowed agency records such as listings, viewing slots, leads, and scheduled viewings for that agency, **Then** the allowed records are returned with pagination.

---

### User Story 2 - Browse, Save, Compare, and Request Listings (Priority: P2)

Users need non-AI core marketplace actions: browse listing records, save listings, compare selected listings, submit inquiries that become structured leads, and request scheduled viewings from available viewing slots.

**Why this priority**: User marketplace behavior must create reliable structured records before user-facing UI and AI flows are added.

**Independent Test**: Can be tested by creating active listings and viewing slots, then acting as a user to save listings, create a comparison session, submit an inquiry, and schedule a viewing.

**Acceptance Scenarios**:

1. **Given** active listings exist, **When** a user lists or filters listings, **Then** the user receives paginated listing results without private agency-only fields.
2. **Given** a user selects listings, **When** they save listings or create a comparison session, **Then** the saved listing and comparison records are tied to that user.
3. **Given** a listing accepts inquiries, **When** a user submits an inquiry, **Then** a structured lead record is created for the listing's agency.
4. **Given** a listing has available viewing slots, **When** a user schedules a viewing, **Then** a scheduled viewing record and initial status history entry are created.

---

### User Story 3 - Track Lead and Viewing Operations (Priority: P3)

Agency admins and support employees need consistent lead and scheduled viewing records with status history, review tracking, notification records, and audit-style transaction logs so later automation can attach to reliable domain events.

**Why this priority**: Lead processing, notifications, AI suggestions, analytics, and platform dashboards depend on stable event and status foundations.

**Independent Test**: Can be tested by changing lead review state, viewing status, and notification state, then verifying history and transaction logs are preserved.

**Acceptance Scenarios**:

1. **Given** a lead exists for an agency, **When** an allowed agency actor marks it reviewed, **Then** a reviewed lead record is stored with reviewer and review time.
2. **Given** a scheduled viewing exists, **When** its status changes, **Then** the current status updates and a status history record is appended.
3. **Given** a domain action creates or changes a critical record, **When** the operation completes, **Then** a domain event or transaction log is recorded for later processing and audit.
4. **Given** notifications are created for users or agency actors, **When** notification records are listed, viewed, marked read, or dismissed, **Then** only the intended recipient can access them.

### Edge Cases

- Cross-tenant access to agency profile, listings, leads, viewing slots, scheduled viewings, employees, notifications, logs, and review records must fail closed.
- A support employee attempting agency-admin-only actions must receive a denial without mutating data.
- Duplicate saved listings for the same user and listing must not create duplicate active saved records.
- A comparison session must reject more than four listings.
- A viewing cannot be scheduled for a slot that is unavailable, full, expired, deleted, or outside the listing's agency.
- Scheduled viewing status must be one of `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, or `no_show`.
- Listing photo metadata can be recorded only as metadata; actual upload, moderation, quality checks, and optimization are out of scope.
- Lead spam, lead level, and suggested reply records can exist as empty or externally supplied result containers only; classification and generation are out of scope.
- Pagination must bound list responses for listings, employees, leads, scheduled viewings, saved listings, comparison sessions, notifications, search logs, and domain logs.
- Deleting or disabling parent records must not expose orphan records across tenants or users.
- Search logs record manual search activity only; AI search, voice search, and area expansion are out of scope.
- Manual listing search must support location text, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, area size, and sort options. Sort options are newest, price low to high, price high to low, area size low to high, and area size high to low.
- Manual listing search, listing inquiries, and viewing booking must be rate limited and reject over-limit requests without partial writes.
- Listing mutations that affect public search visibility or searchable attributes must explicitly invalidate cached listing search results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define core domain records for agency profile, agency employees, listings, listing photo metadata, listing viewing slots, scheduled viewings, scheduled viewing status history, saved listings, comparison sessions and items, leads, lead spam result records, lead level result records, lead suggested reply records, reviewed lead records, notifications, search logs, and domain event or transaction logs.
- **FR-002**: System MUST allow agency admins to create, read, update, and deactivate agency profile records within their own agency.
- **FR-003**: System MUST allow agency admins to create, list, update, and deactivate agency employee records within their own agency.
- **FR-004**: System MUST prevent support employees from creating listings, managing employees, or editing agency profile settings.
- **FR-005**: System MUST allow agency admins to create, list, view, update, activate, deactivate, and archive listings within their own agency using only these Phase 4 statuses: `active`, `inactive`, and `archived`.
- **FR-006**: System MUST allow allowed agency actors to list and view agency listings, listing photo metadata, and viewing slots within their own agency.
- **FR-007**: System MUST allow listing photo metadata to be created, listed, updated, reordered, and removed without performing image upload, image moderation, image quality checks, or image optimization.
- **FR-008**: System MUST allow agency admins to create, list, update, and deactivate viewing slots for listings in their own agency.
- **FR-009**: System MUST allow users to list active listings with manual filters, pagination, and sorting. Manual filters include location text, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, and area size. Sort options include newest, price low to high, price high to low, area size low to high, and area size high to low.
- **FR-010**: System MUST hide private agency-only fields from public listing responses.
- **FR-011**: System MUST allow users to save and unsave active listings, and list their saved listings with pagination.
- **FR-012**: System MUST prevent duplicate active saved listing records for the same user and listing.
- **FR-013**: System MUST allow users to create, update, view, and delete comparison sessions containing up to four listing items.
- **FR-014**: System MUST reject comparison sessions that exceed four listings.
- **FR-015**: System MUST allow users to submit listing inquiries that create structured lead records for the listing's agency.
- **FR-016**: System MUST allow allowed agency actors to list, view, update status fields, and mark leads reviewed within their own agency using only these Phase 4 statuses: `new`, `reviewed`, and `closed`.
- **FR-017**: System MUST store reviewed lead records with reviewer identity, review time, and review outcome metadata.
- **FR-018**: System MUST store lead spam result, lead level result, and lead suggested reply records as data containers only, without performing spam classification, lead scoring, or reply generation.
- **FR-019**: System MUST allow users to request scheduled viewings from available listing viewing slots.
- **FR-020**: System MUST create scheduled viewing records atomically with the initial scheduled viewing status history record.
- **FR-021**: System MUST allow users to list and view their own scheduled viewings.
- **FR-022**: System MUST allow allowed agency actors to list, view, and update scheduled viewings within their agency.
- **FR-023**: System MUST append a scheduled viewing status history record whenever the scheduled viewing status changes.
- **FR-024**: System MUST validate scheduled viewing status transitions and reject invalid transitions using only these Phase 4 statuses: `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, and `no_show`.
- **FR-025**: System MUST provide paginated list behavior for employees, listings, viewing slots, leads, scheduled viewings, saved listings, comparison sessions, notifications, search logs, and domain logs.
- **FR-026**: System MUST enforce tenant isolation on all agency-owned domain records.
- **FR-027**: System MUST enforce user ownership on saved listings, comparison sessions, listing inquiries created by the user, and the user's scheduled viewings.
- **FR-028**: System MUST create domain event or transaction log records for critical creates and status changes, including listing status changes, lead creation, lead review, viewing booking, viewing status changes, and notification state changes.
- **FR-029**: System MUST allow notification records to be created by internal domain services and allow intended recipients to list, view, mark read, and dismiss their notifications.
- **FR-030**: System MUST prevent notification access by users or agency actors who are not the intended recipient.
- **FR-031**: System MUST record manual search logs with actor context where available, filter summary, timestamp, and result count, and allow allowed agency actors to list tenant-scoped search logs with pagination.
- **FR-032**: System MUST allow allowed agency actors to list tenant-scoped domain event or transaction logs with pagination.
- **FR-033**: System MUST apply rate limits to manual listing search, listing inquiry creation, and viewing booking.
- **FR-034**: System MUST explicitly invalidate cached listing search results when listing status or searchable listing fields change.
- **FR-035**: System MUST NOT implement AI search, RAG ingestion, RAG retrieval, image processing, OCR, email sending, dashboards, chatbot behavior, buyer-to-agency real-time chat, spam classification, lead scoring, or generated replies in this phase.

### Key Entities *(include if feature involves data)*

- **Agency Profile**: The tenant-facing profile for an agency, including public business details, contact details, and operational status.
- **Agency Employee**: A membership record connecting one employee to exactly one agency with role, status, and restriction metadata.
- **Listing**: A property record owned by an agency, with public details, operational state, searchable attributes, and status. Status values are `active`, `inactive`, and `archived`.
- **Listing Photo Metadata**: Metadata for listing media, including display order, storage reference, status, and descriptive fields; media processing is out of scope.
- **Listing Viewing Slot**: Agency-defined availability for viewing a listing, including date/time window, capacity, and active state.
- **Scheduled Viewing**: A booking between a user, listing, agency, and viewing slot with current status and scheduling details. Status values are `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, and `no_show`.
- **Scheduled Viewing Status History**: Append-only status change record for scheduled viewings.
- **Saved Listing**: User-owned reference to a listing saved for later.
- **Comparison Session**: User-owned grouping of up to four listings for comparison.
- **Comparison Item**: A listing included in a comparison session.
- **Lead**: Structured inquiry record created from a user's listing inquiry and owned by the listing's agency. Status values are `new`, `reviewed`, and `closed`.
- **Lead Spam Result**: Placeholder record for future spam evaluation output.
- **Lead Level Result**: Placeholder record for future Hot/Normal lead evaluation output.
- **Lead Suggested Reply**: Placeholder record for future agency suggested reply output.
- **Reviewed Lead Record**: Record that an agency actor reviewed a lead and captured review metadata.
- **Notification**: Message/state record intended for a user or agency actor. Intended recipients can list, view, mark read, and dismiss these records.
- **Search Log**: Record of manual listing search filters and result counts. Allowed agency actors can list tenant-scoped search logs with pagination.
- **Domain Event or Transaction Log**: Durable record of critical domain changes for audit and later async processing. Allowed agency actors can list tenant-scoped domain logs with pagination.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This phase touches listings, leads, scheduled viewings, agency employee management, notifications, search logs, and domain logs. It explicitly avoids buyer-to-agency real-time chat; user inquiries create structured lead records and viewing bookings create scheduled viewing records.
- **Tenant/RBAC Impact**: Affected roles are User, Agency Admin, Support Employee, and Platform Admin only as already defined. Agency-owned records require tenant isolation. Support employees can view and work permitted operational records but cannot create listings, manage employees, or edit agency profile settings.
- **AI/RAG Scope**: No AI search, listing AI, agency policy RAG, area RAG, OCR, image moderation, image quality checks, generated replies, spam classification, or lead scoring is included. AI-adjacent lead result tables are storage foundations only.
- **Reliability/Security/Performance**: Critical transactions include listing status changes, lead creation, viewing booking with status history, lead review, notification state changes, saved listing changes, and comparison updates. Pagination is required for all list endpoints. Manual search, inquiry creation, and viewing booking are rate limited. Listing search cache invalidation is explicit on public-search-affecting mutations. Tenant isolation and user ownership checks are blocking. Secrets are not expanded in this phase.
- **Unknowns to Clarify**: No provider or library decisions are required for this phase because AI, RAG, media processing, email sending, OCR, STT/TTS, and background processing providers are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agency admins can complete the core agency setup flow, including profile update, employee creation, listing creation, listing photo metadata entry, and viewing slot creation, with all records visible only inside their agency.
- **SC-002**: Support employees are denied 100% of agency-admin-only actions while retaining access to permitted operational records for their own agency.
- **SC-003**: Users can complete the non-AI marketplace flow of listing browse, save listing, compare up to four listings, submit an inquiry, and schedule a viewing.
- **SC-004**: Cross-tenant attempts to access agency-owned listings, employees, leads, viewing slots, scheduled viewings, notifications, or logs are blocked in all tested cases.
- **SC-005**: List views for employees, listings, viewing slots, leads, scheduled viewings, saved listings, comparison sessions, notifications, search logs, and domain logs return bounded paginated results.
- **SC-006**: Viewing booking creates both the scheduled viewing and the initial status history record in one completed operation, with no partial record left after a failed booking.
- **SC-007**: Lead review and viewing status updates preserve history or review records for 100% of successful state changes.
- **SC-008**: Phase 4 implementation contains no AI, RAG, image processing, OCR, email sending, dashboard, chatbot, or buyer-to-agency real-time chat behavior.

## Assumptions

- Existing Phase 3 authentication, roles, permissions, session invalidation, and tenant context are available and remain the source of access control.
- One employee belongs to only one agency.
- Agency-owned data is always scoped to exactly one agency tenant unless explicitly identified as platform-wide in a later phase.
- Listing search in this phase is manual filter search only.
- Listing photo records store metadata and object references only; media upload and processing arrive in Phase 7.
- Lead spam, lead level, and suggested reply records exist now to support later phases, but no classifier or generator writes those records in Phase 4.
- Notification records are persisted in this phase, but email delivery and reminders arrive in a later phase.
- Platform analytics and Streamlit dashboards are out of scope for this phase even though search logs and domain logs are created as later inputs.
