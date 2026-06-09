import pytest
from sqlalchemy import text


class TestPhase4Permissions:
    async def test_agency_profile_permissions_seeded(self, db_session):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM permissions WHERE key IN ('agency:profile_read', 'agency:profile_write')")
        )
        assert result.scalar() == 2

    async def test_listing_permissions_seeded(self, db_session):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM permissions WHERE key IN ('listing:create', 'listing:read', 'listing:update', 'listing:delete', 'listing:public_read', 'listing:photo_read', 'listing:photo_write', 'listing:save', 'listing:compare')")
        )
        assert result.scalar() == 9

    async def test_viewing_permissions_seeded(self, db_session):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM permissions WHERE key IN ('viewing:slot_read', 'viewing:slot_write', 'viewing:read', 'viewing:write', 'viewing:book')")
        )
        assert result.scalar() == 5

    async def test_lead_permissions_seeded(self, db_session):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM permissions WHERE key IN ('lead:read', 'lead:write', 'lead:inquiry')")
        )
        assert result.scalar() == 3

    async def test_user_has_phase4_permissions(self, db_session):
        result = await db_session.execute(
            text("""
                SELECT COUNT(*) FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.slug = 'user' AND p.key IN ('listing:public_read', 'listing:save', 'listing:compare', 'viewing:book', 'lead:inquiry', 'notification:read', 'notification:write')
            """)
        )
        assert result.scalar() == 7

    async def test_agency_admin_has_phase4_permissions(self, db_session):
        result = await db_session.execute(
            text("""
                SELECT COUNT(*) FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.slug = 'agency_admin' AND p.key IN ('listing:create', 'listing:update', 'listing:delete', 'lead:read', 'lead:write', 'viewing:slot_write', 'viewing:write', 'search:log_read', 'domain:log_read')
            """)
        )
        assert result.scalar() == 9

    async def test_support_employee_missing_admin_permissions(self, db_session):
        result = await db_session.execute(
            text("""
                SELECT COUNT(*) FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.slug = 'support_employee' AND p.key IN ('listing:create', 'listing:update', 'listing:delete', 'agency:profile_write', 'agency:employee_write', 'viewing:slot_write', 'viewing:write', 'lead:write')
            """)
        )
        assert result.scalar() == 0
