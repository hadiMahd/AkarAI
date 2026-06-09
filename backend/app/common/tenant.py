from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class TenantContext:
    actor_id: Optional[UUID] = None
    role: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    tenant_id: Optional[UUID] = None
    membership_id: Optional[UUID] = None
    is_platform_actor: bool = False
    request_id: Optional[str] = None
    source: str = "internal"


def require_tenant(context: Optional[TenantContext]) -> TenantContext:
    if context is None:
        raise PermissionError("Tenant context is required for this operation")
    if context.tenant_id is None and not context.is_platform_actor:
        raise PermissionError("Tenant-scoped access requires an active tenant membership")
    if context.role is None:
        raise PermissionError("Actor role is required for tenant-scoped access")
    return context


def ensure_tenant_match(context: Optional[TenantContext], resource_tenant_id: UUID) -> None:
    if context is None:
        raise PermissionError("Tenant context required")
    if context.is_platform_actor:
        return
    if context.tenant_id != resource_tenant_id:
        raise PermissionError("Cross-tenant access denied")
