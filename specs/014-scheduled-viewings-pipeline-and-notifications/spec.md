# Feature Specification: Scheduled Viewings Pipeline and Notifications

**Feature Branch**: `014-scheduled-viewings-pipeline-and-notifications`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "this phase ask for every decision to be mad"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book and Track a Viewing (Priority: P1)

As a signed-in user, I want to book a viewing for a listing and see the result in my scheduled viewings area so I know the appointment was recorded and what happens next.

**Why this priority**: Viewing booking is the core outcome of this phase. Without reliable creation and visibility of the scheduled viewing record, reminders and agency-side operations do not matter.

**Independent Test**: Can be fully tested by booking a viewing against an available slot, confirming that one scheduled viewing record is created, and verifying that the user can see its status and appointment details.

**Acceptance Scenarios**:

1. **Given** a listing has an available viewing slot and the user is eligible to book, **When** the user confirms a booking, **Then** the system creates exactly one scheduled viewing record and shows it in the user scheduled viewings area.
2. **Given** a booking request is retried or duplicated, **When** the same booking intent is processed more than once, **Then** the system preserves a single scheduled viewing and does not create duplicate notifications.
3. **Given** a viewing changes status after booking, **When** the user opens their scheduled viewings area, **Then** they see the current status and the latest appointment details.

---

### User Story 2 - Manage Agency Viewing Operations (Priority: P2)

As an agency admin or support employee, I want to see and manage scheduled viewings for my agency listings so I can coordinate appointments and keep statuses accurate.

**Why this priority**: Agencies need an operational queue after the booking exists. This is the main staff-facing workflow tied to scheduled viewings.

**Independent Test**: Can be fully tested by opening the agency scheduled viewings page, filtering by date/status/listing/client, and performing allowed status updates on a scheduled viewing.

**Acceptance Scenarios**:

1. **Given** an agency has scheduled viewings across multiple listings, **When** an allowed employee filters the schedule page, **Then** only tenant-scoped viewings matching the selected filters are shown.
2. **Given** a scheduled viewing is awaiting agency action, **When** an allowed employee confirms, cancels, completes, or marks no-show according to the allowed workflow, **Then** the new status is stored and visible to both agency staff and the user.
3. **Given** a support employee opens the schedule page, **When** they view or update a scheduled viewing, **Then** they can only act within the permissions allowed for support employees.

---

### User Story 3 - Deliver Reliable Notifications and Reminders (Priority: P3)

As a user or agency staff member involved in a viewing, I want booking and status-change notifications to arrive reliably so I do not miss or misunderstand the appointment.

**Why this priority**: Notifications are a dependent slice after booking and status management, but they are still required for the phase to be operational.

**Independent Test**: Can be fully tested by creating and updating scheduled viewings, verifying queued notification jobs, retries, dead-letter visibility for terminal failures, and idempotent delivery behavior.

**Acceptance Scenarios**:

1. **Given** a viewing is scheduled or cancelled, **When** the corresponding event is emitted, **Then** notification jobs are queued exactly once for the intended recipients.
2. **Given** a notification or reminder job fails transiently, **When** the worker retries it, **Then** retries follow the configured backoff policy without producing duplicate sends.
3. **Given** a notification or reminder job exceeds retry limits or times out, **When** processing stops, **Then** the failed job becomes visible for operational follow-up.

### Edge Cases

- What happens when two users attempt to book the same viewing slot at nearly the same time?
- How does the system handle a status update that arrives after a viewing has already reached a terminal status?
- What happens when a reminder is due for a viewing that was cancelled shortly before the reminder job runs?
- How does the system behave when a booking request is retried after a network timeout but the original write already succeeded?
- What happens when a user or employee loses permission or tenant access between booking time and notification processing time?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow an eligible signed-in user to book a scheduled viewing only against an available viewing slot for the selected listing.
- **FR-002**: System MUST create one scheduled viewing record per successful booking request and MUST prevent duplicate scheduled viewings from repeated submissions of the same booking intent.
- **FR-003**: System MUST make newly created scheduled viewings visible in the user scheduled viewings area with appointment details and current status.
- **FR-004**: System MUST make tenant-scoped scheduled viewings visible to agency admins and support employees for listings owned by their agency.
- **FR-005**: System MUST support agency-side filtering of scheduled viewings by date, listing, client name, status, and upcoming or past time window.
- **FR-006**: System MUST record and expose scheduled viewing status transitions, including Scheduled, Confirmed, Cancelled, Completed, and No-show.
- **FR-007**: System MUST enforce allowed status transitions and actor permissions for users, agency admins, and support employees. [NEEDS CLARIFICATION: should users be allowed to cancel or reschedule their own scheduled viewings after booking, or are status changes agency-only?]
- **FR-008**: System MUST emit domain events when a scheduled viewing is created or cancelled and MUST use those events to trigger downstream notification work.
- **FR-009**: System MUST send booking and cancellation notifications to the intended recipients through approved delivery channels. [NEEDS CLARIFICATION: is this phase email-only, or should it also send SMS and/or WhatsApp notifications, and which delivery provider should be used?]
- **FR-010**: System MUST queue reminder work for upcoming scheduled viewings and MUST avoid delivering reminders for viewings that are no longer eligible when the job executes.
- **FR-011**: System MUST retry failed notification and reminder jobs with bounded backoff, MUST apply idempotency so duplicate events do not create duplicate notifications, and MUST make terminally failed jobs visible for operations follow-up.
- **FR-012**: System MUST surface the latest notification-related status needed for staff follow-up without exposing cross-tenant data.
- **FR-013**: System MUST preserve all-or-nothing behavior for scheduled viewing creation and its initial event creation so a booking cannot partially commit.
- **FR-014**: System MUST keep user-facing and agency-facing scheduled viewing lists updated after booking creation and status changes.
- **FR-015**: System MUST apply the project’s existing redaction and secret-handling rules to notification job payloads, logs, and worker diagnostics.
- **FR-016**: System MUST schedule reminders based on a single agreed policy for when and how often reminders are sent before a viewing. [NEEDS CLARIFICATION: what reminder cadence should be used, for example one reminder, multiple reminders, and how long before the appointment each reminder should fire?]

### Key Entities *(include if feature involves data)*

- **Scheduled Viewing**: A booked appointment between a user and an agency listing, including listing reference, agency tenant, user contact context, booked slot details, status, and audit timestamps.
- **Viewing Slot**: An agency-defined available appointment window that can be offered for booking and referenced by one or more scheduled viewing operations according to slot rules.
- **Viewing Notification Job**: A queued unit of work created from scheduled viewing events or reminder scheduling, carrying recipient scope, delivery purpose, retry state, timeout state, and terminal failure visibility.
- **Viewing Status History Entry**: A record of a status transition on a scheduled viewing, including prior status, new status, actor, and time of change.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature covers viewing booking operations, scheduled viewing records, reminders, and agency/user viewing management. It does not introduce buyer-to-agency real-time chat and keeps viewing bookings separate from leads.
- **Tenant/RBAC Impact**: Affected roles are User, Agency Admin, and Support Employee. Scheduled viewings, notification jobs, history, and filters must remain tenant-scoped. Support employees can view and operate on agency viewings only within allowed viewing permissions.
- **AI/RAG Scope**: No homepage search, listing AI, area RAG, or agency policy RAG behavior is required by this phase.
- **Reliability/Security/Performance**: Scheduled viewing creation and initial event creation must be atomic. Notification and reminder jobs must be idempotent, retry safely, enforce bounded concurrency and timeouts, and avoid leaking contact data in logs. Scheduled viewing lists must remain paginated and filterable.
- **Unknowns to Clarify**: Notification channel/provider, user self-service cancellation or rescheduling policy, and reminder cadence remain unresolved and materially affect scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successful booking submissions create exactly one visible scheduled viewing for the user and one visible scheduled viewing for the owning agency.
- **SC-002**: 95% of scheduled viewing status changes become visible in both user and agency interfaces within 10 seconds of completion.
- **SC-003**: 100% of duplicate booking submissions for the same booking intent avoid creating a second scheduled viewing record.
- **SC-004**: 95% of notification or reminder jobs that encounter transient failures recover automatically without manual intervention, while 100% of terminal failures become visible for follow-up.

## Assumptions

- Existing viewing slot management from earlier phases remains the source of available appointment windows.
- Scheduled viewings continue to be distinct from leads and do not reuse the lead-processing pipeline.
- User and agency scheduled viewing pages already exist in a basic form and will be extended rather than replaced.
- The phase includes operational visibility for failed jobs, but not a full new admin observability product.
