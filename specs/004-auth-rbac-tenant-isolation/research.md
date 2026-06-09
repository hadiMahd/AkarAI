# Research: Auth, RBAC, and Tenant Isolation

## Decision: Reuse Phase 2 Password and Token Foundations

**Rationale**: Phase 2 already added password hashing and token utility foundations using approved backend dependencies. Reusing them avoids selecting an unspecified auth helper library and keeps Phase 3 scoped to product behavior.

**Alternatives considered**:
- Add a new full authentication framework: Rejected because exact auth helper libraries require user approval and would expand scope.
- Replace Phase 2 utilities: Rejected because tests already cover the foundation and replacement adds risk without product value.

## Decision: Use Access Credentials Plus Rotating Refresh Sessions

**Rationale**: The constitution requires short-lived access tokens and refresh tokens. Refresh sessions must be persisted, revocable, and traceable so logout, password reset, deactivation, and suspicious-session revocation can invalidate old access.

**Alternatives considered**:
- Access credential only: Rejected because users and employees need to stay signed in.
- Non-rotating refresh sessions only: Rejected because rotation improves replay detection and revocation clarity.

## Decision: Keep Public Registration Out of Scope

**Rationale**: PLAN.md Phase 3 lists login, refresh, logout, password reset skeleton, employee deactivation, role guards, and tenant context. It does not include signup. Actors can be created by seed/internal setup now and by later user/admin flows.

**Alternatives considered**:
- Add registration now: Rejected because the spec explicitly excludes self-registration and later phases own user/agency business flows.

## Decision: Minimal Agency Tenant and Employee Records

**Rationale**: Tenant isolation cannot be validated without base agency tenants and employee membership status. Only security-relevant fields are included in Phase 3; full agency profile and employee-management business CRUD stay in Phase 4/later UI phases.

**Alternatives considered**:
- Defer tenants until domain tables: Rejected because tenant guardrails must exist before domain work.
- Build full agency management now: Rejected as Phase 4+ business scope.

## Decision: Fail-Closed Role and Tenant Guards

**Rationale**: Missing actor identity, role, permission, or tenant context must deny protected work. This aligns with the constitution's mandatory tenant isolation and prevents accidental cross-tenant access.

**Alternatives considered**:
- Best-effort tenant inference: Rejected because it risks silent data leakage.
- Platform-wide default access: Rejected because platform oversight must still require explicit platform permissions.

## Decision: Redis-Backed Invalidation and Rate Limits

**Rationale**: The fixed stack assigns Redis to token blacklist/session invalidation and rate limiting. Phase 2 already added Redis helpers, so Phase 3 can build behavior without adding infrastructure.

**Alternatives considered**:
- Database-only blacklist/rate limits: Rejected for auth request hot paths and because Redis is already mandated for these duties.
- Client-only throttling: Rejected because it is bypassable.

## Decision: Audit Every Security Outcome

**Rationale**: Authentication, authorization denial, tenant denial, revocation, password reset, and deactivation affect security posture. Recording them supports later platform admin, incident review, and compliance work.

**Alternatives considered**:
- Audit only successful sign-ins: Rejected because failures and denials are security-critical.
- Wait for platform admin phase: Rejected because events must exist when security behavior is introduced.

## Decision: Password Reset Skeleton Requires Current Password

**Rationale**: Phase 3 requires password reset invalidation behavior, but email sending is explicitly out of scope. Requiring the current password keeps the flow as a secure self-service password change while still revoking sessions without delivering email.

**Alternatives considered**:
- Full reset email flow: Rejected because email sending belongs later.
- Omit reset entirely: Rejected because the constitution requires invalidation for password reset.
