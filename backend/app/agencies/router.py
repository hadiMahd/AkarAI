from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agencies.schemas import (
    AgencyProfileResponse,
    AgencyProfileUpdateRequest,
    AgencyEmployeeResponse,
    AgencyEmployeeCreateRequest,
    AgencyEmployeeUpdateRequest,
    PaginatedEmployeesResponse,
)
from app.agencies.service import AgencyService
from app.auth.dependencies import get_current_actor, get_tenant_context
from app.auth.permissions import PermissionKey
from app.common.dependencies import get_db_session, pagination_params
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext

router = APIRouter(prefix="/agencies", tags=["Agencies"])


@router.get("/me/profile", response_model=AgencyProfileResponse)
async def get_profile(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    return await svc.get_profile()


@router.put("/me/profile", response_model=AgencyProfileResponse)
async def update_profile(
    body: AgencyProfileUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    return await svc.update_profile(body.model_dump(exclude_none=True))


@router.get("/me/employees", response_model=PaginatedEmployeesResponse)
async def list_employees(
    page: int = 1,
    page_size: int = 20,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = AgencyService(db, tenant)
    result = await svc.list_employees(pp)
    return PaginatedEmployeesResponse(
        items=result.items,
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.post("/me/employees", response_model=AgencyEmployeeResponse, status_code=201)
async def create_employee(
    body: AgencyEmployeeCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    return await svc.create_employee(body.model_dump())


@router.get("/me/employees/{employee_id}", response_model=AgencyEmployeeResponse)
async def get_employee(
    employee_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    return await svc.get_employee(employee_id)


@router.patch("/me/employees/{employee_id}", response_model=AgencyEmployeeResponse)
async def update_employee(
    employee_id: UUID,
    body: AgencyEmployeeUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    return await svc.update_employee(employee_id, body.model_dump(exclude_none=True))


@router.delete("/me/employees/{employee_id}", status_code=204)
async def deactivate_employee(
    employee_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = AgencyService(db, tenant)
    await svc.deactivate_employee(employee_id)
