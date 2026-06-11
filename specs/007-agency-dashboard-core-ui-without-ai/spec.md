# Feature Specification: Agency Dashboard Core UI Without AI

**Feature Branch**: `007-agency-dashboard-core-ui-without-ai`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "phase 6"

## Clarifications

### Session 2026-06-10

- Q: For support employees, what should they be allowed to do with leads and schedules? → A: View leads and mark them as reviewed; schedules are view-only.
- Q: Should a new listing be saved as draft first, or published immediately? → A: Published immediately after creation.
- Q: When a support employee marks a lead as reviewed, should it move out of the active leads queue or stay visible there? → A: It moves out of the active queue and into reviewed leads.
- Q: How should agency admins add support employees? → A: Add existing user accounts by email and assign a role.
- Q: Should the policy document page be only a placeholder, or should it accept uploads now? → A: Placeholder only, no upload processing yet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agency Admin Operations (Priority: P1)

Agency admins need a dashboard where they can manage the agency profile, support employees, manual listing creation, listing oversight, viewing slots, leads, reviewed leads, and viewing schedules from one signed-in workspace.

**Why this priority**: This is the primary operations surface for the agency and the core value of the phase.

**Independent Test**: Can be tested by signing in as an agency admin and verifying access to the dashboard, profile settings, employee management, listings, leads, and viewing schedule pages.

**Acceptance Scenarios**:

1. **Given** an agency admin is signed in, **When** they open the dashboard, **Then** they see the agency summary cards and links to the agency management pages.
2. **Given** an agency admin is signed in, **When** they open profile, employee, listing, lead, and viewing schedule screens, **Then** each page loads the expected agency-specific content.
3. **Given** an agency admin is signed in, **When** they open the manual listing form, viewing slots manager, or employee management flow, **Then** they can complete the intended management workflow, add existing support-employee accounts by email, and publish a new listing immediately without seeing user-facing AI features.

---

### User Story 2 - Support Employee Workflows (Priority: P2)

Support employees need a restricted dashboard experience where they can review leads and viewing schedules for their agency while being prevented from performing admin-only actions.

**Why this priority**: Agency operations depend on staff being able to process leads and schedules without exposing elevated controls.

**Independent Test**: Can be tested by signing in as a support employee and confirming access to lead detail, reviewed leads, and viewing schedule pages while admin-only actions remain unavailable.

**Acceptance Scenarios**:

1. **Given** a support employee is signed in, **When** they open the dashboard, **Then** they can see only the pages and actions allowed for their role.
2. **Given** a support employee is signed in, **When** they open lead detail or reviewed leads screens, **Then** they can review agency leads and mark leads as reviewed, after which the lead leaves the active queue and appears in reviewed leads.
3. **Given** a support employee is signed in, **When** they open viewing schedule screens, **Then** they can only view schedules and cannot modify schedule ownership, timing, or assignment.
4. **Given** a support employee is signed in, **When** they try to access employee management or create-listing actions, **Then** those controls are hidden or blocked.

---

### User Story 3 - Operational Placeholders and Navigation (Priority: P3)

Agency users need placeholder surfaces for future policy-document work, spam-lead handling, and dependable navigation/loading behavior across the dashboard.

**Why this priority**: These screens keep the workflow coherent now while reserving unfinished operational areas for later phases.

**Independent Test**: Can be tested by opening the placeholder screens, switching between dashboard sections, and verifying loading and empty states.

**Acceptance Scenarios**:

1. **Given** an agency user opens the spam leads section or policy document upload page, **When** the feature is not yet implemented, **Then** the page clearly shows a placeholder state instead of a broken workflow.
2. **Given** an agency user navigates between dashboard sections, **When** data is slow or absent, **Then** the page shows a visible loading or empty state.

### Edge Cases

- Support employees must not see create-listing or employee-management controls even when navigating directly to those screens.
- Agency users must not see another tenant's listings, leads, viewing schedules, or employee data.
- Empty agency dashboards must still show usable navigation and placeholder content rather than blank screens.
- Listing, lead, and viewing schedule pages must handle empty datasets without breaking navigation.
- Viewing schedule filters must remain usable when no items match the current filter set.
- Placeholder pages for spam leads and policy documents must not imply completed functionality.
- Slow loading states must be visible on dashboard cards, listings, leads, and viewing schedule pages.
- The phase must not expose AI chat, voice, match score, or other AI-assisted agent workflows.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a signed-in agency dashboard entry point for agency users.
- **FR-002**: System MUST show basic agency summary cards on the dashboard.
- **FR-003**: System MUST provide an agency profile settings page for agency administrators.
- **FR-004**: System MUST provide support employee management access for agency administrators, including adding an existing user account by email and assigning the `support_employee` role.
- **FR-005**: System MUST provide a manual listing creation page for agency administrators.
- **FR-006**: System MUST provide a listings management page for viewing the agency's listings.
- **FR-007**: System MUST provide a listing viewing slots manager for agency listings.
- **FR-008**: System MUST provide a leads page for agency users.
- **FR-009**: System MUST provide a lead detail page for reviewing a single lead.
- **FR-010**: System MUST provide a reviewed leads page that surfaces previously reviewed leads after they leave the active leads queue.
- **FR-011**: System MUST provide a viewing schedules page for agency users.
- **FR-012**: System MUST allow agency users to filter viewing schedules by status, listing, start date, and end date.
- **FR-013**: System MUST allow agency administrators to manage agency profile and employees.
- **FR-014**: System MUST allow agency administrators to create and manage listings and publish a newly created listing immediately.
- **FR-015**: System MUST allow agency administrators and support employees to view scheduled viewings, while only agency administrators can mutate schedule records.
- **FR-016**: System MUST prevent support employees from creating listings.
- **FR-017**: System MUST prevent support employees from managing employees.
- **FR-018**: System MUST provide a spam leads section placeholder that clearly indicates the feature is not yet available.
- **FR-019**: System MUST provide a policy document upload page placeholder that clearly indicates the feature is not yet available and does not accept uploads in this phase.
- **FR-020**: System MUST provide visible loading states for all primary dashboard pages.
- **FR-021**: System MUST provide clear empty states when an agency has no listings, leads, or scheduled viewings.
- **FR-022**: System MUST keep dashboard navigation usable across all supported agency screens.
- **FR-023**: System MUST scope all agency data to the signed-in user's agency.
- **FR-024**: System MUST NOT expose user-facing AI widgets, chat flows, voice search, or match score in the agency dashboard.

### Key Entities *(include if feature involves data)*

- **Agency Dashboard Summary**: High-level operational cards showing agency status and key counts.
- **Agency Profile Settings**: Editable agency information and operational settings for administrators.
- **Support Employee**: A restricted agency staff member with lead and schedule access only.
- **Listing Management View**: The agency surface for creating and reviewing listings.
- **Viewing Slot Manager**: The listing-level view for creating and maintaining available viewing times.
- **Lead Record**: A submitted prospect inquiry that agency staff can review and track.
- **Reviewed Lead Record**: A lead whose underlying lead status is `reviewed` and that appears in the reviewed queue after leaving the active non-reviewed queue.
- **Viewing Schedule**: The agency view of confirmed or pending viewing appointments.
- **Placeholder Operational Section**: A reserved page or panel for future workflow expansion.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This phase covers agency operations UI only. It does not add buyer-to-agency real-time chat, and it does not add any AI-powered agency workflows.
- **Tenant/RBAC Impact**: Agency admin and support employee access must remain tenant-scoped. Support employees must not access employee management or listing creation. Agency data must stay inside the signed-in agency boundary.
- **AI/RAG Scope**: This phase explicitly excludes AI chat, voice, listing AI, RAG, generated replies, and match score behavior.
- **Reliability/Security/Performance**: The dashboard must show loading and empty states, keep key pages navigable, and preserve role restrictions on all agency screens.
- **Unknowns to Clarify**: None. Employee onboarding uses existing accounts matched by email, active leads are all non-reviewed leads, reviewed leads are loaded from the reviewed lead status, and viewing schedule filters are status/listing/date based.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agency administrators can complete the core agency dashboard flows in all validated scenarios: profile settings, employee management, listing management, lead review, and viewing schedule review.
- **SC-002**: Support employees can complete their allowed flows in all validated scenarios while admin-only actions remain inaccessible.
- **SC-003**: Viewing schedule filters return the expected subset of records in every validated scenario.
- **SC-004**: All primary dashboard pages display either content, loading state, or empty state in every validated scenario; no blank screen is acceptable.
- **SC-005**: No validated screen in this phase exposes AI chat, voice, match score, or other AI-assisted agency behavior.

## Assumptions

- Existing authentication and tenant-scoped agency data from earlier phases are available to the dashboard.
- Agency users are already signed in before they reach this dashboard.
- Policy document upload is placeholder-only and does not accept uploads in this phase.
- Support employee permissions are already defined by the earlier auth and RBAC phases.
- The dashboard follows the same product design direction as the rest of the app and should remain production-oriented and role-specific.
- New listings are published immediately after the agency admin submits the creation form.
- Reviewed leads move from the active non-reviewed leads queue into the reviewed leads area when marked reviewed.
- Support employees are added by matching an existing user account by email and assigning the `support_employee` membership role.
