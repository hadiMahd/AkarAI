# Feature Specification: Platform Admin Dashboard

**Feature Branch**: `015-platform-admin-streamlit`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "phase 15 now ask for decisions"

## Clarifications

### Session 2026-06-17

- Q: What should the extra admin-only dashboard access gate be? → A: Shared auth plus a dedicated dashboard access permission/allowlist.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Marketplace Demand Insights (Priority: P1)

As a platform admin, I want a dashboard of marketplace demand signals so I can understand what users are searching for, where demand is concentrated, and where supply is missing.

**Why this priority**: Marketplace demand insights are the core purpose of this phase. Without them, the platform admin surface does not deliver its main business value.

**Independent Test**: Can be fully tested by signing in as a platform admin, opening the dashboard, and confirming that demand insight views show marketplace-wide search trends, popular areas, budgets, property types, and demand gaps over a selectable date range plus `city`, `property_type`, and `listing_purpose` filters.

**Acceptance Scenarios**:

1. **Given** marketplace search and event data exists, **When** the platform admin opens the dashboard, **Then** they can see demand insights for popular searched areas, budgets, property types, demand gaps, and search volume trends.
2. **Given** the platform admin changes the selected date range or supported filters (`city`, `property_type`, `listing_purpose`), **When** the dashboard refreshes, **Then** all visible insight cards and charts update consistently to the same scope.
3. **Given** there is insufficient data for part of the selected scope, **When** the platform admin opens that view, **Then** the dashboard shows an empty-state explanation rather than misleading numbers.

---

### User Story 2 - Review AI Audit Activity Safely (Priority: P2)

As a platform admin, I want to inspect AI audit activity across the marketplace so I can review usage patterns, investigate incidents, and monitor risky workflows without mutating agency data.

**Why this priority**: The platform admin needs operational visibility into AI activity after insights are available, but this is still secondary to the primary marketplace intelligence surface.

**Independent Test**: Can be fully tested by opening the AI audit log viewer, filtering by date, actor role, feature area, and result type, and confirming that logs remain read-only and safely redacted.

**Acceptance Scenarios**:

1. **Given** AI audit events exist, **When** the platform admin opens the audit log viewer, **Then** they can browse and filter read-only AI audit entries across the marketplace.
2. **Given** an audit log entry contains sensitive fields, **When** the platform admin opens entry details, **Then** the viewer shows only the allowed redacted representation.
3. **Given** the platform admin attempts to access audit views, **When** they use the dashboard, **Then** they cannot mutate agency data or bypass existing backend permissions.

---

### User Story 3 - Inspect Platform Access Boundaries (Priority: P3)

As a platform admin, I want a simple overview of platform roles and access boundaries so I can understand who is allowed to use which product surfaces.

**Why this priority**: This is a useful governance aid, but it depends on the dashboard and audit views existing first.

**Independent Test**: Can be fully tested by opening the access overview and confirming that the visible roles and their high-level permissions match the enforced backend model.

**Acceptance Scenarios**:

1. **Given** the platform admin opens the access overview, **When** the page loads, **Then** they can see the supported product roles and their high-level access boundaries.
2. **Given** a role is not allowed to use a surface, **When** the overview is displayed, **Then** that restriction is shown clearly in read-only form.

### Edge Cases

- What happens when the selected date range has partial or no source data for one or more insight panels?
- How does the dashboard behave when an audit log result is available but its related object was later deleted or archived?
- What happens when search data volume is high enough that raw result listing would be too large for one page?
- How does the system behave when the platform admin session expires while a dashboard filter change is in progress?
- What happens when multiple views are open and cached insight data becomes stale while newer events arrive?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require the existing platform admin authentication and session flow before allowing entry to the platform admin dashboard, and MUST enforce an additional admin-only dashboard access permission or allowlist before the dashboard is shown.
- **FR-002**: System MUST provide a read-only platform admin dashboard for marketplace-wide analysis and oversight.
- **FR-003**: System MUST present marketplace demand insights covering popular searched areas, popular budgets, popular property types, demand gaps, and search volume trends.
- **FR-004**: System MUST allow the platform admin to constrain demand insights by a supported date range and the supported marketplace filters for `city`, `property_type`, and `listing_purpose`.
- **FR-005**: System MUST keep all insight panels within the same selected scope so the visible numbers and charts are internally consistent.
- **FR-006**: System MUST keep demand insights at the marketplace aggregate level only for this phase and MUST NOT expose per-agency drill-down or tenant comparison views.
- **FR-007**: System MUST show safe empty states when there is not enough source data to compute a requested insight accurately.
- **FR-008**: System MUST provide a read-only AI audit log viewer for platform admins.
- **FR-009**: System MUST allow platform admins to filter AI audit logs by date range, feature area, actor role, and result.
- **FR-010**: System MUST keep AI audit log entries redacted according to the project's existing secret and PII handling rules.
- **FR-011**: System MUST limit platform-admin audit investigations to redacted in-app viewing only for this phase and MUST NOT provide audit log export.
- **FR-012**: System MUST include a read-only overview of product roles and their high-level permission boundaries.
- **FR-013**: System MUST prevent the platform admin dashboard from mutating agency data unless a separately authorized endpoint explicitly allows that action.
- **FR-014**: System MUST paginate or otherwise bound large dashboard tables so platform-level views remain usable at high volume.
- **FR-015**: System MUST preserve tenant-safe access boundaries when presenting aggregated marketplace data and audit information.
- **FR-016**: System MUST show dashboard and audit views in a form that remains usable when underlying source events arrive asynchronously or slightly later than user actions.

### Key Entities *(include if feature involves data)*

- **Demand Insight Snapshot**: A read model representing marketplace-wide search and usage signals for a selected scope, including trend counts, popular segments, and demand gap measures.
- **AI Audit Log Entry**: A read-only record of an AI-related action or event, including actor role, feature area, outcome, timestamps, and a redacted detail payload.
- **Role Access Summary**: A read-only summary of supported product roles and the surfaces or actions they are allowed or not allowed to access.
- **Dashboard Filter Scope**: The chosen time range and supported filters (`city`, `property_type`, `listing_purpose`) applied consistently across insight and audit views.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature adds the platform admin dashboard only. It does not add buyer-to-agency chat, does not change lead or viewing semantics, and does not mutate tenant-owned business data.
- **Tenant/RBAC Impact**: Affected role is Platform Admin. The feature reads marketplace-wide aggregated data and read-only audit information while preserving tenant-safe boundaries and avoiding direct mutation of agency-scoped records.
- **AI/RAG Scope**: The phase consumes existing AI audit data but does not add new homepage AI, listing AI, agency policy RAG, or area RAG behavior.
- **Reliability/Security/Performance**: Sensitive audit content must stay redacted, large views must be bounded, dashboard reads must tolerate delayed event arrival without showing unsafe or inconsistent data, and dashboard entry must pass both the existing platform-admin session flow and the additional dashboard-specific access permission or allowlist gate.
- **Unknowns to Clarify**: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of authenticated platform admins can open the dashboard and view marketplace demand insights without using tenant-specific agency screens.
- **SC-002**: 100% of tested dashboard scope changes keep all visible insight panels aligned to the same selected time range and supported filters.
- **SC-003**: 100% of AI audit log views available to platform admins remain read-only and respect redaction rules.
- **SC-004**: 90% of common platform oversight questions covered by this phase can be answered from the dashboard without direct database access.

## Assumptions

- Existing search logs, AI audit logs, and related event data from earlier phases are already available as the source material for this dashboard.
- This phase focuses on read-only platform oversight and does not introduce platform-driven agency data editing flows.
- Basic role and permission definitions already exist in the backend and can be summarized without inventing new roles.
- The dashboard will extend existing marketplace event data rather than requiring a new analytics product outside the main backend.
- The extra admin-only access gate reuses the existing platform-admin identity and session and adds a dedicated dashboard access permission or allowlist rather than creating a second standalone login system.
