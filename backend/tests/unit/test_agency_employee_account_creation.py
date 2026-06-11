from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agencies.models import AgencyEmployeeMembership
from app.common.tenant import TenantContext


@pytest.mark.asyncio
async def test_create_employee_creates_new_user_account():
    from app.agencies.service import AgencyService

    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=["manage_employees"],
    )

    created_user = MagicMock()
    created_user.id = uuid4()
    created_user.email = "support.new@agency.test"

    mock_users_repo = MagicMock()
    mock_users_repo.get_user_by_email = AsyncMock(return_value=None)
    mock_users_repo.create_user = AsyncMock(return_value=created_user)

    support_role = MagicMock()
    support_role.id = uuid4()

    mock_role_result = MagicMock()
    mock_role_result.scalar_one_or_none.return_value = support_role
    mock_session.execute = AsyncMock(return_value=mock_role_result)

    created_membership = AgencyEmployeeMembership(
        id=uuid4(),
        agency_tenant_id=mock_tenant.tenant_id,
        user_id=created_user.id,
        role_id=support_role.id,
        status="active",
        display_name="New Support Employee",
        work_email="support.new@agency.test",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_employee_repo = MagicMock()
    mock_employee_repo.create = AsyncMock(return_value=created_membership)

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.agencies.service.UsersRepository", lambda s: mock_users_repo)
        mp.setattr("app.agencies.service.AgencyEmployeeRepository", lambda s, t: mock_employee_repo)
        mp.setattr("app.agencies.service.write_domain_event_log", AsyncMock())

        service = AgencyService(mock_session, mock_tenant)
        result = await service.create_employee({
            "work_email": "support.new@agency.test",
            "display_name": "New Support Employee",
            "role_slug": "support_employee",
        })

        assert result.work_email == "support.new@agency.test"
        assert result.display_name == "New Support Employee"
        mock_users_repo.create_user.assert_called_once()
        mock_employee_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_employee_rejects_existing_user_email():
    from app.agencies.service import AgencyService
    from app.common.exceptions import ValidationError

    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=["manage_employees"],
    )

    existing_user = MagicMock()
    existing_user.id = uuid4()
    existing_user.email = "existing@agency.test"

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.agencies.service.UsersRepository", lambda s: MagicMock(
            get_user_by_email=AsyncMock(return_value=existing_user),
        ))

        service = AgencyService(mock_session, mock_tenant)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_employee({
                "work_email": "existing@agency.test",
                "display_name": "Existing User",
                "role_slug": "support_employee",
            })

        assert "already exists" in str(exc_info.value.detail)
