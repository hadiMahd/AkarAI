import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import engine, Base


class TestAuthMigrations:
    @pytest.mark.anyio
    async def test_roles_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'roles')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_permissions_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'permissions')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_access_revocations_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'access_revocations')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_agency_tenants_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agency_tenants')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_agency_employee_memberships_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agency_employee_memberships')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_users_has_role_id_column(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role_id')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_users_has_status_column(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'status')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_users_has_password_changed_at_column(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_changed_at')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_refresh_sessions_has_last_used_at_column(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'refresh_sessions' AND column_name = 'last_used_at')")
        )
        assert result.scalar() is True

    @pytest.mark.anyio
    async def test_seeded_roles_exist(self, db_session: AsyncSession):
        result = await db_session.execute(text("SELECT COUNT(*) FROM roles"))
        count = result.scalar()
        assert count >= 4

    @pytest.mark.anyio
    async def test_seeded_users_exist(self, db_session: AsyncSession):
        result = await db_session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        assert count >= 4

    @pytest.mark.anyio
    async def test_seeded_agency_tenants_exist(self, db_session: AsyncSession):
        result = await db_session.execute(text("SELECT COUNT(*) FROM agency_tenants"))
        count = result.scalar()
        assert count >= 2
