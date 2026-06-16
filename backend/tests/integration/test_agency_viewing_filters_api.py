import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.viewings.service import ViewingBookingService
from app.viewings.models import ScheduledViewing
from app.common.tenant import TenantContext
from app.common.exceptions import ForbiddenError


@pytest.mark.anyio
async def test_list_tenant_viewings_with_filters():
    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=["view_viewings"],
    )
    
    mock_repo = MagicMock()
    mock_repo.list_by_tenant = AsyncMock(return_value=([], 0))
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.viewings.service.ScheduledViewingRepository", lambda s, t: mock_repo)
        
        service = ViewingBookingService(mock_session, mock_tenant)
        from app.common.pagination import PaginationRequest
        result = await service.list_tenant_viewings(
            PaginationRequest(page=1, page_size=20),
            status="scheduled",
            listing_id=uuid4(),
            date_from="2026-01-01",
            date_to="2026-12-31"
        )
        
        mock_repo.list_by_tenant.assert_called_once()
        call_args = mock_repo.list_by_tenant.call_args
        assert call_args[1]["status"] == "scheduled"
        assert call_args[1]["listing_id"] is not None
        assert call_args[1]["date_from"] == "2026-01-01"
        assert call_args[1]["date_to"] == "2026-12-31"


@pytest.mark.anyio
async def test_update_viewing_status_forbidden_for_support_employee():
    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="support_employee",
        permissions=["view_viewings"],
    )
    
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=MagicMock(
        agency_tenant_id=mock_tenant.tenant_id
    ))
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.viewings.service.ScheduledViewingRepository", lambda s, t: mock_repo)
        
        service = ViewingBookingService(mock_session, mock_tenant)
        
        with pytest.raises(ForbiddenError) as exc_info:
            await service.update_viewing_status(uuid4(), "completed")
        
        assert "Support employees cannot modify viewing schedules" in str(exc_info.value.detail)