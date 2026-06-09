# Agencies Module

Phase 3 limit: minimal agency tenant and employee-membership records for security isolation only.
Full agency profile, business CRUD, and agency management stay in Phase 4+.

- `models.py` — AgencyTenant and AgencyEmployeeMembership ORM models.
- `service.py` — Agency tenant and employee deactivation business logic.
- `repository.py` — Tenant and membership persistence.

## Guardrails

- Tenant isolation is mandatory.  Agency-scoped actions require an active tenant and active membership.
- Fail closed: missing tenant or membership context denies access.
- Employee deactivation invalidates active sessions and emits audit events.
- No listings, leads, viewings, or business CRUD in this phase.
