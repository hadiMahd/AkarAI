# Feature Specification: Auth, RBAC, and Tenant Isolation

**Feature Branch**: `004-auth-rbac-tenant-isolation`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "read PLAN.md and create the spec for Phase 3 only: Auth, RBAC, and Tenant Isolation."

## Clarifications

### Session 2026-06-09

- Q: Can one agency employee belong to more than one agency tenant? -> A: One employee belongs to only one agency.
- Q: How should password reset be triggered without email in this phase? -> A: Current password required to change password.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authenticate Existing Actors (Priority: P1)

An existing user or agency employee can sign in, stay signed in through refresh, and sign out so that later protected product flows can trust a verified actor identity.

**Why this priority**: Authentication is the entry point for every protected user, agency, support, and platform workflow.

**Independent Test**: Create an existing active actor, sign in with valid credentials, refresh the session, sign out, and confirm the signed-out session can no longer be used.

**Acceptance Scenarios**:

1. **Given** an active actor with valid credentials, **When** they sign in, **Then** they receive a short-lived access credential and a refresh session.
2. **Given** an active actor with a valid refresh session, **When** they refresh access, **Then** they receive a new valid access credential without signing in again.
3. **Given** an active actor is signed in, **When** they sign out, **Then** the current access credential and refresh session are invalidated.
4. **Given** an inactive, deactivated, or unknown actor, **When** sign-in is attempted, **Then** access is denied without revealing whether the identifier exists.

---

### User Story 2 - Enforce Roles and Permissions (Priority: P1)

Protected actions can require one of the approved project roles and explicit permissions so that User, Agency Admin, Support Employee, and Platform Admin actors receive only the access intended for them.

**Why this priority**: Later domain features depend on a single role and permission contract before exposing listings, leads, viewings, agency management, or platform operations.

**Independent Test**: Assign each approved role to test actors and verify allowed actions pass while forbidden actions are denied with a consistent authorization outcome.

**Acceptance Scenarios**:

1. **Given** a protected action requires a permission, **When** an actor with that permission attempts it, **Then** the action is allowed.
2. **Given** a protected action requires a permission, **When** an actor without that permission attempts it, **Then** the action is denied.
3. **Given** a Support Employee actor, **When** they attempt agency owner-only actions, **Then** the action is denied.
4. **Given** a Platform Admin actor, **When** they access platform-level protected checks, **Then** tenant-scoped agency restrictions do not incorrectly block platform oversight.

---

### User Story 3 - Establish Tenant Context for Agencies (Priority: P1)

Every protected request carries actor identity, role, permissions, and tenant context so later agency data cannot be accessed across tenant boundaries.

**Why this priority**: Multi-tenant isolation must exist before agency profiles, employees, listings, leads, viewings, policy documents, RAG chunks, AI tool calls, audit logs, or agency metrics are added.

**Independent Test**: Create two agency tenants and actors for each tenant, then verify that tenant context is available for allowed actions and cross-tenant access is denied.

**Acceptance Scenarios**:

1. **Given** an agency actor signs in, **When** they access a tenant-scoped protected action, **Then** the action receives the actor's tenant context.
2. **Given** an agency actor from Tenant A, **When** they attempt to access Tenant B context, **Then** access is denied.
3. **Given** a User actor without an agency tenant, **When** they access user-owned protected actions, **Then** tenant context remains explicit and does not impersonate an agency.
4. **Given** a Platform Admin actor, **When** they access cross-tenant oversight, **Then** the action is allowed only where the platform role explicitly permits it.

---

### User Story 4 - Revoke Access After Security Events (Priority: P2)

Security events such as password reset, employee deactivation, and suspicious-session revocation invalidate affected sessions so old credentials cannot continue to access protected workflows.

**Why this priority**: Revocation limits the blast radius of compromised credentials and agency staffing changes.

**Independent Test**: Sign in an actor, trigger each revocation event, and verify old access and refresh credentials stop working while unaffected actors remain signed in.

**Acceptance Scenarios**:

1. **Given** an actor has active sessions, **When** their password is reset, **Then** all previous sessions are invalidated.
2. **Given** an agency employee has active sessions, **When** they are deactivated, **Then** all their sessions are invalidated and future sign-in is blocked.
3. **Given** a suspicious session is revoked, **When** that session is used again, **Then** access is denied while unrelated sessions remain valid.

---

### User Story 5 - Throttle Authentication Abuse (Priority: P2)

Repeated authentication attempts are rate limited by request source and actor context so credential stuffing and refresh abuse are slowed without blocking normal use.

**Why this priority**: Authentication flows are high-risk entry points and must be protected before public demo or domain feature work.

**Independent Test**: Repeatedly attempt sign-in, refresh, and reset flows from the same source and confirm limits apply predictably while normal-volume attempts succeed.

**Acceptance Scenarios**:

1. **Given** repeated failed sign-in attempts from the same source, **When** the allowed threshold is exceeded, **Then** further attempts are temporarily denied.
2. **Given** normal sign-in and refresh usage, **When** attempts stay within limits, **Then** access is not blocked.
3. **Given** rate limiting denies a request, **When** the client receives the response, **Then** the response clearly communicates that retry must wait.

### Edge Cases

- Valid credentials for a deactivated employee must not create a session.
- A refresh session that was already used, expired, revoked, or belongs to a deactivated actor must fail.
- Logout must be idempotent when repeated for an already-revoked session.
- Password reset must require the actor's current password before allowing new access.
- Permission checks must fail closed when role or permission data is missing.
- Tenant context must fail closed when a protected tenant-scoped action lacks tenant information.
- Agency employee assignment must reject attempts to attach the same employee to more than one agency tenant.
- Platform Admin access must not accidentally grant agency employee privileges inside a tenant.
- Rate limiting must handle anonymous requests, signed-in actors, and malformed credentials consistently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support sign-in for existing active actors using verified credentials.
- **FR-002**: The system MUST issue short-lived access credentials and longer-lived refresh sessions after successful sign-in.
- **FR-003**: The system MUST support refreshing access only from a valid, unexpired, non-revoked refresh session.
- **FR-004**: The system MUST support sign-out that invalidates the current access credential and refresh session.
- **FR-005**: The system MUST reject sign-in and refresh attempts for inactive, deactivated, unknown, or suspended actors.
- **FR-006**: The system MUST support a password reset skeleton that requires the actor's current password, changes the actor password, and invalidates previous sessions without sending email in this phase.
- **FR-007**: The system MUST support suspicious-session revocation for a single session and all-session revocation for an actor.
- **FR-008**: The system MUST provide the only approved roles: User, Agency Admin, Support Employee, and Platform Admin.
- **FR-009**: The system MUST evaluate protected actions through explicit permissions assigned to roles.
- **FR-010**: The system MUST deny protected actions when actor identity, role, permission, or tenant context is missing or invalid.
- **FR-011**: The system MUST provide a base agency tenant record sufficient to associate agency actors with a tenant.
- **FR-012**: The system MUST provide agency employee membership records with active/deactivated status, and each agency employee MUST belong to only one agency tenant.
- **FR-013**: The system MUST block deactivated employees from sign-in, refresh, and protected tenant-scoped actions.
- **FR-014**: The system MUST invalidate all active sessions for an employee when that employee is deactivated.
- **FR-015**: The system MUST attach actor identity, role, permissions, and tenant context to protected request handling.
- **FR-016**: The system MUST prevent agency actors from accessing another agency tenant's protected context.
- **FR-017**: The system MUST allow Platform Admin actors to perform platform-level protected checks only through explicit platform permissions.
- **FR-018**: The system MUST apply rate limits to sign-in, refresh, sign-out, password reset, and session revocation flows.
- **FR-019**: The system MUST record audit events for sign-in success, sign-in failure, refresh, sign-out, password reset, employee deactivation, session revocation, permission denial, and tenant denial.
- **FR-020**: The system MUST keep secret values out of committed files and rely on the approved secret source for credential-signing and other sensitive values.
- **FR-021**: The system MUST NOT implement user self-registration, listings, leads, scheduled viewings, RAG ingestion, RAG retrieval, AI workflows, email sending, dashboards, or agency business CRUD beyond the base tenant and employee records required for security.

### Key Entities *(include if feature involves data)*

- **Actor**: A person who can authenticate and be authorized, including User, agency employee, and Platform Admin identities.
- **Credential**: Secret proof used to verify an actor during sign-in; stored only as a protected verifier, never as plain text.
- **Access Credential**: Short-lived proof of authenticated actor identity.
- **Refresh Session**: Longer-lived session record used to issue new access credentials and support revocation.
- **Role**: One of the four approved role names that describes the actor's broad access category.
- **Permission**: A named ability required by a protected action.
- **Agency Tenant**: Base tenant identity for an agency; used only for access isolation in this phase.
- **Agency Employee Membership**: Link between an actor and exactly one agency tenant, including active or deactivated status.
- **Tenant Context**: Actor, role, permissions, and tenant information attached to protected work.
- **Revocation Record**: Record or marker showing that a credential or session can no longer be used.
- **Audit Event**: Security-relevant record of authentication, authorization, tenant, and revocation outcomes.
- **Rate Limit Decision**: The decision that a request source or actor is within or beyond allowed authentication usage.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature secures access before product workflows. It does not implement buyer-to-agency real-time chat, listings, leads, viewing bookings, search, RAG, AI assistance, dashboards, or agency business CRUD beyond base tenant and employee security records.
- **Tenant/RBAC Impact**: Affects all approved roles: User, Agency Admin, Support Employee, and Platform Admin. Tenant isolation is established for future agency-scoped data and must fail closed for missing or mismatched tenant context.
- **AI/RAG Scope**: No homepage AI search, listing AI, area RAG, agency policy RAG, ingestion, retrieval, provider call, or AI tool behavior is included. This phase only prepares role and tenant context that later AI/RAG tools must enforce.
- **Reliability/Security/Performance**: Requires session invalidation for logout, password reset, employee deactivation, and suspicious-session revocation; audit records for security events; rate limits for auth flows; and secret values only from the approved secret source.
- **Unknowns to Clarify**: No product-scope unknowns block this specification. Any new supporting-tool choice must be handled during planning and must not bypass the existing Phase 2 security foundation without user approval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active test actors for each approved role can sign in, refresh, and sign out through the documented authentication flow.
- **SC-002**: 100% of revoked, expired, deactivated, or invalid sessions are denied during verification tests.
- **SC-003**: 100% of role guard tests allow actors with required permission and deny actors without it.
- **SC-004**: 100% of cross-tenant access attempts by agency actors are denied in tenant isolation tests.
- **SC-005**: 100% of employee deactivation tests block new access and invalidate pre-existing sessions for the deactivated employee.
- **SC-006**: Authentication abuse tests show repeated attempts are throttled while normal-volume attempts continue to succeed.
- **SC-007**: Security audit verification finds records for all required authentication, authorization, tenant denial, and revocation events.
- **SC-008**: A scope scan finds zero implementation of listings, leads, scheduled viewings, RAG, AI workflows, email sending, dashboards, or buyer-to-agency real-time chat in this phase.

## Assumptions

- Phase 3 starts from the merged Phase 2 core foundation, including central settings, security event records, credential utilities, session invalidation helpers, role placeholders, tenant context placeholders, rate limiting helpers, and health checks.
- Actors already exist through seed data, internal setup, or later admin flows; public self-registration is out of scope for this phase.
- Password reset in this phase is a security flow skeleton only; email delivery and user-facing notification content remain out of scope.
- Agency tenant and employee records are minimal security records only; full agency profile management and employee management screens belong to later phases.
- User-facing and agency interfaces may receive only minimal placeholders needed to exercise authentication state, not full business pages.
