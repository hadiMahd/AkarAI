"""Auth, RBAC, and Tenant Isolation

- users: add role_id, status, password_changed_at
- refresh_sessions: add last_used_at
- access_revocations: JTI revocation markers
- agency_tenants: minimal agency tenant records for security isolation
- agency_employee_memberships: employee-to-agency membership
- seed approved roles, permissions, role_permissions
- seed test actors for each approved role
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None

ROLES = [
    ("User", "user", "user", "Standard platform user"),
    ("Agency Admin", "agency_admin", "agency", "Agency tenant administrator"),
    ("Support Employee", "support_employee", "agency", "Agency support staff"),
    ("Platform Admin", "platform_admin", "platform", "Platform-wide administrator"),
]

AGENCY_PERMISSIONS = [
    ("agency:read", "agency", "Read agency information"),
    ("agency:update", "agency", "Update agency information"),
]

AUTH_PERMISSIONS = [
    ("auth:login", "auth", "Sign in to the platform"),
    ("auth:refresh", "auth", "Refresh access token"),
    ("auth:logout", "auth", "Sign out"),
    ("auth:password_reset", "auth", "Reset own password"),
    ("auth:session_revoke", "auth", "Revoke refresh sessions"),
    ("auth:employee_deactivate", "agency", "Deactivate agency employees"),
]

PLATFORM_PERMISSIONS = [
    ("platform:read", "platform", "Read platform data"),
    ("platform:manage", "platform", "Manage platform"),
]

SYSTEM_PERMISSIONS = [
    ("system:admin", "system", "System administration"),
]

ROLE_PERMISSION_MAP = {
    "user": [
        "auth:login", "auth:refresh", "auth:logout",
        "auth:password_reset",
    ],
    "agency_admin": [
        "auth:login", "auth:refresh", "auth:logout",
        "auth:password_reset", "auth:session_revoke",
        "auth:employee_deactivate",
        "agency:read", "agency:update",
    ],
    "support_employee": [
        "auth:login", "auth:refresh", "auth:logout",
        "auth:password_reset",
        "agency:read",
    ],
    "platform_admin": [
        "auth:login", "auth:refresh", "auth:logout",
        "auth:password_reset", "auth:session_revoke",
        "auth:employee_deactivate",
        "agency:read", "agency:update",
        "platform:read", "platform:manage",
        "system:admin",
    ],
}

SEED_USERS = [
    ("user@akarai.test", "User One", "user", "active"),
    ("agency.admin@akarai.test", "Agency Admin", "agency_admin", "active"),
    ("support@akarai.test", "Support Employee", "support_employee", "active"),
    ("platform.admin@akarai.test", "Platform Admin", "platform_admin", "active"),
]

SEED_TENANTS = [
    ("Alpha Agency", "alpha-agency"),
    ("Beta Agency", "beta-agency"),
]

SEED_PASSWORD_HASH = "$2b$12$voLEREVBh.b1cY7zV/LlD.9bnUtP7q6qjTwXnql0vcBhDcZEAjQZm"  # "Test1234!"


def upgrade() -> None:
    conn = op.get_bind()

    # Add new columns to users
    op.add_column("users", sa.Column("role_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, "users", "roles", ["role_id"], ["id"], ondelete="RESTRICT")
    op.add_column("users", sa.Column("status", sa.String(16), server_default="active", nullable=False))
    op.create_index("ix_users_status", "users", ["status"])
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))

    # Add last_used_at to refresh_sessions
    op.add_column("refresh_sessions", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))

    # Create access_revocations
    op.create_table(
        "access_revocations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("jti", sa.String(128), unique=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_access_revocations_jti", "access_revocations", ["jti"])
    op.create_index("ix_access_revocations_user_id", "access_revocations", ["user_id"])

    # Create agency_tenants
    op.create_table(
        "agency_tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), unique=True, nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agency_tenants_slug", "agency_tenants", ["slug"])
    op.create_index("ix_agency_tenants_status", "agency_tenants", ["status"])

    # Create agency_employee_memberships
    op.create_table(
        "agency_employee_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deactivation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agency_employee_memberships_tenant_id", "agency_employee_memberships", ["agency_tenant_id"])
    op.create_index("ix_agency_employee_memberships_user_id", "agency_employee_memberships", ["user_id"])
    op.create_index("ix_agency_employee_memberships_status", "agency_employee_memberships", ["status"])

    # Seed roles
    role_ids = {}
    for name, slug, scope, desc in ROLES:
        role_id = str(uuid.uuid4())
        role_ids[slug] = role_id
        conn.execute(
            sa.text(
                "INSERT INTO roles (id, name, slug, scope, description, created_at, updated_at) "
                "VALUES (:id, :name, :slug, :scope, :desc, :now, :now) "
                "ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name, scope=EXCLUDED.scope"
            ),
            {"id": role_id, "name": name, "slug": slug, "scope": scope, "desc": desc, "now": datetime.now(timezone.utc)},
        )

    # Seed permissions
    all_perms = AGENCY_PERMISSIONS + AUTH_PERMISSIONS + PLATFORM_PERMISSIONS + SYSTEM_PERMISSIONS
    perm_ids = {}
    for key, scope, desc in all_perms:
        perm_id = str(uuid.uuid4())
        perm_ids[key] = perm_id
        conn.execute(
            sa.text(
                "INSERT INTO permissions (id, key, scope, description, created_at, updated_at) "
                "VALUES (:id, :key, :scope, :desc, :now, :now) "
                "ON CONFLICT (key) DO UPDATE SET scope=EXCLUDED.scope"
            ),
            {"id": perm_id, "key": key, "scope": scope, "desc": desc, "now": datetime.now(timezone.utc)},
        )

    # Seed role_permissions
    for role_slug, perm_keys in ROLE_PERMISSION_MAP.items():
        rid = role_ids[role_slug]
        for pk in perm_keys:
            pid = perm_ids[pk]
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id, created_at) "
                    "VALUES (:rid, :pid, :now) "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ),
                {"rid": rid, "pid": pid, "now": datetime.now(timezone.utc)},
            )

    # Seed users
    user_ids = {}
    for email, name, role_slug, status in SEED_USERS:
        uid = str(uuid.uuid4())
        user_ids[email] = uid
        rid = role_ids[role_slug]
        conn.execute(
            sa.text(
                "INSERT INTO users (id, email, password_hash, name, role_id, is_active, status, created_at, updated_at) "
                "VALUES (:id, :email, :pw, :name, :rid, true, :status, :now, :now) "
                "ON CONFLICT (email) DO UPDATE SET password_hash=EXCLUDED.password_hash, role_id=EXCLUDED.role_id, status=EXCLUDED.status"
            ),
            {"id": uid, "email": email, "pw": SEED_PASSWORD_HASH, "name": name, "rid": rid, "status": status, "now": datetime.now(timezone.utc)},
        )

    # Seed agency tenants
    tenant_ids = {}
    for name, slug in SEED_TENANTS:
        tid = str(uuid.uuid4())
        tenant_ids[slug] = tid
        conn.execute(
            sa.text(
                "INSERT INTO agency_tenants (id, name, slug, status, created_at, updated_at) "
                "VALUES (:id, :name, :slug, 'active', :now, :now) "
                "ON CONFLICT (slug) DO NOTHING"
            ),
            {"id": tid, "name": name, "slug": slug, "now": datetime.now(timezone.utc)},
        )

    # Seed agency memberships: agency admin + support employee into alpha agency
    agency_admin_role = role_ids["agency_admin"]
    support_role = role_ids["support_employee"]
    alpha_tid = tenant_ids["alpha-agency"]

    for email, role_slug, role_id in [
        ("agency.admin@akarai.test", "agency_admin", role_ids["agency_admin"]),
        ("support@akarai.test", "support_employee", role_ids["support_employee"]),
    ]:
        conn.execute(
            sa.text(
                "INSERT INTO agency_employee_memberships (id, agency_tenant_id, user_id, role_id, status, created_at, updated_at) "
                "VALUES (:id, :tid, :uid, :rid, 'active', :now, :now) "
                "ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid.uuid4()), "tid": alpha_tid, "uid": user_ids[email], "rid": role_id, "now": datetime.now(timezone.utc)},
        )


def downgrade() -> None:
    op.drop_table("agency_employee_memberships")
    op.drop_table("agency_tenants")
    op.drop_table("access_revocations")
    op.drop_column("refresh_sessions", "last_used_at")
    op.drop_index("ix_users_status", "users")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_id_fkey")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "status")
    op.drop_column("users", "role_id")
