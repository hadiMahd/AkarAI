"""Add platform dashboard read permission and grant it to platform_admin.

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-17

This migration:
- Inserts the ``platform:dashboard_read`` permission row (idempotent).
- Grants it to the existing ``platform_admin`` role.
- Leaves the permission off every other role so non-platform-admins
  cannot read the marketplace dashboard.
"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | None = None
depends_on: str | None = None


PLATFORM_DASHBOARD_PERMISSION_KEY = "platform:dashboard_read"
PLATFORM_DASHBOARD_PERMISSION_DESC = "Read aggregate marketplace demand insights, redacted AI audit logs, and the role overview in the platform admin dashboard."


def upgrade() -> None:
    conn = op.get_bind()

    # Idempotently seed the permission row.
    perm_id = str(uuid.uuid4())
    conn.execute(
        sa.text(
            "INSERT INTO permissions (id, key, scope, description, created_at, updated_at) "
            "VALUES (:id, :key, 'platform', :desc, :now, :now) "
            "ON CONFLICT (key) DO UPDATE SET description=EXCLUDED.description"
        ),
        {
            "id": perm_id,
            "key": PLATFORM_DASHBOARD_PERMISSION_KEY,
            "desc": PLATFORM_DASHBOARD_PERMISSION_DESC,
            "now": datetime.now(timezone.utc),
        },
    )

    # Look up the (possibly pre-existing) permission id and the platform_admin role id.
    perm_row = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key = :key"),
        {"key": PLATFORM_DASHBOARD_PERMISSION_KEY},
    ).fetchone()
    if perm_row is None:
        return
    real_perm_id = perm_row[0]

    role_row = conn.execute(
        sa.text("SELECT id FROM roles WHERE slug = 'platform_admin'")
    ).fetchone()
    if role_row is None:
        return
    role_id = role_row[0]

    conn.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id, created_at) "
            "VALUES (:rid, :pid, :now) "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        ),
        {"rid": role_id, "pid": real_perm_id, "now": datetime.now(timezone.utc)},
    )


def downgrade() -> None:
    conn = op.get_bind()
    perm_row = conn.execute(
        sa.text("SELECT id FROM permissions WHERE key = :key"),
        {"key": PLATFORM_DASHBOARD_PERMISSION_KEY},
    ).fetchone()
    if perm_row is None:
        return
    perm_id = perm_row[0]
    conn.execute(
        sa.text("DELETE FROM role_permissions WHERE permission_id = :pid"),
        {"pid": perm_id},
    )
    conn.execute(
        sa.text("DELETE FROM permissions WHERE id = :pid"),
        {"pid": perm_id},
    )
