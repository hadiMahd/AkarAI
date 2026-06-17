# Platform Admin Backend Module

Read-only backend support for the Streamlit platform admin dashboard.

This module exists to keep platform-admin reads separate from agency
operations. The admin container never connects to Postgres directly; it
calls these backend APIs over HTTP and receives shaped, read-only
responses.

## Endpoints

All routes live under `/api/v1/platform`:

- `GET /dashboard/insights`
- `GET /audit-logs`
- `GET /roles/overview`

## Access gate

Every route is protected by
`app.auth.dependencies.require_platform_dashboard_access()`.

The gate is intentionally two-stage:

1. actor must be `platform_admin`
2. actor must hold `platform:dashboard_read`

This prevents agency admins, support employees, and partially seeded
platform roles from reaching any dashboard data.

## Module layout

- [router.py](./router.py): read-only FastAPI routes and query parsing
- [service.py](./service.py): cache-aware orchestration and view-audit
  logging
- [query_service.py](./query_service.py): aggregate read queries and
  response shaping helpers
- [schemas.py](./schemas.py): platform dashboard request/response models

## Data boundaries

### Marketplace insights

The insights route builds aggregate-only demand views from existing
listing inventory and search-log activity. It must not return per-agency
operational detail in this phase.

Supported filters:

- date window
- `city`
- `property_type`
- `listing_purpose`

### Audit logs

The audit route is read-only and returns paginated, redacted audit-log
entries. Feature-area labeling and metadata cleanup are delegated to the
audit helpers in `app.audit.feature_mapping` and the shared redaction
pipeline.

Supported filters:

- date window
- `feature_area`
- `actor_role`
- `result`

### Role overview

The role overview route summarizes granted permissions and surface
boundaries from the backend auth model. It is descriptive only and does
not mutate roles or permissions.

## Caching

`service.py` keeps short-lived cache namespaces for:

- `platform_dashboard:insights`
- `platform_dashboard:audit`
- `platform_dashboard:roles`

Write-side flows in search/listing paths are responsible for invalidating
insights when underlying demand/supply inputs change.

## Audit trail

Platform dashboard reads write auth/audit events such as:

- `platform_dashboard.insights.read`
- `platform_dashboard.audit_logs.read`
- `platform_dashboard.roles.read`

Audit failures must never break the read path.

## Tests

Relevant coverage lives in:

- `backend/tests/unit/test_platform_dashboard_insights.py`
- `backend/tests/unit/test_platform_audit_logs.py`
- `backend/tests/unit/test_platform_role_overview.py`
- `backend/tests/integration/test_platform_dashboard_api.py`
- `backend/tests/integration/test_platform_audit_logs_api.py`
- `backend/tests/integration/test_platform_role_overview_api.py`
- `backend/tests/rbac/test_platform_dashboard_access.py`
- `backend/tests/rbac/test_platform_audit_access.py`
