# Auth Module

Security ownership lives here:

- `models.py` — Role, Permission, RolePermission, RefreshSession, AccessRevocation ORM models.
- `permissions.py` — BuiltinRole and PermissionKey enumerations.
- `service.py` — Credential issuance, rotation, revocation, password-reset primitives.
- `repository.py` — User lookup and session persistence.
- `schemas.py` — Request/response shapes for auth endpoints.
- `dependencies.py` — Current-actor, role-guard, permission-guard dependency callables.
- `router.py` — Login, refresh, logout, password-reset, session-revocation, employee-deactivation, current-actor routes.

## Guardrails

- Secrets come from HashiCorp Vault via `configure_secrets()`.  Do not embed or default JWT secrets.
- Password hashing and token creation use `app.common.security`.
- Token invalidation uses Redis-backed blacklists and session marker keys.
- Audit events are emitted for every security outcome (success, failure, denied) via `app.audit.service`.
- Fail closed on missing actor, role, permission, or tenant context.
- No public registration in Phase 3.  Actors are created internally or by seed data.
