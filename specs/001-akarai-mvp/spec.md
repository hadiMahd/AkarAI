# Feature Specification: Akarai MVP

**Feature Branch**: `001-akarai-mvp`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "Create the initial product specification for
the Akarai MVP using the project constitution and available planning context
as the source of truth."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search and Compare Listings (Priority: P1)

A user can search for listings manually, by text, or by voice; browse
paginated results; save listings; add listings to a comparison set; and review
structured comparisons before opening a listing.

**Why this priority**: Search is the entry point for the MVP and determines
whether users can reach inventory at all.

**Independent Test**: A user can search, filter, sort, save, compare up to four
listings, and open a listing without using agency tooling.

**Acceptance Scenarios**:

1. **Given** a user enters a manual or AI search, **When** results are
   returned, **Then** the user sees a paginated listing list with filters and
   sorting.
2. **Given** a user saves or compares listings, **When** the user opens the
   comparison page, **Then** the user sees structured listing fields and an AI
   comparison summary for up to four listings.

---

### User Story 2 - Inspect a Listing and Ask AI (Priority: P1)

A user can open a listing page, review property details, and use the unified AI
widget to ask about the listing, agency policy, create an inquiry, or schedule
a viewing.

**Why this priority**: The listing page is the main conversion point for the
MVP.

**Independent Test**: A user can open a listing, ask the AI widget a question,
and confirm an inquiry or viewing request before it is created.

**Acceptance Scenarios**:

1. **Given** a user opens a listing, **When** they inspect the page, **Then**
   they see photos, specs, price, location, parking, floor, furnished status,
   available viewing dates, agency preview, and the unified AI widget.
2. **Given** a user asks the listing AI to create an inquiry or schedule a
   viewing, **When** they do not confirm, **Then** no lead or viewing record is
   created.

---

### User Story 3 - Agency Manage Leads and Viewings (Priority: P1)

An agency admin or support employee can manage listings, review leads, review
scheduled viewings, and use the support assistant for tenant-aware AI help.

**Why this priority**: Agencies need operational value on day one for the MVP
to be usable.

**Independent Test**: An agency user can view leads, distinguish valid and
spam leads, inspect lead details, review scheduled viewings, and use suggested
replies externally.

**Acceptance Scenarios**:

1. **Given** a structured lead enters the agency workflow, **When** spam and
   hot/normal classification runs, **Then** the lead appears in the correct
   queue with reviewer metadata after review.
2. **Given** a support employee opens a lead detail, **When** the system shows
   a suggested reply, **Then** the reply is meant for external sending through
   WhatsApp or email and is not sent inside the app.

---

### User Story 4 - Administer the Marketplace (Priority: P2)

A platform admin can inspect marketplace demand insights, AI audit logs, and
role/permission settings from the platform admin dashboard.

**Why this priority**: Platform oversight is needed for governance and demand
tracking, but it is secondary to core search and agency workflows.

**Independent Test**: A platform admin can review search trends, demand gaps,
and AI logs without agency-scoped editing access.

**Acceptance Scenarios**:

1. **Given** a platform admin opens the dashboard, **When** they review market
   data, **Then** they can inspect popular searched areas, budgets, property
   types, demand gaps, and search trends.
2. **Given** a platform admin inspects AI audit logs, **When** they review the
   log stream, **Then** they can see logged AI activity without breaking tenant
   boundaries.

### Edge Cases

- A vague search term such as "around Beirut" must still return useful results
  through area/neighborhood retrieval.
- A buyer must not be able to trigger agency chat, because real-time buyer to
  agency chat is out of scope.
- A viewing request or inquiry must not be created until the user confirms.
- A low-quality listing photo may be accepted with a warning, but an NSFW photo
  must be rejected.
- A support employee must not access platform-wide data, policy deletion, or
  employee management.
- A lead classified as spam must remain separate from valid leads.
- Re-ingestion of policy documents must remove orphaned chunks and stale vector
  records.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support manual search, AI text search, and AI
  voice search from the homepage.
- **FR-002**: The system MUST extract listing filters from AI search using
  AI-assisted interpretation.
- **FR-003**: The system MUST use area/neighborhood retrieval when the search
  location is vague.
- **FR-004**: The system MUST present search results in a paginated listings
  page with filters and sorting.
- **FR-005**: The system MUST allow users to save listings and compare up to
  four listings.
- **FR-006**: The system MUST provide a comparison page with structured fields
  and an AI comparison summary.
- **FR-007**: The system MUST provide a listing page with photos, property
  specs, description, price, location, parking, floor, furnished status,
  available viewing dates, agency preview, and a unified AI widget.
- **FR-008**: The system MUST require explicit user confirmation before
  creating an inquiry or scheduling a viewing.
- **FR-009**: The system MUST create a structured Lead for a confirmed inquiry.
- **FR-010**: The system MUST create a ScheduledViewing for a confirmed viewing
  request.
- **FR-011**: The system MUST keep scheduled viewings visible in the user
  profile.
- **FR-012**: The system MUST allow Agency Admin users to manage agency profile,
  upload policy documents, create and manage listings, view leads, view
  scheduled viewings, manage support employees, and access the dashboard.
- **FR-013**: The system MUST allow Support Employees to view or edit listings
  only where allowed, view leads, handle suggested replies externally, mark
  leads reviewed, use the support assistant, and view scheduled viewings.
- **FR-014**: The system MUST prevent Support Employees from creating listings,
  managing employees, editing agency profile settings, uploading or deleting
  policy documents, or accessing platform-wide data.
- **FR-015**: The system MUST accept agency policy and FAQ documents for
  searchable AI knowledge ingestion rather than manual policy editing.
- **FR-016**: The system MUST support AI listing generation, document/photo
  spec extraction, and image upload checks on the create-listing flow.
- **FR-017**: The system MUST reject NSFW listing photos and warn on low-quality
  photos.
- **FR-018**: The system MUST separate valid leads from spam leads and classify
  valid leads as Hot or Normal.
- **FR-019**: The system MUST display one suggested reply on the lead detail
  page and support external sending through WhatsApp or email.
- **FR-020**: The system MUST track reviewer identity and timestamp when a lead
  is reviewed.
- **FR-021**: The system MUST provide viewing schedule filtering by date,
  listing, client, status, and upcoming/past/today/week views.
- **FR-022**: The system MUST support viewing statuses of Scheduled, Confirmed,
  Cancelled, Completed, and No-show.
- **FR-023**: The system MUST provide the platform admin with marketplace demand
  insights, AI audit logs, and role/permission management if needed.
- **FR-024**: The system MUST keep knowledge metadata linked to original
  documents and extracted page text.
- **FR-025**: The system MUST preserve page-level source context, searchable
  child chunks, previous-page context where needed, and chunk hash tracking.
- **FR-026**: The system MUST keep agency policy knowledge tenant-aware and
  separate from platform-owned area/neighborhood knowledge.
- **FR-027**: The system MUST compare old and new chunk hashes during
  re-ingestion and remove orphaned searchable chunks from all relevant stores.
- **FR-028**: The system MUST preserve clear feature ownership for users,
  agencies, listings, leads, viewings, knowledge retrieval, AI, auth, and
  notifications.
- **FR-029**: The system MUST keep critical state changes atomic for lead
  creation, viewing booking, listing publish, knowledge metadata writes, and
  event recording.
- **FR-030**: The system MUST use short-lived access sessions, refresh
  sessions, rate limiting, session invalidation, tenant isolation, and role
  enforcement for operational tools and AI tool calls.
- **FR-031**: The system MUST keep AI, voice, document extraction, retrieval,
  and reranking providers swappable for fallback-ready operation.
- **FR-032**: The system MUST use pagination for listings, leads, scheduled
  viewings, saved listings, audit logs, knowledge documents, and admin tables.

### Non-Functional Requirements

- **NFR-001**: The experience MUST remain multi-tenant and tenant-isolated for
  agency data, knowledge chunks, tool calls, audit logs, and metrics.
- **NFR-002**: The platform MUST keep the user and agency interfaces responsive
  enough that slow pages use skeleton loading.
- **NFR-003**: The platform MUST support background processing for uploads,
  document extraction, knowledge ingestion, email, reminders, and other heavy
  jobs.
- **NFR-004**: The platform MUST keep secrets out of code and store them in the
  approved managed secret vault.
- **NFR-005**: The platform MUST redact personal data from AI logs and prompts
  where needed.
- **NFR-006**: The platform MUST make background jobs safe to retry without
  duplicate side effects.
- **NFR-007**: The platform MUST support fallback-ready AI provider design
  without hardcoded provider logic in feature services.

### Role Permissions

- **User**: search listings, save listings, compare listings, submit inquiries,
  schedule viewings, and view personal scheduled viewings.
- **Agency Admin**: manage agency profile, upload policy documents, manage
  listings, manage employees, review leads, review scheduled viewings, and view
  dashboard metrics.
- **Support Employee**: view and edit allowed listings, review leads, use the
  support assistant, handle suggested replies externally, and view scheduled
  viewings.
- **Platform Admin**: inspect demand insights, AI audit logs, and role or
  permission settings when needed.

### Main Workflows

1. A user searches for listings manually, by text, or by voice.
2. The system extracts filters, applies area/neighborhood retrieval when needed,
   and returns paginated results.
3. The user opens a listing, uses the unified AI widget, and confirms any
   inquiry or viewing request.
4. The system creates a Lead or ScheduledViewing and shows the new record in
   the appropriate profile or agency view.
5. An agency admin uploads policy documents and manages listings.
6. A support employee reviews leads, sees one suggested reply, and sends the
   reply externally outside the app.
7. A platform admin reviews demand insights and AI audit logs.

### Data Entities

- **Listing**: a property record with photos, specs, price, location,
  availability, and agency association.
- **Lead**: a structured inquiry with classification, review metadata, and
  tenant ownership.
- **ScheduledViewing**: a confirmed or planned property viewing with status and
  calendar context.
- **AgencyPolicyDocument**: an uploaded policy or FAQ document stored for
  searchable AI knowledge.
- **KnowledgeChunk**: a searchable knowledge unit with source document links,
  page links, hashes, and retrieval references.
- **ComparisonSet**: a temporary or saved set of up to four listings for side
  by side review.
- **UserProfile**: the user contact and preference record limited to the MVP
  profile fields.
- **AuditLogEntry**: an administrative AI or platform audit record.

### Out of Scope

- Buyer-to-agency real-time chat.
- Match score display in the MVP.
- Manual editing of agency policy text records inside the app.
- Public platform search outside the defined homepage, listing, and dashboard
  flows.
- Any payment, billing, or monetization workflow.
- Any implementation-specific AI provider selection not yet confirmed.

### Open Questions

- Which exact AI provider will be used first for assistant responses,
  embeddings, reranking, voice, and document extraction?
- Which document extraction and voice providers will back the create-listing
  and search flows?
- Which email provider will handle signup, password reset, lead, viewing, and
  reminder messages?
- Which deployment target and hosting environment will be used for the MVP?
- Which UI library or design system should the user and agency apps use?
- Which background worker library should orchestrate jobs and retries?

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of users can complete a search-to-listing-open flow in under
  60 seconds during acceptance testing.
- **SC-002**: 100% of inquiry and viewing creation attempts require explicit
  user confirmation before a record is created.
- **SC-003**: Agency users can review valid leads, spam leads, and scheduled
  viewings with zero cross-tenant data exposure in permission tests.
- **SC-004**: A platform admin can inspect demand insights and AI audit logs in
  under 3 clicks from the admin dashboard entry point.
- **SC-005**: Re-ingesting an uploaded policy document leaves zero stale
  searchable chunks in acceptance tests.

## Assumptions

- The MVP starts with one primary AI provider and keeps the provider choice
  configurable for future fallback support.
- The initial scope favors clarity and workflow completeness over advanced
  personalization.
- Agency policy documents are treated as uploaded source material, not manually
  curated page content.
- Search, listing, lead, and viewing flows are the highest-priority user
  journeys for launch.
