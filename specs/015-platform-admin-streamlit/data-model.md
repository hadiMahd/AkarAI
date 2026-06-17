# Data Model: Platform Admin Dashboard

## Overview

This phase is primarily read-model driven. It reuses existing persisted entities such as `SearchLog`, `AuditLog`, `User`, `Role`, `Permission`, and listing inventory data, then adds platform-admin-oriented query shapes and one new permission concept for dashboard entry.

## Persisted Entities Reused

### Search Log

- **Purpose**: Source of marketplace demand activity.
- **Relevant fields**:
  - `id`
  - `created_at`
  - `source_mode`
  - `event_type`
  - `raw_query_redacted`
  - `transcript_redacted`
  - `intent`
  - `filters`
  - `result_count`
  - `provider`
  - `fallback_reason`
- **Usage in this phase**:
  - popular searched areas
  - popular budgets
  - popular property types
  - search volume trends
  - demand gap inputs

### Audit Log

- **Purpose**: Source of platform-level AI activity visibility.
- **Relevant fields**:
  - `id`
  - `request_id`
  - `actor_user_id`
  - `tenant_id`
  - `action`
  - `resource_type`
  - `resource_id`
  - `result`
  - `event_metadata`
  - `ip_address`
  - `user_agent`
  - `created_at`
- **Usage in this phase**:
  - paginated audit viewer
  - filters by feature area, actor role, date, and outcome
  - redacted detail drill-in

### Role / Permission / RolePermission

- **Purpose**: Source of access overview and dashboard-entry enforcement.
- **Relevant fields**:
  - role slug
  - permission key
  - role-permission membership
- **Usage in this phase**:
  - role overview page
  - dedicated dashboard access permission check

### Listing Inventory

- **Purpose**: Supply-side denominator for demand gap analysis.
- **Relevant fields**:
  - listing status
  - city / location attributes
  - property type
  - listing purpose
  - price / budget-aligned range
- **Usage in this phase**:
  - active supply counts by dimension
  - comparison against search demand aggregates

## New Permission Concept

### Platform Dashboard Access Permission

- **Type**: Permission key in the existing auth permission model
- **Purpose**: Second gate beyond `platform_admin` role for access to platform dashboard routes and Streamlit entry
- **Validation rules**:
  - actor must already be authenticated
  - actor role must be `platform_admin`
  - actor permissions must include the dedicated dashboard access permission
- **Notes**:
  - no standalone login system
  - no ad hoc hardcoded email allowlist in phase 15 unless explicitly added later

## Read Models / Response Shapes

### Dashboard Filter Scope

- **Fields**:
  - `date_from`
  - `date_to`
  - `range_preset`
  - `city`
  - `property_type`
  - `listing_purpose`
- **Validation rules**:
  - `date_from <= date_to`
  - requested range must be bounded to an allowed maximum window
  - `city`, `property_type`, and `listing_purpose` are optional filters and must use known enum/value sets already supported by marketplace search/listing data
- **Relationships**:
  - used by all insight and audit queries in this phase

### Demand Insight Snapshot

- **Fields**:
  - `generated_at`
  - `scope`
  - `search_volume_total`
  - `top_areas[]`
  - `top_budget_bands[]`
  - `top_property_types[]`
  - `demand_gaps[]`
- **Validation rules**:
  - all panels in one response must use the same scope
  - empty datasets return explicit zero/empty-state payloads, not null-only shapes

### Search Volume Trend Point

- **Fields**:
  - `bucket_start`
  - `bucket_end`
  - `search_count`
- **Validation rules**:
  - points must be returned in chronological order
  - bucket granularity must be consistent within one response

### Ranked Segment

- **Fields**:
  - `label`
  - `search_count`
  - `share`
  - `rank`
- **Usage**:
  - top searched areas
  - top budget bands
  - top property types

### Demand Gap Entry

- **Fields**:
  - `dimension_type` (`city`, `property_type`, `budget_band`, or combined segment)
  - `dimension_label`
  - `demand_count`
  - `supply_count`
  - `gap_score`
  - `gap_direction`
- **Validation rules**:
  - `demand_count >= 0`
  - `supply_count >= 0`
  - `gap_score` derived deterministically from demand versus supply
- **Notes**:
  - phase 15 keeps this aggregate-only

### Platform Audit Log View

- **Fields**:
  - `id`
  - `created_at`
  - `actor_role`
  - `actor_user_id`
  - `tenant_scope_label`
  - `feature_area`
  - `action`
  - `result`
  - `redacted_metadata`
- **Validation rules**:
  - metadata must already be sanitized/redacted before reaching Streamlit
  - result values must stay within known audit result vocabulary

### Role Access Summary

- **Fields**:
  - `role_slug`
  - `display_name`
  - `granted_permissions[]`
  - `surface_access[]`
  - `restricted_surfaces[]`
- **Usage**:
  - read-only platform access overview page

## Relationships

- `Dashboard Filter Scope` applies to `Demand Insight Snapshot` and `Platform Audit Log View`.
- `Demand Insight Snapshot` is derived from `SearchLog` plus active listing inventory aggregates.
- `Platform Audit Log View` is derived from `AuditLog` plus actor role lookup.
- `Role Access Summary` is derived from `Role`, `Permission`, and `RolePermission`.
- `Platform Dashboard Access Permission` is checked before any platform dashboard read model is returned.

## State / Lifecycle Notes

- This phase adds no new end-user transactional lifecycle.
- Audit views are append-only from the dashboard perspective.
- Insight snapshots are computed on read for the selected scope unless a later phase introduces materialized snapshots or scheduled aggregation.
