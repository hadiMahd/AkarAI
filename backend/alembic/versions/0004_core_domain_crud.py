"""Core Domain CRUD: Phase 4 domain tables, permissions, and seeds

- agency_profiles: public agency profile records
- listings: property listings with status lifecycle
- listing_photo_metadata: placeholder photo metadata
- listing_viewing_slots: viewing availability slots
- scheduled_viewings: user viewing bookings
- scheduled_viewing_status_history: append-only status history
- saved_listings: user saved listing records
- comparison_sessions: user comparison grouping
- comparison_items: listings in comparison sessions
- leads: structured listing inquiries
- lead_spam_results: placeholder spam classification
- lead_level_results: placeholder lead scoring
- lead_suggested_replies: placeholder AI replies
- reviewed_lead_records: audit-style review records
- search_logs: durable manual search records
- domain_event_logs: critical domain change audit log
- notifications: add read_at column
- seed Phase 4 permissions and role-permission assignments
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None

PHASE4_PERMISSIONS = [
    ("agency:profile_read", "agency", "Read own agency profile"),
    ("agency:profile_write", "agency", "Update own agency profile"),
    ("agency:employee_read", "agency", "List agency employees"),
    ("agency:employee_write", "agency", "Manage agency employees"),
    ("listing:create", "agency", "Create listings"),
    ("listing:read", "agency", "Read tenant listings"),
    ("listing:update", "agency", "Update listings"),
    ("listing:delete", "agency", "Archive/delete listings"),
    ("listing:public_read", "platform", "Search and view active listings"),
    ("listing:photo_read", "agency", "Read listing photo metadata"),
    ("listing:photo_write", "agency", "Manage listing photo metadata"),
    ("listing:save", "platform", "Save/unsave listings"),
    ("listing:compare", "platform", "Compare listings"),
    ("viewing:slot_read", "agency", "Read viewing slots"),
    ("viewing:slot_write", "agency", "Manage viewing slots"),
    ("viewing:read", "agency", "Read scheduled viewings"),
    ("viewing:write", "agency", "Update scheduled viewing status"),
    ("viewing:book", "platform", "Book a viewing"),
    ("lead:read", "agency", "Read tenant leads"),
    ("lead:write", "agency", "Update lead status/review"),
    ("lead:inquiry", "platform", "Submit listing inquiry"),
    ("notification:read", "platform", "Read notifications"),
    ("notification:write", "platform", "Mark notifications read/dismissed"),
    ("search:log_read", "agency", "Read tenant search logs"),
    ("domain:log_read", "agency", "Read tenant domain event logs"),
]

PHASE4_ROLE_PERMISSION_MAP = {
    "user": [
        "listing:public_read",
        "listing:save",
        "listing:compare",
        "viewing:book",
        "lead:inquiry",
        "notification:read",
        "notification:write",
    ],
    "agency_admin": [
        "agency:profile_read",
        "agency:profile_write",
        "agency:employee_read",
        "agency:employee_write",
        "listing:create",
        "listing:read",
        "listing:update",
        "listing:delete",
        "listing:public_read",
        "listing:photo_read",
        "listing:photo_write",
        "listing:save",
        "listing:compare",
        "viewing:slot_read",
        "viewing:slot_write",
        "viewing:read",
        "viewing:write",
        "viewing:book",
        "lead:read",
        "lead:write",
        "lead:inquiry",
        "notification:read",
        "notification:write",
        "search:log_read",
        "domain:log_read",
    ],
    "support_employee": [
        "agency:profile_read",
        "agency:employee_read",
        "listing:read",
        "listing:public_read",
        "listing:photo_read",
        "viewing:slot_read",
        "viewing:read",
        "lead:read",
        "notification:read",
        "notification:write",
        "search:log_read",
        "domain:log_read",
    ],
    "platform_admin": [
        "agency:profile_read",
        "agency:profile_write",
        "agency:employee_read",
        "agency:employee_write",
        "listing:create",
        "listing:read",
        "listing:update",
        "listing:delete",
        "listing:public_read",
        "listing:photo_read",
        "listing:photo_write",
        "listing:save",
        "listing:compare",
        "viewing:slot_read",
        "viewing:slot_write",
        "viewing:read",
        "viewing:write",
        "viewing:book",
        "lead:read",
        "lead:write",
        "lead:inquiry",
        "notification:read",
        "notification:write",
        "search:log_read",
        "domain:log_read",
    ],
}


def upgrade() -> None:
    conn = op.get_bind()

    # ── agency_profiles ──────────────────────────────────────────────
    op.create_table(
        "agency_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website_url", sa.String(512), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agency_profiles_tenant_id", "agency_profiles", ["agency_tenant_id"])
    op.create_index("ix_agency_profiles_status", "agency_profiles", ["status"])

    # ── listings ─────────────────────────────────────────────────────
    op.create_table(
        "listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("property_type", sa.String(64), nullable=True),
        sa.Column("listing_purpose", sa.String(32), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Integer(), nullable=True),
        sa.Column("area_size", sa.Numeric(12, 2), nullable=True),
        sa.Column("area_unit", sa.String(8), nullable=True),
        sa.Column("furnishing", sa.String(32), nullable=True),
        sa.Column("location_text", sa.String(512), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), server_default="inactive", nullable=False),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_listings_tenant_id", "listings", ["agency_tenant_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_status_tenant", "listings", ["status", "agency_tenant_id"])
    op.create_index("ix_listings_property_type", "listings", ["property_type"])
    op.create_index("ix_listings_listing_purpose", "listings", ["listing_purpose"])
    op.create_index("ix_listings_bedrooms", "listings", ["bedrooms"])
    op.create_index("ix_listings_bathrooms", "listings", ["bathrooms"])
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_area_size", "listings", ["area_size"])
    op.create_index("ix_listings_furnishing", "listings", ["furnishing"])

    # ── listing_photo_metadata ───────────────────────────────────────
    op.create_table(
        "listing_photo_metadata",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("caption", sa.String(512), nullable=True),
        sa.Column("alt_text", sa.String(512), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(16), server_default="pending_upload", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_listing_photo_metadata_listing_id", "listing_photo_metadata", ["listing_id"])
    op.create_index("ix_listing_photo_metadata_tenant_id", "listing_photo_metadata", ["agency_tenant_id"])

    # ── listing_viewing_slots ────────────────────────────────────────
    op.create_table(
        "listing_viewing_slots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("reserved_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_listing_viewing_slots_listing_id", "listing_viewing_slots", ["listing_id"])
    op.create_index("ix_listing_viewing_slots_tenant_id", "listing_viewing_slots", ["agency_tenant_id"])
    op.create_index("ix_listing_viewing_slots_status", "listing_viewing_slots", ["status"])

    # ── scheduled_viewings ───────────────────────────────────────────
    op.create_table(
        "scheduled_viewings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("viewing_slot_id", UUID(as_uuid=True), sa.ForeignKey("listing_viewing_slots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), server_default="scheduled", nullable=False),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_scheduled_viewings_tenant_id", "scheduled_viewings", ["agency_tenant_id"])
    op.create_index("ix_scheduled_viewings_listing_id", "scheduled_viewings", ["listing_id"])
    op.create_index("ix_scheduled_viewings_user_id", "scheduled_viewings", ["user_id"])
    op.create_index("ix_scheduled_viewings_status", "scheduled_viewings", ["status"])
    op.create_index("ix_scheduled_viewings_slot_id", "scheduled_viewings", ["viewing_slot_id"])

    # ── scheduled_viewing_status_history ─────────────────────────────
    op.create_table(
        "scheduled_viewing_status_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scheduled_viewing_id", UUID(as_uuid=True), sa.ForeignKey("scheduled_viewings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.String(32), nullable=True),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column("changed_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_viewing_status_history_viewing_id", "scheduled_viewing_status_history", ["scheduled_viewing_id"])
    op.create_index("ix_viewing_status_history_tenant_id", "scheduled_viewing_status_history", ["agency_tenant_id"])

    # ── saved_listings ───────────────────────────────────────────────
    op.create_table(
        "saved_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_saved_listings_user_id", "saved_listings", ["user_id"])
    op.create_index("ix_saved_listings_listing_id", "saved_listings", ["listing_id"])
    op.create_index("ix_saved_listings_user_listing", "saved_listings", ["user_id", "listing_id"], unique=True)

    # ── comparison_sessions ──────────────────────────────────────────
    op.create_table(
        "comparison_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_comparison_sessions_user_id", "comparison_sessions", ["user_id"])

    # ── comparison_items ─────────────────────────────────────────────
    op.create_table(
        "comparison_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("comparison_session_id", UUID(as_uuid=True), sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_comparison_items_session_id", "comparison_items", ["comparison_session_id"])
    op.create_index("ix_comparison_items_session_listing", "comparison_items", ["comparison_session_id", "listing_id"], unique=True)

    # ── leads ────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(16), server_default="new", nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_leads_tenant_id", "leads", ["agency_tenant_id"])
    op.create_index("ix_leads_listing_id", "leads", ["listing_id"])
    op.create_index("ix_leads_user_id", "leads", ["user_id"])
    op.create_index("ix_leads_status", "leads", ["status"])

    # ── lead_spam_results ────────────────────────────────────────────
    op.create_table(
        "lead_spam_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("label", sa.String(64), nullable=True),
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_spam_results_lead_id", "lead_spam_results", ["lead_id"])

    # ── lead_level_results ───────────────────────────────────────────
    op.create_table(
        "lead_level_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("level", sa.String(32), nullable=True),
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_level_results_lead_id", "lead_level_results", ["lead_id"])

    # ── lead_suggested_replies ───────────────────────────────────────
    op.create_table(
        "lead_suggested_replies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_suggested_replies_lead_id", "lead_suggested_replies", ["lead_id"])

    # ── reviewed_lead_records ────────────────────────────────────────
    op.create_table(
        "reviewed_lead_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewed_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_reviewed_lead_records_lead_id", "reviewed_lead_records", ["lead_id"])

    # ── search_logs ──────────────────────────────────────────────────
    op.create_table(
        "search_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("sort", sa.String(32), nullable=True),
        sa.Column("result_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_search_logs_tenant_id", "search_logs", ["agency_tenant_id"])
    op.create_index("ix_search_logs_user_id", "search_logs", ["user_id"])

    # ── domain_event_logs ────────────────────────────────────────────
    op.create_table(
        "domain_event_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_name", sa.String(128), nullable=False),
        sa.Column("aggregate_type", sa.String(64), nullable=True),
        sa.Column("aggregate_id", sa.String(64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_domain_event_logs_tenant_id", "domain_event_logs", ["agency_tenant_id"])
    op.create_index("ix_domain_event_logs_event_name", "domain_event_logs", ["event_name"])

    # ── notifications: add read_at ───────────────────────────────────
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))

    # ── Seed Phase 4 permissions ─────────────────────────────────────
    perm_ids = {}
    for key, scope, desc in PHASE4_PERMISSIONS:
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

    # ── Seed Phase 4 role-permission assignments ─────────────────────
    now = datetime.now(timezone.utc)
    for role_slug, perm_keys in PHASE4_ROLE_PERMISSION_MAP.items():
        role_row = conn.execute(
            sa.text("SELECT id FROM roles WHERE slug = :slug"),
            {"slug": role_slug},
        ).fetchone()
        if role_row is None:
            continue
        rid = role_row[0]
        for pk in perm_keys:
            pid = perm_ids.get(pk)
            if pid is None:
                perm_row = conn.execute(
                    sa.text("SELECT id FROM permissions WHERE key = :key"),
                    {"key": pk},
                ).fetchone()
                if perm_row is None:
                    continue
                pid = perm_row[0]
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id, created_at) "
                    "VALUES (:rid, :pid, :now) "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ),
                {"rid": rid, "pid": pid, "now": now},
            )


def downgrade() -> None:
    op.drop_column("notifications", "read_at")
    op.drop_table("domain_event_logs")
    op.drop_table("search_logs")
    op.drop_table("reviewed_lead_records")
    op.drop_table("lead_suggested_replies")
    op.drop_table("lead_level_results")
    op.drop_table("lead_spam_results")
    op.drop_table("leads")
    op.drop_table("comparison_items")
    op.drop_table("comparison_sessions")
    op.drop_table("saved_listings")
    op.drop_table("scheduled_viewing_status_history")
    op.drop_table("scheduled_viewings")
    op.drop_table("listing_viewing_slots")
    op.drop_table("listing_photo_metadata")
    op.drop_table("listings")
    op.drop_table("agency_profiles")
