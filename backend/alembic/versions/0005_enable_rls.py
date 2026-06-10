"""Enable RLS and enforce tenant/user-isolation policies on Phase 3+4 tables.

Uses SET LOCAL transaction-scoped context variables (set via set_config) for:
  app.tenant_id, app.user_id, app.role, app.is_platform_admin

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-10
"""

from uuid import uuid4

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

HELPER_SQL = """
CREATE FUNCTION rls_tenant_check(check_tenant_id uuid)
RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY INVOKER
AS $$
BEGIN
    RETURN current_setting('app.is_platform_admin', true) = 'true'
        OR (
            current_setting('app.tenant_id', true) IS NOT NULL
            AND current_setting('app.tenant_id', true) != ''
            AND check_tenant_id IS NOT NULL
            AND check_tenant_id = current_setting('app.tenant_id')::uuid
        );
END;
$$;

CREATE FUNCTION rls_user_check(check_user_id uuid)
RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY INVOKER
AS $$
BEGIN
    RETURN current_setting('app.is_platform_admin', true) = 'true'
        OR (
            current_setting('app.user_id', true) IS NOT NULL
            AND current_setting('app.user_id', true) != ''
            AND check_user_id IS NOT NULL
            AND check_user_id = current_setting('app.user_id')::uuid
        );
END;
$$;
"""

DROP_HELPER_SQL = """
DROP FUNCTION IF EXISTS rls_tenant_check(uuid);
DROP FUNCTION IF EXISTS rls_user_check(uuid);
"""

TENANT_POLICY = """
CREATE POLICY {table}_tenant_isolation ON {table}
FOR ALL
USING (rls_tenant_check(agency_tenant_id))
WITH CHECK (rls_tenant_check(agency_tenant_id));
"""

TENANT_POLICY_DROP = """
DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};
"""


# Tables with agency_tenant_id, tenant-only access
TENANT_TABLES = [
    "agency_profiles",
    "listing_photo_metadata",
    "listing_viewing_slots",
    "scheduled_viewing_status_history",
    "lead_spam_results",
    "lead_level_results",
    "lead_suggested_replies",
    "reviewed_lead_records",
]

# Tables with agency_tenant_id + user_id (tenant OR user access)
TENANT_USER_TABLES = [
    "scheduled_viewings",
    "leads",
]

# Tables with user_id only
USER_TABLES = [
    "saved_listings",
    "comparison_sessions",
    "refresh_sessions",
    "access_revocations",
]

LISTING_POLICIES = """
CREATE POLICY listing_public_read ON listings
FOR SELECT
USING (status = 'active');

CREATE POLICY listing_tenant_isolation ON listings
FOR SELECT
USING (rls_tenant_check(agency_tenant_id));

CREATE POLICY listing_tenant_insert ON listings
FOR INSERT
WITH CHECK (rls_tenant_check(agency_tenant_id));

CREATE POLICY listing_tenant_update ON listings
FOR UPDATE
USING (rls_tenant_check(agency_tenant_id))
WITH CHECK (rls_tenant_check(agency_tenant_id));

CREATE POLICY listing_tenant_delete ON listings
FOR DELETE
USING (rls_tenant_check(agency_tenant_id));
"""

DROP_LISTING_POLICIES = """
DROP POLICY IF EXISTS listing_public_read ON listings;
DROP POLICY IF EXISTS listing_tenant_isolation ON listings;
DROP POLICY IF EXISTS listing_tenant_insert ON listings;
DROP POLICY IF EXISTS listing_tenant_update ON listings;
DROP POLICY IF EXISTS listing_tenant_delete ON listings;
"""

TENANT_USER_POLICY = """
CREATE POLICY {table}_tenant_user_isolation ON {table}
FOR ALL
USING (rls_tenant_check(agency_tenant_id) OR rls_user_check(user_id))
WITH CHECK (rls_tenant_check(agency_tenant_id) OR rls_user_check(user_id));
"""

TENANT_USER_POLICY_DROP = """
DROP POLICY IF EXISTS {table}_tenant_user_isolation ON {table};
"""

USER_POLICY_INSERT = """
CREATE POLICY {table}_user_insert ON {table}
FOR INSERT
WITH CHECK (true);
"""

USER_POLICY_SELECT = """
CREATE POLICY {table}_user_select ON {table}
FOR SELECT
USING (rls_user_check(user_id));
"""

USER_POLICY_UPDATE = """
CREATE POLICY {table}_user_update ON {table}
FOR UPDATE
USING (rls_user_check(user_id));
"""

USER_POLICY_DELETE = """
CREATE POLICY {table}_user_delete ON {table}
FOR DELETE
USING (rls_user_check(user_id));
"""

USER_POLICY_DROP = """
DROP POLICY IF EXISTS {table}_user_insert ON {table};
DROP POLICY IF EXISTS {table}_user_select ON {table};
DROP POLICY IF EXISTS {table}_user_update ON {table};
DROP POLICY IF EXISTS {table}_user_delete ON {table};
"""

COMPARISON_ITEMS_POLICY = """
CREATE POLICY comparison_items_insert ON comparison_items
FOR INSERT
WITH CHECK (true);

CREATE POLICY comparison_items_via_session ON comparison_items
FOR SELECT
USING (
    rls_user_check(
        (SELECT cs.user_id FROM comparison_sessions cs WHERE cs.id = comparison_items.comparison_session_id)
    )
);

CREATE POLICY comparison_items_via_session_update ON comparison_items
FOR UPDATE
USING (
    rls_user_check(
        (SELECT cs.user_id FROM comparison_sessions cs WHERE cs.id = comparison_items.comparison_session_id)
    )
);

CREATE POLICY comparison_items_via_session_delete ON comparison_items
FOR DELETE
USING (
    rls_user_check(
        (SELECT cs.user_id FROM comparison_sessions cs WHERE cs.id = comparison_items.comparison_session_id)
    )
);
"""

DROP_COMPARISON_ITEMS_POLICY = """
DROP POLICY IF EXISTS comparison_items_insert ON comparison_items;
DROP POLICY IF EXISTS comparison_items_via_session ON comparison_items;
DROP POLICY IF EXISTS comparison_items_via_session_update ON comparison_items;
DROP POLICY IF EXISTS comparison_items_via_session_delete ON comparison_items;
"""

SEARCH_LOGS_POLICIES = """
CREATE POLICY search_logs_tenant_or_user_select ON search_logs
FOR SELECT
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(user_id)
);

CREATE POLICY search_logs_public_insert ON search_logs
FOR INSERT
WITH CHECK (true);

CREATE POLICY search_logs_tenant_or_user_update ON search_logs
FOR UPDATE
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(user_id)
);

CREATE POLICY search_logs_tenant_or_user_delete ON search_logs
FOR DELETE
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(user_id)
);
"""

DROP_SEARCH_LOGS_POLICIES = """
DROP POLICY IF EXISTS search_logs_tenant_or_user_select ON search_logs;
DROP POLICY IF EXISTS search_logs_public_insert ON search_logs;
DROP POLICY IF EXISTS search_logs_tenant_or_user_update ON search_logs;
DROP POLICY IF EXISTS search_logs_tenant_or_user_delete ON search_logs;
"""

NOTIFICATIONS_POLICIES = """
CREATE POLICY notifications_owner_select ON notifications
FOR SELECT
USING (
    rls_user_check(recipient_user_id)
    OR rls_tenant_check(tenant_id)
);

CREATE POLICY notifications_owner_insert ON notifications
FOR INSERT
WITH CHECK (true);

CREATE POLICY notifications_owner_update ON notifications
FOR UPDATE
USING (
    rls_user_check(recipient_user_id)
    OR rls_tenant_check(tenant_id)
);

CREATE POLICY notifications_owner_delete ON notifications
FOR DELETE
USING (
    rls_user_check(recipient_user_id)
    OR rls_tenant_check(tenant_id)
);
"""

DROP_NOTIFICATIONS_POLICIES = """
DROP POLICY IF EXISTS notifications_owner_select ON notifications;
DROP POLICY IF EXISTS notifications_owner_insert ON notifications;
DROP POLICY IF EXISTS notifications_owner_update ON notifications;
DROP POLICY IF EXISTS notifications_owner_delete ON notifications;
"""

DOMAIN_EVENT_LOGS_POLICIES = """
CREATE POLICY domain_event_logs_tenant_or_user_select ON domain_event_logs
FOR SELECT
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(actor_user_id)
);

CREATE POLICY domain_event_logs_insert ON domain_event_logs
FOR INSERT
WITH CHECK (true);

CREATE POLICY domain_event_logs_tenant_or_user_update ON domain_event_logs
FOR UPDATE
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(actor_user_id)
);

CREATE POLICY domain_event_logs_tenant_or_user_delete ON domain_event_logs
FOR DELETE
USING (
    rls_tenant_check(agency_tenant_id)
    OR rls_user_check(actor_user_id)
);
"""

DROP_DOMAIN_EVENT_LOGS_POLICIES = """
DROP POLICY IF EXISTS domain_event_logs_tenant_or_user_select ON domain_event_logs;
DROP POLICY IF EXISTS domain_event_logs_insert ON domain_event_logs;
DROP POLICY IF EXISTS domain_event_logs_tenant_or_user_update ON domain_event_logs;
DROP POLICY IF EXISTS domain_event_logs_tenant_or_user_delete ON domain_event_logs;
"""

AUDIT_LOGS_POLICIES = """
CREATE POLICY audit_logs_tenant_or_user_select ON audit_logs
FOR SELECT
USING (
    rls_tenant_check(tenant_id)
    OR rls_user_check(actor_user_id)
);

CREATE POLICY audit_logs_insert ON audit_logs
FOR INSERT
WITH CHECK (true);

CREATE POLICY audit_logs_tenant_or_user_update ON audit_logs
FOR UPDATE
USING (
    rls_tenant_check(tenant_id)
    OR rls_user_check(actor_user_id)
);

CREATE POLICY audit_logs_tenant_or_user_delete ON audit_logs
FOR DELETE
USING (
    rls_tenant_check(tenant_id)
    OR rls_user_check(actor_user_id)
);
"""

DROP_AUDIT_LOGS_POLICIES = """
DROP POLICY IF EXISTS audit_logs_tenant_or_user_select ON audit_logs;
DROP POLICY IF EXISTS audit_logs_insert ON audit_logs;
DROP POLICY IF EXISTS audit_logs_tenant_or_user_update ON audit_logs;
DROP POLICY IF EXISTS audit_logs_tenant_or_user_delete ON audit_logs;
"""


def upgrade() -> None:
    op.execute(HELPER_SQL)

    op.execute("DROP POLICY IF EXISTS agency_employee_memberships_tenant_isolation ON agency_employee_memberships")
    op.execute("ALTER TABLE agency_employee_memberships NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agency_employee_memberships DISABLE ROW LEVEL SECURITY")

    for table in TENANT_TABLES:
        _enable_and_force_rls(table)
        op.execute(TENANT_POLICY.format(table=table))

    for table in TENANT_USER_TABLES:
        _enable_and_force_rls(table)
        op.execute(TENANT_USER_POLICY.format(table=table))

    for table in USER_TABLES:
        _enable_and_force_rls(table)
        op.execute(USER_POLICY_INSERT.format(table=table))
        op.execute(USER_POLICY_SELECT.format(table=table))
        op.execute(USER_POLICY_UPDATE.format(table=table))
        op.execute(USER_POLICY_DELETE.format(table=table))

    _enable_and_force_rls("listings")
    op.execute(LISTING_POLICIES)

    _enable_and_force_rls("comparison_items")
    op.execute(COMPARISON_ITEMS_POLICY)

    _enable_and_force_rls("search_logs")
    op.execute(SEARCH_LOGS_POLICIES)

    _enable_and_force_rls("notifications")
    op.execute(NOTIFICATIONS_POLICIES)

    _enable_and_force_rls("domain_event_logs")
    op.execute(DOMAIN_EVENT_LOGS_POLICIES)

    _enable_and_force_rls("audit_logs")
    op.execute(AUDIT_LOGS_POLICIES)


def downgrade() -> None:
    tables_and_policy_drops = [
        *[(t, TENANT_POLICY_DROP.format(table=t), "rls_tenant") for t in TENANT_TABLES],
        *[(t, TENANT_USER_POLICY_DROP.format(table=t), "rls_tenant_user") for t in TENANT_USER_TABLES],
        *[(t, USER_POLICY_DROP.format(table=t), "rls_user") for t in USER_TABLES],
    ]

    for table, drop_sql, _category in tables_and_policy_drops:
        op.execute(drop_sql)
        _disable_rls(table)

    op.execute(DROP_LISTING_POLICIES)
    _disable_rls("listings")

    op.execute(DROP_COMPARISON_ITEMS_POLICY)
    _disable_rls("comparison_items")

    op.execute(DROP_SEARCH_LOGS_POLICIES)
    _disable_rls("search_logs")

    op.execute(DROP_NOTIFICATIONS_POLICIES)
    _disable_rls("notifications")

    op.execute(DROP_DOMAIN_EVENT_LOGS_POLICIES)
    _disable_rls("domain_event_logs")

    op.execute(DROP_AUDIT_LOGS_POLICIES)
    _disable_rls("audit_logs")

    op.execute(DROP_HELPER_SQL)


def _enable_and_force_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def _disable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
