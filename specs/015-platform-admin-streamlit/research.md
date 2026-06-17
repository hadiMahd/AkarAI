# Research: Platform Admin Dashboard

## Decision 1: Reuse existing platform-admin auth with a dedicated dashboard permission

- **Decision**: Reuse the existing bearer-token platform-admin auth/session flow and add a dedicated dashboard access permission checked by both backend platform routes and the Streamlit entry flow.
- **Rationale**: The repo already has `platform_admin` role handling, `/auth/me`, and permission plumbing. Adding a dashboard-specific permission gives a second production-grade gate without creating a second login system or mixing platform-admin access with agency-admin access.
- **Alternatives considered**:
  - Separate Streamlit-only login: rejected because it duplicates auth/session behavior and raises maintenance cost.
  - Role check only: rejected because it gives less operational control than a dedicated permission gate.
  - Fresh re-auth before dashboard entry: rejected because the dashboard is read-only and the added friction is not justified in this phase.

## Decision 2: Serve Streamlit entirely from backend read APIs

- **Decision**: The Streamlit app will call dedicated backend platform routes for insights, audit logs, and role overview instead of opening direct database connections from the admin service.
- **Rationale**: This preserves one authorization layer, keeps redaction and pagination server-side, reuses existing RLS/context patterns where relevant, and avoids creating a second place where business logic can drift.
- **Alternatives considered**:
  - Direct database queries from Streamlit: rejected because it splits authorization, redaction, and aggregation logic across services.
  - Reusing agency dashboard endpoints: rejected because those are tenant-scoped and not designed for marketplace-wide reads.

## Decision 3: Keep insights aggregate-only in this phase

- **Decision**: Provide marketplace aggregate insights only. Do not add per-agency drill-down or tenant comparisons in phase 15.
- **Rationale**: This matches the clarified spec, keeps tenant boundary risk low, and is enough to satisfy the marketplace-demand oversight goal.
- **Alternatives considered**:
  - Aggregate plus per-agency drill-down: rejected because it expands scope and privacy sensitivity.
  - Aggregate plus tenant comparison views: rejected because it adds even more sensitive cross-tenant visibility than this phase requires.

## Decision 4: Compute demand gaps from search demand versus active inventory

- **Decision**: Define demand gaps as aggregate search demand counts compared against active listing supply counts for the same city, property type, and budget band within the selected date scope.
- **Rationale**: The repo already has search logs and listing inventory. This gives an explainable marketplace gap metric without introducing a new ML model or requiring hidden heuristics.
- **Alternatives considered**:
  - Manual curation of demand gaps: rejected because it is not scalable or reproducible.
  - AI-generated demand gap narratives only: rejected because the dashboard first needs deterministic numeric views.
  - Raw search popularity only: rejected because it does not answer the "gap" question without supply context.

## Decision 5: Keep audit investigations in-app and redacted only

- **Decision**: Platform admins may view filtered audit logs in the Streamlit dashboard, but may not export them in this phase.
- **Rationale**: This matches the clarified spec and keeps the first platform-audit surface simpler and safer while still useful for operational review.
- **Alternatives considered**:
  - Redacted export: rejected because it adds file-generation scope and secondary data-handling risk.
  - Full-detail export: rejected because it is unnecessary for this phase and weakens privacy boundaries.

## Decision 6: Extend the existing placeholder `admin/` service

- **Decision**: Upgrade the current `admin/app.py` Streamlit placeholder into a multi-section platform dashboard rather than creating a new admin application.
- **Rationale**: The repo already ships an `admin` Docker service and health-check page. Extending it is lower risk and fits the fixed stack.
- **Alternatives considered**:
  - New React admin app: rejected by constitution and project plan.
  - New Python admin service separate from Streamlit: rejected because Streamlit is already the fixed platform-admin surface.
