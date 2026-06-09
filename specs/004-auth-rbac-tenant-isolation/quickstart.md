# Quickstart: Auth, RBAC, and Tenant Isolation

## Prerequisites

- Phase 1 and Phase 2 are merged.
- `.env` exists locally and contains only non-secret runtime values plus Vault bootstrap values.
- Docker Compose stack can start all base services.
- Vault is reachable and seeded with JWT secrets through the existing local workflow.

## Start Stack

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Expected:
- Backend, worker, PostgreSQL, PgBouncer, Redis, MinIO, Vault, user app, agency app, and admin services are healthy.
- Alembic applies Phase 3 auth/RBAC/tenant migrations.

## Validate Health

```bash
docker compose exec backend curl -s http://localhost:8000/ready
```

Expected:
- Response status is `ready`.
- Vault, PostgreSQL through PgBouncer, pgvector, Redis, and object storage checks pass.

## Validate Authentication Flow

Use seeded actors for each approved role:
- User
- Agency Admin
- Support Employee
- Platform Admin

Run:

```bash
docker compose exec backend pytest tests/integration/test_auth_flow.py
```

Expected:
- Active actors can sign in.
- Refresh rotates sessions and returns new access.
- Logout invalidates the current session.
- Invalid, inactive, deactivated, and unknown actors are denied.

## Validate Revocation and Password Reset Skeleton

```bash
docker compose exec backend pytest tests/integration/test_session_revocation.py
docker compose exec backend pytest tests/integration/test_password_reset_skeleton.py
```

Expected:
- Single-session revocation blocks only that session.
- All-session revocation blocks every session for the actor.
- Password reset changes the actor password and invalidates previous sessions.
- No email is sent in Phase 3.

## Validate Employee Deactivation

```bash
docker compose exec backend pytest tests/integration/test_employee_deactivation.py
```

Expected:
- Deactivated employees cannot sign in or refresh.
- Existing sessions for the employee are invalidated.
- Deactivation emits a security audit event.

## Validate RBAC and Tenant Isolation

```bash
docker compose exec backend pytest tests/rbac/test_role_guards.py
docker compose exec backend pytest tests/rbac/test_tenant_isolation.py
```

Expected:
- Role guards allow actors with required permissions.
- Role guards deny actors without required permissions.
- Support Employee restrictions are enforced.
- Agency actors cannot access another agency tenant's protected context.
- Platform Admin access requires explicit platform permissions.

## Validate Rate Limits and Audit Events

```bash
docker compose exec backend pytest tests/integration/test_auth_rate_limits.py
docker compose exec backend pytest tests/integration/test_security_audit_events.py
```

Expected:
- Repeated abusive auth attempts are throttled.
- Normal-volume auth attempts still work.
- Audit records exist for sign-in success/failure, refresh, sign-out, password reset, session revocation, employee deactivation, permission denial, tenant denial, and rate limiting.

## Run Full Phase 3 Verification

```bash
docker compose exec backend pytest
docker compose exec worker python -m pytest tests
```

Expected:
- All existing Phase 1 and Phase 2 tests still pass.
- New Phase 3 auth/RBAC/tenant tests pass.
- Worker foundation tests still pass.

## Scope Guard

Before accepting Phase 3, scan for forbidden scope:

```bash
rg -n "listing|lead|viewing|rag|ocr|moderation|email send|dashboard|analytics|chat" backend/app workers specs/004-auth-rbac-tenant-isolation
find backend/app -name "dao.py" -o -name "*dao*.py"
```

Expected:
- No implementation of listings, leads, scheduled viewings, RAG, AI workflows, image processing, email sending, dashboards, or buyer-to-agency chat.
- No DAO files.

## Validate Secret Source

Confirm Vault-backed secret values are used and no secret values are committed.

Expected:
- Secret values come from the approved Vault bootstrap path.
- No secret values appear in tracked files.

## Completion Checklist

- [ ] Login, refresh, and logout work for active actors.
- [ ] Invalidated tokens and sessions stop working.
- [ ] Password reset skeleton invalidates old sessions and sends no email.
- [ ] Employee deactivation blocks access and revokes sessions.
- [ ] Role guards work for all approved roles.
- [ ] Tenant context is available for protected work.
- [ ] Cross-tenant access is denied.
- [ ] Auth flow rate limits work.
- [ ] Security audit records are written.
- [ ] Secrets come from Vault bootstrap values and remain out of committed files.
- [ ] No out-of-scope business features were added.
