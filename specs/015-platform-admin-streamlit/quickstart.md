# Quickstart: Platform Admin Dashboard

## Purpose

Validate that the platform admin Streamlit dashboard boots, enforces the extra dashboard access gate, shows aggregate marketplace demand insights, exposes redacted AI audit logs, and stays read-only.

## Prerequisites

- Docker Compose stack is available
- Backend and admin services can start successfully
- At least one authenticated `platform_admin` user exists
- The platform admin role has the dedicated dashboard access permission
- Search logs, listings, and audit logs exist so the dashboard has source data

## Start the stack

```bash
docker compose up -d postgres pgbouncer redis minio vault backend admin
```

## Validation Scenarios

### 1. Dashboard boot and entry gate

1. Open `http://localhost:8501`
2. Authenticate as a platform admin through the existing auth flow used by the app
3. Confirm the dashboard only loads when the actor is both:
   - `platform_admin`
   - granted the dedicated dashboard access permission
4. Confirm a platform admin without that permission is blocked from dashboard data
5. Confirm an `agency_admin` cannot load platform dashboard data even if authenticated elsewhere in the system

Expected outcome:
- Authorized platform admins can enter
- Agency admins and unauthorized platform actors are rejected cleanly

### 2. Aggregate demand insights

1. Choose a date range with known search activity
2. Load the demand insights view
3. Verify the dashboard shows:
   - popular searched areas
   - popular budgets
   - popular property types
   - demand gaps
   - search volume trends
4. Change the date range and apply `city`, `property_type`, and `listing_purpose` filters
5. Confirm all panels refresh to the same scope

Expected outcome:
- All panels stay in sync with the selected scope
- Empty or sparse ranges show explicit empty-state messaging instead of misleading values

### 3. Redacted AI audit log viewer

1. Open the AI audit logs view
2. Filter by date range, actor role, feature area, and result
3. Open at least one log detail row
4. Confirm sensitive fields remain redacted
5. Confirm there is no export action in this phase

Expected outcome:
- Audit logs are paginated, filterable, and read-only
- Redaction is preserved in the dashboard

### 4. Role overview

1. Open the role and permission overview section
2. Confirm the displayed roles and access boundaries match the backend role model
3. Confirm the page is read-only

Expected outcome:
- Platform admins can inspect role boundaries without mutating anything

## Contract References

- API contract: [contracts/platform-admin.openapi.yaml](./contracts/platform-admin.openapi.yaml)
- Data model: [data-model.md](./data-model.md)
- Feature spec: [spec.md](./spec.md)

## Suggested Test Commands

Run the backend tests covering the new platform routes and query services:

```bash
docker compose exec backend pytest backend/tests/unit backend/tests/integration backend/tests/rbac -q
```

Run admin app validation:

```bash
docker compose exec admin python -m pytest
```

If Streamlit-specific automated coverage is added under the admin package, run that suite from the same container.

## Expected End State

- Streamlit admin loads at `http://localhost:8501`
- Platform dashboard remains read-only
- Aggregate marketplace insights are visible
- AI audit logs are redacted and filterable
- Agency admins cannot access platform dashboard data
