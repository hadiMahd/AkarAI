# Auth Foundation (Phase 2)

This module provides auth utility foundations only. The following are **out of scope** for Phase 2:

- Login endpoint (POST /auth/login)
- Registration endpoint (POST /auth/register)
- Password reset flow
- Email verification flow
- Full JWT middleware enforcement
- Business authorization on listings, leads, viewings, etc.

## Phase 2 Scope

- `models.py` — Role, Permission, RolePermission, RefreshSession ORM models
- `permissions.py` — Role constants and permission key enum
- `dependencies.py` — Stub `get_current_user` and `require_permission` placeholders
- `service.py` — Redis token blacklist helpers

Real authentication flows, registration, login, password reset, and full RBAC enforcement are deferred to later feature phases.
