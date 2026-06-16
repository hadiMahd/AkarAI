import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.leads.service import LeadService
from app.leads.models import Lead
from app.common.tenant import TenantContext


@pytest.mark.anyio
async def test_list_tenant_leads_filtered_by_reviewed():
    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=["view_leads"],
    )
    
    mock_repo = MagicMock()
    mock_repo.list_by_tenant = AsyncMock(return_value=([], 0))
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.leads.service.LeadRepository", lambda s, t: mock_repo)
        
        service = LeadService(mock_session, mock_tenant)
        from app.common.pagination import PaginationRequest
        result = await service.list_tenant_leads(
            PaginationRequest(page=1, page_size=20),
            reviewed=False
        )
        
        mock_repo.list_by_tenant.assert_called_once()
        call_args = mock_repo.list_by_tenant.call_args
        assert call_args[1]["reviewed"] is False


@pytest.mark.anyio
async def test_list_tenant_leads_filtered_by_status():
    mock_session = AsyncMock()
    mock_tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=["view_leads"],
    )
    
    mock_repo = MagicMock()
    mock_repo.list_by_tenant = AsyncMock(return_value=([], 0))
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.leads.service.LeadRepository", lambda s, t: mock_repo)
        
        service = LeadService(mock_session, mock_tenant)
        from app.common.pagination import PaginationRequest
        result = await service.list_tenant_leads(
            PaginationRequest(page=1, page_size=20),
            status="reviewed"
        )
        
        mock_repo.list_by_tenant.assert_called_once()
        call_args = mock_repo.list_by_tenant.call_args
        assert call_args[1]["status"] == "reviewed"