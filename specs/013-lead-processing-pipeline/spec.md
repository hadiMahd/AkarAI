# Feature Specification: Lead Processing Pipeline

**Feature Branch**: `[013-lead-processing-pipeline]`

**Created**: 2026-06-16

**Status**: Draft

**Input**: User description: "current phase"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Lead Classification (Priority: P1)

When a new lead is created, the system checks whether it is spam first, then assigns a Hot or Normal classification if it is not spam.

**Why this priority**: This is the core operational flow for lead handling.

**Independent Test**: Create a new lead and verify it appears with a spam or Hot/Normal outcome without manual intervention.

**Acceptance Scenarios**:

1. **Given** a valid new lead, **When** it is submitted, **Then** the system classifies it for spam first and stores the result.
2. **Given** a non-spam lead, **When** classification completes, **Then** the system stores a Hot or Normal result.

---

### User Story 2 - Lead Review Workbench (Priority: P2)

Support employees can review leads, view spam leads separately, and mark leads as reviewed.

**Why this priority**: Review actions are needed to turn classification into daily agency work.

**Independent Test**: Open the lead list, filter to spam leads, mark one lead reviewed, and confirm the state persists.

**Acceptance Scenarios**:

1. **Given** a classified lead, **When** a support employee marks it reviewed, **Then** the reviewed state is saved and visible later.
2. **Given** a spam lead, **When** a support employee opens the spam leads view, **Then** the lead is listed there.

---

### User Story 3 - Lead Analytics Trail (Priority: P3)

The system records lead processing outcomes so agencies can track lead volume, review activity, and classification trends over time.

**Why this priority**: Analytics supports follow-up work and later reporting, but does not block daily lead handling.

**Independent Test**: Create and review leads, then confirm processing records are available for reporting.

**Acceptance Scenarios**:

1. **Given** a processed lead, **When** the outcome is stored, **Then** the system records a durable processing event.
2. **Given** multiple processed leads, **When** the agency views trends, **Then** the classification and review history can be summarized.

### Edge Cases

- If a lead is created with an empty message, the system treats it as spam and skips Hot/Normal ranking.
- How does the system behave if classification is delayed or unavailable?
- If the same user submits the same inquiry twice, both leads are kept, but processing and callback application stay idempotent per lead record.
- If a reviewed lead receives a late classification callback, the system updates only the spam and Hot/Normal result fields and never resets or overwrites the review state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record a lead-created event when a new lead is stored.
- **FR-002**: The system MUST classify every new lead for spam before any other lead categorization.
- **FR-003**: The system MUST classify non-spam leads as Hot or Normal.
- **FR-004**: The system MUST store the spam outcome, Hot/Normal outcome, and review state for each lead.
- **FR-005**: Support employees and agency admins MUST be able to view spam leads in a dedicated lead view or filter.
- **FR-006**: Support employees MUST be able to mark a lead as reviewed and see that state persist after refresh.
- **FR-007**: The system MUST keep lead processing data tenant-scoped.
- **FR-008**: The system MUST record lead processing outcomes for later reporting and trend analysis.
- **FR-009**: The system MUST classify each new lead in two stages through the lead model service: first as spam or non-spam, then as Hot or Normal only if it is non-spam.
- **FR-010**: The system MUST handle classification failure without losing the original lead record.
- **FR-011**: The system MUST classify leads with an empty message as spam without sending them through the Hot/Normal stage.
- **FR-012**: The system MUST keep duplicate submissions as separate leads while ensuring processing and callback application remain idempotent per lead.
- **FR-013**: The system MUST allow late classification callbacks to update classification fields on reviewed leads without modifying the persisted review state.
- **FR-014**: The agency lead queues, lead detail view, and analytics widgets MUST auto-refresh after classification callbacks until the lead leaves the pending state.
- **FR-015**: The system MUST use the existing domain event log and lead result tables as the reporting source for lead-processing history in this phase.

### Key Entities *(include if feature involves data)*

- **Lead**: A user inquiry submitted to an agency, including its classification state and review state.
- **Lead Classification Result**: The spam or Hot/Normal outcome produced for a lead.
- **Lead Review Metadata**: The reviewed flag and review audit details for a lead.
- **Lead Created Event**: A durable event representing that a lead entered the system.
- **Lead Processing Record**: The reporting view built from `domain_event_logs`, `lead_spam_results`, and `lead_level_results`.
- **Lead Model Service**: The dedicated service that loads the lead classifier assets and returns spam and Hot/Normal outcomes.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature processes inquiries into leads only. It does not add buyer-to-agency chat or viewing booking behavior.
- **Tenant/RBAC Impact**: Lead data stays tenant-scoped. Support employees and agency admins can review leads; other roles cannot access agency lead processing views.
- **AI/RAG Scope**: AI is limited to lead spam and Hot/Normal classification. The lead pipeline uses spam detection first, then Hot/Normal ranking for non-spam leads through a separate model service. No search, RAG, or policy document changes are introduced here.
- **Reliability/Security/Performance**: Lead creation must remain durable even if classification is delayed. Processing outcomes must be recorded reliably and not duplicated on retries. The model service must support retryable processing for each stage.
- **UI Behavior**: Agency lead views auto-refresh while classification is pending so users can see results without manually reloading.
- **Unknowns to Clarify**: None remain for the lead classification flow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly created leads receive a visible spam or Hot/Normal outcome.
- **SC-002**: Support employees can mark a lead as reviewed and see the state remain after returning to the lead list.
- **SC-003**: Agencies can filter or isolate spam leads without opening each lead one by one.
- **SC-004**: Lead creation remains available even when classification is temporarily unavailable.
- **SC-005**: Agencies can summarize lead processing history for reporting from stored processing records.
- **SC-006**: Pending classification results become visible in the agency lead UI without requiring manual page refresh.

## Assumptions

- Lead classification uses the project's existing classifier assets through a dedicated model service for spam detection and Hot/Normal ranking.
- Support employees are the primary users of the spam leads and review workflow.
- Reporting needs are limited to stored history and simple trend summaries in this phase, using existing event and result tables rather than a new reporting table.
